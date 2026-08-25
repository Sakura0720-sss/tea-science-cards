"""全局配置：从 .env 读取，未配置时使用默认值。"""
import os
import sys
from pathlib import Path

# Windows 终端默认 GBK，强制 stdout/stderr 用 UTF-8，避免 print emoji/中文报错
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

# 项目根目录 = 本文件上两级（tea-rag/）
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


# ===== LLM 生成模型（DeepSeek）=====
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

# ===== Embedding 向量模型 =====
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "https://api.siliconflow.cn/v1")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")

# ===== 向量库 =====
CHROMA_DIR = os.getenv("CHROMA_DIR", str(BASE_DIR / "chroma_db"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "tea_knowledge")

# ===== 切块 / 检索参数 =====
CHUNK_SIZE = _get_int("CHUNK_SIZE", 500)
CHUNK_OVERLAP = _get_int("CHUNK_OVERLAP", 100)
TOP_K = _get_int("TOP_K", 4)


def check_config() -> None:
    """启动前检查密钥是否已配置，缺失则给出清晰提示。"""
    missing = []
    if not LLM_API_KEY:
        missing.append("LLM_API_KEY（DeepSeek 密钥）")
    if not EMBEDDING_API_KEY:
        missing.append("EMBEDDING_API_KEY（Embedding 密钥）")
    if missing:
        raise RuntimeError(
            "缺少以下配置，请在 .env 中填写（可参考 .env.example）：\n  - "
            + "\n  - ".join(missing)
        )
