"""批量处理剩余冷门标准（data/remaining.json）。

用法（在 tea-rag 目录下）：
    .venv\\Scripts\\python scripts\\batch_remaining.py

流程与 batch_process.py 一致：下载 → 转图 → OCR(跳过封面/前言) → 输出 markdown。
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pymupdf
from rapidocr_onnxruntime import RapidOCR

BASE = Path(__file__).resolve().parent.parent
PDF_DIR = BASE / "data" / "pdfs"
IMG_DIR = BASE / "data" / "images"
OUT_DIR = BASE / "data" / "knowledge"

SKIP_PAGES = 2
NOISE_KEYWORDS = ["315.com", "刮涂层", "查真伪", "电话4006982315"]


def safe_filename(title: str) -> str:
    no = re.search(r"(GB\s*/?\s*T?\s*\d+(?:\.\d+)?)", title, re.I)
    no = no.group(1).replace(" ", "").replace("/", "") if no else ""
    name = re.sub(r"[\\/:*?\"<>|\s]+", "", title)
    return f"{no}_{name}"[:80]


def clean_line(t: str) -> bool:
    t = t.strip()
    if not t:
        return False
    return not any(k in t for k in NOISE_KEYWORDS)


def ocr_pdf(engine, pdf: Path, out_md: Path) -> None:
    doc = pymupdf.open(pdf)
    parts = []
    for i in range(SKIP_PAGES, len(doc)):
        pix = doc[i].get_pixmap(dpi=300)
        img_path = IMG_DIR / pdf.stem / f"page_{i+1:03d}.png"
        img_path.parent.mkdir(parents=True, exist_ok=True)
        pix.save(img_path)
        result, _ = engine(str(img_path))
        if result:
            lines = [t for _, t, _ in result if clean_line(t)]
            parts.append("\n".join(lines))
    doc.close()
    title = pdf.stem.replace("_", " ")
    out_md.write_text(f"# {title}\n\n" + "\n\n".join(parts), encoding="utf-8")


def main():
    data = json.load(open(BASE / "data" / "remaining.json", encoding="utf-8"))
    print(f"待处理 {len(data)} 个标准\n")

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    engine = RapidOCR()

    ok = 0
    for it in data:
        title = it.get("title", "").strip()
        url = it.get("url", "")
        if not url:
            print(f"⚠️ 无下载地址：{title}")
            continue
        pdf = PDF_DIR / f"{safe_filename(title)}.pdf"
        out_md = OUT_DIR / f"OCR_{safe_filename(title)}.md"

        print(f"📥 {title}")
        if pdf.exists() and pdf.stat().st_size > 0:
            print(f"  已存在，跳过下载")
        else:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                pdf.write_bytes(urllib.request.urlopen(req, timeout=120).read())
            except Exception as e:
                print(f"  ⚠️ 下载失败：{e}")
                continue

        try:
            ocr_pdf(engine, pdf, out_md)
            ok += 1
            print(f"  ✅ → {out_md.name}")
        except Exception as e:
            print(f"  ❌ OCR 失败：{e}")

    print(f"\n===== 完成：成功处理 {ok}/{len(data)} 个 =====")
    print("下一步：.venv\\Scripts\\python scripts/build_index.py 重建索引")


if __name__ == "__main__":
    main()
