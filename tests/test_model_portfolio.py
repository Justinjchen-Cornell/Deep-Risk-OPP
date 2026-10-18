# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "update_model_portfolio",
    Path(__file__).resolve().parents[1] / "scripts" / "update_model_portfolio.py",
)
ump = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ump)


def card(alloc, wti=100.0, gold=100.0, copper=100.0):
    return {
        "allocation": alloc,
        "data": {
            "WTI原油": {"price": wti},
            "黄金期货": {"price": gold},
            "COMEX铜": {"price": copper},
        },
    }


def pf(weights, prices, today="2026-10-18", nav=100.0):
    return {
        "base_nav": 100.0,
        "nav": nav,
        "weights": weights,
        "last_prices": prices,
        "history": [{"date": today, "nav": nav, "bench_spy": 100.0, "bench_6040": 100.0}],
        "trades": [],
        "inception_cost_paid": True,
        "benchmarks": {
            "spy": {"nav": 100.0, "last_price": prices.get("spy")},
            "6040": {"nav": 100.0, "last_price_spy": prices.get("spy"),
                     "last_price_agg": prices.get("agg")},
        },
    }


def test_all_legs_and_benchmarks():
    weights = {"油气": 25, "黄金": 25, "A股": 25, "铜": 25, "现金": 0}
    old = {"wti": 100, "gold": 100, "ashare": 100, "copper": 100, "spy": 100, "agg": 100}
    p = pf(weights, old, today="2026-10-18")
    prices = {"wti": 110, "gold": 110, "ashare": 110, "copper": 110, "spy": 110, "agg": 100}
    changed, _ = ump.run(p, card(weights, 110, 110, 110), prices, "2026-10-19", cost_bps=0)
    assert changed
    assert round(p["nav"], 4) == 110.0          # all four legs +10%
    assert round(p["benchmarks"]["spy"]["nav"], 4) == 110.0
    assert round(p["benchmarks"]["6040"]["nav"], 4) == 106.0
    row = p["history"][-1]
    assert row["bench_spy"] == 110.0 and row["bench_6040"] == 106.0


def test_cash_earns_zero():
    weights = {"油气": 0, "黄金": 0, "A股": 0, "铜": 0, "现金": 100}
    p = pf(weights, {"wti": 100, "gold": 100, "ashare": 100, "copper": 100,
                     "spy": 100, "agg": 100})
    prices = {"wti": 150, "gold": 150, "ashare": 150, "copper": 150,
              "spy": 110, "agg": 105}
    ump.run(p, card(weights, 150, 150, 150), prices, "2026-10-19", cost_bps=0)
    assert p["nav"] == 100.0


def test_rebalance_cost():
    old_weights = {"油气": 100, "黄金": 0, "A股": 0, "铜": 0, "现金": 0}
    p = pf(old_weights, {"wti": 100, "gold": 100, "ashare": 100, "copper": 100,
                         "spy": 100, "agg": 100}, today="2026-10-18")
    new_weights = {"油气": 50, "黄金": 0, "A股": 0, "铜": 0, "现金": 50}
    ump.run(p, card(new_weights, 100, 100, 100),
            {"wti": 100, "gold": 100, "ashare": 100, "copper": 100,
             "spy": 100, "agg": 100}, "2026-10-19", cost_bps=10)
    # turnover = 50% one-way; cost = 100 * 0.50 * 10bps = 0.05
    assert round(p["nav"], 4) == 99.95
    assert round(p["costs_paid"], 4) == 0.05
    trade = p["trades"][-1]
    assert trade["action"] == "rebalance" and trade["turnover_pct"] == 50.0


def test_same_day_is_idempotent():
    weights = {"油气": 50, "黄金": 50, "A股": 0, "铜": 0, "现金": 0}
    p = pf(weights, {"wti": 100, "gold": 100, "ashare": 100, "copper": 100,
                     "spy": 100, "agg": 100}, today="2026-10-19")
    prices = {"wti": 200, "gold": 200, "ashare": 200, "copper": 200,
              "spy": 200, "agg": 200}
    ump.run(p, card(weights, 200, 200, 200), prices, "2026-10-19", cost_bps=0)
    ump.run(p, card(weights, 200, 200, 200), prices, "2026-10-19", cost_bps=0)
    assert p["nav"] == 100.0
    assert len(p["history"]) == 1


def test_inception_cost():
    weights = {"油气": 50, "黄金": 0, "A股": 0, "铜": 0, "现金": 50}
    p = pf(weights, {"wti": 100, "gold": 100, "ashare": 100, "copper": 100,
                     "spy": 100, "agg": 100}, today="2026-10-18")
    p["inception_cost_paid"] = False
    ump.run(p, card(weights, 100, 100, 100),
            {"wti": 100, "gold": 100, "ashare": 100, "copper": 100,
             "spy": 100, "agg": 100}, "2026-10-18", cost_bps=5)
    # invested 50% × 5 bps = 0.025
    assert round(p["nav"], 4) == 99.975
    assert p["trades"][-1]["action"] == "inception"


def test_benchmark_first_run_then_next_day():
    weights = {"油气": 0, "黄金": 0, "A股": 0, "铜": 0, "现金": 100}
    p = {"base_nav": 100.0, "nav": 100.0, "weights": weights,
         "last_prices": {}, "history": [], "trades": [], "inception_cost_paid": True}
    prices = {"wti": 100, "gold": 100, "ashare": 100, "copper": 100,
              "spy": 100, "agg": 100}
    ump.run(p, card(weights), prices, "2026-10-18", cost_bps=0)
    assert p["benchmarks"]["spy"]["nav"] == 100.0
    assert p["benchmarks"]["6040"]["nav"] == 100.0
    prices2 = {"wti": 100, "gold": 100, "ashare": 100, "copper": 100,
               "spy": 110, "agg": 105}
    ump.run(p, card(weights), prices2, "2026-10-19", cost_bps=0)
    assert round(p["benchmarks"]["spy"]["nav"], 4) == 110.0
    assert round(p["benchmarks"]["6040"]["nav"], 4) == 108.0
