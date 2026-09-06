"""
Deep-Risk-OPP - mode goldmac (Gold Macro Validator, easing score)
=================================================================
Gold macro support factor (easing theme), replicated from Macrosynergy
"Gold and macro factors" (Sep 2026) with free FRED data. Validated
2016-2026 in-house: quarterly hit rate 67.5%, long-short Sharpe ~1.1
(see 08.投资决策框架/黄金宏观因子复刻).

Score: how strongly US macro pushes the Fed toward easing ->
lower real rates -> gold tailwind.
  > +1 strong easing bias (gold supportive)
  0..+1 mild easing | -1..0 mild tightening | < -1 strong tightening

Combined rule (GOR x easing):
  GOR extreme + easing high  -> oil leads, gold stays (double confirm)
  GOR extreme + easing low   -> oil on supply story; do NOT add gold
  GOR recovery + easing high -> gold re-rating window opens (add)
  GOR recovery + easing low  -> stand aside, cash

Usage: python run.py --mode goldmac
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

Z_THRESH = {"strong_ease": 1.0, "mild_ease": 0.0, "mild_tight": -1.0}
MIN_OBS = 36
WINSOR = 3.0
MIN_CONCEPTS = 2


def _fred():
    import fredapi
    key = os.getenv("FRED_API_KEY")
    if not key:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            key = os.getenv("FRED_API_KEY")
        except Exception:
            pass
    if not key:
        p = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), ".env")
        if os.path.exists(p):
            for line in open(p, encoding="utf-8", errors="ignore"):
                if line.strip().upper().startswith("FRED"):
                    key = line.split("=", 1)[1].strip()
                    break
    if not key:
        raise RuntimeError("FRED_API_KEY missing (env or repo .env)")
    return fredapi.Fred(key)


def _monthly(s, agg="last"):
    m = s.resample("ME")
    return (m.last() if agg == "last" else m.mean()).dropna()


def _z_rolling(x, window=120, min_obs=60):
    """Trailing rolling-window z (paper-style, no look-ahead)."""
    import numpy as np
    vals = np.asarray(x.values, dtype=float)
    out = np.full(len(vals), np.nan)
    for i in range(len(vals)):
        if i < min_obs:
            continue
        hist = vals[max(0, i - window):i]
        mu = hist.mean()
        sd = hist.std(ddof=1)
        if sd <= 0:
            continue
        z = (vals[i] - mu) / sd
        out[i] = max(-WINSOR, min(WINSOR, z))
    return __import__("pandas").Series(out, index=x.index)


def compute_easing():
    import numpy as np
    import pandas as pd

    f = _fred()
    m = _monthly

    cpi = m(f.get_series("CPIAUCSL"))
    cpcy = cpi.pct_change(12) * 100
    core = m(f.get_series("PCEPILFE"))
    core6 = (core / core.shift(6) - 1) * 200
    unrate = m(f.get_series("UNRATE"))
    un_yoy = unrate.rolling(3, min_periods=3).mean().diff(12)
    sloos_q = f.get_series("DRTSCILM")
    house = m(f.get_series("CSUSHPINSA"))
    house_yoy = house.pct_change(12) * 100

    cal = cpcy.index
    cal = cal[cal >= "1990-01-31"]                    # paper-like modern sample
    sloos_m = m(sloos_q).reindex(cal).ffill()

    concepts = {
        "cpi_gap": -(cpcy - 2.0).reindex(cal).ffill(),
        "core6_gap": -(core6 - 2.0).reindex(cal).ffill(),
        "unemp_rise": un_yoy.reindex(cal).ffill(),
        "sloos": sloos_m,
        "house_short": -((house_yoy - cpcy) - 1.5).reindex(cal).ffill(),
    }
    zs = {k: _z_rolling(v) for k, v in concepts.items()}
    panel = pd.DataFrame(zs)
    n_avail = panel.notna().sum(axis=1)
    mean = panel.mean(axis=1)
    mean[n_avail < MIN_CONCEPTS] = float("nan")
    score = _z_rolling(mean)
    valid = score.dropna()

    last = float(score.iloc[-1])
    if last > Z_THRESH["strong_ease"]:
        zone = "strong_ease"
    elif last > Z_THRESH["mild_ease"]:
        zone = "mild_ease"
    elif last > Z_THRESH["mild_tight"]:
        zone = "mild_tight"
    else:
        zone = "strong_tight"
    trend3 = last - float(score.iloc[-4]) if len(valid) >= 4 else 0.0
    trend6 = last - float(score.iloc[-7]) if len(valid) >= 7 else 0.0

    comp_last = {}
    for k in concepts:
        z = float(panel[k].iloc[-1])
        raw_series = concepts[k].dropna()
        comp_last[k] = {"raw": round(float(raw_series.iloc[-1]), 3)
                        if len(raw_series) else None,
                        "z": round(z, 2) if z == z else None}
    return {"score": round(last, 3), "zone": zone,
            "trend_3m": round(trend3, 2), "trend_6m": round(trend6, 2),
            "components": comp_last,
            "as_of": str(score.index[-1].date()),
            "history_start": str(valid.index[0].date()),
            "n": int(len(valid))}


def _gor_zone():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        with open(os.path.join(base, "gor_latest.json"), encoding="utf-8") as fh:
            d = json.load(fh)
        gor = float(d.get("gor_wti", 0) or 0)
        zone = None
        for name, zi in config.GOR_ZONES.items():
            if zi["min"] <= gor < zi["max"]:
                zone = name
                break
        return {"gor_wti": gor, "zone": zone,
                "regime": d.get("regime", ""),
                "as_of": d.get("updated", "")}
    except Exception:
        return None


def _action(ezone, gor):
    lab = {"strong_ease": "强宽松(利好黄金)", "mild_ease": "温和宽松",
           "mild_tight": "温和收紧", "strong_tight": "强收紧(压黄金)"}
    zone_label = lab.get(ezone, ezone)
    if gor is None:
        action = "GOR 数据缺失; easing 独立判断: " + (
            "黄金倾向可加档(等 GOR 双确认)" if ezone in ("strong_ease", "mild_ease")
            else "黄金不加档, 等利率战结束信号")
        return zone_label, action
    gz = gor.get("zone")
    if gz == "extreme":
        if ezone in ("strong_ease", "mild_ease"):
            action = "GOR 极端区(油便宜) + 宽松偏向 -> 油主攻, 金当盾; 黄金底仓保留(可微加)"
        else:
            action = "GOR 极端区 + 收紧 -> 油靠自身供给故事; 黄金不加档"
    elif gz == "recovery":
        if ezone in ("strong_ease", "mild_ease"):
            action = "GOR 恢复区 + 宽松转正 -> 黄金重估第二波窗口, 金可加档"
        else:
            action = "GOR 恢复区 + 收紧 -> 双逆风, 守现金"
    else:
        action = "GOR 中性区: easing 作辅助观察, 不单独触发动作"
    return zone_label, action


def mode_goldmac():
    print("  Gold Macro Validator (easing) - FRED 月频, 季频命中率 67.5% (2016-26 回测)")
    print("=" * 70)
    try:
        e = compute_easing()
    except Exception as ex:
        print("  [!] 计算失败:", type(ex).__name__, str(ex)[:150])
        print("      检查 FRED_API_KEY 与网络; 重试: python run.py --mode goldmac")
        return
    zone_label, action = _action(e["zone"], _gor_zone())
    print("  读数日期 : %s  (窗口 %s, n=%d)"
          % (e["as_of"], e["history_start"], e["n"]))
    print("  easing 分: %+.2f  |  3m %+.2f / 6m %+.2f  |  %s"
          % (e["score"], e["trend_3m"], e["trend_6m"], zone_label))
    print("  ---------------------------------------------")
    print("  组成(概念 -> z):")
    lab = {"cpi_gap": "CPI 低于目标", "core6_gap": "核心PCE走弱",
           "unemp_rise": "失业上行", "sloos": "信贷收紧",
           "house_short": "房价实质走弱"}
    for k, v in e["components"].items():
        z = v["z"]
        print("    %-14s z=%s" % (lab.get(k, k),
                                  "%+.2f" % z if z is not None else "n/a"))
    print("  ---------------------------------------------")
    print("  Action :", action)
    try:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(base, "goldmac_latest.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(e, fh, ensure_ascii=False, indent=1)
        print("  [saved] goldmac_latest.json")
    except Exception:
        pass
    print("  NOTE   : 慢信号(季频), 用于黄金仓位档位, 非择时交易信号。")
