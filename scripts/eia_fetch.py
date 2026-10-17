#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EIA 数据获取工具（能源通胀研究 P4）
====================================
用法：
  python scripts/eia_fetch.py --test              # 测试清单内全部序列可达性
  python scripts/eia_fetch.py --pull              # 拉取全部 → 看板日志/cache/eia/
  python scripts/eia_fetch.py --pull --only SPR   # 按标签关键词只拉一条
  python scripts/eia_fetch.py --discover petroleum/sum/sndw --freq weekly   # 枚举数据集内序列

说明：
- API key 从本地 .env 读取（EIA_API_KEY，不入库）
- 缓存：看板日志/cache/eia/<label>.csv + _manifest.json（本地，gitignored）
- 12 大类可达性实测（2026-10-03）：见 CATEGORIES
"""
import os, sys, csv, json, argparse, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CACHE = BASE / "看板日志" / "cache" / "eia"

try:
    from dotenv import load_dotenv
    load_dotenv(BASE / ".env")
except Exception:
    pass

# Windows GBK 控制台兼容：避免 ✓/✗ 等字符在 print 时抛 UnicodeEncodeError（曾致 pull 中途崩溃）
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(errors="replace")
    except Exception:
        pass

import requests

API = "https://api.eia.gov/v2"
TIMEOUT = 25

# label, route, series_id, frequency
WATCHLIST = [
    ("SPR战略储备",        "petroleum/stoc/wstk", "WCSSTUS1",                 "weekly"),
    ("商业原油库存",        "petroleum/stoc/wstk", "WCESTUS1",                 "weekly"),
    ("馏分油库存",          "petroleum/stoc/wstk", "WDISTUS1",                 "weekly"),
    ("汽油库存",            "petroleum/stoc/wstk", "WGTSTUS1",                 "weekly"),
    ("Cushing库存",         "petroleum/stoc/wstk", "W_EPC0_SAX_YCUOK_MBBL",    "weekly"),
    ("炼化利用率",          "petroleum/sum/sndw",  "WPULEUS3",                 "weekly"),
    ("原油产量",            "petroleum/sum/sndw",  "WCRFPUS2",                 "weekly"),
    ("原油出口",            "petroleum/sum/sndw",  "WCREXUS2",                 "weekly"),
    ("天然气库存48州",       "natural-gas/stor/wkly", "NW2_EPG0_SWO_R48_BCF",  "weekly"),
]

# 12 大类可达性登记（2026-10-03 实测；参数模板待调的类别可用 --discover 扩展）
CATEGORIES = [
    ("electricity",        "电力",        "root ✓ · 零售价格参数模板待调"),
    ("natural-gas",        "天然气",      "root ✓ · 库存序列已接入"),
    ("petroleum",          "石油",        "root ✓ · 9 序列已接入（+原油出口）"),
    ("crude-oil-imports",  "原油进口",    "root ✓ · 参数模板待调"),
    ("coal",               "煤炭",        "root ✓ · 参数模板待调"),
    ("densified-biomass",  "致密生物质",   "root ✓"),
    ("nuclear-outages",    "核电停运",    "root ✓ · 参数模板待调"),
    ("steo",               "短期能源展望", "root ✓ · 序列可查（示例 ABRIPUS）"),
    ("total-energy",       "总能源",      "root ✓"),
    ("seds",               "州级能源(SEDS)", "root ✓（CO2 已并入）"),
    ("co2-emissions",      "碳排放",      "root ✓（deprecated → SEDS）"),
    ("international",      "国际能源",    "root ✓"),
]


def _key():
    k = os.environ.get("EIA_API_KEY")
    if not k:
        sys.exit("缺少 EIA_API_KEY（本地 .env）")
    return k


def fetch_series(route, sid, freq="weekly", start="2015-01-01", length=800):
    """拉取单个序列全部历史 → [(period, value), ...]"""
    url = f"{API}/{route}/data/"
    params = {
        "api_key": _key(), "frequency": freq, "data[0]": "value",
        "facets[series][]": sid, "start": start,
        "sort[0][column]": "period", "sort[0][direction]": "asc",
        "length": length,
    }
    r = requests.get(url, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    rows = r.json().get("response", {}).get("data", [])
    return [(row["period"], float(row["value"])) for row in rows if row.get("value") is not None]


def test():
    print("== EIA 序列可达性测试 ==")
    ok = 0
    for label, route, sid, freq in WATCHLIST:
        try:
            rows = fetch_series(route, sid, freq, start="2026-01-01", length=60)
            tail = rows[-1] if rows else ("-", "-")
            print(f"  ✓ {label:12} {sid:24} n={len(rows):3} last={tail[0]} {tail[1]}")
            ok += 1
        except Exception as e:
            print(f"  ✗ {label:12} {sid:24} {str(e)[:60]}")
    print(f"== {ok}/{len(WATCHLIST)} 可达 ==")


def pull(only=None):
    CACHE.mkdir(parents=True, exist_ok=True)
    manifest, n_ok = [], 0
    for label, route, sid, freq in WATCHLIST:
        if only and only.lower() not in label.lower() and only.upper() != sid:
            continue
        try:
            rows = fetch_series(route, sid, freq)
            fp = CACHE / f"{label}.csv"
            with open(fp, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["date", "value"])
                w.writerows(rows)
            manifest.append({"label": label, "route": route, "series": sid,
                             "rows": len(rows), "last": rows[-1][0] if rows else None})
            n_ok += 1
            print(f"  ✓ {label:12} → {fp.name}  ({len(rows)} 行, 至 {rows[-1][0]})")
        except Exception as e:
            print(f"  ✗ {label:12} {str(e)[:70]}")
    mpath = CACHE / "_manifest.json"
    old = []
    if mpath.exists():
        try:
            old = json.loads(mpath.read_text(encoding="utf-8"))
        except Exception:
            old = []
    merged = {x["label"]: x for x in old}
    for x in manifest:
        merged[x["label"]] = x
    mpath.write_text(json.dumps(list(merged.values()), ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"== 完成 {n_ok}/{len(WATCHLIST)} → 缓存于 {CACHE} ==")


def discover(route, freq="weekly", n=10):
    """枚举数据集内序列 ID（打印最近 n 行的 id 与值）"""
    url = f"{API}/{route}/data/"
    params = {"api_key": _key(), "length": n, "data[0]": "value",
              "sort[0][column]": "period", "sort[0][direction]": "desc"}
    if freq:
        params["frequency"] = freq
    r = requests.get(url, params=params, timeout=TIMEOUT)
    print(f"HTTP {r.status_code}")
    rows = r.json().get("response", {}).get("data", [])
    seen = set()
    for row in rows:
        sid = row.get("seriesId") or row.get("series") or row.get("series_id") or "(无ID字段)"
        if sid in seen:
            continue
        seen.add(sid)
        print(f"  {row.get('period')} | {str(sid)[:45]} | {row.get('value')}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--pull", action="store_true")
    ap.add_argument("--only", default=None)
    ap.add_argument("--discover", default=None, metavar="ROUTE")
    ap.add_argument("--freq", default="weekly")
    a = ap.parse_args()
    if a.test:
        test()
    elif a.pull:
        pull(only=a.only)
    elif a.discover:
        discover(a.discover, freq=a.freq)
    else:
        print(__doc__)
