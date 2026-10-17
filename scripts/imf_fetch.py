#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IMF Data SDMX API 工具（2026-10 接入）
====================================
用法：
  python scripts/imf_fetch.py --test               # 目标数据集可达性
  python scripts/imf_fetch.py --discover COFER     # 搜索 dataflow（共 223 个）
  python scripts/imf_fetch.py --pull               # 拉取 COFER 份额 + PCPS 油价 → 看板日志/cache/imf/

说明：
- 密钥从本地 .env 读取（IMF_API_KEY，不入库）；订阅 10/15/2026，账户备忘见 .env 注释
- 取数键：flow/key，维度按 Series 属性顺序，空位留通配（全量用 all + 时间窗）
- 缓存：看板日志/cache/imf/*.csv
"""
import os, sys, re, csv, argparse, requests
from pathlib import Path
from collections import defaultdict

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass

# Windows GBK 控制台兼容：避免 ✓/✗ 等字符在 print 时抛 UnicodeEncodeError
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(errors="replace")
    except Exception:
        pass

BASE = "https://api.imf.org/external/sdmx/2.1"
CACHE = Path(__file__).resolve().parent.parent / "看板日志" / "cache" / "imf"

def _key():
    k = os.environ.get("IMF_API_KEY")
    if not k:
        sys.exit("缺少 IMF_API_KEY（本地 .env）")
    return k

def _get(path, params=None):
    r = requests.get(f"{BASE}/{path}", headers={"Ocp-Apim-Subscription-Key": _key()},
                     params=params or {}, timeout=120)
    r.raise_for_status()
    return r.text

def _series(xml):
    out = []
    for attrs, body in re.findall(r'<Series ([^>]*)>(.*?)</Series>', xml, re.S):
        a = dict(re.findall(r'([A-Z_0-9]+)="([^"]*)"', attrs))
        obs = re.findall(r'TIME_PERIOD="([^"]+)" OBS_VALUE="([^"]+)"', body)
        out.append((a, obs))
    return out

def _num(x, n=4):
    try:
        return round(float(x), n)
    except Exception:
        return ""

def test():
    targets = [
        ("COFER 储备份额", "data/IMF.STA,COFER/all", {"startPeriod": "2026-Q1", "endPeriod": "2026-Q2"}),
        ("PCPS 布伦特(USD)", "data/IMF.RES,PCPS/G001.POILBRE.USD.M", {"startPeriod": "2026-07", "endPeriod": "2026-08"}),
        ("dataflow 列表", "dataflow/all/all/latest", None),
    ]
    ok = 0
    for name, path, p in targets:
        try:
            xml = _get(path, p)
            s = _series(xml)
            n = sum(len(o) for _, o in s)
            extra = f"dataflows={xml.count('Dataflow ')}" if not s and "dataflow" in path else f"series={len(s)} obs={n}"
            print(f"  ✓ {name:14s} {extra}")
            ok += 1
        except Exception as e:
            print(f"  ✗ {name:14s} {str(e)[:80]}")
    print(f"== {ok}/{len(targets)} 可达 ==")

def discover(kw):
    xml = _get("dataflow/all/all/latest")
    flows = re.findall(r'<str:Dataflow[^>]*agencyID="([^"]+)"[^>]*id="([^"]+)"[^>]*>.*?<com:Name xml:lang="en">([^<]*)</com:Name>', xml, re.S)
    n = 0
    for ag, fid, name in flows:
        if kw.lower() in (fid + " " + name).lower():
            print(f"  [{ag}] {fid:30s} | {name[:70]}")
            n += 1
    print(f"== 匹配 {n} / 共 {len(flows)} ==")

def pull():
    CACHE.mkdir(parents=True, exist_ok=True)
    # 1) COFER 全球份额
    xml = _get("data/IMF.STA,COFER/all", {"startPeriod": "1999-Q1", "endPeriod": "2026-Q2"})
    shares, imp, usd_h, tot_h = defaultdict(dict), {}, {}, {}
    CUR = ["CI_USD","CI_EUR","CI_CNY","CI_JPY","CI_GBP","CI_AUD","CI_CAD","CI_CHF","CI_OTHC"]
    for a, obs in _series(xml):
        if a.get("COUNTRY") != "G001":
            continue
        ind, cur, typ = a.get("INDICATOR"), a.get("FXR_CURRENCY"), a.get("TYPE_OF_TRANSFORMATION")
        for t, v in obs:
            if ind == "AFXRA" and typ == "SHRO_PT" and cur in CUR: shares[t][cur] = _num(v)
            elif ind == "TFXRA_IMP" and typ == "SHRO_PT": imp[t] = _num(v, 2)
            elif ind == "AFXRA" and typ == "NV_USD" and cur == "CI_USD": usd_h[t] = _num(v, 0)
            elif ind == "AFXRA" and typ == "NV_USD" and cur == "CI_T": tot_h[t] = _num(v, 0)
    rows = []
    for t in sorted(shares):
        d = shares[t]
        if "CI_USD" not in d:
            continue
        rows.append([t] + [d.get(c, "") for c in CUR] + [imp.get(t, ""),
                     _num((usd_h.get(t) or 0)/1e12, 3), _num((tot_h.get(t) or 0)/1e12, 3)])
    with open(CACHE / "COFER_world_shares.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["period","USD","EUR","CNY","JPY","GBP","AUD","CAD","CHF","OTHC","imputed_pct","usd_hold_TUSD","total_hold_TUSD"])
        w.writerows(rows)
    print(f"  ✓ COFER -> COFER_world_shares.csv ({len(rows)} 季)")

    # 2) PCPS 油价（Brent/WTI/Dubai，USD，月度）
    def prices(code):
        xml = _get(f"data/IMF.RES,PCPS/G001.{code}.USD.M", {"startPeriod": "1990-01", "endPeriod": "2026-12"})
        s = _series(xml)
        return {t: float(v) for t, v in (s[0][1] if s else []) if v not in ("", "NaN")}
    brent, wti, dubai = prices("POILBRE"), prices("POILWTI"), prices("POILDUB")
    periods = sorted(set(brent) | set(wti) | set(dubai))
    with open(CACHE / "PCPS_oil_prices.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["period", "brent_usd", "wti_usd", "dubai_usd"])
        for p in periods:
            w.writerow([p, brent.get(p, ""), wti.get(p, ""), dubai.get(p, "")])
    print(f"  ✓ PCPS -> PCPS_oil_prices.csv ({len(periods)} 月)")
    print(f"== 完成 → {CACHE} ==")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--discover", default=None, metavar="KEYWORD")
    ap.add_argument("--pull", action="store_true")
    a = ap.parse_args()
    if a.test: test()
    elif a.discover is not None: discover(a.discover)
    elif a.pull: pull()
    else: ap.print_help()
