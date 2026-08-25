"""把知识库的 61 个国标清单导入 SpringBoot 后端 tea_product 表。

数据源：tea-rag/data/api_result.json（全国茶叶标准化技术委员会产品标准清单）

用法（在 tea-rag 目录下）：
    .venv\\Scripts\\python scripts/import_tea_data.py          # 只打印解析结果（dry-run）
    .venv\\Scripts\\python scripts/import_tea_data.py --apply  # 实际调用后端 API 灌入
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BACKEND = "http://127.0.0.1:8080"
API_JSON = Path(__file__).resolve().parent.parent / "data" / "api_result.json"

# 地理标志名茶 → 茶类（名称关键词映射，用于 title 里没有茶类关键词的情况）
GEO_CATEGORY = {
    "龙井茶": "绿茶", "蒙山茶": "绿茶", "武夷岩茶": "乌龙茶",
    "碧螺春": "绿茶", "黄山毛峰": "绿茶", "安溪铁观音": "乌龙茶",
    "狗牯脑": "绿茶", "太平猴魁": "绿茶", "安吉白茶": "绿茶",
    "乌牛早": "绿茶", "雨花茶": "绿茶", "庐山云雾": "绿茶",
    "永春佛手": "乌龙茶", "政和白茶": "白茶", "普洱茶": "黑茶",
    "信阳毛尖": "绿茶", "坦垟工夫": "红茶", "坦洋工夫": "红茶",
    "崂山绿茶": "绿茶",
}


def parse_std_no(title: str) -> str:
    """提取标准号，原样保留（去掉首尾空格）。兼容全角连字符 － 和破折号 —。"""
    m = re.search(r"GB\s*/?\s*T?\s*\d+(?:\.\d+)?\s*[-－—]\s*\d{4}", title)
    if m:
        return re.sub(r"\s+", "", m.group(0))
    return ""


def parse_name(title: str) -> str:
    """提取茶名。去掉标准号、通用前缀、'第N部分：'格式。"""
    t = title.strip().replace(" ", " ").strip()
    # 去标准号
    t = re.sub(r"^GB\s*/?\s*T?\s*\d+(?:\.\d+)?\s*[-－—]\s*\d{4}\s*", "", t)
    # 去通用前缀
    t = t.replace("地理标志产品质量要求", "").replace("地理标志产品", "")
    t = t.replace("食品安全国家标准", "")
    t = t.strip()
    # 处理「大类 第N部分：具体茶名」
    m = re.search(r"第\s*\d+\s*部分\s*[：:]\s*(.+)", t)
    if m:
        part = m.group(1).strip()
        if part == "基本要求":
            # 基本要求 → 用大类名（如「绿茶」「乌龙茶」）
            name = re.sub(r"第\s*\d+\s*部分.*", "", t).strip()
        else:
            name = part
    else:
        name = t
    return name.strip()


def category_of(title: str, name: str) -> str:
    """判定茶类。注意顺序：安吉白茶必须在「白茶」判断之前。"""
    t = title
    if "安吉白茶" in name or "安吉白茶" in t:
        return "绿茶"
    if "紧压茶" in t:
        return "紧压茶"
    if "红茶" in t:
        return "红茶"
    if "绿茶" in t:
        return "绿茶"
    if "乌龙茶" in t:
        return "乌龙茶"
    if "白茶" in t:
        return "白茶"
    if "黄茶" in t:
        return "黄茶"
    if "黑茶" in t:
        return "黑茶"
    if "茶制品" in t:
        return "茶制品"
    if "茉莉花茶" in t:
        return "花茶"
    if "茶饮料" in t:
        return "茶饮料"
    if "袋泡茶" in t:
        return "袋泡茶"
    if "抹茶" in t:
        return "抹茶"
    if "食品安全" in t:
        return "基础标准"
    # 地理标志名茶兜底
    for k, v in GEO_CATEGORY.items():
        if k in name:
            return v
    return "其他"


def load_items():
    data = json.load(open(API_JSON, encoding="utf-8"))
    return data["result"]["items"]


def post_tea(payload: dict):
    req = urllib.request.Request(
        BACKEND + "/api/tea",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))


def main():
    apply_mode = "--apply" in sys.argv
    items = load_items()
    parsed = []
    for it in items:
        title = it["title"].strip().replace(" ", " ")
        std_no = parse_std_no(title)
        name = parse_name(title)
        category = category_of(title, name)
        parsed.append({"stdNo": std_no, "nameZh": name, "category": category, "title": title})

    # 打印解析结果
    print(f"共 {len(parsed)} 个标准\n")
    for i, p in enumerate(parsed, 1):
        print(f"{i:2d}. [{p['category']:6s}] {p['stdNo']:18s} {p['nameZh']}")

    if not apply_mode:
        print("\n（dry-run 模式，未写入。加 --apply 实际灌入后端）")
        return

    # 实际灌入
    print("\n开始灌入后端...")
    ok = 0
    for p in parsed:
        try:
            post_tea({
                "stdNo": p["stdNo"],
                "nameZh": p["nameZh"],
                "category": p["category"],
            })
            ok += 1
            print(f"  ✅ {p['nameZh']}")
        except Exception as e:
            print(f"  ❌ {p['nameZh']}: {e}")
    print(f"\n完成：成功 {ok}/{len(parsed)}")


if __name__ == "__main__":
    main()
