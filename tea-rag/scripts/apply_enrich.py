"""把已有的 enriched.json 结果灌入后端（不重新提取）。

用法：
    .venv\\Scripts\\python scripts/apply_enrich.py
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BACKEND = "http://127.0.0.1:8080"
ENRICHED = Path(__file__).resolve().parent.parent / "data" / "enriched.json"


def request_json(method, url, data=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json"}, method=method)
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))


def stdno_key(s):
    m = re.search(r"GB[_\s/]*T?[_\s/]*(\d+(?:\.\d+)?)", s or "")
    return re.sub(r"[^0-9]", "", m.group(1)) if m else ""


def main():
    enriched = json.load(open(ENRICHED, encoding="utf-8"))
    teas = request_json("GET", BACKEND + "/api/tea")
    stdno_to_tea = {}
    for t in teas:
        key = stdno_key(t.get("stdNo", ""))
        if key:
            stdno_to_tea[key] = t

    ok = 0
    skip = 0
    for fname, data in enriched.items():
        name = data["teaName"]
        key = stdno_key(data.get("sourceFile", ""))
        match = stdno_to_tea.get(key)
        if not match:
            skip += 1
            print(f"  ⚠️ 未匹配: {name}")
            continue
        tid = match["id"]
        name = match["nameZh"]
        # 更新茶品 origin/process/flavor
        try:
            request_json("PUT", f"{BACKEND}/api/tea/{tid}", {
                "origin": data.get("origin", ""),
                "process": data.get("process", ""),
                "flavor": data.get("flavor", ""),
            })
        except Exception as e:
            print(f"  ❌ 更新失败 {name}: {e}")
        # 写成分
        n_comp = 0
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
                n_comp += 1
            except Exception as e:
                print(f"  ❌ 成分失败 {name}/{c.get('name')}: {e}")
        ok += 1
        print(f"  ✅ {name}: 产地/工艺/香气 + {n_comp} 项成分")

    print(f"\n完成：成功 {ok}，未匹配 {skip}，共 {len(enriched)}")


if __name__ == "__main__":
    main()
