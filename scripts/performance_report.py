#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Content performance tracker — contract clause 6.

Source of truth: performance_log.json (repo root, committed)
Generated outputs:
  - performance_latest.json (public dashboard feed, committed)
  - 看板日志/linkedin/00_index/performance_log.md (local archive; 看板日志/ is gitignored)

Rules: never guess. Missing platform data is recorded as pending / no_data.

Usage:
  python scripts/performance_report.py --write
  python scripts/performance_report.py --list
  python scripts/performance_report.py --set 017-siphon-en-linkedin \
      --impressions 1200 --likes 18 --comments 4 --shares 2 --followers 3 --clicks 25
  python scripts/performance_report.py --no-data 015-brent-wti-cn-zhihu --note "平台未保留"
  python scripts/performance_report.py --import-linkedin-csv linkedin_export.csv --write
  python scripts/performance_report.py --check   # exit 1 if any 7d window is overdue
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import os
import re
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_JSON = os.path.join(BASE, "performance_log.json")
LOG_MD = os.path.join(BASE, "看板日志", "linkedin", "00_index", "performance_log.md")
OUT_JSON = os.path.join(BASE, "performance_latest.json")
TEMPLATE_CSV = os.path.join(BASE, "performance_backfill_template.csv")
BJ = timezone(timedelta(hours=8))
METRIC_FIELDS = ("impressions", "likes", "comments", "shares", "followers", "clicks")

# LinkedIn analytics exports vary by account type/locale. Match headers fuzzily.
LINKEDIN_ALIASES = {
    "id": ("id", "entry id"),
    "date": ("posted on", "post date", "date posted", "date", "created date",
             "publish date", "posted date", "发布日期", "发布日", "日期"),
    "title": ("post title", "title", "post text", "post content", "content",
              "post", "update", "description", "帖子标题", "标题", "帖子内容"),
    "url": ("post url", "url", "permalink", "link", "帖子链接", "链接"),
    "impressions": ("impressions", "impression", "post impressions",
                    "total impressions", "views", "曝光", "曝光次数",
                    "展示", "展示次数"),
    "likes": ("reactions", "likes", "reaction", "reaction count",
              "reactions count", "like count", "点赞", "赞", "赞同"),
    "comments": ("comments", "comment", "comment count", "评论", "评论数"),
    "shares": ("reposts", "shares", "reposts shares", "repost count",
               "share count", "转发", "转发数", "分享", "分享数"),
    "followers": ("followers", "followers gained", "new followers",
                  "follower growth", "follows", "follows gained",
                  "粉丝", "新增粉丝", "粉丝增长", "关注", "新增关注"),
    "clicks": ("clicks", "link clicks", "click count", "点击", "链接点击"),
    "engagements": ("engagements", "engagement", "total engagements",
                    "social engagements", "互动", "互动数", "互动次数"),
}


def _norm_header(s):
    return " ".join(re.sub(r"[^\w]+", " ", str(s).lower()).split())


def _norm_title(s):
    return _norm_header(s)


def _num(raw):
    """Parse '1,234', '2.5K', '12%', '—' -> int or None."""
    if raw is None:
        return None
    s = str(raw).strip().replace(",", "").replace(" ", "")
    if not s or s.lower() in ("-", "—", "–", "n/a", "na", "none", "null"):
        return None
    mult = 1
    if s[-1].lower() == "k":
        mult, s = 1000, s[:-1]
    elif s[-1].lower() == "m":
        mult, s = 1_000_000, s[:-1]
    s = s.rstrip("%")
    try:
        return int(round(float(s) * mult))
    except ValueError:
        return None


def _date_norm(raw):
    """Normalize common LinkedIn export date formats to YYYY-MM-DD."""
    s = str(raw or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d",
                "%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


def _map_linkedin_headers(fieldnames):
    normalized = {_norm_header(h): h for h in (fieldnames or []) if h}
    mapping = {}
    for field, aliases in LINKEDIN_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                mapping[field] = normalized[alias]
                break
    return mapping


def now_bj():
    return datetime.now(BJ)


def _parse_date(s):
    return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()


def _end_of_day(d):
    return datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=BJ)


