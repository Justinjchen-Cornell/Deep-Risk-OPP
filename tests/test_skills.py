# -*- coding: utf-8 -*-
"""Smoke tests for the vendored skills toolkit."""
import importlib.util
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dq = load("dq", "skills/data-quality-checker/dq_check.py")
gate = load("gate", "skills/pre-trade-discipline-gate/gate.py")
pm = load("pm", "skills/signal-postmortem/postmortem.py")
bt = load("bt", "skills/backtest-harness/backtest.py")


def _card():
    return {
        "updated": "2026-11-14 09:27",
        "gor_wti": 43.72, "gor_brent": 40.46,
        "final_position": 30,
        "allocation": {"油气": 20, "黄金": 15, "现金": 58, "A股": 7, "铜": 0},
        "screener": {"verdict": "红"},
        "data": {
            "黄金期货": {"price": 3887.6}, "WTI原油": {"price": 88.92},
            "布伦特原油": {"price": 96.08}, "美元指数DXY": {"price": 103.41},
            "10Y美债收益率": {"price": 5.1}, "VIX恐慌指数": {"price": 19.3},
            "COMEX铜": {"price": 6.1525},
        },
    }


def test_dq_valid_card():
    dq.ISSUES.clear()
    dq.check_card(_card())
    assert not [i for i in dq.ISSUES if i["severity"] == "ERROR"]


def test_dq_bad_allocation():
    dq.ISSUES.clear()
    c = _card(); c["allocation"]["现金"] = 50
    dq.check_card(c)
    assert any(i["code"] == "alloc_sum" for i in dq.ISSUES)


def test_gate_blocks_planless(monkeypatch):
    rc = gate.main(["--action", "add", "--asset", "oil", "--weight", "5", "--json"])
    assert rc == 1


def test_gate_blocks_oversized(monkeypatch):
    rc = gate.main(["--action", "add", "--asset", "oil", "--weight", "15",
                    "--thesis", "t", "--invalidation", "i", "--horizon", "3m",
                    "--max-loss", "2", "--json"])
    assert rc == 1


def test_gate_allows_planned_add(monkeypatch):
    rc = gate.main(["--action", "add", "--asset", "oil", "--weight", "5",
                    "--thesis", "t", "--invalidation", "i", "--horizon", "3m",
                    "--max-loss", "2", "--json"])
    assert rc == 0


def test_postmortem_threshold_hit():
    ser = {date(2026, 11, 1): 44.0, date(2026, 11, 2): 46.0}
    sig = {"date": "2026-11-01", "threshold": 45, "condition": "above", "horizon_days": 5}
    status, evidence = pm.eval_threshold(sig, ser)
    assert status == "hit" and "46" in evidence


def test_postmortem_threshold_miss():
    ser = {date(2020, 1, 1): 40.0, date(2020, 1, 2): 41.0}
    sig = {"date": "2020-01-01", "threshold": 45, "condition": "above", "horizon_days": 5}
    status, _ = pm.eval_threshold(sig, ser)
    assert status == "miss"


def test_backtest_runs(capsys):
    rc = bt.main(["--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert "full" in out and "strategy" in out["full"]
    assert out["params"]["cost_bps"] == 10.0
