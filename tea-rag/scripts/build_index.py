"""建索引脚本：把 data/knowledge/ 下文档写入向量库。

用法（在 tea-rag 目录下）：
    .venv\\Scripts\\python scripts\\build_index.py
"""
import sys
from pathlib import Path

# 把项目根目录加入搜索路径，保证从 scripts/ 目录运行时也能导入 app 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config
from app.vectorstore import build_index

if __name__ == "__main__":
    config.check_config()
    n = build_index()
    print(f"✅ 完成，共写入 {n} 个知识块。现在可以启动服务并调用 /ask 了。")
