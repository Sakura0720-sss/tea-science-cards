"""用 DeepSeek 从 OCR 文本提取茶品结构化信息（产地/工艺/香气/成分）。

用法（在 tea-rag 目录下）：
    .venv\\Scripts\\python scripts/extract_enrich.py --tea 龙井茶       # 单个提取
    .venv\\Scripts\\python scripts/extract_enrich.py --all             # 批量提取全部
    .venv\\Scripts\\python scripts/extract_enrich.py --all --apply     # 批量提取并写入后端

输出：data/enriched.json
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openai import OpenAI

from app import config

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge"
OUT_JSON = Path(__file__).resolve().parent.parent / "data" / "enriched.json"
BACKEND = "http://127.0.0.1:8080"

PROMPT = """你是茶叶专家。下面是一份茶叶国家标准的 OCR 文本（可能有错别字）。请从中提取结构化信息。

只输出一个 JSON 对象，不要输出任何其他文字。字段如下：
{
  "origin": "产地（一句话，如：浙江杭州西湖区。若文本无产地则空字符串）",
  "process": "关键工艺（一句话概括，如：杀青、揉捻、干燥。若无则空字符串）",
  "flavor": "香气与风味（一句话，如：豆花香，鲜爽甘醇。若无则空字符串）",
  "compositions": [
    {"name": "成分名（如茶多酚）", "value": 数值, "unit": "单位（如 % 或 mg/g）"}
  ]
}

要求：
1. 成分 value 必须是纯数字（如 22.5），不要带符号、单位、范围。若文本给的是范围，取中间值；若给的是「≤6.5%」这类限量值，不要提取。
2. 成分只提取「茶多酚、咖啡碱、氨基酸、儿茶素、茶黄素、水浸出物」这类与茶叶品质相关的指标；不要提取水分、灰分、粉末、碎茶等加工检测指标。
3. 若某个字段信息不存在，给空字符串或空数组，不要编造。

OCR 文本：
{text}
"""


def list_ocr_files():
    return sorted(KNOWLEDGE_DIR.glob("OCR_*.md"))


def tea_name_of(path: Path) -> str:
    """从文件名提取茶名，用于匹配后端 tea_product。"""
    stem = path.stem
    if stem.startswith("OCR_"):
        stem = stem[4:]
    # 取最后一个下划线后的部分
    name = stem.rsplit("_", 1)[-1]
    # 去掉标准号、年份、通用前缀
    name = re.sub(r"^GB\s*/?\s*T?\s*\d+(?:\.\d+)?[-－—]\s*\d{4}", "", name)
    name = re.sub(r"^(地理标志产品|地理标志产品质量要求)", "", name)
    name = re.sub(r"^第\s*\d+\s*部分[:：]\s*", "", name)
    name = name.strip()
    return name


def extract_with_llm(text: str) -> dict:
    """调用 DeepSeek 提取，返回解析后的 dict。"""
    client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)
    resp = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[{"role": "user", "content": PROMPT.replace("{text}", text[:6000])}],
        temperature=0.1,
    )
    raw = resp.choices[0].message.content.strip()
    # 去掉可能的 markdown 代码块包裹（```json ... ```）
    raw = re.sub(r"^```[a-zA-Z]*\s*", "", raw).strip()
    raw = re.sub(r"\s*```$", "", raw).strip()
    # 截取第一个 { 到最后一个 } 之间的内容
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start : end + 1]
    data = json.loads(raw)
    # 成分 value 转数字
    for c in data.get("compositions", []):
        val = c.get("value")
        if isinstance(val, str):
            m = re.search(r"\d+(?:\.\d+)?", val)
            c["value"] = float(m.group(0)) if m else None
    return data


def main():
    args = sys.argv[1:]
    apply_mode = "--apply" in args
    all_mode = "--all" in args
    tea_filter = None
    if "--tea" in args:
        tea_filter = args[args.index("--tea") + 1]

    files = list_ocr_files()
    results = {}

    for f in files:
        name = tea_name_of(f)
        if tea_filter and tea_filter not in name:
            continue
        if not all_mode and not tea_filter:
            break  # 默认只跑第一个（需显式 --all 或 --tea）
        text = f.read_text(encoding="utf-8")
        print(f"提取中: {name} ...")
        try:
            data = extract_with_llm(text)
            data["teaName"] = name
            data["sourceFile"] = f.name
            results[f.name] = data
            print(f"  ✅ 产地={data.get('origin','')[:20]} 香气={data.get('flavor','')[:20]}")
        except Exception as e:
            print(f"  ❌ 失败: {e}")

    # 保存结果
    existing = {}
    if OUT_JSON.exists():
        existing = json.load(open(OUT_JSON, encoding="utf-8"))
    existing.update(results)
    json.dump(existing, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n已保存 {len(existing)} 条到 {OUT_JSON.name}")

    if apply_mode:
        _apply_to_backend(results)


def _apply_to_backend(results: dict):
    """把提取结果写入后端：更新 tea_product 的 origin/process/flavor，插入 composition。"""
    import urllib.request

    def request_json(method, url, data=None):
        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body,
                                     headers={"Content-Type": "application/json"}, method=method)
        return json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))

    # 查后端所有茶品，建立「标准号数字主体（不含年份）」-> (id, nameZh) 映射
    teas = request_json("GET", BACKEND + "/api/tea")
    def stdno_key(s):
        # 提取 GB/T 后面的数字主体（含小数点，不含 -年份），归一化为纯数字
        m = re.search(r"GB\s*/?\s*T?\s*(\d+(?:\.\d+)?)", s or "")
        return re.sub(r"[^0-9]", "", m.group(1)) if m else ""
    stdno_to_tea = {}
    for t in teas:
        key = stdno_key(t.get("stdNo", ""))
        if key:
            stdno_to_tea[key] = t

    for fname, data in results.items():
        name = data["teaName"]
        # 从 sourceFile 提取标准号主体来匹配（同样的规则）
        key = stdno_key(data.get("sourceFile", ""))
        match = stdno_to_tea.get(key)
        if not match:
            print(f"  ⚠️ 后端无此标准: {name} ({data.get('sourceFile','')[:40]})，跳过")
            continue
        tid = match["id"]
        name = match["nameZh"]
        # 1) 更新茶品 origin/process/flavor
        try:
            request_json("PUT", f"{BACKEND}/api/tea/{tid}", {
                "origin": data.get("origin", ""),
                "process": data.get("process", ""),
                "flavor": data.get("flavor", ""),
            })
        except Exception as e:
            print(f"  ❌ 茶品更新失败 {name}: {e}")
        # 2) 写成分
        for c in data.get("compositions", []):
            if c.get("value") is None:
                continue
            try:
                request_json("POST", BACKEND + "/api/tea/composition", {
                    "teaProductId": tid,
                    "name": c.get("name"),
                    "value": c.get("value"),
                    "unit": c.get("unit", ""),
                })
            except Exception as e:
                print(f"  ❌ 成分写入失败 {name}/{c.get('name')}: {e}")
        print(f"  ✅ {name}: 更新完成（成分 {len(data.get('compositions', []))} 项）")


if __name__ == "__main__":
    main()
