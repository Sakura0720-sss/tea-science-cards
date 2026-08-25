"""批量检查 61 个标准在「国家标准全文公开系统」的状态。

输出每个标准的：标准号、是否采标、现行/废止状态、hcno（详情ID）。
采标（采用了 ISO/IEC 国际标准）的标准，官方系统因版权不提供全文。
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

API = "http://openstd.samr.gov.cn/bzgk/gb/std_list_type"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "http://openstd.samr.gov.cn/bzgk/gb/index",
}


def extract_std_no(title: str) -> str:
    """从标题提取标准号，如 'GB/T 9833.1-2013' / 'GBT19598-2025'。"""
    m = re.search(r"(GB\s*/?\s*T?\s*\d+(?:\.\d+)?)", title, re.I)
    return m.group(1).replace(" ", "") if m else ""


def search(std_no: str):
    """搜索标准号，返回该标准最新现行版本的 (是否采标, hcno, 标准名)。"""
    params = urllib.parse.urlencode({"r": "0.1", "p.p1": "0", "p.p2": std_no})
    url = f"{API}?{params}"
    req = urllib.request.Request(url, headers=HEADERS)
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")

    # 每个结果行：showInfo('hcno') 是详情ID，旁边有「采」标签表示采标
    rows = re.findall(r"showInfo\('([0-9A-F]+)'\);\">(.*?)</a>", html)
    if not rows:
        return None

    # 取第一条（通常是最新版本）
    hcno = rows[0][0]
    std_name = re.sub(r"<[^>]+>", "", rows[0][1]).strip()
    # 判断该行是否含「采」标签：取该 hcno 附近 200 字符
    idx = html.find(hcno)
    seg = html[idx : idx + 400]
    is_caibiao = "采</span>" in seg or 'label-warning' in seg
    return {"hcno": hcno, "name": std_name, "caibiao": is_caibiao}


def main():
    data = json.load(open("data/api_result.json", encoding="utf-8"))
    items = data["result"]["items"]
    results = []
    for i, it in enumerate(items, 1):
        title = it.get("title", "")
        std_no = extract_std_no(title)
        if not std_no:
            results.append({"n": i, "title": title, "std_no": "", "status": "无法解析"})
            print(f"{i:2d}. [跳过] {title}")
            continue
        try:
            r = search(std_no)
            if r:
                tag = "采标(无全文)" if r["caibiao"] else "非采标(可能有全文)"
                results.append({"n": i, "title": title, "std_no": std_no, **r, "tag": tag})
                print(f"{i:2d}. {std_no}  {tag}  现行名: {r['name']}")
            else:
                results.append({"n": i, "title": title, "std_no": std_no, "status": "未收录"})
                print(f"{i:2d}. {std_no}  [未收录]")
        except Exception as e:
            results.append({"n": i, "title": title, "std_no": std_no, "status": f"错误:{e}"})
            print(f"{i:2d}. {std_no}  [错误] {e}")
        time.sleep(1.0)  # 避免频繁请求被封

    open("data/_检查结果.json", "w", encoding="utf-8").write(
        json.dumps(results, ensure_ascii=False, indent=2)
    )
    n_cb = sum(1 for r in results if r.get("caibiao"))
    n_ok = sum(1 for r in results if r.get("hcno") and not r.get("caibiao"))
    print(f"\n===== 汇总 =====\n采标(无全文): {n_cb}  非采标(可能有全文): {n_ok}  总计: {len(results)}")


if __name__ == "__main__":
    main()
