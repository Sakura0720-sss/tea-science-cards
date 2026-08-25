"""向量模型封装。默认走云端 OpenAI 兼容接口，可换成本地 bge-m3。"""
from langchain_openai import OpenAIEmbeddings

from app import config


def get_embeddings() -> OpenAIEmbeddings:
    """返回用于「入库」和「检索」的同一个 embedding 实例。

    注意：入库和检索必须用同一个模型，否则向量空间对不上，检索会随机。
    """
    return OpenAIEmbeddings(
        model=config.EMBEDDING_MODEL,
        base_url=config.EMBEDDING_BASE_URL,
        api_key=config.EMBEDDING_API_KEY,
    )
