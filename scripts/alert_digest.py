#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""08:30 Beijing daily digest: P1/P2 alerts since last digest + current card.

P0 is sent immediately by alert_check; this digest never re-sends P0.
Usage:
  python scripts/alert_digest.py            # print only
  python scripts/alert_digest.py --send --write
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.delivery import configured_channels, send_text, has_any_success

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(BASE, "alerts", "log.jsonl")
STATE = os.path.join(BASE, "alerts", "digest_state.json")
CARD = os.path.join(BASE, "gor_latest.json")


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=LOG)
    ap.add_argument("--state", default=STATE)
    ap.add_argument("--card", default=CARD)
    ap.add_argument("--hours", type=float, default=24.0)
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    st = load_json(args.state, {}) or {}
    since = st.get("last_digest")
    try:
        since_dt = datetime.fromisoformat(since) if since else now - timedelta(hours=args.hours)
    except Exception:
        since_dt = now - timedelta(hours=args.hours)

    entries = []
    if os.path.exists(args.log):
        with open(args.log, encoding="utf-8") as f:
            for line in f:
                try:
                    a = json.loads(line)
                    created = datetime.fromisoformat(a.get("created", ""))
                except Exception:
                    continue
                delivered = any(v == "ok" for v in (a.get("delivery") or {}).values())
                if created > since_dt and a.get("severity") in ("P1", "P2") and not delivered:
                    entries.append(a)

    card = load_json(args.card, {}) or {}
    s = card.get("screener") or {}
    d = card.get("data") or {}
    wti = (d.get("WTI原油") or {}).get("price")
    vix = s.get("vix")

    lines = [
        "📊 Deep-Risk-OPP · 08:30 摘要",
        "状态：GOR " + str(card.get("gor_wti")) + " · " + str(card.get("regime")) +
        " · 仓位 " + str(card.get("final_position")) + "%" +
        " · 筛选器 " + str(s.get("verdict")),
        "合同：WTI " + str(wti) + " · 完成度 " + str(
            round((wti / 69.87 - 1) / 0.54 * 100, 1) if isinstance(wti, (int, float)) else "—") + "%",
        "观察：VIX " + str(vix) + "（门槛 " + str(s.get("vix_thr")) + "）· 油分位 " + str(s.get("oil_pctl")),
        "",
    ]
    if entries:
        lines.append("过去 24h · P1/P2 共 " + str(len(entries)) + " 条：")
        for a in entries[-10:]:
            lines.append("  [" + a.get("severity", "?") + "] " + a.get("title", "") +
                         " — " + a.get("message", ""))
    else:
        lines.append("过去 24h：无 P1/P2 状态变化。")
    # Weekly GOR change + daily price change
    try:
        import json as _json
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        wk = _json.load(open(os.path.join(base, 'history_weekly.json'), encoding='utf-8')).get('rows', [])
        dl = _json.load(open(os.path.join(base, 'history.json'), encoding='utf-8')).get('rows', [])
        if len(wk) >= 2:
            a, b = wk[-2], wk[-1]
            lines.append('较上周：GOR ' + str(b.get('gor_wti')) + '（上周 ' + str(a.get('gor_wti')) + '，' + ('%+.2f' % ((b.get('gor_wti') or 0) - (a.get('gor_wti') or 0))) + '）')
        if len(dl) >= 2:
            a, b = dl[-2], dl[-1]
            def _d(k):
                return ('%+.2f' % ((b.get(k) or 0) - (a.get(k) or 0))) if isinstance(b.get(k), (int, float)) and isinstance(a.get(k), (int, float)) else '—'
            lines.append('较上次：WTI ' + _d('wti') + ' · VIX ' + _d('vix') + ' · 仓位 ' + str(b.get('position')) + '%')
    except Exception:
        pass
    lines += ["", "P0 仍即时推送；本摘要不重复 P0。", "卡片: https://justinjchen-cornell.github.io/Deep-Risk-OPP"]
    text = "\n".join(lines)

    print(text)
    if args.send:
        channels = configured_channels()
        if not channels:
            print("send: no channels configured")
            sys.exit(1)
        res = send_text(text, title="08:30 摘要", severity="P2",
                        alert_id=now.strftime("%Y-%m-%dT%H:%MZ") + "-digest")
        print("send: " + json.dumps(res, ensure_ascii=False))
        if not has_any_success(res):
            sys.exit(1)
    if args.write:
        os.makedirs(os.path.dirname(args.state), exist_ok=True)
        with open(args.state, "w", encoding="utf-8") as f:
            json.dump({"last_digest": now.isoformat()}, f, ensure_ascii=False, indent=2)
        print("wrote: " + args.state)


if __name__ == "__main__":
    main()