def _engagements(e):
    if e.get("engagements") is not None:
        return int(e["engagements"])
    vals = [e.get("likes"), e.get("comments"), e.get("shares")]
    if all(v is None for v in vals):
        return None
    return sum(int(v or 0) for v in vals)


def load_doc(path=LOG_JSON):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_doc(doc, path=LOG_JSON):
    doc["updated"] = now_bj().strftime("%Y-%m-%d")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)


def build_report(doc, now=None):
    now = now or now_bj()
    today = now.date()
    baseline = _parse_date((doc.get("contract") or {}).get("baseline_start", "1970-01-01"))
    rows = []
    for e in doc.get("entries") or []:
        pub = _parse_date(e["publish_date"])
        status = e.get("status") or "pending"
        scope = "backfill" if pub < baseline else "contract"
        measured = status == "measured" and e.get("impressions") is not None
        mdt = None
        if e.get("measured_at"):
            try:
                mdt = datetime.fromisoformat(e["measured_at"])
                if mdt.tzinfo is None:
                    mdt = mdt.replace(tzinfo=BJ)
            except ValueError:
                mdt = None
        within_24h = bool(measured and mdt and mdt <= _end_of_day(pub + timedelta(days=1)))
        within_7d = bool(measured and mdt and mdt <= _end_of_day(pub + timedelta(days=7)))
        overdue_24h = (scope == "contract" and not measured and status != "planned"
                       and now > _end_of_day(pub + timedelta(days=1)))
        overdue_7d = (scope == "contract" and not measured and status != "planned"
                      and now > _end_of_day(pub + timedelta(days=7)))
        rows.append({
            "id": e.get("id"),
            "publish_date": pub.isoformat(),
            "platform": e.get("platform"),
            "title": e.get("title"),
            "piece": e.get("piece"),
            "language": e.get("language"),
            "scope": scope,
            "status": status,
            "impressions": e.get("impressions"),
            "engagements": _engagements(e),
            "followers": e.get("followers"),
            "clicks": e.get("clicks"),
            "measured": measured,
            "measured_at": e.get("measured_at"),
            "within_24h": within_24h,
            "within_7d": within_7d,
            "overdue_24h": overdue_24h,
            "overdue_7d": overdue_7d,
            "note": e.get("note") or "",
        })

    all_published = [r for r in rows
                     if r["status"] != "planned" and r["publish_date"] <= today.isoformat()]
    published = [r for r in all_published if r["scope"] == "contract"]
    backfill_rows = [r for r in all_published if r["scope"] == "backfill"]
    planned = [r for r in rows if r["status"] == "planned"]
    measured_rows = [r for r in published if r["measured"]]

    def _agg(group):
        imp = sum(int(r["impressions"] or 0) for r in group)
        eng = sum(int(r["engagements"] or 0) for r in group)
        fol = sum(int(r["followers"] or 0) for r in group)
        clk = sum(int(r["clicks"] or 0) for r in group)
        return {
            "published": len(group),
            "measured": sum(1 for r in group if r["measured"]),
            "impressions": imp,
            "engagements": eng,
            "followers": fol,
            "clicks": clk,
            "engagement_rate_pct": round(100.0 * eng / imp, 2) if imp else None,
            "follower_rate_pct": round(100.0 * fol / imp, 3) if imp else None,
        }

    by_platform = {}
    for p in sorted({r["platform"] for r in all_published}):
        by_platform[p] = _agg([r for r in all_published if r["platform"] == p])

    totals = _agg(all_published)
    backfill = _agg(backfill_rows)
    published_n = len(published)
    measured_n = len(measured_rows)
    overdue_7d = sum(1 for r in published if r["overdue_7d"])
    completeness = round(100.0 * measured_n / published_n, 1) if published_n else 0.0
    if published_n == 0:
        status = "not_started"
    elif measured_n == published_n:
        status = "ok"
    elif overdue_7d:
        status = "breach"
    else:
        status = "at_risk"

    return {
        "as_of": now.strftime("%Y-%m-%d %H:%M"),
        "contract": doc.get("contract") or {},
        "contract6": {
            "baseline_start": baseline.isoformat(),
            "published": published_n,
            "measured": measured_n,
            "completeness_pct": completeness,
            "within_24h": sum(1 for r in measured_rows if r["within_24h"]),
            "within_7d": sum(1 for r in measured_rows if r["within_7d"]),
            "overdue_24h": sum(1 for r in published if r["overdue_24h"]),
            "overdue_7d": overdue_7d,
            "status": status,
        },
        "backfill": backfill,
        "totals": totals,
        "by_platform": by_platform,
        "entries": sorted(rows, key=lambda r: (r["publish_date"], r["platform"]), reverse=True),
        "planned": planned,
    }


