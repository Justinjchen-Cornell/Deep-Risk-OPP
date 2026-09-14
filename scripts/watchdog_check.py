#!/usr/bin/env python3
"""
Pipeline Watchdog — checks that gor_latest.json was refreshed today.

Rule: the daily pipeline (cron 00:00 UTC = 08:00 Beijing) writes
gor_latest.json with `updated` = "YYYY-MM-DD 12:00" (Beijing date).
If the date is not today's Beijing date, the pipeline missed at least
one run → the public site is serving stale data → exit 1.

Usage:
    python scripts/watchdog_check.py [--path file] [--grace-days N]
"""
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone

BASE_DIR = Path(__file__).resolve().parent.parent
BEIJING = timezone(timedelta(hours=8))


def load(path):
    d = json.loads(path.read_text(encoding='utf-8'))
    updated = str(d.get('updated', '')).strip()
    return d, updated


def check(path: Path, grace_days: int) -> tuple[bool, str]:
    """Returns (fresh, message)."""
    if not path.exists():
        return False, f"STALE: {path.name} does not exist"
    try:
        d, updated = load(path)
    except Exception as e:
        return False, f"STALE: {path.name} unreadable or invalid JSON: {e}"

    # Sanity: must contain a GOR number
    if not isinstance(d.get('gor_wti'), (int, float)):
        return False, f"STALE: gor_wti missing in {path.name}"

    try:
        updated_date = datetime.strptime(updated[:10], '%Y-%m-%d').date()
    except ValueError:
        return False, f"STALE: bad updated format: {updated!r}"

    today_bj = datetime.now(BEIJING).date()
    oldest_ok = today_bj - timedelta(days=grace_days)
    if updated_date < oldest_ok:
        return False, (
            f"STALE: updated={updated} | today(Beijing)={today_bj} | "
            f"missed run(s) — site is serving old data"
        )
    return True, (
        f"FRESH: updated={updated} | today(Beijing)={today_bj} | "
        f"gor_wti={d['gor_wti']}"
    )


LIVE_URL = "https://justinjchen-cornell.github.io/Deep-Risk-OPP/gor_latest.json"


def check_live(repo_updated: str) -> tuple:
    """Compare the LIVE site's data date against the repo's.
    Catches the silent failure class where the repo is fresh but the Pages
    deployment was never triggered (bot commits don't fire push events).
    Incident: repo fresh from 2026-09-07 onward, site frozen at 09-07 for a week."""
    import urllib.request
    try:
        req = urllib.request.Request(LIVE_URL, headers={"User-Agent": "deep-risk-watchdog"})
        with urllib.request.urlopen(req, timeout=20) as r:
            live = json.loads(r.read().decode("utf-8"))
        live_updated = str(live.get("updated", ""))[:10]
        repo_date = str(repo_updated)[:10]
        if not live_updated:
            return False, "DEPLOY STALE: live site gor_latest.json has no 'updated' field"
        if live_updated < repo_date:
            return False, (
                "DEPLOY STALE: live site shows " + live_updated + " but repo has " + repo_date +
                " — Pages deployment did not run (check static.yml workflow_run trigger)"
            )
        return True, "live site OK (" + live_updated + ")"
    except Exception as e:
        return False, "DEPLOY CHECK FAILED: cannot fetch live site (" + type(e).__name__ + ": " + str(e) + ")"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--path', default=str(BASE_DIR / 'gor_latest.json'))
    ap.add_argument('--grace-days', type=int, default=0)
    ap.add_argument('--no-live', action='store_true',
                    help='skip the live-site freshness check (offline runs)')
    args = ap.parse_args()
    fresh, msg = check(Path(args.path), args.grace_days)
    print(msg)

    # Second gate: live site must be as fresh as the repo (catches missed Pages deploys)
    if fresh and not args.no_live:
        repo_updated = ""
        try:
            d = json.loads(Path(args.path).read_text(encoding="utf-8"))
            repo_updated = str(d.get("updated", ""))
        except Exception:
            pass
        live_ok, live_msg = check_live(repo_updated)
        print(live_msg)
        if not live_ok:
            sys.exit(1)

    sys.exit(0 if fresh else 1)


if __name__ == '__main__':
    main()
