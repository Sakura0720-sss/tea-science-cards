# 茶叶知识 RAG 问答服务

基于 FastAPI + LangChain + Chroma 的茶叶知识 RAG 问答智能体。

## 架构流程

```
data/knowledge/*.md  →  切块(chunking)  →  向量化(embedding)  →  Chroma 向量库
                                                                        ↓
用户问题  →  向量化  →  相似度检索 top-k  →  拼 prompt  →  DeepSeek 生成答案
```

## 目录结构

```
tea-rag/
├── app/
│   ├── config.py        # 配置（读 .env）
│   ├── chunking.py      # 文档加载 + 切块
│   ├── embeddings.py    # 向量模型
│   ├── vectorstore.py   # Chroma 入库/查询
│   ├── llm.py           # DeepSeek 生成模型
│   ├── rag.py           # RAG 主流程（检索→生成）
│   └── main.py          # FastAPI 入口（/ask、/health）
├── scripts/
│   └── build_index.py   # 建索引脚本
├── data/knowledge/      # 知识文档放这里（.txt/.md）
├── requirements.txt
└── .env.example
```

## 快速开始

### 1. 创建虚拟环境并装依赖

```bash
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置密钥

```bash
copy .env.example .env
```

编辑 `.env`，填入：
- `LLM_API_KEY` —— DeepSeek 密钥（https://platform.deepseek.com）
- `EMBEDDING_API_KEY` —— SiliconFlow 密钥（https://siliconflow.cn，用免费额度）

### 3. 放知识文档

把茶叶知识 `.md` / `.txt` 文件放进 `data/knowledge/`（参考 `_模板.md` 的格式）。

### 4. 建索引

```bash
.venv\Scripts\python scripts\build_index.py
```

### 5. 启动服务

```bash
.venv\Scripts\python -m uvicorn app.main:app --reload
```

- 接口文档（Swagger）：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/health

### 6. 测试问答

浏览器打开 `/docs`，或命令行：

```bash
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -d "{\"question\":\"西湖龙井的香气特征是什么\"}"
```

## 切换向量模型

| 方案 | 修改 `.env` |
|------|------------|
| SiliconFlow 云端 bge-m3（默认） | `EMBEDDING_MODEL=BAAI/bge-m3` |
| 通义 text-embedding-v3 | `EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`<br>`EMBEDDING_MODEL=text-embedding-v3` |
| 本地 bge-m3（免费离线） | 见下文 |

### 切到本地 bge-m3（免费、离线、中文最强）

1. 安装：
```bash
pip install sentence-transformers
```
2. 把 `app/embeddings.py` 里 `get_embeddings()` 替换为：
```python
from langchain_huggingface import HuggingFaceEmbeddings

def get_embeddings():
    return HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
```
3. **重新建索引**（换模型必须重建，否则向量空间对不上）：
```bash
.venv\Scripts\python scripts\build_index.py
```

## 常见问题

- **报 `缺少以下配置`**：`.env` 没填密钥，或 `.env` 没放在 `tea-rag/` 根目录。
- **建索引时 `未找到知识文档`**：`data/knowledge/` 里没有 `.txt/.md`，或文件名以下划线开头（会被忽略）。
- **换了向量模型后检索不准**：换了模型必须重新跑 `build_index.py`。
