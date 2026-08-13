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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--path', default=str(BASE_DIR / 'gor_latest.json'))
    ap.add_argument('--grace-days', type=int, default=0)
    args = ap.parse_args()
    fresh, msg = check(Path(args.path), args.grace_days)
    print(msg)
    sys.exit(0 if fresh else 1)


if __name__ == '__main__':
    main()
