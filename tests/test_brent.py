# -*- coding: utf-8 -*-
import sys

from data_pipeline import common
from data_pipeline.quotes import provisional_card


def quality_data(**kw):
    d = {
        "gold": 4186.5, "wti": 101.84, "brent": 109.86, "copper": 6.56,
        "us10y": 5.1, "dxy": 101.84, "vix": 19.99, "us30y": 5.43,
        "fed_rate": 3.88, "fed_balance": 6.76, "m2": 23.34,
        "_q_gold": "akshare GC", "_q_wti": "akshare CL", "_q_brent": "yahoo",
        "_q_copper": "akshare HG", "_q_us10y": "FRED", "_q_dxy": "yfinance",
        "_q_vix": "cboe",
    }
    d.update(kw)
    return d


def test_real_brent_is_not_a_fallback():
    dq = common.build_data_quality(quality_data())
    assert dq["ok"] is True
    assert "布伦特" not in dq["fallbacks"]
    assert dq["sources"]["布伦特"] == "Yahoo BZ=F"


def test_synthetic_brent_marks_degraded():
    dq = common.build_data_quality(quality_data(_q_brent="estimated", brent=107.95))
    assert dq["ok"] is False
    assert "布伦特" in dq["fallbacks"]
    assert "合成" in dq["fallbacks"]["布伦特"]
    assert dq["warnings"]


def test_lagged_fred_brent_is_flagged():
    dq = common.build_data_quality(quality_data(_q_brent="fred-spot"))
    assert "布伦特" in dq["fallbacks"]
    assert "滞后" in dq["fallbacks"]["布伦特"]


def test_provisional_card_keeps_real_brent_source():
    card = {
        "data": {"WTI原油": {"price": 101.84}, "黄金期货": {"price": 4186.5},
                 "布伦特原油": {"price": 107.95}},
        "screener": {"vix": 19.99, "vix_thr": 22.46, "s2": False},
        "data_quality": {"ok": True, "fallbacks": {}, "sources": {}},
    }
    quotes = {
        "wti": {"price": 101.84, "time": "2026-10-16T20:59:00+00:00", "source": "yahoo"},
        "gold": {"price": 4186.5, "time": "2026-10-16T20:59:00+00:00", "source": "yahoo"},
        "brent": {"price": 109.86, "time": "2026-10-16T20:59:00+00:00", "source": "yahoo"},
        "vix": {"price": 19.99, "time": "2026-10-16T20:59:00+00:00", "source": "cboe-delayed"},
    }
    c = provisional_card(card, quotes)
    assert c["brent_source"] == "yahoo"
    assert c["gor_brent"] == round(4186.5 / 109.86, 2)
    assert c["data_quality"]["sources"]["布伦特"] == "yahoo"


def test_provisional_card_synthetic_is_explicit():
    card = {
        "data": {"WTI原油": {"price": 101.84}, "黄金期货": {"price": 4186.5}},
        "screener": {"vix": 19.99, "vix_thr": 22.46, "s2": False},
        "data_quality": {"ok": True, "fallbacks": {}, "sources": {}},
    }
    quotes = {
        "wti": {"price": 101.84, "time": "2026-10-16T20:59:00+00:00", "source": "yahoo"},
        "gold": {"price": 4186.5, "time": "2026-10-16T20:59:00+00:00", "source": "yahoo"},
        "vix": {"price": 19.99, "time": "2026-10-16T20:59:00+00:00", "source": "cboe-delayed"},
    }
    c = provisional_card(card, quotes)
    assert c["brent_source"] == "estimated"
    assert c["data_quality"]["ok"] is False
    assert "合成" in c["data_quality"]["fallbacks"]["布伦特"]


def test_fetch_brent_prefers_yahoo(monkeypatch):
    monkeypatch.setattr("data_pipeline.quotes._yahoo",
                        lambda sym: {"price": 109.86, "time": "t", "source": "yahoo"})
    price, source, asof = common.fetch_brent_price(101.84)
    assert (price, source, asof) == (109.86, "yahoo", "t")


def test_fetch_brent_falls_back_to_fred(monkeypatch):
    def boom(_sym):
        raise RuntimeError("no yahoo")
    monkeypatch.setattr("data_pipeline.quotes._yahoo", boom)
    monkeypatch.setattr("data_pipeline.quotes._tencent", boom)
    monkeypatch.setattr(common, "fred_get_last", lambda sid: (126.55, "2026-10-14"))
    price, source, asof = common.fetch_brent_price(101.84)
    assert (price, source, asof) == (126.55, "fred-spot", "2026-10-14")


def test_fetch_brent_last_resort_is_marked(monkeypatch):
    def boom(_sym):
        raise RuntimeError("no feed")
    monkeypatch.setattr("data_pipeline.quotes._yahoo", boom)
    monkeypatch.setattr("data_pipeline.quotes._tencent", boom)
    monkeypatch.setattr(common, "fred_get_last", lambda sid: (None, None))
    monkeypatch.setitem(sys.modules, "akshare", object())
    price, source, asof = common.fetch_brent_price(100.0)
    assert (price, source, asof) == (106.0, "estimated", None)


def test_save_gor_keeps_brent_source(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "BASE_DIR", tmp_path)
    monkeypatch.setattr(common, "DATA_DIR", tmp_path / "data")
    data = quality_data()
    gor = {
        "gor_brent": 38.11, "gor_wti": 41.11, "regime": "修复周期",
        "final_position": 30,
        "allocation": {"油气": 20, "黄金": 15, "现金": 58, "A股": 7, "铜": 0},
        "alerts": [], "screener": None,
    }
    out = common.save_gor_json(data, gor)
    assert out["brent_source"] == "yahoo"
    assert out["data_quality"]["sources"]["布伦特"] == "Yahoo BZ=F"

