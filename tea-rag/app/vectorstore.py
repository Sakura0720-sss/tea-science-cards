"""向量库（Chroma）：入库与查询。"""
from langchain_chroma import Chroma

from app import config
from app.chunking import load_documents, split_documents
from app.embeddings import get_embeddings


def get_vectorstore() -> Chroma:
    """打开已持久化的向量库（用于查询）。"""
    return Chroma(
        collection_name=config.COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=config.CHROMA_DIR,
    )


def build_index() -> int:
    """把 data/knowledge/ 下所有文档切块、向量化、写入 Chroma。返回写入的块数。"""
    docs = load_documents()
    if not docs:
        print("⚠️  未找到知识文档。请先在 data/knowledge/ 放入 .txt/.md 文件（参考 _模板.md）。")
        return 0

    chunks = split_documents(docs)
    print(f"📄 读取文档 {len(docs)} 篇，切块 {len(chunks)} 块，开始向量化入库...")

    Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        collection_name=config.COLLECTION_NAME,
        persist_directory=config.CHROMA_DIR,
    )
    return len(chunks)
