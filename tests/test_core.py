"""
P1-3: 三个核心纯函数的单元测试
get_gor_zone / check_dynamic_hard_stop / get_allocation (+get_gor_blend)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modes.common import get_gor_zone, get_gor_blend, check_dynamic_hard_stop, get_allocation
import config


# ============ get_gor_zone ============
class TestGorZone:
    def test_extreme_upper(self):
        assert get_gor_zone(100) == "extreme"

    def test_extreme_lower_bound(self):
        assert get_gor_zone(45.0) == "extreme"          # 45 含入 extreme

    def test_recovery(self):
        assert get_gor_zone(44.9) == "recovery"
        assert get_gor_zone(30.0) == "recovery"

    def test_fair_value(self):
        assert get_gor_zone(29.9) == "fair_value"
        assert get_gor_zone(20.0) == "fair_value"

    def test_oil_bubble(self):
        assert get_gor_zone(19.9) == "oil_bubble"
        assert get_gor_zone(10) == "oil_bubble"

    def test_negative_unknown(self):
        assert get_gor_zone(-5) == "unknown"


# ============ get_gor_blend（43-47过渡带，消除18%跳变） ============
class TestGorBlend:
    def test_below_band_full_recovery(self):
        zone, blend = get_gor_blend(42.0)
        assert zone == "recovery" and blend == 0.0

    def test_band_midpoint(self):
        zone, blend = get_gor_blend(45.0)
        assert zone in ("extreme", "recovery")
        assert abs(blend - 0.5) < 1e-9               # (45-43)/4 = 0.5

    def test_band_top_full_extreme(self):
        zone, blend = get_gor_blend(47.0)
        assert zone == "extreme" and blend == 1.0

    def test_above_band_full_extreme(self):
        zone, blend = get_gor_blend(50.0)
        assert zone == "extreme" and blend == 1.0

    def test_blend_monotonic(self):
        blends = [get_gor_blend(g)[1] for g in (42, 43, 44, 45, 46, 47, 48)]
        assert blends == sorted(blends)


# ============ check_dynamic_hard_stop ============
def hist(prices, gors=None):
    """构造 wti_history 条目列表。"""
    n = len(prices)
    gors = gors or [60.0] * n
    return [{"date": f"2026-01-{i+1:02d}", "wti": p, "gold": 4000,
             "vix": 15, "gor_wti": g, "gor_brent": g} for i, (p, g) in enumerate(zip(prices, gors))]


class TestDynamicHardStop:
    def test_absolute_floor_always_triggers(self):
        ok, reason, shock = check_dynamic_hard_stop(wti=59.5, gor=60)
        assert ok and shock == "absolute_floor"

    def test_static_fallback_no_history(self):
        ok, reason, shock = check_dynamic_hard_stop(wti=74.0, gor=60, wti_history=None)
        assert ok and shock == "static_fallback"      # 无历史 → 回退静态$75
        ok2, _, shock2 = check_dynamic_hard_stop(wti=76.0, gor=60)
        assert not ok2 and shock2 == "none"

    def test_static_fallback_short_history(self):
        ok, _, shock = check_dynamic_hard_stop(wti=74.0, gor=60, wti_history=hist([80.0]*5))
        assert ok and shock == "static_fallback"      # <30天可用 → 静态回退

    def test_dynamic_no_trigger_above_sma(self):
        # 60天均价100，动态线85；WTI 90 > 85 → 不触发
        ok, _, _ = check_dynamic_hard_stop(wti=90.0, gor=55, wti_history=hist([100.0]*60))
        assert not ok

    def test_demand_shock_triggers(self):
        # WTI 80 < 85 动态线；GOR 5日 -10%（非供给冲击）→ 触发
        prices = [100.0]*55 + [80.0]*5
        gors = [55.0]*59 + [55.0, 50.0, 49.0, 48.0, 47.0]  # 近5日GOR下行
        ok, reason, shock = check_dynamic_hard_stop(wti=80.0, gor=47.0, vix=22,
                                                    wti_history=hist(prices, gors))
        assert ok and shock == "demand_shock"

    def test_supply_shock_overrides(self):
        # 同场景但 GOR 5日 +10%、VIX 15 → 供给冲击覆盖（不触发）
        prices = [100.0]*55 + [80.0]*5
        gors = [50.0]*59 + [50.0, 52.0, 54.0, 56.0, 58.0]
        ok, reason, shock = check_dynamic_hard_stop(wti=80.0, gor=58.0, vix=15,
                                                    wti_history=hist(prices, gors))
        assert not ok and shock == "supply_shock"


# ============ get_allocation ============
class TestAllocation:
    @staticmethod
    def _alloc(zone, **kw):
        """返回解包后的 alloc 字典（忽略 adjustments/hs/shock）。"""
        return get_allocation(zone, **kw)[0]

    def test_extreme_base(self):
        a = self._alloc("extreme", wti=90, gor=55)
        assert a["total"] == 70

    def test_dxy_and_yield_corrections_stack(self):
        a = self._alloc("extreme", dxy=100, yield_10y=4.5, wti=90, gor=55)
        assert a["total"] == 50                      # 70 -10 -10

    def test_components_scale_with_total(self):
        # FIX-2: 分项加总 = 风险敞口 (total)，现金补足100
        a = self._alloc("extreme", dxy=100, yield_10y=4.5, wti=90, gor=55)
        risk = a["oil"] + a["gold"] + a["a_shares"] + a["copper"]
        assert abs(risk - a["total"]) < 0.5
        assert abs(a["cash"] + risk - 100) < 0.5

    def test_hard_stop_caps_oil_at_5(self):
        a, adj, hs, shock = get_allocation("extreme", wti=70, gor=55)  # 无历史 → 静态回退触发
        assert hs and a["oil"] <= 5

    def test_transition_band_no_jump(self):
        # 43-47 过渡带：43与47之间仓位连续变化，且中间值介于两端之间
        a_low = self._alloc("recovery", wti=90, gor=43.5)
        a_mid = self._alloc("recovery", wti=90, gor=45.0)
        a_top = self._alloc("extreme", wti=90, gor=46.5)
        assert a_low["oil"] < a_mid["oil"] < a_top["oil"]

    def test_cash_never_negative(self):
        a = self._alloc("extreme", dxy=101, yield_10y=4.8, wti=70, gor=55)
        assert a["cash"] >= 0