def render_markdown(report):
    c = report["contract6"]
    t = report["totals"]
    b = report.get("backfill") or {}

    def table_rows(rows, contract=True):
        out = []
        for r in rows:
            if r["status"] == "planned":
                continue
            if r["measured"]:
                vals = (r["impressions"], r["engagements"], r["followers"])
                status = "已回填" if contract else "已补录"
            elif r["status"] == "no_data":
                vals = ("无数据", "无数据", "无数据")
                status = "无数据"
            else:
                vals = ("无数据", "无数据", "无数据")
                if contract and r["overdue_7d"]:
                    status = "逾期(7d)"
                elif contract and r["overdue_24h"]:
                    status = "逾期(24h)"
                else:
                    status = "待回填" if contract else "待补录"
            out.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
                r["publish_date"], r["platform"], r["title"], vals[0], vals[1], vals[2],
                status, r["note"]))
        return out

    lines = [
        "# 内容绩效日志",
        "",
        "> 用途：兑现内容契约第 6 条（数据必须回收）+ 90 天证伪线（至 2027-01-14）。",
        "> 数据源：`performance_log.json`（结构化）；本页由 `scripts/performance_report.py` 生成，勿手改。",
        "> 回填节奏：发布后 24 小时一次、7 天一次；没有数据写“无数据”，不猜。",
        "",
        "<!-- PERFORMANCE:START -->",
        "## 契约第 6 条 · 回填状态（截至 %s）" % report["as_of"],
        "",
        "- 契约基线 **%s**：已发布 **%d** · 已回填 **%d**（**%.1f%%**）· 24h 回填 **%d** · 7d 回填 **%d** · 7d 逾期 **%d** · 状态 **%s**" % (
            c["baseline_start"], c["published"], c["measured"], c["completeness_pct"],
            c["within_24h"], c["within_7d"], c["overdue_7d"], c["status"]),
        "- 全口径曝光 **%s** · 互动 **%s**（%s）· 涨粉 **%s**（%s）；契约前补录 **%d** 条（已补 **%d**）" % (
            t["impressions"], t["engagements"],
            ("%.2f%%" % t["engagement_rate_pct"]) if t["engagement_rate_pct"] is not None else "—",
            t["followers"],
            ("%.3f%%" % t["follower_rate_pct"]) if t["follower_rate_pct"] is not None else "—",
            b.get("published", 0), b.get("measured", 0)),
        "",
        "### 契约内条目（基线 %s 起，计入契约 6）" % c["baseline_start"],
        "",
        "| 日期 | 平台 | 篇目 | 曝光 | 互动 | 涨粉 | 状态 | 备注 |",
        "|---|---|---|---:|---:|---:|---|---|",
    ]
    contract_rows = [r for r in report["entries"] if r.get("scope") == "contract"]
    backfill_rows = [r for r in report["entries"] if r.get("scope") == "backfill"]
    lines += table_rows(contract_rows, contract=True)
    if backfill_rows:
        lines += [
            "",
            "### 契约前基线补录（不计入契约 6 状态）",
            "",
            "| 日期 | 平台 | 篇目 | 曝光 | 互动 | 涨粉 | 状态 | 备注 |",
            "|---|---|---|---:|---:|---:|---|---|",
        ]
        lines += table_rows(backfill_rows, contract=False)
    if report["planned"]:
        lines += ["", "**计划发布**："]
        for r in report["planned"]:
            lines.append("- %s · %s · %s（%s）" % (
                r["publish_date"], r["platform"], r["title"], r["note"]))
    lines += [
        "",
        "### 回填命令",
        "",
        "```bash",
        "python scripts/performance_report.py --template          # 导出待填 CSV（9 条）",
        "python scripts/performance_report.py --import-csv performance_backfill_template.csv --write",
        "python scripts/performance_report.py --import-linkedin-csv linkedin_export.csv          # 预览匹配",
        "python scripts/performance_report.py --import-linkedin-csv linkedin_export.csv --write  # 保存",
        "python scripts/performance_report.py --set <id> --impressions N --likes N --comments N --shares N --followers N --clicks N",
        "python scripts/performance_report.py --no-data <id> --note \"平台未保留\"",
        "python scripts/performance_report.py --write",
        "```",
        "",
        "<!-- PERFORMANCE:END -->",
        "",
    ]
    return "\n".join(lines)


