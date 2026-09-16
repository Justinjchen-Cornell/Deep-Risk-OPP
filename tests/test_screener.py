"""机制筛选器单元测试（纯函数 + 配置不变量，源自延伸研究 #01/#02）"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.screener import evaluate, _pctl_threshold, _pctl_rank
import config


class TestEvaluate:
    def test_oil_leg_panic_low_oil_green(self):
        # 油腿（金平油崩）+ 恐慌 + 油低位 → 绿，上限 100%
        r = evaluate([100.0] * 72, [100.0] * 72, [15.0] * 120,
                     gold_now=105.0, oil_now=40.0, vix_now=45.0)
        assert r["s1"] is True and r["s2"] is True and r["s3"] is True
        assert r["verdict"] == "绿" and r["oil_cap_factor"] == 1.0

    def test_gold_leg_calm_red(self):
        # 金腿（金暴涨、油平）+ 平静 + 油高位 → 红，上限 0
        r = evaluate([100.0] * 72, [100.0] * 72, [20.0] * 120,
                     gold_now=170.0, oil_now=101.0, vix_now=15.0)
        assert r["s1"] is False and r["s2"] is False and r["s3"] is False
        assert r["verdict"] == "红" and r["oil_cap_factor"] == 0.0

    def test_panic_but_only_one_screen_yellow(self):
        # 恐慌✓ 但只有 1/3 → 黄，上限 50%
        r = evaluate([100.0] * 72, [100.0] * 72, [15.0] * 120,
                     gold_now=160.0, oil_now=100.0, vix_now=45.0)
        assert r["s2"] is True and r["npass"] == 1
        assert r["verdict"] == "黄" and r["oil_cap_factor"] == 0.5

    def test_calm_but_two_screens_yellow(self):
        # 无恐慌但 ≥2/3 → 黄（v1.1 规则：恐慌是一票必要条件，故不给绿）
        r = evaluate([100.0] * 72, [100.0] * 72, [20.0] * 120,
                     gold_now=105.0, oil_now=40.0, vix_now=15.0)
        assert r["s2"] is False and r["npass"] >= 2
        assert r["verdict"] == "黄"

    def test_insufficient_data(self):
        r = evaluate([], [], [], gold_now=4300.0, oil_now=104.0, vix_now=17.0)
        assert r["verdict"] == "数据不足" and r["oil_cap_factor"] is None


class TestHelpers:
    def test_pctl_threshold(self):
        vals = list(range(1, 101))
        assert 80 <= _pctl_threshold(vals, 0.80) <= 81

    def test_pctl_rank(self):
        assert _pctl_rank([1, 2, 3, 4], 4) == 1.0
        assert _pctl_rank([1, 2, 3, 4], 0) == 0.0


class TestConfig:
    def test_cap_invariants(self):
        caps = config.SCREENER_OIL_CAP
        assert caps["绿"] >= caps["黄"] >= caps["红"]
        assert all(0.0 <= v <= 1.0 for v in caps.values())

    def test_version_bumped_v23(self):
        assert config.SKILL_VERSION >= "2.3.0"
