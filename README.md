# 中国茶科学卡片（Tea Science Cards）

一个面向茶叶知识的全栈项目：**国标知识库 → RAG 智能问答 → 茶科学卡片可视化**。

## 项目组成

```
D:\BMCY
├── tea-rag/         Python RAG 服务（FastAPI + LangChain + Chroma + DeepSeek）
├── tea-backend/     Java 后端（Spring Boot 4 + SQLite/JPA）
├── tea-frontend/    uni-app 前端（Vue3，选茶卡片 + 成分可视化 + 智能问答）
├── start-all.bat    一键启动后端（RAG + SpringBoot）
└── stop-all.bat     一键停止
```

| 服务 | 端口 | 技术栈 | 说明 |
|------|------|--------|------|
| RAG 服务 | 8000 | FastAPI + LangChain + Chroma + DeepSeek | 茶叶知识问答 |
| 后端 | 8080 | Spring Boot 4 + JPA + SQLite | 茶品/成分/风味数据、硬件数据接收 |
| 前端 | H5/小程序 | uni-app + Vue3 | 选茶卡片、成分可视化、问答 |

## 快速开始

### 1. 配置 API 密钥

```bash
cd tea-rag
copy .env.example .env   # Windows
cp .env.example .env     # Linux/Mac
```

编辑 `.env`，填入：
- `LLM_API_KEY` —— DeepSeek 密钥（https://platform.deepseek.com）
- `EMBEDDING_API_KEY` —— SiliconFlow 密钥（https://siliconflow.cn，用免费额度）

### 2. 安装依赖

```bash
# Python（RAG）
cd tea-rag
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Java（后端）
# 需要 JDK 17+，用 Maven Wrapper 自动下载依赖
cd tea-backend
mvnw.cmd spring-boot:run        # Windows
./mvnw spring-boot:run          # Linux/Mac

# 前端
# 用 HBuilderX 打开 tea-frontend，点「运行到浏览器」
```

### 3. 一键启动后端

双击 `start-all.bat`（Windows），自动启动 RAG 和 SpringBoot 两个服务。

---

## 贡献知识库（完善向量库）

**任何人都可以添加茶叶资料来完善知识库。** 知识库的数据源在 `tea-rag/data/knowledge/`，支持两种贡献方式：

### 方式一：直接添加文本知识（最简单，推荐）

把茶叶知识写成 `.md` 或 `.txt` 文件，放进 `tea-rag/data/knowledge/` 目录即可。

**格式要求**（参考 `tea-rag/data/knowledge/_模板.md`）：
- 一个段落只讲一个知识点
- 单条 100~500 字为宜
- 表述自包含（不要只写「它产自浙江」，要写「西湖龙井产自浙江杭州」）
- 覆盖维度：品种、产地、工艺、香气、成分、冲泡、鉴别、文化

**重新构建索引：**
```bash
cd tea-rag
.venv\Scripts\python scripts/build_index.py
```

### 方式二：通过 PR 贡献

1. Fork 本仓库
2. 在 `tea-rag/data/knowledge/` 下添加你的知识 `.md` 文件
3. 提交 Pull Request

> 注意：`data/images/`（PDF 转图）和 `data/pdfs/`（PDF 源文件）体积大，**不要提交**，
> 它们可通过 `scripts/` 下的脚本重新生成。只提交 `data/knowledge/` 里的知识文本。

### 批量导入国标标准

项目内置了从「全国茶叶标准化技术委员会」导入国标的完整流程：

```bash
cd tea-rag

# 1. 批量处理核心名茶（下载 → 转图 → OCR → 输出 markdown）
.venv\Scripts\python scripts/batch_process.py

# 2. 用 DeepSeek 从 OCR 文本提取结构化信息（产地/工艺/香气/成分）
.venv\Scripts\python scripts/extract_enrich.py --all

# 3. 导入后端数据库
.venv\Scripts\python scripts/import_tea_data.py --apply
.venv\Scripts\python scripts/apply_enrich.py

# 4. 重建向量库
.venv\Scripts\python scripts/build_index.py
```

---

## 数据模型

后端 `tea_product` 表存茶品结构化信息（标准号、名称、茶类、产地、工艺、香气），
`composition` 表存成分数据（茶多酚、咖啡碱、水浸出物等），`device_data` 表统一接收硬件/流水线数据。

## 技术亮点

- **RAG 混合检索**：向量检索（bge-m3）+ 关键词检索（茶名词典），解决专有名词检索不准的问题
- **国标 OCR 流水线**：跳过封面/前言页 + 按章节切块 + 过滤引用文件清单，让国标文本适合 RAG
- **LLM 结构化提取**：用 DeepSeek 从 OCR 文本提取产地/工艺/香气/成分

## License

项目中的国标标准文本版权归标准发布方所有，仅供学习研究使用。
