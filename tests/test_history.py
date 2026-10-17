# -*- coding: utf-8 -*-
import json

from data_pipeline import history as H


def test_week_key():
    assert H.week_key('2026-10-17') == '2026-W42'


def make_output(wti=101.84, vix=19.99):
    return {
        "gor_wti": 41.11, "gor_brent": 38.78, "regime": "修复周期",
        "final_position": 30, "screener": {"verdict": "红"},
        "capital_three_flows": {"total": "收缩", "direction": "向心坍缩", "speed": "放缓"},
        "data": {
            "黄金期货": {"price": 4186.5}, "WTI原油": {"price": wti},
            "布伦特原油": {"price": 107.95}, "VIX恐慌指数": {"price": vix},
            "美元指数DXY": {"price": 101.84}, "10Y美债收益率": {"price": 5.1},
        },
    }


def test_record_upserts_same_day(tmp_path, monkeypatch):
    monkeypatch.setattr(H, "HISTORY", str(tmp_path / "history.json"))
    monkeypatch.setattr(H, "CHANGES", str(tmp_path / "changes.jsonl"))
    monkeypatch.setattr(H, "WEEKLY", str(tmp_path / "weekly.json"))
    monkeypatch.setattr(H, "WEEKLY_CHANGES", str(tmp_path / "weekly_changes.jsonl"))

    H.record(make_output())
    H.record(make_output())
    rows = json.load(open(tmp_path / "history.json", encoding="utf-8"))["rows"]
    assert len(rows) == 1
    assert rows[0]["gor_wti"] == 41.11

    H.record(make_output(vix=20.5))
    rows = json.load(open(tmp_path / "history.json", encoding="utf-8"))["rows"]
    assert len(rows) == 1 and rows[0]["vix"] == 20.5
    assert (tmp_path / "changes.jsonl").exists()
