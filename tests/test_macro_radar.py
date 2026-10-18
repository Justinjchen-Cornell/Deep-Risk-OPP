# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "macro_radar",
    Path(__file__).resolve().parents[1] / "scripts" / "macro_radar.py",
)
mr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mr)


def test_suggestions_cover_events_news_trends_linkedin():
    calendar = [
        {"event": "CPI", "importance": "★★★"},
        {"event": "FOMC 决议 + 发布会", "importance": "★★★"},
        {"event": "EIA Weekly Petroleum Status Report", "importance": "★★★"},
    ]
    news = {"Oil": [{"title": "Oil rises"}], "Gold": [{"title": "Gold falls"}]}
    trends = [{"title": "oil price", "macro": True}]
    linkedin = [{"title": "Gold +64%", "engagements": 715}]
    out = mr.build_suggestions(calendar, news, trends, linkedin)
    text = "\n".join(out)
    assert "通胀" in text
    assert "FOMC" in text
    assert "EIA" in text
    assert "LinkedIn" in text
    assert "Google News" in text


def test_linkedin_briefs_cover_events_and_gor():
    calendar = [
        {"event": "FOMC 决议 + 发布会", "importance": "★★★"},
        {"event": "GDP", "importance": "★★★"},
        {"event": "EIA Weekly Petroleum Status Report", "importance": "★★★"},
    ]
    news = {
        "Oil": [{"title": "Citi sees $150"}],
        "Gold": [{"title": "Gold +64%"}],
        "Fed/Rates": [{"title": "Fed pause debate"}],
        "Treasury": [{"title": "24-year high"}],
        "China": [{"title": "IMF urges stimulus"}],
        "Inflation": [{"title": "CPI 3.7%"}],
    }
    gor = {
        "gor_wti": 41.11, "gor_brent": 38.78, "final_position": 30,
        "data": {"WTI原油": {"price": 101.84}, "黄金期货": {"price": 4186.5},
                 "VIX恐慌指数": {"price": 19.99}},
    }
    briefs = mr.build_linkedin_briefs(calendar, news, [], [{"title": "WEF", "engagements": 715}], gor)
    titles = " ".join(b["title"] for b in briefs)
    assert "GOR 41.11" in titles
    assert "FOMC" in titles
    assert "GDP" in titles
    assert "EIA" in titles
    assert any(b["priority"] == "P0" for b in briefs)


def test_render_contains_all_sections():
    radar = {
        "date": "2026-10-18",
        "generated_at": "2026-10-18 22:00",
        "days": 14,
        "news_days": 7,
        "geo": "US",
        "calendar": [{
            "date": "2026-10-29", "weekday": "Thu", "bjt": "20:30",
            "et": "10-29 08:30", "event": "GDP", "importance": "★★★",
            "source": "FRED", "note": "",
        }],
        "news": {"Oil": [{"title": "Oil rises", "link": "https://x", "source": "Reuters", "date": "2026-10-18 10:00"}]},
        "trends": [{"title": "oil price", "traffic": "200+", "source": "x", "macro": True}],
        "eia": [{"feed": "Today in Energy", "title": "Solar", "date": "2026-10-16 22:00", "link": "https://eia"}],
        "linkedin": [{"title": "Gold +64%", "author": "WEF", "engagements": 715,
                      "reactions": 566, "comments": 26, "reposts": 123}],
        "suggestions": ["测试建议"],
    }
    md = mr.render_markdown(radar)
    assert "未来 14 天日历" in md
    assert "Google News" in md
    assert "Google Trends" in md
    assert "EIA 最新" in md
    assert "LinkedIn 热点交叉" in md
    assert "测试建议" in md

