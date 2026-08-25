"""知识文档加载、清洗与切块（chunking）。

约定：
- 把知识文档（.txt / .md）放进 data/knowledge/ 目录
- 以「_」开头的文件会被忽略（例如 _模板.md 是说明文件，不会被入库）

清洗策略（针对国标 OCR 文本，封面/前言已在 OCR 阶段跳过）：
- 去掉「2 规范性引用文件」整章（大段 GB 编号，对问答无价值）
- 按章节号切块，保证「产品定义/分类」这类知识点完整不被切断
"""
import re
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document

from app import config

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge"
SUPPORTED_SUFFIX = {".txt", ".md"}

# 章节号：1 / 1.1 / 3.1 / 4.2.1 等，行首出现且后面跟中文
_CHAPTER_RE = re.compile(r"^(\d+(?:\.\d+)*)\s*[一-鿿]")


def clean_text(text: str) -> str:
    """去掉「规范性引用文件」整章（从该标题到下一个正文章节之前）。"""
    lines = text.splitlines()
    out = []
    in_ref_section = False
    for line in lines:
        s = line.strip()
        if not s:
            continue
        # 进入引用文件清单
        if re.match(r"^2?\s*规范性引用文件", s):
            in_ref_section = True
            continue
        # 遇到正文章节（3 产品 / 4 要求 / 5 试验方法…）→ 退出
        if in_ref_section and re.match(r"^[3-9]\d*\s*[一-鿿]", s):
            in_ref_section = False
        if in_ref_section:
            continue
        out.append(s)
    return "\n".join(out)


def load_documents():
    """读取 data/knowledge/ 下所有 .txt/.md 文件（跳过 _ 开头），并清洗。"""
    docs = []
    if not KNOWLEDGE_DIR.exists():
        return docs
    for path in sorted(KNOWLEDGE_DIR.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIX and not path.name.startswith("_"):
            loader = TextLoader(str(path), encoding="utf-8")
            loaded = loader.load()
            for d in loaded:
                d.page_content = clean_text(d.page_content)
            docs.extend(loaded)
    return docs


def split_documents(docs):
    """按国标章节切块，保证每个知识点（定义/分类/感官品质）完整。

    同时从文件名提取茶名，作为主题标签前置到每个 chunk，
    解决「茶名关键词在切块后被稀释、检索命不中正确文档」的问题。
    """
    chunks = []
    for d in docs:
        tea_name = _extract_tea_name(d.metadata.get("source", ""))
        for text in _split_by_chapter(d.page_content):
            if _keep_chunk(text):
                # 茶名标签前置，增强检索命中
                tagged = f"【主题：{tea_name}】\n{text}" if tea_name else text
                chunks.append(Document(page_content=tagged, metadata=dict(d.metadata)))
    return chunks


def _extract_tea_name(source: str) -> str:
    """从文件名提取茶名，如 OCR_GBT18650_...龙井茶.md → 龙井茶。

    文件名格式：OCR_<标准号>_<标准号>-<年份><茶名>.md
    取最后一个下划线之后的部分，去掉标准号/年份/通用修饰词。
    """
    stem = Path(source).stem           # 去 .md
    if stem.startswith("OCR_"):
        stem = stem[4:]
    # 取最后一个「_」之后的内容（茶名部分）
    name = stem.rsplit("_", 1)[-1]
    # 去掉开头的标准号（如 GBT18650-2008）和通用修饰词
    name = re.sub(r"^GB\s*/?\s*T?\s*\d+(\.\d+)*-\d+\s*", "", name)
    name = re.sub(r"^(地理标志产品|地理标志产品质量要求)\s*", "", name)
    name = re.sub(r"^(质量要求|产品|第\d+部分[:：])\s*", "", name)
    name = re.sub(r"^(乌龙茶|绿茶|红茶|白茶|黑茶|黄茶|紧压白茶|台式乌龙茶)\s*", "", name)
    name = re.sub(r"^第\d+部分[:：]\s*", "", name)
    name = name.strip()
    return name if name and re.search(r"[一-鿿]", name) else ""


def _split_by_chapter(text: str):
    """按章节号切块。子章节过短会合并到相邻块，保证每块信息量足够。"""
    lines = text.splitlines()
    sections = []      # 每个章节的文本
    cur = []

    for line in lines:
        s = line.strip()
        if _CHAPTER_RE.match(s):
            if cur:
                sections.append("\n".join(cur))
            cur = [s]
        else:
            cur.append(s)
    if cur:
        sections.append("\n".join(cur))

    # 合并过短的相邻章节，达到 CHUNK_SIZE 才切出一个块
    result = []
    buf = []
    for sec in sections:
        buf.append(sec)
        if sum(len(b) for b in buf) >= config.CHUNK_SIZE:
            result.append("\n\n".join(buf))
            buf = []
    if buf:
        result.append("\n\n".join(buf))
    return result


def _keep_chunk(text: str) -> bool:
    """过滤无问答价值的纯碎片块（如表格单元格堆叠）。"""
    if "。" in text or "；" in text:
        return True
    if len(text) < 60:
        return False
    return True
