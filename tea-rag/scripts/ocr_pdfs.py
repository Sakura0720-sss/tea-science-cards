"""对 data/images/ 下每个 PDF 的页面图片做 OCR，合并成 markdown，输出到 data/knowledge/。

用法（在 tea-rag 目录下）：
    .venv\\Scripts\\python scripts\\ocr_pdfs.py

输出文件命名：以「OCR_」开头，避免与手工整理的语料混淆（见 chunking.py 的下划线规则）。
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rapidocr_onnxruntime import RapidOCR

IMAGES_DIR = Path(__file__).resolve().parent.parent / "data" / "images"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge"

# 防伪水印/页脚噪声，识别到这些关键词的行会被丢弃
NOISE_KEYWORDS = [
    "315.com",
    "刮涂层",
    "查真伪",
    "电话4006982315",
]

# 跳过前 N 页（国标固定：第1页封面、第2页前言，正文从第3页「1 范围」开始）
SKIP_PAGES = 2


def clean_line(text: str) -> bool:
    """返回 True 表示该行应保留。"""
    t = text.strip()
    if not t:
        return False
    for kw in NOISE_KEYWORDS:
        if kw in t:
            return False
    return True


def ocr_image(engine, img_path) -> str:
    result, _ = engine(str(img_path))
    if not result:
        return ""
    lines = [text for _, text, _ in result if clean_line(text)]
    return "\n".join(lines)


def main():
    engine = RapidOCR()
    dirs = sorted(IMAGES_DIR.iterdir())
    if not dirs:
        print("未找到图片，请先运行 pdf_to_images.py")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    for d in dirs:
        if not d.is_dir():
            continue
        pages = sorted(d.glob("page_*.png"))
        if not pages:
            continue
        # 跳过封面+前言
        pages = pages[SKIP_PAGES:]
        parts = []
        for p in pages:
            text = ocr_image(engine, p)
            if text:
                parts.append(text)
        content = "\n\n".join(parts)
        # 标题行：用目录名（含标准号+名称）作为一级标题
        title = d.name.replace("_", " ")
        md = f"# {title}\n\n{content}\n"
        out_path = OUT_DIR / f"OCR_{d.name}.md"
        out_path.write_text(md, encoding="utf-8")
        total += 1
        print(f"✅ {d.name} → {out_path.name}（跳过前{SKIP_PAGES}页，识别{len(pages)} 页，{len(content)} 字）")

    print(f"\n完成，共处理 {total} 个标准。下一步：python scripts/build_index.py 重建索引。")


if __name__ == "__main__":
    main()
