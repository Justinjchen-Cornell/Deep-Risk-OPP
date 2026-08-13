"""
Deep-Risk-OPP — 核心纯函数 (P1-1 拆分自 run.py)
GOR 区间判定 / 动态硬止损 / 仓位分配。供 modes/* 与 pytest 共用。
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

def get_gor_zone(gor_value):
    """Classify GOR value into zone."""
    for zone_name, zone_info in config.GOR_ZONES.items():
        if zone_info["min"] <= gor_value < zone_info["max"]:
            return zone_name
    return "unknown"


def get_gor_blend(gor_value):
    """
    FIX-3: Linear transition band between extreme(>=45) and recovery(30-45).
    Returns (zone, blend) where blend in [0,1]:
      0.0 = fully recovery allocation
      1.0 = fully extreme allocation
    Band: GOR 43-47 interpolates linearly. Eliminates the 18% oil jump at 45.
    """
    zone = get_gor_zone(gor_value)
    if zone == "extreme":
        if gor_value < 47:
            blend = (gor_value - 43) / 4.0  # 43→0, 47→1
            return ("extreme", max(0.0, min(1.0, blend)))
        return ("extreme", 1.0)
    if zone == "recovery":
        if gor_value >= 43:
            blend = (gor_value - 43) / 4.0
            return ("recovery", max(0.0, min(1.0, blend)))
        return ("recovery", 0.0)
    return (zone, 1.0 if zone == "extreme" else 0.0)


def check_dynamic_hard_stop(wti, gor, vix=None, dxy=None, wti_history=None):
    """
    Dynamic Hard Stop (v2.1): replaces static $75 rule.

    Returns: (is_hard_stop: bool, reason: str, shock_type: str)

    Logic:
      1. Absolute floor: WTI < WTI_ABSOLUTE_FLOOR → ALWAYS trigger
      2. Technical trigger: WTI < 60-day SMA × 0.85?
      3. If triggered, check shock type:
         - Supply shock (GOR↑ > 5% while WTI↓, VIX calm) → OVERRIDE (no stop)
         - Demand shock (GOR flat/↓ while WTI↓, VIX elevated) → TRIGGER
      4. Without history data → fall back to static comparison against SMA
    """
    # Absolute floor — always trigger
    if wti is not None and wti < config.WTI_ABSOLUTE_FLOOR:
        return (True, f"WTI ${wti:.2f} < absolute floor ${config.WTI_ABSOLUTE_FLOOR}", "absolute_floor")

    # Need historical data for dynamic rule
    if wti_history is None or len(wti_history) < 10:
        # Fallback: compare to static $75 (legacy behavior)
        if wti is not None and wti < config.WTI_HARD_STOP:
            return (True, f"WTI ${wti:.2f} < ${config.WTI_HARD_STOP} (legacy static fallback — no history data)", "static_fallback")
        return (False, f"WTI ${wti:.2f} >= ${config.WTI_HARD_STOP} (legacy static)", "none")

    # Compute 60-day SMA
    recent_prices = [d.get("wti", 0) for d in wti_history[-config.HARD_STOP_MA_PERIOD:] if d.get("wti", 0) > 0]
    if len(recent_prices) < 30:
        # Not enough data — fall back
        if wti is not None and wti < config.WTI_HARD_STOP:
            return (True, f"WTI ${wti:.2f} < ${config.WTI_HARD_STOP} (not enough history for dynamic SMA)", "static_fallback")
        return (False, f"WTI ${wti:.2f} >= ${config.WTI_HARD_STOP}", "none")

    sma_60 = sum(recent_prices) / len(recent_prices)
    dynamic_threshold = sma_60 * config.HARD_STOP_MA_MULTIPLIER

    # Technical trigger: is WTI below the dynamic threshold?
    if wti is None or wti >= dynamic_threshold:
        return (False, f"WTI ${wti:.2f} >= 60d SMA×0.85 = ${dynamic_threshold:.2f}", "none")

    # --- Technical trigger fired. Now determine shock type. ---

    # Compute 5-day GOR change
    if len(wti_history) >= 6:
        gor_5d_ago = wti_history[-6].get("gor_wti", gor)
        gor_change_5d = (gor - gor_5d_ago) / gor_5d_ago if gor_5d_ago > 0 else 0
    else:
        gor_change_5d = 0

    # Determine shock type:
    # Supply shock = GOR rising (gold holds, oil drops) + VIX not spiking
    # Demand shock = GOR flat/falling (everything drops) + VIX elevated
    is_supply_shock = (
        gor_change_5d > config.GOR_SUPPLY_SHOCK_RISE
        and (vix is None or vix < config.VIX_DEMAND_CONFIRM)
    )

    vix_str = f"{vix:.1f}" if vix else "N/A"
    if is_supply_shock:
        return (False,
                f"Supply shock detected: GOR change +{gor_change_5d:.1%} (5d), VIX {vix_str} < {config.VIX_DEMAND_CONFIRM}. "
                f"WTI ${wti:.2f} < SMA threshold ${dynamic_threshold:.2f} but hard stop OVERRIDDEN.",
                "supply_shock")
    else:
        vix_confirm = f", VIX {vix:.1f} >= {config.VIX_DEMAND_CONFIRM}" if vix and vix >= config.VIX_DEMAND_CONFIRM else ""
        return (True,
                f"Demand shock: WTI ${wti:.2f} < SMA threshold ${dynamic_threshold:.2f}. "
                f"GOR change {gor_change_5d:+.1%} (5d){vix_confirm}. Hard stop TRIGGERED.",
                "demand_shock")


def get_allocation(zone, dxy=None, yield_10y=None, wti=None, gor=None, vix=None, wti_history=None):
    """Compute allocation with risk corrections (v2.1: dynamic hard stop)."""
    # FIX-3: blend across transition band
    base = config.BASE_ALLOCATION.get(zone, config.BASE_ALLOCATION["fair_value"])
    alloc = dict(base)
    adjustments = []
    hard_stop_active = False
    shock_type = "none"

    # Apply transition blend for extreme<->recovery boundary (GOR 43-47)
    if gor is not None and zone in ("extreme", "recovery"):
        blend_zone, blend = get_gor_blend(gor)
        if 0.0 < blend < 1.0:
            other_zone = "recovery" if zone == "extreme" else "extreme"
            other_alloc = config.BASE_ALLOCATION[other_zone]
            for k in alloc:
                if zone == "extreme":
                    # blend=1 → 全 extreme；blend=0 → 全 recovery
                    alloc[k] = round(alloc[k] * blend + other_alloc[k] * (1 - blend), 1)
                else:
                    # recovery 侧：blend 表示向 extreme 的权重，当前 zone 权重为 (1-blend)
                    # FIX-4: 原公式 recovery*blend + extreme*(1-blend) 反转了两侧权重
                    alloc[k] = round(alloc[k] * (1 - blend) + other_alloc[k] * blend, 1)
            adjustments.append(f"GOR {gor:.1f} in transition band: {zone}({1-blend:.0%}) + {other_zone}({blend:.0%})")
    # Snapshot blended risk BEFORE corrections (for FIX-2 scaling)
    risk_keys = ["oil", "gold", "a_shares", "copper"]
    blended_risk = sum(alloc.get(k, 0) for k in risk_keys)

    # Dynamic hard stop (v2.1)
    if wti is not None and gor is not None:
        hard_stop_active, hard_stop_reason, shock_type = check_dynamic_hard_stop(
            wti, gor, vix=vix, wti_history=wti_history
        )
        adjustments.append(hard_stop_reason)

    # Apply hard stop if triggered
    if hard_stop_active:
        oil_before = alloc.get("oil", 0)
        alloc["oil"] = min(alloc["oil"], 5)
        alloc["cash"] = alloc.get("cash", 50) + (oil_before - alloc["oil"])

    # DXY correction
    if dxy is not None and dxy > config.DXY_THRESHOLD:
        adj = -10
        alloc["total"] = max(5, alloc["total"] + adj)
        adjustments.append(f"DXY {dxy:.2f} > {config.DXY_THRESHOLD}: total {adj:+d}%")

    # Yield correction
    if yield_10y is not None and yield_10y > config.YIELD_THRESHOLD:
        adj = -10
        alloc["total"] = max(5, alloc["total"] + adj)
        adjustments.append(f"10Y {yield_10y:.2f}% > {config.YIELD_THRESHOLD}%: total {adj:+d}%")

    # FIX-2: Scale risk components proportionally to corrected total.
    # total = oil + gold + a_shares + copper (risk assets). cash = 100 - risk.
    # Prevents "total 50% but components sum 100%" inconsistency.
    target_risk = max(5, alloc["total"])  # total after corrections
    if blended_risk > 0:
        scale = target_risk / blended_risk
        for k in risk_keys:
            alloc[k] = round(alloc.get(k, 0) * scale, 1)
    alloc["cash"] = max(0, 100 - sum(alloc.get(k, 0) for k in risk_keys))

    # FIX-5: 比例缩放可能把 oil 放大回 5% 以上 —— 硬止损上限必须最后再施加一次
    if hard_stop_active and alloc.get("oil", 0) > 5:
        alloc["cash"] += alloc["oil"] - 5
        alloc["oil"] = 5

    return alloc, adjustments, hard_stop_active, shock_type
