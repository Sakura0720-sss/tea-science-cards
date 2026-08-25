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

【资料】
{context}

【问题】
{question}

【回答】"""

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


def ask(question: str) -> dict:
    """输入问题，返回 {answer, sources}。"""
    docs = hybrid_search(question)

    context = "\n\n".join(
        f"（来源：{d.metadata.get('source', '未知')}）\n{d.page_content}" for d in docs
    )
    sources = [d.metadata.get("source", "未知") for d in docs]

    llm = get_llm()
    prompt = PROMPT_TEMPLATE.format(context=context, question=question)
    answer = llm.invoke(prompt).content

    return {"answer": answer, "sources": sources}
