# -*- coding: utf-8 -*-
"""Deep-Risk-OPP — 机制筛选器 v1.1（v2.2 · 2026-09）

源自「定量建模训练场」延伸研究 #01（比值极端后回归：半程 64.7% / 1/3 失败）
与 #02（机制论证：恐慌组半程回归 82.6% vs 平静组 47.8%）。

三个屏幕：
  1. 拆腿：GOR 走高由「油腿」（油跌）还是「金腿」（金涨）主导？金腿 → 退出油回归逻辑
  2. 恐慌签名（必要条件）：VIX ≥ 其滚动 10 年 P80？
  3. 油迫近：WTI ≤ 其滚动 10 年 P25？（供给压力的粗代理）

裁决（v1.1）：绿 = 恐慌✓ 且 ≥2/3（历史预期命中率 ≈ 83%）｜黄 = 观察区｜红 = 体制重定价候选。
数据全部来自现有缓存/当日数据；任何缺失都优雅降级（verdict=数据不足，不改变原有仓位逻辑）。
"""
import csv
import datetime
import math
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

CACHE_DIR = BASE_DIR / "看板日志" / "backtest_cache"
GOLD_WTI_CSV = CACHE_DIR / "gold_wti_history.csv"
VIX_CSV = CACHE_DIR / "vix_history.csv"

ROLL_WIN = 120          # 滚动 10 年（月）
VIX_PCTL = 0.80
OIL_PCTL = 0.25
LEG_LOOKBACK_M = 12

try:
    import config
    OIL_CAP = dict(getattr(config, "SCREENER_OIL_CAP", {"绿": 1.0, "黄": 0.5, "红": 0.0}))
except Exception:
    OIL_CAP = {"绿": 1.0, "黄": 0.5, "红": 0.0}


def _pctl_rank(vals, x):
    if not vals:
        return None
    return sum(1 for v in vals if v <= x) / len(vals)


def _pctl_threshold(vals, p):
    s = sorted(vals)
    if not s:
        return None
    k = max(0, min(len(s) - 1, int(round(p * (len(s) - 1)))))
    return s[k]


def evaluate(gold_hist, oil_hist, vix_hist, gold_now, oil_now, vix_now):
    """纯函数：三屏 + 裁决。hist 为旧→新的月度序列（不含当期）。"""
    res = {"d_gold": None, "d_oil": None, "leg": None, "s1": None,
           "vix": vix_now, "vix_thr": None, "s2": None,
           "oil": oil_now, "oil_pctl": None, "s3": None}

    hist_g = list(gold_hist) + ([gold_now] if gold_now else [])
    hist_o = list(oil_hist) + ([oil_now] if oil_now else [])

    # 屏幕 1：拆腿（12 个月腿部贡献）
    if (len(hist_g) >= LEG_LOOKBACK_M + 1 and len(hist_o) >= LEG_LOOKBACK_M + 1
            and hist_g[-13] and hist_o[-13] and hist_g[-1] and hist_o[-1]):
        dg = math.log(hist_g[-1] / hist_g[-13])
        do = math.log(hist_o[-1] / hist_o[-13])
        res.update(d_gold=round(dg, 4), d_oil=round(do, 4),
                   s1=abs(do) > abs(dg),
                   leg=("油腿主导" if abs(do) > abs(dg) else "金腿主导"))

    # 屏幕 2：恐慌签名（必要条件）
    vh = list(vix_hist) + ([vix_now] if vix_now else [])
    if len(vh) >= 60 and vh[-1]:
        win = vh[-ROLL_WIN:]
        thr = _pctl_threshold(win, VIX_PCTL)
        res.update(vix_thr=round(thr, 2), s2=vh[-1] >= thr)

    # 屏幕 3：油迫近
    if len(hist_o) >= 60 and hist_o[-1]:
        win = hist_o[-ROLL_WIN:]
        rk = _pctl_rank(win, hist_o[-1])
        res.update(oil_pctl=round(rk, 3), s3=rk <= OIL_PCTL)

    # 裁决（v1.1：恐慌签名为一票必要条件）
    avail = [x for x in (res["s1"], res["s2"], res["s3"]) if x is not None]
    if res["s2"] is None or len(avail) < 2:
        res.update(npass=None, verdict="数据不足", oil_cap_factor=None)
    else:
        npass = sum(1 for x in avail if x)
        res["npass"] = npass
        if res["s2"] and npass >= 2:
            verdict = "绿"
        elif (res["s2"] and npass <= 1) or ((not res["s2"]) and npass >= 2):
            verdict = "黄"
        else:
            verdict = "红"
        res.update(verdict=verdict, oil_cap_factor=OIL_CAP.get(verdict, 1.0))
    return res


