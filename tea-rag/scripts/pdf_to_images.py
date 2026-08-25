"""把 data/pdfs/ 下的 PDF 每页渲染成 PNG，输出到 data/images/<pdf名>/。

用法（在 tea-rag 目录下）：
    .venv\\Scripts\\python scripts\\pdf_to_images.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pymupdf

PDF_DIR = Path(__file__).resolve().parent.parent / "data" / "pdfs"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "images"
DPI = 300  # OCR 建议 300 DPI，清晰度与速度的平衡点


def main():
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        print("未找到 PDF，请先放入 data/pdfs/")
        return
    for pdf in pdfs:
        out_sub = OUT_DIR / pdf.stem
        out_sub.mkdir(parents=True, exist_ok=True)
        doc = pymupdf.open(pdf)
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=DPI)
            img_path = out_sub / f"page_{i+1:03d}.png"
            pix.save(img_path)
        doc.close()
        print(f"✅ {pdf.name} → {len(doc) if False else i+1} 页 已输出到 {out_sub.name}")


if __name__ == "__main__":
    main()
