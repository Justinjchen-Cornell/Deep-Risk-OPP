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


# ============ 每日管道 v2.1/v2.3 接线回归（2026-09-22 修复） ============
class TestDailyPipelineWiring:
    """生产路径 = data_pipeline.common.compute_gor（daily.yml → scripts/gor_daily.py）。

    历史回归：该文件曾从 run.py 导入 check_dynamic_hard_stop——P1-1 重构后函数已移入
    modes/common.py，ImportError 被 except 静默吞掉 → 动态硬止损沦为死代码。
    """

    def test_hard_stop_helper_uses_modes_common(self):
        from data_pipeline.common import _apply_dynamic_hard_stop
        alerts = []
        # 需求冲击：WTI 70 < 100×0.85=85，GOR 5日持平、VIX 30 ≥ 20 → 触发，返回上限 5
        cap = _apply_dynamic_hard_stop(70.0, 50.0, 30.0, hist([100.0] * 60), alerts)
        assert cap == 5
        assert alerts and alerts[0]["level"] == "critical"

    def test_hard_stop_helper_supply_override(self):
        from data_pipeline.common import _apply_dynamic_hard_stop
        alerts = []
        prices = [100.0] * 55 + [90.0] * 5
        gors = [50.0] * 55 + [50.0, 52.0, 54.0, 56.0, 58.0]
        # WTI 70 < 动态线；GOR 5日 +18%、VIX 15 平静 → 供给冲击覆盖，不触发
        cap = _apply_dynamic_hard_stop(70.0, 59.0, 15.0, hist(prices, gors), alerts)
        assert cap is None
        assert alerts and "供给冲击" in alerts[0]["title"]

    def test_screener_never_loosens_hard_stop(self):
        from data_pipeline.common import _overlay_screener
        green = {"oil_cap_factor": 1.0, "verdict": "绿", "npass": 3, "s1": True,
                 "s2": True, "vix": 30, "vix_thr": 22, "oil_pctl": 0.1}
        red = dict(green, oil_cap_factor=0.0, verdict="红", npass=1, s2=False)
        # 硬止损 5% + 绿（目标 25%）→ 维持 5%（旧实现会被抬回 25%）
        assert _overlay_screener(5, 25, 5, green, []) == 5
        # 硬止损 5% + 红（目标 0%）→ 0%
        assert _overlay_screener(5, 25, 5, red, []) == 0
        # 无硬止损 + 红 → 0%（线上现行公开行为，保持不变）
        assert _overlay_screener(25, 25, None, red, []) == 0
        # 无硬止损 + 绿 → 25%（不变）
        assert _overlay_screener(25, 25, None, green, []) == 25

    def test_compute_gor_smoke_no_screener(self, monkeypatch, tmp_path):
        """全链路冒烟：筛选器离线降级时也不得崩溃，且回归 extreme 基线。

        回归点：compute_gor 曾引用未定义的 v（动态止损传参）→ 静默回退。
        """
        import data_pipeline.common as dp_mod
        import data_pipeline.screener as scr_mod
        monkeypatch.setattr(dp_mod, "BASE_DIR", tmp_path)  # 不读仓库 wti_history.json，保证确定性
        monkeypatch.setattr(scr_mod, "load_and_compute",
                            lambda **kw: (_ for _ in ()).throw(RuntimeError("offline")))
        data = {"gold": 4380.4, "wti": 92.93, "brent": 96.26, "dxy": 100.39, "us10y": 5.01, "vix": 14.81}
        out = dp_mod.compute_gor(data)
        assert out["regime"] == "原油极端低估"
        assert out["allocation"]["油气"] == 25      # 无筛选器 → 基线
        assert out["allocation"]["黄金"] == 20
        assert out["allocation"]["现金"] == 48
        assert out["final_position"] == 50
        assert out["screener"] is None


# ============ config schema 校验 ============
class TestConfigSchema:
    def test_valid_config_passes(self):
        from data_pipeline.config_schema import validate_config
        assert validate_config() == []

    def test_detects_broken_zone_boundary(self):
        import config
        old = config.GOR_ZONES['extreme']['min']
        try:
            config.GOR_ZONES['extreme']['min'] = 30
            from data_pipeline.config_schema import validate_config
            problems = validate_config()
            assert any('extreme.min' in p for p in problems)
        finally:
            config.GOR_ZONES['extreme']['min'] = old

    def test_detects_bad_multiplier(self):
        import config
        old = config.HARD_STOP_MA_MULTIPLIER
        try:
            config.HARD_STOP_MA_MULTIPLIER = 1.5
            from data_pipeline.config_schema import validate_config
            problems = validate_config()
            assert any('HARD_STOP_MA_MULTIPLIER' in p for p in problems)
        finally:
            config.HARD_STOP_MA_MULTIPLIER = old