def _fetch_gold_wti_from_sources():
    """无本地缓存时的后备：FRED DCOILWTICO（WTI 月均）+ datahub LBMA（黄金月频）。
    GitHub Action 环境（看板日志/ 未入库）依赖此路径；返回 (gold, oil) 两个月度列表。"""
    import io
    import urllib.request

    oil = []
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / ".env")
        from fredapi import Fred
        key = os.getenv("FRED_API_KEY")
        if key:
            s = Fred(api_key=key).get_series("DCOILWTICO")
            buck = {}
            for ts, v in s.dropna().items():
                buck.setdefault(ts.strftime("%Y-%m"), []).append(float(v))
            oil = [sum(vs) / len(vs) for _, vs in sorted(buck.items())]
    except Exception:
        oil = []

    gold = []
    try:
        req = urllib.request.Request("https://datahub.io/core/gold-prices/r/monthly.csv",
                                     headers={"User-Agent": "Mozilla/5.0"})
        txt = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")
        rows = list(csv.reader(io.StringIO(txt)))
        gb = {}
        for row in rows[1:]:
            try:
                gb[str(row[0])[:7]] = float(row[1])
            except Exception:
                continue
        gold = [gb[k] for k in sorted(gb)]
    except Exception:
        gold = []
    return gold, oil


def _load_gold_wti():
    """返回 (gold_monthly, oil_monthly, last_date)。当月不取缓存（由当日实时值代表）。
    本地缓存缺失（如 Action 环境）时回退到在线源现拉。"""
    if not GOLD_WTI_CSV.exists():
        gold, oil = _fetch_gold_wti_from_sources()
        return gold, oil, "fetched"
    pairs = []
    with open(GOLD_WTI_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                pairs.append((row["date"], float(row["gold"]), float(row["wti"])))
            except Exception:
                continue
    cur_key = datetime.date.today().strftime("%Y-%m")
    gb, ob = {}, {}
    for d, g, w in pairs:
        key = d[:7]
        if key == cur_key:
            continue
        if g > 0:
            gb.setdefault(key, []).append(g)
        if w > 0:
            ob.setdefault(key, []).append(w)
    gold = [sum(v) / len(v) for _, v in sorted(gb.items())]
    oil = [sum(v) / len(v) for _, v in sorted(ob.items())]
    last_date = pairs[-1][0] if pairs else None
    return gold, oil, last_date


def _load_vix(max_age_days=30):
    """读缓存；缺失/过期尝试 FRED VIXCLS 刷新（失败则用旧缓存；全失败返回 []）。"""
    def _read(path):
        vals = []
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    vals.append((row["date"], float(row["vix"])))
                except Exception:
                    continue
        return vals

    fresh = False
    if VIX_CSV.exists():
        age = (datetime.date.today() - datetime.date.fromtimestamp(VIX_CSV.stat().st_mtime)).days
        fresh = age <= max_age_days
    if not fresh:
        try:
            import os
            from dotenv import load_dotenv
            load_dotenv(BASE_DIR / ".env")
            from fredapi import Fred
            key = os.getenv("FRED_API_KEY")
            if key:
                s = Fred(api_key=key).get_series("VIXCLS")
                buck = {}
                for ts, v in s.dropna().items():
                    buck.setdefault(ts.strftime("%Y-%m"), []).append(float(v))
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                with open(VIX_CSV, "w", encoding="utf-8", newline="") as f:
                    wr = csv.writer(f)
                    wr.writerow(["date", "vix"])
                    for k in sorted(buck):
                        wr.writerow([k + "-01", round(sum(buck[k]) / len(buck[k]), 4)])
        except Exception:
            pass
    if not VIX_CSV.exists():
        return []
    cur_key = datetime.date.today().strftime("%Y-%m")
    return [v for d, v in _read(VIX_CSV) if d[:7] != cur_key]


def load_and_compute(current_gold=None, current_oil=None, current_vix=None):
    """读缓存 + 当日值 → 三屏结果 dict（含 verdict / npass / oil_cap_factor）。"""
    gold, oil, last_date = _load_gold_wti()
    vix = _load_vix()
    res = evaluate(gold, oil, vix, current_gold, current_oil, current_vix)
    res["ts"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    res["history_last"] = last_date
    return res