def write_outputs(doc, report, save_source=False):
    if save_source:
        save_doc(doc)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    os.makedirs(os.path.dirname(LOG_MD), exist_ok=True)
    with open(LOG_MD, "w", encoding="utf-8") as f:
        f.write(render_markdown(report))


def find_entry(doc, entry_id):
    for e in doc.get("entries") or []:
        if e.get("id") == entry_id:
            return e
    raise SystemExit("unknown id: %s" % entry_id)


def write_template(doc, path=TEMPLATE_CSV):
    """Export all published, unmeasured entries as a fill-in CSV (metrics left blank)."""
    baseline = _parse_date((doc.get("contract") or {}).get("baseline_start", "1970-01-01"))
    rows = []
    for e in doc.get("entries") or []:
        if e.get("status") == "planned" or e.get("status") == "measured":
            continue
        pub = _parse_date(e["publish_date"])
        rows.append({
            "id": e.get("id"),
            "scope": "contract" if pub >= baseline else "backfill",
            "publish_date": e.get("publish_date"),
            "platform": e.get("platform"),
            "title": e.get("title"),
            "impressions": "",
            "likes": "",
            "comments": "",
            "shares": "",
            "followers": "",
            "clicks": "",
            "note": e.get("note") or "",
        })
    fields = ["id", "scope", "publish_date", "platform", "title"] + list(METRIC_FIELDS) + ["note"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return path, len(rows)


def import_csv(doc, path):
    """Import filled metrics from a backfill CSV. Blank metric rows are skipped."""
    n = 0
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if not row.get("id"):
                continue
            has_metric = any(str(row.get(k) or "").strip() for k in METRIC_FIELDS)
            if not has_metric:
                continue
            e = find_entry(doc, row["id"])
            for k in METRIC_FIELDS:
                raw = str(row.get(k) or "").strip()
                if raw:
                    e[k] = int(float(raw))
            e["status"] = "measured"
            e["measured_at"] = now_bj().isoformat(timespec="minutes")
            if row.get("note"):
                e["note"] = row["note"]
            n += 1
    return n


def _linkedin_entries(doc):
    return [e for e in doc.get("entries") or []
            if str(e.get("platform", "")).lower() == "linkedin"
            and e.get("status") != "planned"]


def _match_linkedin_entry(doc, row, headers):
    entries = _linkedin_entries(doc)

    if "id" in headers:
        eid = str(row.get(headers["id"]) or "").strip()
        for e in entries:
            if e.get("id") == eid:
                return e, "id"

    if "url" in headers:
        url = str(row.get(headers["url"]) or "").strip().rstrip("/")
        if url:
            for e in entries:
                if str(e.get("url") or "").strip().rstrip("/") == url:
                    return e, "url"

    date = _date_norm(row.get(headers["date"])) if "date" in headers else None
    if date:
        cands = [e for e in entries if e.get("publish_date") == date]
        if len(cands) == 1:
            return cands[0], "date"

    title = str(row.get(headers["title"]) or "") if "title" in headers else ""
    if title:
        nt = _norm_title(title)
        cands = []
        for e in entries:
            et = _norm_title(e.get("title", ""))
            if et == nt or (len(et) >= 4 and len(nt) >= 4 and (et in nt or nt in et)):
                cands.append(e)
        if len(cands) == 1:
            return cands[0], "title"
        for kw in ("siphon", "diesel", "brent", "gor pulse"):
            if kw in nt:
                cands = [e for e in entries if kw in _norm_title(e.get("title", ""))]
                if len(cands) == 1:
                    return cands[0], "keyword:" + kw

    return None, None


def _row_metrics(row, headers):
    vals = {}
    for k in METRIC_FIELDS:
        if k in headers:
            v = _num(row.get(headers[k]))
            if v is not None:
                vals[k] = v
    if "engagements" in headers:
        v = _num(row.get(headers["engagements"]))
        if v is not None:
            vals["engagements"] = v
    return vals


def import_linkedin_csv(doc, path, create_missing=False):
    """Parse a LinkedIn analytics CSV and plan metric updates.

    Returns (planned_doc, rows). Does not mutate the input document.
    Matching order: explicit id -> post URL -> publish date -> title/keyword.
    """
    planned = copy.deepcopy(doc)
    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        headers = _map_linkedin_headers(reader.fieldnames or [])
        if not any(k in headers for k in METRIC_FIELDS + ("engagements",)):
            raise SystemExit(
                "LinkedIn CSV has no recognized metric columns. Headers: %s" %
                ", ".join(reader.fieldnames or []))

        results = []
        for line, row in enumerate(reader, start=2):
            metrics = _row_metrics(row, headers)
            if not metrics:
                results.append({"line": line, "id": "", "match": "no_metrics", "metrics": {}})
                continue
            e, how = _match_linkedin_entry(planned, row, headers)
            if e is None:
                if not create_missing:
                    results.append({"line": line, "id": "", "match": "unmatched", "metrics": metrics})
                    continue
                title = str(row.get(headers.get("title", "")) or "").strip() or "LinkedIn post"
                date = _date_norm(row.get(headers.get("date", ""))) or now_bj().date().isoformat()
                slug = re.sub(r"[^a-z0-9]+", "-", _norm_title(title)).strip("-")[:40] or "post"
                eid = "li-%s-%s" % (date.replace("-", ""), slug)
                base, n = eid, 2
                while any(x.get("id") == eid for x in planned.get("entries") or []):
                    eid = "%s-%d" % (base, n)
                    n += 1
                e = {
                    "id": eid, "publish_date": date, "platform": "LinkedIn",
                    "title": title, "piece": "", "language": "EN",
                    "url": str(row.get(headers.get("url", "")) or "").strip(),
                    "status": "measured", "impressions": None, "likes": None,
                    "comments": None, "shares": None, "followers": None,
                    "clicks": None, "measured_at": None,
                    "note": "created from LinkedIn CSV import",
                }
                planned.setdefault("entries", []).append(e)
                how = "created"

            for k, v in metrics.items():
                e[k] = v
            e["status"] = "measured"
            e["measured_at"] = now_bj().isoformat(timespec="minutes")
            url = str(row.get(headers.get("url", "")) or "").strip()
            if url and not e.get("url"):
                e["url"] = url
            note = e.get("note") or ""
            if "LinkedIn CSV 导入" not in note:
                e["note"] = (note + "；" if note else "") + "LinkedIn CSV 导入"
            results.append({"line": line, "id": e.get("id"), "match": how, "metrics": metrics})

    return planned, results


def main(argv=None):
    ap = argparse.ArgumentParser(description="Content performance tracker (contract clause 6)")
    ap.add_argument("--set", dest="set_id", help="entry id to update with measured numbers")
    ap.add_argument("--no-data", dest="no_data_id", help="entry id to mark as no_data")
    ap.add_argument("--impressions", type=int)
    ap.add_argument("--likes", type=int)
    ap.add_argument("--comments", type=int)
    ap.add_argument("--shares", type=int)
    ap.add_argument("--engagements", type=int)
    ap.add_argument("--followers", type=int)
    ap.add_argument("--clicks", type=int)
    ap.add_argument("--note")
    ap.add_argument("--template", nargs="?", const=TEMPLATE_CSV,
                    help="export published, unmeasured entries to a fill-in CSV")
    ap.add_argument("--import-csv", dest="import_csv", metavar="PATH",
                    help="import filled metrics from a backfill CSV")
    ap.add_argument("--import-linkedin-csv", dest="import_linkedin_csv", metavar="PATH",
                    help="import a LinkedIn analytics export (CSV/TSV); preview unless --write")
    ap.add_argument("--create-missing", action="store_true",
                    help="create a new LinkedIn entry when a CSV row matches nothing")
    ap.add_argument("--list", action="store_true", help="list pending/overdue entries")
    ap.add_argument("--check", action="store_true", help="exit 1 if any 7d window is overdue")
    ap.add_argument("--write", action="store_true", help="write performance_latest.json + markdown")
    ap.add_argument("--json", action="store_true", help="print machine-readable report")
    args = ap.parse_args(argv)

    doc = load_doc()
    touched = False

    if args.template:
        path, n = write_template(doc, args.template)
        print("wrote template: %s (%d unmeasured entries)" % (path, n))

    if args.import_linkedin_csv:
        planned, results = import_linkedin_csv(
            doc, args.import_linkedin_csv, create_missing=args.create_missing)
        if not args.json:
            print("linkedin CSV: %d row(s)" % len(results))
            for r in results:
                print("  line %-3s %-38s %-12s %s" % (
                    r["line"], r["id"] or "-", r["match"], r["metrics"]))
        if args.write:
            doc = planned
            touched = touched or any(
                r["match"] not in ("unmatched", "no_metrics") for r in results)
        elif not args.json:
            print("  preview only — add --write to save")

    if args.import_csv:
        n = import_csv(doc, args.import_csv)
        touched = touched or n > 0
        print("imported %d measured entries from %s" % (n, args.import_csv))

    if args.set_id:
        e = find_entry(doc, args.set_id)
        for k in ("impressions", "likes", "comments", "shares", "engagements",
                  "followers", "clicks"):
            v = getattr(args, k)
            if v is not None:
                e[k] = v
        e["status"] = "measured"
        e["measured_at"] = now_bj().isoformat(timespec="minutes")
        if args.note:
            e["note"] = args.note
        touched = True

    if args.no_data_id:
        e = find_entry(doc, args.no_data_id)
        e["status"] = "no_data"
        if args.note:
            e["note"] = args.note
        touched = True

    report = build_report(doc)

    if args.list:
        for r in report["entries"]:
            if r["status"] == "planned":
                continue
            if not r["measured"]:
                flag = "OVERDUE-7D" if r["overdue_7d"] else ("overdue-24h" if r["overdue_24h"] else "pending")
                print("%-8s %-38s %-10s %s" % (r["publish_date"], r["id"], flag, r["title"]))

    if args.write or touched:
        write_outputs(doc, report, save_source=touched)
        if not args.json:
            print("wrote", OUT_JSON)
            print("wrote", LOG_MD)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif not args.list:
        c = report["contract6"]
        print("contract6: published=%d measured=%d (%.1f%%) 24h=%d 7d=%d overdue_7d=%d status=%s" % (
            c["published"], c["measured"], c["completeness_pct"], c["within_24h"],
            c["within_7d"], c["overdue_7d"], c["status"]))

    if args.check and report["contract6"]["overdue_7d"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
