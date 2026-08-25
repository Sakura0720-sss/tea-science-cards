"""批量处理核心名茶：下载 PDF → 转图 → OCR(跳过封面/前言) → 输出 markdown。

用法（在 tea-rag 目录下）：
    .venv\\Scripts\\python scripts\\batch_process.py

数据来源：data/api_result.json（全国茶叶标准化技术委员会产品标准清单）。
筛选规则：标题含「地理标志」或属于六大茶类核心标准。
"""
import json
import re
import subprocess
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

SKIP_PAGES = 2  # 国标：第1页封面、第2页前言
NOISE_KEYWORDS = ["315.com", "刮涂层", "查真伪", "电话4006982315"]

# 核心名茶关键词
KEYWORDS = [
    "地理标志", "龙井", "武夷岩茶", "碧螺春", "黄山毛峰", "铁观音", "蒙山",
    "狗牯脑", "太平猴魁", "安吉白茶", "乌牛早", "雨花茶", "庐山云雾",
    "永春佛手", "政和白茶", "普洱茶", "信阳毛尖", "崂山", "白茶", "茉莉花茶",
    "黄茶", "抹茶", "乌龙茶", "水仙", "肉桂", "单丛", "黄金桂", "佛手",
    "白芽奇兰", "大叶种绿茶", "中小叶种绿茶", "珠茶", "眉茶", "蒸青茶",
]


def std_no_of(title: str) -> str:
    """从标题提取标准号，用作文件名。"""
    m = re.search(r"(GB\s*/?\s*T?\s*\d+(?:\.\d+)?)", title, re.I)
    if m:
        return m.group(1).replace(" ", "")
    # 兜底：用标题前12字
    return re.sub(r"[^\w一-鿿]+", "_", title)[:20]


def safe_filename(title: str) -> str:
    """标题 → 安全文件名（含标准号，去掉 Windows 非法字符）。"""
    no = std_no_of(title).replace("/", "").replace(" ", "")
    # 标题部分去掉标准号重复、空格、非法字符
    name = re.sub(r"[\\/:*?\"<>|\s]+", "", title)
    return f"{no}_{name}"[:80]


def download(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  已存在，跳过下载：{dest.name}")
        return True
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        data = urllib.request.urlopen(req, timeout=120).read()
        dest.write_bytes(data)
        return True
    except Exception as e:
        print(f"  ⚠️ 下载失败：{e}")
        return False


def clean_line(t: str) -> bool:
    t = t.strip()
    if not t:
        return False
    return not any(k in t for k in NOISE_KEYWORDS)


def ocr_pdf(engine, pdf: Path, out_md: Path) -> None:
    doc = pymupdf.open(pdf)
    parts = []
    total_pages = len(doc)
    for i in range(SKIP_PAGES, total_pages):
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
    data = json.load(open(BASE / "data" / "api_result.json", encoding="utf-8"))
    items = data["result"]["items"]
    selected = [it for it in items if any(k in it.get("title", "") for k in KEYWORDS)]
    print(f"筛选到 {len(selected)} 个核心名茶标准\n")

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    engine = RapidOCR()

    ok = 0
    for it in selected:
        title = it.get("title", "").strip()
        dic = it.get("dicFile") or {}
        slt = dic.get("slt") or {}
        url = slt.get("fileUrl", "")
        if not url:
            print(f"⚠️ 无下载地址，跳过：{title}")
            continue
        pdf = PDF_DIR / f"{safe_filename(title)}.pdf"
        out_md = OUT_DIR / f"OCR_{safe_filename(title)}.md"

        print(f"📥 {title}")
        if download(url, pdf):
            print(f"  🔍 OCR 识别中...")
            try:
                ocr_pdf(engine, pdf, out_md)
                ok += 1
                print(f"  ✅ → {out_md.name}")
            except Exception as e:
                print(f"  ❌ OCR 失败：{e}")

    print(f"\n===== 完成：成功处理 {ok}/{len(selected)} 个 =====")
    print("下一步：.venv\\Scripts\\python scripts/build_index.py 重建索引")


if __name__ == "__main__":
    main()
