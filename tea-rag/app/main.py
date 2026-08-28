"""FastAPI 入口：提供 RAG 问答接口。"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import config
from app.rag import ask

app = FastAPI(title="茶叶知识 RAG 问答服务", version="0.1.0")

# 允许跨域（后续 Vue 前端会直接调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str  # user / assistant
    content: str


class AskRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []  # 多轮对话历史，可选


class AskResponse(BaseModel):
    answer: str
    sources: list[str]


@app.get("/health")
def health():
    return {"status": "ok", "service": "tea-rag"}


@app.post("/ask", response_model=AskResponse)
def ask_endpoint(req: AskRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")
    try:
        history = [m.model_dump() for m in req.history]
        return ask(req.question, history)
    except RuntimeError as e:
        # 密钥缺失等配置错误，返回清晰提示而非 500 堆栈
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答失败：{e}")
