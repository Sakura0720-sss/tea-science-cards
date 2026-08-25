"""LLM 生成模型封装（DeepSeek，OpenAI 兼容）。"""
from langchain_openai import ChatOpenAI

from app import config


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=config.LLM_MODEL,
        base_url=config.LLM_BASE_URL,
        api_key=config.LLM_API_KEY,
        temperature=0.3,  # 偏低，减少瞎编
    )
