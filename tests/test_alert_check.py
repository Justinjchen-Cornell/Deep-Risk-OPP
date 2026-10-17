# -*- coding: utf-8 -*-
import json
from datetime import datetime, timezone

from data_pipeline.alerts import (build_state, evaluate, hard_stop_threshold,
                                  load_state, save_state)


def make_card(wti=100.0, gold=4000.0, gor=40.0, regime="修复周期", position=30,
              verdict="红", vix=16.0, vix_thr=22.46, oil_pctl=0.90,
              s2=False, s3=False):
    return {
        "updated": "2026-10-17 12:00",
        "gor_wti": gor,
        "gor_brent": gor - 2.0,
        "regime": regime,
        "final_position": position,
        "screener": {
            "vix": vix, "vix_thr": vix_thr, "oil_pctl": oil_pctl,
            "s2": s2, "s3": s3, "verdict": verdict, "npass": 1,
        },
        "data": {
            "WTI原油": {"price": wti},
            "黄金期货": {"price": gold},
        },
    }


def flat_history(wti=100.0, n=60):
    return [{"date": "2026-01-%02d" % (i % 28 + 1), "wti": wti} for i in range(n)]


def state(wti=100.0, **kw):
    return build_state(make_card(wti=wti, **kw), flat_history(100.0))


def test_hard_stop_threshold():
    assert hard_stop_threshold(flat_history(100.0)) == 85.0
    assert hard_stop_threshold(flat_history(100.0, n=10)) is None


def test_baseline_no_alerts():
    assert evaluate(None, state()) == []


def test_hard_stop_transition():
    prev = state(wti=100.0)
    curr = state(wti=80.0)
    rules = [a["rule"] for a in evaluate(prev, curr)]
    assert "hard_stop" in rules
    assert evaluate(prev, curr)[0]["severity"] == "P0"


def test_capitulation_transition():
    prev = state(s2=False, s3=True, vix=16.0)
    curr = state(s2=True, s3=True, vix=25.0)
    rules = [a["rule"] for a in evaluate(prev, curr)]
    assert "capitulation" in rules


def test_regime_and_position_change():
    prev = state(regime="修复周期", position=30)
    curr = state(regime="极端区", position=50, gor=46.0)
    rules = [a["rule"] for a in evaluate(prev, curr)]
    assert "regime_change" in rules
    assert "position_change" in rules


def test_contract_target_hit():
    prev = state(wti=107.0)
    curr = state(wti=108.0)
    rules = [a["rule"] for a in evaluate(prev, curr)]
    assert "contract_target" in rules


def test_contract_90_crossing():
    prev = state(wti=100.0)
    curr = state(wti=104.0)
    rules = [a["rule"] for a in evaluate(prev, curr)]
    assert "contract_90" in rules


def test_gor_cross_below_42():
    prev = state(gor=43.0)
    curr = state(gor=41.5)
    alerts = evaluate(prev, curr)
    rules = [a["rule"] for a in alerts]
    assert "gor_below_42" in rules
    assert all(a["severity"] == "P2" for a in alerts if a["rule"] == "gor_below_42")


def test_no_alerts_when_unchanged():
    s = state()
    assert evaluate(s, s) == []


def test_state_roundtrip(tmp_path):
    p = tmp_path / "state.json"
    s = state(wti=101.84)
    save_state(p, s)
    loaded = load_state(p)
    assert loaded["wti"] == 101.84
    assert loaded["regime"] == "修复周期"
    assert load_state(tmp_path / "missing.json") is None


def test_intraday_suppresses_slow_rules():
    prev = state(regime="修复周期", position=30)
    curr = state(regime="极端区", position=50, gor=46.0)
    rules = [a["rule"] for a in evaluate(prev, curr, intraday=True)]
    assert "regime_change" not in rules
    assert "position_change" not in rules
    assert "gor_below_42" not in rules


def test_intraday_keeps_core_rules():
    prev = state(wti=100.0)
    curr = state(wti=80.0)
    rules = [a["rule"] for a in evaluate(prev, curr, intraday=True)]
    assert "hard_stop" in rules


def test_delivery_no_channels(monkeypatch):
    from data_pipeline import delivery
    for k in ("FEISHU_WEBHOOK", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
              "DINGTALK_WEBHOOK", "SERVERCHAN_SENDKEY"):
        monkeypatch.delenv(k, raising=False)
    assert delivery.configured_channels() == []


def test_delivery_message_contains_id():
    from data_pipeline import delivery
    a = {"severity": "P0", "rule": "hard_stop", "title": "硬止损触发",
         "message": "WTI < 阈值", "id": "2026-10-17T07:12Z-hard_stop",
         "current": {"gor_wti": 41.1, "wti": 58.2, "vix": 30.0, "position": 30}}
    msg = delivery.format_message(a)
    assert "P0" in msg and "硬止损触发" in msg
    assert "2026-10-17T07:12Z-hard_stop" in msg


def test_select_for_delivery():
    from data_pipeline.alerts import select_for_delivery
    alerts = [{"severity": "P0"}, {"severity": "P1"}, {"severity": "P2"}]
    assert len(select_for_delivery(alerts, "P0")) == 1
    assert len(select_for_delivery(alerts, "P1")) == 2
    assert len(select_for_delivery(alerts, "P2")) == 3
