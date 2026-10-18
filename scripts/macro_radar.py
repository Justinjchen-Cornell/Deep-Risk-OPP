#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Weekly macro radar: Google News RSS + Google Trends + EIA RSS + FRED/FOMC calendar.

Local-first; no API keys beyond FRED_API_KEY in .env. Outputs:
  看板日志/data/macro-radar/macro_radar_YYYY-MM-DD.md
  看板日志/data/macro-radar/macro_radar_YYYY-MM-DD.json

Usage:
  python scripts/macro_radar.py
  python scripts/macro_radar.py --days 7 --geo US
"""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, time, timedelta
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "看板日志", "data", "macro-radar")
LINKEDIN_DIR = os.path.join(BASE, "看板日志", "data", "linkedin-analytics")
BJ = ZoneInfo("Asia/Shanghai")
ET_TZ = ZoneInfo("America/New_York")
HEADERS = {"User-Agent": "Mozilla/5.0 (Deep-Risk macro radar)"}

NEWS_TOPICS = [
    ("Oil", "oil price when:7d"),
    ("Gold", "gold price when:7d"),
    ("Fed/Rates", '"Federal Reserve" rates when:7d'),
    ("Treasury", '"Treasury yields" when:7d'),
    ("Inflation", "inflation CPI when:7d"),
    ("China", "China economy stimulus when:7d"),
]

# FRED release_id, display name, importance, typical ET time
FRED_RELEASES = [
    (10, "CPI", "★★★", time(8, 30)),
    (46, "PPI", "★★", time(8, 30)),
    (50, "Employment Situation", "★★★", time(8, 30)),
    (53, "GDP", "★★★", time(8, 30)),
    (54, "PCE", "★★★", time(8, 30)),
    (13, "Industrial Production", "★★", time(9, 15)),
]

MACRO_TREND_WORDS = re.compile(
    r"oil|gold|fed|federal reserve|inflation|cpi|ppi|treasury|yield|dollar|"
    r"china|recession|stock market|tariff|rate cut|rate hike|bitcoin|crypto|"
    r"bank|economy|jobs|unemployment|gdp|debt|deficit|energy|crude|opec",
    re.I,
)


def now_bj():
    return datetime.now(BJ)


def http_get(url, timeout=25):
    req = urllib.request.Request(url, headers=HEADERS)
    return urllib.request.urlopen(req, timeout=timeout).read()


def parse_rss_date(s):
    try:
        dt = parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return dt
    except Exception:
        return None


def bj_fmt(dt):
    return dt.astimezone(BJ).strftime("%Y-%m-%d %H:%M") if dt else "—"


def et_fmt(dt):
    return dt.astimezone(ET_TZ).strftime("%Y-%m-%d %H:%M") if dt else "—"


def fetch_google_news(days):
    out = {}
    for label, q in NEWS_TOPICS:
        url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote_plus(q) +
               "&hl=en-US&gl=US&ceid=US:en")
        try:
            root = ET.fromstring(http_get(url))
            items = []
            for it in root.findall(".//item"):
                title = (it.findtext("title") or "").strip()
                source = (it.findtext("source") or "").strip()
                if source and title.endswith(" - " + source):
                    title = title[:-(len(source) + 3)]
                dt = parse_rss_date(it.findtext("pubDate"))
                if dt and (now_bj() - dt.astimezone(BJ)).days > days + 1:
                    continue
                items.append({
                    "title": title,
                    "source": source,
                    "date": bj_fmt(dt),
                    "link": (it.findtext("link") or "").strip(),
                })
            items.sort(key=lambda x: x["date"], reverse=True)
            out[label] = items[:5]
        except Exception as e:
            out[label] = [{"error": repr(e)[:160]}]
    return out


def fetch_google_trends(geo):
    url = "https://trends.google.com/trending/rss?geo=" + geo
    root = ET.fromstring(http_get(url))
    ns = "{https://trends.google.com/trending/rss}"
    items = []
    for it in root.findall(".//item"):
        title = (it.findtext("title") or "").strip()
        traffic = (it.findtext(ns + "approx_traffic") or "").strip()
        source = (it.findtext(ns + "picture_source") or "").strip()
        dt = parse_rss_date(it.findtext("pubDate"))
        items.append({
            "title": title,
            "traffic": traffic,
            "source": source,
            "date": bj_fmt(dt),
            "macro": bool(MACRO_TREND_WORDS.search(title)),
        })
    return items


def fetch_eia_rss(days):
    out = []
    for name, url in [
        ("Today in Energy", "https://www.eia.gov/rss/todayinenergy.xml"),
        ("EIA Press", "https://www.eia.gov/rss/press_rss.xml"),
    ]:
        try:
            root = ET.fromstring(http_get(url))
            for it in root.findall(".//item"):
                dt = parse_rss_date(it.findtext("pubDate"))
                if dt is None:
                    continue
                if (now_bj() - dt.astimezone(BJ)).days > days + 1:
                    continue
                out.append({
                    "feed": name,
                    "title": (it.findtext("title") or "").strip(),
                    "date": bj_fmt(dt),
                    "_sort": bj_fmt(dt) if dt else "1970-01-01 00:00",
                    "link": (it.findtext("link") or "").strip(),
                    "summary": re.sub(r"<[^>]+>", "", it.findtext("description") or "")[:220],
                })
        except Exception as e:
            out.append({"feed": name, "error": repr(e)[:160], "_sort": ""})
    out.sort(key=lambda x: x.get("_sort", ""), reverse=True)
    for x in out:
        x.pop("_sort", None)
    return out[:12]


def fred_key():
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(BASE, ".env"))
    except Exception:
        pass
    return os.environ.get("FRED_API_KEY")


def fetch_fred_calendar(days):
    key = fred_key()
    if not key:
        return []
    start = now_bj().date().isoformat()
    end = (now_bj().date() + timedelta(days=days)).isoformat()
    events = []
    for rid, name, importance, et_time in FRED_RELEASES:
        url = ("https://api.stlouisfed.org/fred/release/dates?" +
               urllib.parse.urlencode({
                   "release_id": rid, "api_key": key, "file_type": "json",
                   "realtime_start": start, "realtime_end": end,
                   "include_release_dates_with_no_data": "true",
                   "sort_order": "asc", "limit": 50,
               }))
        try:
            data = json.loads(http_get(url))
            for row in data.get("release_dates", []):
                d = datetime.strptime(row["date"], "%Y-%m-%d").date()
                if not (now_bj().date() <= d <= now_bj().date() + timedelta(days=days)):
                    continue
                dt_et = datetime.combine(d, et_time, tzinfo=ET_TZ)
                bjt_dt = dt_et.astimezone(BJ)
                events.append({
                    "date": bjt_dt.date().isoformat(),
                    "weekday": bjt_dt.strftime("%a"),
                    "bjt": bjt_dt.strftime("%H:%M"),
                    "et": dt_et.strftime("%m-%d %H:%M"),
                    "event": name,
                    "importance": importance,
                    "source": "FRED",
                    "note": "时间按惯例，以官方为准",
                })
        except Exception as e:
            events.append({"date": "—", "event": name, "error": repr(e)[:160]})
    return events


def fetch_fomc_calendar(days):
    year = now_bj().year
    try:
        html = http_get("https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm").decode("utf-8", "ignore")
        m = re.search(rf"{year} FOMC Meetings.*?(?=<div class=\"panel-heading\"|$)", html, re.S)
        if not m:
            return []
        section = m.group(0)
        rows = re.findall(
            r"fomc-meeting__month[^>]*><strong>(\w+)</strong>.*?"
            r"fomc-meeting__date[^>]*>([^<]+)<", section, re.S)
        events = []
        for month, dates in rows:
            last = re.sub(r"\D", "", dates.split("-")[-1])
            if not last:
                continue
            d = datetime.strptime(f"{month} {last} {year}", "%B %d %Y").date()
            if not (now_bj().date() <= d <= now_bj().date() + timedelta(days=days)):
                continue
            dt_et = datetime.combine(d, time(14, 0), tzinfo=ET_TZ)
            bjt_dt = dt_et.astimezone(BJ)
            events.append({
                "date": bjt_dt.date().isoformat(), "weekday": bjt_dt.strftime("%a"),
                "bjt": bjt_dt.strftime("%H:%M"),
                "et": dt_et.strftime("%m-%d %H:%M"),
                "event": "FOMC 决议 + 发布会",
                "importance": "★★★", "source": "Fed",
                "note": "决议 14:00 ET，发布会 14:30 ET",
            })
        return events
    except Exception:
        return []


def fetch_eia_schedule(days):
    events = []
    d = now_bj().date()
    for i in range(days + 1):
        day = d + timedelta(days=i)
        if day.weekday() == 2:  # Wednesday
            dt_et = datetime.combine(day, time(10, 30), tzinfo=ET_TZ)
            bjt_dt = dt_et.astimezone(BJ)
            events.append({
                "date": bjt_dt.date().isoformat(), "weekday": bjt_dt.strftime("%a"),
                "bjt": bjt_dt.strftime("%H:%M"), "et": dt_et.strftime("%m-%d %H:%M"),
                "event": "EIA Weekly Petroleum Status Report",
                "importance": "★★★", "source": "EIA",
                "note": "库存/产量/炼化；能源腿核心",
            })
        if day.weekday() == 3:  # Thursday
            dt_et = datetime.combine(day, time(10, 30), tzinfo=ET_TZ)
            bjt_dt = dt_et.astimezone(BJ)
            events.append({
                "date": bjt_dt.date().isoformat(), "weekday": bjt_dt.strftime("%a"),
                "bjt": bjt_dt.strftime("%H:%M"), "et": dt_et.strftime("%m-%d %H:%M"),
                "event": "EIA Natural Gas Storage Report",
                "importance": "★★", "source": "EIA",
                "note": "天然气库存",
            })
    return events


def latest_linkedin_hot():
    if not os.path.isdir(LINKEDIN_DIR):
        return []
    files = sorted(f for f in os.listdir(LINKEDIN_DIR) if f.startswith("hot_posts_") and f.endswith(".json"))
    if not files:
        return []
    try:
        data = json.load(open(os.path.join(LINKEDIN_DIR, files[-1]), encoding="utf-8"))
        return data.get("posts", [])[:3]
    except Exception:
        return []


def load_gor():
    try:
        return json.load(open(os.path.join(BASE, "gor_latest.json"), encoding="utf-8"))
    except Exception:
        return {}


def news_titles(news, topic, n=2):
    return [x["title"] for x in news.get(topic, []) if "error" not in x][:n]


def own_stats():
    path = os.path.join(LINKEDIN_DIR, "linkedin_posts_analytics_export.json")
    try:
        posts = json.load(open(path, encoding="utf-8"))["posts"]
    except Exception:
        return {}
    def cat(p):
        d, t = p.get("post_date"), (p.get("title") or "").lower()
        if d in ("2026-10-12", "2026-10-07", "2026-10-04", "2026-09-25"):
            return "Energy/Oil"
        if d in ("2026-09-22", "2026-09-14", "2026-09-05", "2026-08-30",
                 "2026-08-29", "2026-08-12", "2026-07-27", "2026-07-20", "2026-07-13"):
            return "GOR/Gold"
        if d == "2026-08-23":
            return "Rates/Treasury" if "treasury" in t else "Macro/Other"
        if d in ("2026-10-03", "2026-09-08", "2026-08-09"):
            return "Rates/Treasury"
        if d in ("2026-09-17", "2026-09-16"):
            return "FOMC"
        if d in ("2026-09-10", "2026-09-02", "2026-08-31"):
            return "China/Currency"
        return "Macro/Other"
    stats = {}
    for p in posts:
        c = cat(p)
        s = stats.setdefault(c, {"n": 0, "imp": 0, "eng": 0, "fol": 0})
        s["n"] += 1
        s["imp"] += p.get("impressions") or 0
        s["eng"] += p.get("social_engagements") or 0
        s["fol"] += p.get("followers_gained") or 0
    for c, s in stats.items():
        s["avg_imp"] = round(s["imp"] / s["n"], 0) if s["n"] else 0
        s["eng_rate"] = round(100 * s["eng"] / s["imp"], 2) if s["imp"] else 0
    return stats


def build_linkedin_briefs(calendar, news, trends, linkedin, gor):
    """Generate specific LinkedIn post briefs from the radar + own analytics."""
    g = gor or {}
    d = g.get("data") or {}
    wti = (d.get("WTI原油") or {}).get("price")
    gold = (d.get("黄金期货") or {}).get("price")
    vix = (d.get("VIX恐慌指数") or {}).get("price")
    gor_w = g.get("gor_wti")
    gor_b = g.get("gor_brent")
    comp = None
    gap = None
    if isinstance(wti, (int, float)):
        comp = round(100 * (wti / 69.87 - 1) / (107.60 / 69.87 - 1), 1)
        gap = round(107.60 - wti, 2)
    stats = own_stats()
    events = " ".join(e.get("event", "") for e in calendar if "error" not in e)
    briefs = []

    def add(priority, timing, title, hook, fmt, evidence, cta, why):
        briefs.append({
            "priority": priority, "timing": timing, "title": title, "hook": hook,
            "format": fmt, "evidence": [x for x in evidence if x],
            "cta": cta, "why": why,
        })

    if gor_w is not None:
        add("P0", "10/19 08:00–09:00 BJT（若未发）",
            "GOR %.2f：45 线破了，40 是下一层地板吗？" % gor_w,
            "五周拉锯后，45 线终于破了——但机器仍然不动。",
            "1 个数字 + 3 条证据 + 二选一问题",
            ["GOR(WTI) %.2f / GOR(Brent) %.2f" % (gor_w, gor_b or 0),
             "合同完成度 %.1f%%，缺口 $%.2f" % (comp or 0, gap or 0),
             "VIX %s vs 门槛 22.5；仓位 %s%%" % (vix, g.get("final_position"))],
            "40 成为下一层地板，还是 45 线重新压回？",
            "GOR/Gold 是你互动率最高的类型（%.2f%%）；用固定格式承接 #008。" %
            (stats.get("GOR/Gold", {}).get("eng_rate", 0)))

    if "FOMC" in events:
        add("P0", "10/28–29（决议 10/29 02:00 BJT）",
            "FOMC 前夜：这次“暂停”比“加息”更难交易",
            "市场在赌 10 月暂停、12 月重启；真正的变量是发布会和点阵图。",
            "预注册 scorecard：3 个鹰派信号 vs 3 个鸽派信号 + 二选一",
            news_titles(news, "Fed/Rates", 2) + [
                "长端收益率 24 年新高；热通胀未退（CPI 3.7%）"],
            "暂停 = 鸽，还是“暂停但保留 12 月” = 鹰？",
            "FOMC 记分卡有差异化，但过去互动偏低；这次必须给一个可投票的问题。")

    if "GDP" in events or "PCE" in events:
        add("P0", "10/29 20:30 BJT",
            "GDP + PCE 同日：增长和通胀的错位",
            "同一天两份数据，市场只会选一个交易。",
            "数据卡片：预期 vs 前值 vs 资产反应；二选一",
            news_titles(news, "Inflation", 2) + ["GDP/PCE 同日发布"],
            "增长下修 + 通胀粘性，先交易衰退还是先交易利率？",
            "你的 Rates/Treasury 类型平均曝光 606、互动率 0.41%，是“曝光×互动”最平衡的题材。")

    if "EIA Weekly Petroleum" in events:
        add("P1", "10/21 或 10/28 22:30 BJT",
            "EIA 库存周：柴油、裂解、Brent–WTI，哪个先动？",
            "原油库存是头条，柴油和价差才是信号。",
            "一个对象，四种价格（WTI/Brent/柴油/黄金）",
            news_titles(news, "Oil", 2) + [
                "自己的 Brent–WTI 帖：773 曝光 / 87 触达"],
            "如果库存下降但柴油裂解不涨，是需求还是补库？",
            "Energy/Oil 平均曝光最高（794），但互动率只有 0.13%；用“四种价格”结构补互动。")

    oil_news = news_titles(news, "Oil", 3)
    if oil_news:
        add("P1", "本周（Oil 新闻热度最高）",
            "Hormuz 正常化 vs $150 尾部：油价的两种世界",
            "Citi 说 $150，JPM 说出口已恢复——同一个海峡，两个叙事。",
            "两种情景 + 一个被低估的变量（柴油/价差）",
            oil_news[:2] + ["J.P. Morgan：Hormuz 出口接近恢复（397 互动）"],
            "你交易正常化，还是尾部？",
            "Oil 是本周 Google News 最热话题；也是你曝光最强的类型。")

    gold_news = news_titles(news, "Gold", 3)
    if gold_news:
        add("P1", "本周（Gold 热点）",
            "Gold +64% 之后：GOR 现在告诉你什么",
            "WEF 的 +64%% 是过去；GOR %.2f 是现在。" % (gor_w or 0),
            "一个数字 + 三条反例 + 二选一",
            ["WEF：Gold +64%（715 互动）"] + gold_news[:1] + [
                "GOR(WTI) %.2f；合同完成度 %.1f%%" % (gor_w or 0, comp or 0)],
            "金价再涨 20%，油要涨多少才能让 GOR 回到 30？",
            "Gold/GOR 是 LinkedIn 互动最高的主题；WEF 已经把钩子做热。")

    treasury_news = news_titles(news, "Treasury", 3)
    if treasury_news:
        add("P2", "本周（Treasury 热点）",
            "24 年新高收益率：谁先撑不住？",
            "收益率新高不是“机会”，是一个压力测试。",
            "机制图：利率 → 美元 → 黄金/油；三个受害者",
            treasury_news[:2] + ["CPI 3.7%；热通胀 + AI 交易裂缝"],
            "先崩的是估值、信用，还是美元？",
            "Treasury 题材曝光不低，但“机会”角度互动弱；换成“谁先撑不住”。")

    china_news = news_titles(news, "China", 3)
    if china_news:
        add("P2", "本周（中国数据/刺激）",
            "中国刺激迟到：用美国利率看，而不是用中国情绪看",
            "IMF 喊刺激、信贷收缩、增长低于 4.5%——但交易在美元和长端。",
            "二阶思维：中国 → 商品 → 美元/利率",
            china_news[:2] + ["China/Currency 历史：0 互动、0 涨粉"],
            "中国刺激会先推高铜/油，还是先压美元？",
            "China/Currency 是你最弱的类型；必须换框架，不要单写中国。")

    if linkedin:
        add("P2", "本周（LinkedIn 热点拆解）",
            "WEF 的 Gold +64% 漏掉了什么？",
            "+64% 是价格故事；GOR 是相对故事。",
            "反方/二阶：用 GOR 拆 WEF 的黄金叙事",
            ["WEF Gold +64%：715 互动（赞 566 / 评 26 / 转 123）",
             "J.P. Morgan Hormuz：397 互动",
             "你的 GOR：%.2f / 合同 %.1f%%" % (gor_w or 0, comp or 0)],
            "如果金价再涨 20%，油要涨多少才能让 GOR 回到 30？",
            "LinkedIn 热点已经验证了 gold 叙事；用反方/数据拆解切入，比复述更容易互动。")

    if stats:
        top = max(stats.items(), key=lambda kv: kv[1]["avg_imp"])
        add("P2", "常青（随时可发）",
            "One barrel, four prices：把本周热点压成一张图",
            "WTI、Brent、柴油、黄金——四个价格，一个故事。",
            "一个对象，四种价格 + 可视化",
            ["One barrel, four prices：1,164 曝光",
             "Petroleum Engineers 蒸馏图：324 互动",
             "Energy/Oil 平均曝光 %.0f" % top[1]["avg_imp"]],
            "四个价格里，哪一个最失真？",
            "这是你曝光最强的结构；可视化解释帖也验证了互动。")

    # dedupe + cap
    seen, out = set(), []
    for b in briefs:
        if b["title"] in seen:
            continue
        seen.add(b["title"])
        out.append(b)
    return out[:8]


def build_suggestions(calendar, news, trends, linkedin):
    out = []
    high = [e for e in calendar if e.get("importance") == "★★★"]
    names = " ".join(e.get("event", "") for e in high)
    if "CPI" in names or "PCE" in names or "PPI" in names:
        out.append("通胀数据周：做一张“预期 vs 前值 vs 资产反应”卡片；从 GOR/黄金或长端利率切入。")
    if "Employment" in names:
        out.append("就业数据：用“强/弱就业 → 利率 → 美元 → 金/油”的链条，而不是只报数字。")
    if "GDP" in names:
        out.append("GDP：区分名义/实际与赤字路径；长端利率比增速本身更有交易含义。")
    if "FOMC" in names:
        out.append("FOMC：预注册 scorecard；用二选一问题（鹰/鸽、点阵图/发布会）引导评论。")
    if "EIA Weekly Petroleum" in names:
        out.append("EIA 库存周：结合柴油裂解、Brent–WTI 价差与 Borrowed Oil 叙事。")
    topic_counts = []
    for label, items in news.items():
        valid = [x for x in items if "error" not in x]
        if valid:
            topic_counts.append((label, len(valid)))
    if topic_counts:
        top = max(topic_counts, key=lambda kv: kv[1])[0]
        out.append("Google News 热度集中在 **%s**；用你的框架给反例/二阶影响，不要复述标题。" % top)
    macro_trends = [t for t in trends if t.get("macro")]
    if macro_trends:
        out.append("Google Trends 出现宏观词：%s；可作为开场钩子。" % "、".join(t["title"] for t in macro_trends[:3]))
    if linkedin:
        out.append("LinkedIn 高互动：%s（%d 互动）；可做数据拆解或反方观点。" % (
            linkedin[0].get("title", "")[:60], linkedin[0].get("engagements", 0)))
    if not out:
        out.append("本周无高重要度事件；适合做常青解释帖（一个对象，四种价格）。")
    return out[:6]


def render_markdown(radar):
    L = ["# 每周宏观热点雷达 · %s" % radar["date"], "",
         "> 窗口：未来 **%d 天** 日历 + 过去 **%d 天** 新闻" % (radar["days"], radar["news_days"]),
         "> 来源：Google News RSS · Google Trends RSS · EIA RSS · FRED release calendar · Fed FOMC calendar",
         "> 生成：%s BJT" % radar["generated_at"], ""]
    L += ["## 1. 未来 %d 天日历" % radar["days"], "",
          "| 北京日期 | 星期 | 北京 | 美东 | 事件 | 重要度 | 来源 | 备注 |",
          "|---|---|---|---:|---|---|---|---|"]
    cal = sorted(radar["calendar"], key=lambda x: (x.get("date", ""), x.get("bjt", "")))
    for e in cal:
        if "error" in e:
            L.append("| — | — | — | — | %s | — | — | ERROR: %s |" % (e.get("event"), e["error"]))
        else:
            L.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
                e["date"], e["weekday"], e["bjt"], e["et"], e["event"],
                e["importance"], e["source"], e.get("note", "")))
    if not cal:
        L.append("| — | — | — | — | 无高重要度事件 | — | — | — |")
    L += ["", "## 2. Google News（过去 %d 天）" % radar["news_days"], ""]
    for label, items in radar["news"].items():
        L.append("### %s" % label)
        valid = [x for x in items if "error" not in x]
        if not valid:
            L.append("- 无数据 / 抓取失败")
        for x in valid[:5]:
            L.append("- [%s](%s) — %s · %s" % (x["title"], x["link"], x["source"], x["date"]))
        L.append("")
    L += ["## 3. Google Trends · %s" % radar["geo"], ""]
    trends = radar["trends"]
    macro = [t for t in trends if t.get("macro")]
    shown = macro if macro else trends[:5]
    if not shown:
        L.append("- 无数据")
    for t in shown:
        L.append("- **%s** · %s · %s%s" % (
            t["title"], t.get("traffic", ""), t.get("source", ""),
            "" if t.get("macro") else "（非宏观，仅作背景）"))
    L += ["", "## 4. EIA 最新", ""]
    if not radar["eia"]:
        L.append("- 无数据 / 抓取失败")
    for x in radar["eia"][:8]:
        if "error" in x:
            L.append("- %s: ERROR %s" % (x.get("feed"), x["error"]))
        else:
            L.append("- [%s](%s) — %s · %s" % (x["title"], x["link"], x["feed"], x["date"]))
    L += ["", "## 5. LinkedIn 热点交叉", ""]
    if radar["linkedin"]:
        for x in radar["linkedin"]:
            L.append("- **%s** — %s · 互动 %d（赞 %d / 评 %d / 转 %d）" % (
                x.get("title", "")[:70], x.get("author", ""), x.get("engagements", 0),
                x.get("reactions", 0), x.get("comments", 0), x.get("reposts", 0)))
    else:
        L.append("- 暂无 LinkedIn 热点数据；先跑 `linkedin_intel.py hot`。")
    L += ["", "## 6. LinkedIn 选题引导", "",
          "| 优先级 | 时机 | 标题 | 结构 |", "|---|---|---|---|"]
    briefs = radar.get("linkedin_briefs") or []
    for b in briefs:
        L.append("| %s | %s | %s | %s |" % (
            b["priority"], b["timing"], b["title"].replace("|", "｜"),
            b["format"].replace("|", "｜")))
    if not briefs:
        L.append("| — | — | 暂无 | — |")
    for b in briefs:
        L += ["", "### %s · %s" % (b["priority"], b["title"]),
              "- **钩子**：%s" % b["hook"],
              "- **结构**：%s" % b["format"],
              "- **证据**：%s" % "；".join(b["evidence"]),
              "- **CTA**：%s" % b["cta"],
              "- **为什么**：%s" % b["why"]]
    L += ["", "## 7. 本周选题建议", ""]
    for s in radar["suggestions"]:
        L.append("- " + s)
    L += ["", "## 8. 口径与限制", "",
          "- FRED 日历使用 release_id + realtime 窗口；时间为通常发布时间，以官方为准。",
          "- Google News RSS 是聚合结果，存在标题党/重复；链接为 Google News 跳转。",
          "- Google Trends RSS 是美国日趋势，宏观词不一定每天都有。",
          "- EIA 日历按惯例：周三石油库存、周四天然气库存；节假日可能调整。",
          "- 本报告只做信号聚合，不构成投资建议。", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Weekly macro radar")
    ap.add_argument("--days", type=int, default=14, help="calendar lookahead days")
    ap.add_argument("--news-days", type=int, default=7, help="news lookback days")
    ap.add_argument("--geo", default="US")
    ap.add_argument("--out-dir", default=OUT_DIR)
    ap.add_argument("--latest", action="store_true",
                    help="also write macro_radar_latest.json/.md at repo root")
    ap.add_argument("--no-trends", action="store_true")
    args = ap.parse_args(argv)

    news = fetch_google_news(args.news_days)
    trends = []
    if not args.no_trends:
        try:
            trends = fetch_google_trends(args.geo)
        except Exception as e:
            print("google trends failed:", repr(e)[:160])
    eia = fetch_eia_rss(args.news_days)
    calendar = (fetch_fred_calendar(args.days) + fetch_eia_schedule(args.days) +
                fetch_fomc_calendar(args.days))
    linkedin = latest_linkedin_hot()
    gor = load_gor()
    briefs = build_linkedin_briefs(calendar, news, trends, linkedin, gor)
    suggestions = build_suggestions(calendar, news, trends, linkedin)

    radar = {
        "date": now_bj().strftime("%Y-%m-%d"),
        "generated_at": now_bj().strftime("%Y-%m-%d %H:%M"),
        "days": args.days,
        "news_days": args.news_days,
        "geo": args.geo,
        "calendar": calendar,
        "news": news,
        "trends": trends,
        "eia": eia,
        "linkedin": linkedin,
        "linkedin_briefs": briefs,
        "suggestions": suggestions,
    }
    os.makedirs(args.out_dir, exist_ok=True)
    stamp = now_bj().strftime("%Y-%m-%d")
    json_path = os.path.join(args.out_dir, "macro_radar_%s.json" % stamp)
    md_path = os.path.join(args.out_dir, "macro_radar_%s.md" % stamp)
    md = render_markdown(radar)
    json.dump(radar, open(json_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(md_path, "w", encoding="utf-8").write(md)
    print("saved:", json_path)
    print("saved:", md_path)
    if args.latest:
        latest_json = os.path.join(BASE, "macro_radar_latest.json")
        latest_md = os.path.join(BASE, "macro_radar_latest.md")
        json.dump(radar, open(latest_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        open(latest_md, "w", encoding="utf-8").write(md)
        print("saved:", latest_json)
        print("saved:", latest_md)
    print("calendar events:", len(calendar), "| news topics:", len(news),
          "| trends:", len(trends), "| EIA:", len(eia))
    for s in suggestions:
        print("  -", s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
