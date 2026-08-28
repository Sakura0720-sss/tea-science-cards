"""RAG 主流程：混合检索（向量 + 关键词）→ 拼 prompt → 生成。"""
import re

from app import config
from app.llm import get_llm
from app.vectorstore import get_vectorstore

PROMPT_TEMPLATE = """你是专业的茶叶知识助手。请**只根据**下面提供的资料回答用户问题。

要求：
1. 如果资料中没有相关信息，直接回答"抱歉，我目前的知识库中没有相关资料"，不要编造。
2. 回答准确、简洁，使用中文。
3. 回答末尾用「参考：」列出本次用到的来源。

【历史对话】
{history}

【资料】
{context}

【问题】
{question}

【回答】"""

# 问题改写 prompt：把带指代的多轮提问改写成独立完整的问题
REWRITE_PROMPT = """下面是用户和茶叶助手的对话历史，以及用户的最新问题。

请把最新问题改写成**独立完整的问题**，消解其中的指代（如「它」「这个」「那种茶」等要替换成具体茶名），使其脱离上下文也能看懂。

只输出改写后的问题，不要输出任何其他文字。

【历史对话】
{history}

【最新问题】
{question}

【改写后的问题】"""

# 查询中的停用词/疑问词，提取关键词时排除
_QUERY_STOPWORDS = {
    "什么", "怎么", "哪里", "为什么", "哪些", "如何", "是否", "吗", "呢", "啊",
    "是", "的", "了", "有", "在", "和", "与", "或", "跟", "及", "等",
    "属于", "关于", "请问", "茶类", "种类", "区别", "特点", "特征", "介绍",
}

# 茶名词典缓存（从文件名动态加载，避免硬编码）
_TEA_NAMES: list[str] = []


def _load_tea_names() -> list[str]:
    """从 knowledge 文件名提取所有茶名，构建词典。"""
    global _TEA_NAMES
    if _TEA_NAMES:
        return _TEA_NAMES
    from app.chunking import KNOWLEDGE_DIR, _extract_tea_name
    names = []
    for p in sorted(KNOWLEDGE_DIR.glob("OCR_*.md")):
        n = _extract_tea_name(str(p))
        if n and n not in names:
            names.append(n)
    _TEA_NAMES = names
    return names


def _extract_keywords(question: str) -> list[str]:
    """从查询中提取关键词（茶名 + 概念词片段）。

    1) 茶名词典做子串匹配（如「铁观音」「安吉白茶」），长词优先。
    2) 删掉停用词后，对剩余中文取连续片段，
       以覆盖词典未收录的概念词（如「茶多酚」「紧压茶」「熟茶」）。
    """
    kws = []
    names = sorted(_load_tea_names(), key=len, reverse=True)  # 长词优先
    for name in names:
        if name in question and name not in kws:
            kws.append(name)

    # 先把停用词从查询里删掉，再提取连续中文片段
    cleaned = question
    for sw in sorted(_QUERY_STOPWORDS, key=len, reverse=True):
        cleaned = cleaned.replace(sw, " ")
    tokens = re.findall(r"[一-鿿]{2,}", cleaned)
    for t in tokens:
        if t in _QUERY_STOPWORDS:
            continue
        # 若已命中茶名包含该片段，跳过（避免重复）
        if any(t in k for k in kws):
            continue
        if t not in kws:
            kws.append(t)
    return kws


def _keyword_score(doc_text: str, keywords: list[str]) -> int:
    """统计 chunk 命中关键词的次数（含【主题：】标签的命中权重更高）。"""
    score = 0
    for kw in keywords:
        score += doc_text.count(kw)
    # 主题标签命中加权（【主题：铁观音】这类精确匹配）
    for kw in keywords:
        if f"主题：{kw}" in doc_text:
            score += 10
    return score


def _all_documents():
    """取向量库全部 chunk（含文档文本和元数据）。127 个 chunk 全扫很快。"""
    store = get_vectorstore()
    col = store._collection
    data = col.get(include=["documents", "metadatas"])
    from langchain_core.documents import Document
    docs = []
    for text, meta in zip(data["documents"], data["metadatas"]):
        docs.append(Document(page_content=text, metadata=meta))
    return docs


def hybrid_search(question: str, k: int = None):
    """混合检索：关键词路 + 向量路独立召回，合并去重。

    - 关键词路：全库扫描含查询关键词的 chunk，按命中次数排序（专有名词精准匹配）
    - 向量路：语义相似度 top-N（覆盖同义/宽泛问题）
    - 关键词命中的排最前，向量结果补在后面
    """
    k = k or config.TOP_K
    store = get_vectorstore()
    keywords = _extract_keywords(question)

    # 向量路
    vector_docs = store.similarity_search(question, k=30)

    # 关键词路（全库扫描）
    kw_docs = []
    if keywords:
        for d in _all_documents():
            score = _keyword_score(d.page_content, keywords)
            if score > 0:
                kw_docs.append((score, d))
        kw_docs.sort(key=lambda x: -x[0])

    # 合并：关键词命中的在前，向量结果补后，去重
    seen = set()
    result = []
    for _, d in kw_docs:
        key = d.page_content[:50]
        if key not in seen:
            seen.add(key)
            result.append(d)
    for d in vector_docs:
        key = d.page_content[:50]
        if key not in seen:
            seen.add(key)
            result.append(d)
        if len(result) >= k:
            break
    return result[:k]


def _format_history(history: list[dict]) -> str:
    """把对话历史格式化成文本。history 形如 [{"role": "user", "content": "..."}, ...]"""
    if not history:
        return "（无）"
    lines = []
    for msg in history:
        role = "用户" if msg.get("role") == "user" else "助手"
        content = msg.get("content", "").strip()
        if content:
            lines.append(f"{role}：{content}")
    return "\n".join(lines) if lines else "（无）"


def _rewrite_question(question: str, history: list[dict]) -> str:
    """把带指代的问题改写成独立完整的问题。无历史时直接返回原问题。"""
    if not history:
        return question
    llm = get_llm()
    prompt = REWRITE_PROMPT.format(
        history=_format_history(history[-6:]),  # 只保留最近 6 条，避免太长
        question=question,
    )
    try:
        rewritten = llm.invoke(prompt).content.strip()
        # 去掉可能的引号包裹
        rewritten = rewritten.strip('"').strip("“”").strip()
        return rewritten if rewritten else question
    except Exception:
        return question


def ask(question: str, history: list[dict] = None) -> dict:
    """输入问题（可选历史），返回 {answer, sources}。"""
    history = history or []

    # 1) 问题改写：消解「它」「这个」等指代，让检索更准
    search_question = _rewrite_question(question, history)

    # 2) 用改写后的问题检索
    docs = hybrid_search(search_question)

    context = "\n\n".join(
        f"（来源：{d.metadata.get('source', '未知')}）\n{d.page_content}" for d in docs
    )
    sources = [d.metadata.get("source", "未知") for d in docs]

    # 3) 生成答案（prompt 带上历史）
    llm = get_llm()
    prompt = PROMPT_TEMPLATE.format(
        history=_format_history(history[-6:]),
        context=context,
        question=question,
    )
    answer = llm.invoke(prompt).content

    return {"answer": answer, "sources": sources}
