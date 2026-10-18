# -*- coding: utf-8 -*-
import importlib.util
from datetime import datetime, timezone, timedelta
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "performance_report",
    Path(__file__).resolve().parents[1] / "scripts" / "performance_report.py",
)
pr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pr)

NOW = datetime(2026, 10, 18, 20, 0, tzinfo=timezone(timedelta(hours=8)))


def entry(eid="a", pub="2026-10-17", status="pending", **kw):
    e = {
        "id": eid, "publish_date": pub, "platform": "LinkedIn", "title": "T",
        "piece": "017", "language": "EN", "status": status,
        "impressions": None, "likes": None, "comments": None, "shares": None,
        "followers": None, "clicks": None, "measured_at": None, "note": "",
    }
    e.update(kw)
    return e


def test_zero_data_is_breach():
    doc = {"contract": {"clause": 6}, "entries": [
        entry("a", "2026-10-07", "pending"),
        entry("b", "2026-10-17", "pending"),
        entry("c", "2026-10-19", "planned"),
    ]}
    r = pr.build_report(doc, now=NOW)
    c = r["contract6"]
    assert c["published"] == 2
    assert c["measured"] == 0
    assert c["overdue_7d"] == 1
    assert c["status"] == "breach"


def test_measured_entry_and_rates():
    doc = {"contract": {"clause": 6}, "entries": [
        entry("a", "2026-10-17", "measured", impressions=1000, likes=10,
              comments=5, shares=5, followers=2, clicks=20,
              measured_at="2026-10-18T09:00+08:00"),
    ]}
    r = pr.build_report(doc, now=NOW)
    c = r["contract6"]
    assert c["measured"] == 1 and c["completeness_pct"] == 100.0
    assert c["within_24h"] == 1 and c["within_7d"] == 1
    assert r["totals"]["engagements"] == 20
    assert r["totals"]["engagement_rate_pct"] == 2.0
    assert r["totals"]["follower_rate_pct"] == 0.2


def test_backfill_not_counted_in_contract6():
    doc = {"contract": {"clause": 6, "baseline_start": "2026-10-16"}, "entries": [
        entry("a", "2026-10-07", "pending"),
        entry("b", "2026-10-17", "pending"),
        entry("c", "2026-10-19", "planned"),
    ]}
    r = pr.build_report(doc, now=NOW)
    c = r["contract6"]
    assert c["published"] == 1
    assert c["overdue_7d"] == 0
    assert c["status"] == "at_risk"
    assert r["backfill"]["published"] == 1
    md = pr.render_markdown(r)
    assert "契约前基线补录" in md


def test_no_data_is_counted_as_published_not_measured():
    doc = {"contract": {"clause": 6}, "entries": [
        entry("a", "2026-10-07", "no_data"),
    ]}
    r = pr.build_report(doc, now=NOW)
    assert r["contract6"]["published"] == 1
    assert r["contract6"]["measured"] == 0
    assert r["entries"][0]["status"] == "no_data"


def test_markdown_never_invents_numbers():
    doc = {"contract": {"clause": 6}, "entries": [
        entry("a", "2026-10-07", "pending"),
    ]}
    md = pr.render_markdown(pr.build_report(doc, now=NOW))
    assert "无数据" in md
    assert "逾期(7d)" in md
    assert "| 2026-10-07 | LinkedIn | T | 无数据 |" in md

