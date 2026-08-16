"""
Deep-Risk-OPP — RSS/Atom feed 生成 (交付层 L0)
每日管道调用：把当日决策卡追加进 feed.xml（保留最近 30 条）。
用户可以订阅 https://justinjchen-cornell.github.io/feed.xml
"""
import html
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.common import BASE_DIR, log

SITE = "https://justinjchen-cornell.github.io"
FEED_PATH = BASE_DIR / "feed.xml"
MAX_ENTRIES = 30


def build_entry(updated, d, prev=None):
    """根据一日数据构造 Atom entry。"""
    date_str = updated[:10]
    gor_w = d.get('gor_wti')
    gor_b = d.get('gor_brent')
    regime = d.get('regime', '')
    pos = d.get('final_position', 0)
    alloc = d.get('allocation', {})
    alerts = d.get('alerts', [])
    data = d.get('data', {})
    cf = d.get('capital_three_flows', {})
    dq = d.get('data_quality', {})

    def p(key):
        v = (data.get(key) or {}).get('price')
        return f"{v:,.1f}" if isinstance(v, (int, float)) else "N/A"

    title = f"GOR {gor_w:.1f} · {regime}"
    if isinstance(pos, (int, float)):
        title += f" · 仓位 {pos}%"
    lines = [
        f"<p><b>GOR(WTI) {gor_w:.1f}</b> (Brent {gor_b:.1f}) — {regime}</p>",
        f"<p>黄金 ${p('黄金期货')} · WTI ${p('WTI原油')} · 布伦特 ${p('布伦特原油')} · DXY {p('美元指数DXY')} · 10Y {p('10Y美债收益率')}% · VIX {p('VIX恐慌指数')}</p>",
    ]
    if isinstance(pos, (int, float)):
        lines.append(f"<p>仓位 {pos}%：油气 {alloc.get('油气', 0)}% · 黄金 {alloc.get('黄金', 0)}% · 现金 {alloc.get('现金', 0)}% · A股 {alloc.get('A股', 0)}%</p>")
    if cf.get('total'):
        lines.append(f"<p>三流：总量{cf.get('total', '?')} · 方向{cf.get('direction', '?')} · 流速{cf.get('speed', '?')}</p>")
    # 昨日验证：前一日信号 vs 今日 WTI 实际
    wti_now = (data.get('WTI原油') or {}).get('price')
    if prev and isinstance(prev.get('wti'), (int, float)) and isinstance(wti_now, (int, float)) and wti_now > 0:
        pv_wti = prev['wti']
        pv_gor = prev.get('gor_wti')
        chg = (wti_now - pv_wti) / pv_wti * 100
        pv_zone = '极端区' if (pv_gor or 0) >= 45 else ('修复区' if (pv_gor or 0) >= 30 else '其他')
        verdict = '✅ 验证通过' if (pv_gor or 0) >= 45 and chg > 0 else '⚠️ 验证中/未验证'
        lines.append(f"<p>昨日验证：前日 GOR {pv_gor:.1f}（{pv_zone}）→ 今日 WTI {chg:+.1f}% {verdict}</p>")
    if alerts:
        alert_lines = "".join(f"<li>[{a.get('level', '')}] {a.get('title', '')} — {a.get('detail', '')}</li>" for a in alerts)
        lines.append(f"<ul>{alert_lines}</ul>")
    if not (dq.get('ok', True)):
        lines.append(f"<p>⚠️ 数据源降级：{', '.join(dq.get('degraded_fields', []))}</p>")
    lines.append(f"<p><a href='{SITE}/'>完整看板 →</a> · 研究框架，不构成投资建议</p>")

    entry = f"""  <entry>
    <title>{html.escape(title)}</title>
    <link href="{SITE}/dashboard.html"/>
    <id>tag:justinjchen-cornell.github.io,{date_str}:signal</id>
    <updated>{date_str}T00:00:00Z</updated>
    <content type="html">{''.join(lines)}</content>
  </entry>"""
    return entry


def generate_feed(gor_output=None):
    """重新生成 feed.xml：历史(最多N-1条) + 当日一条。"""
    entries = []
    # 1) 历史：wti_history.json（旧格式含 gor_wti 等）
    hist_path = BASE_DIR / "wti_history.json"
    hist = []
    if hist_path.exists():
        try:
            hist = json.loads(hist_path.read_text(encoding='utf-8'))
        except Exception:
            hist = []
    for idx, h in enumerate(hist[-MAX_ENTRIES + 1:]):
        prev = hist[-MAX_ENTRIES + 1:][idx - 1] if idx > 0 else None
        # 把 wti_history 条目扩成 feed 需要的形状
        d = {
            "gor_wti": h.get("gor_wti"), "gor_brent": h.get("gor_brent"),
            "regime": "极端区" if (h.get("gor_wti") or 0) >= 45 else "修复区",
            "final_position": None, "allocation": {}, "alerts": [],
            "data": {
                "黄金期货": {"price": h.get("gold")}, "WTI原油": {"price": h.get("wti")},
                "美元指数DXY": {"price": None}, "10Y美债收益率": {"price": None},
                "VIX恐慌指数": {"price": h.get("vix")}, "布伦特原油": {"price": None},
            },
            "capital_three_flows": {"total": "", "direction": "", "speed": ""},
            "data_quality": {"ok": True, "degraded_fields": []},
        }
        entries.append(build_entry(h.get("date"), d, prev=prev))
    # 2) 当日
    if gor_output is None:
        g_path = BASE_DIR / "gor_latest.json"
        if g_path.exists():
            gor_output = json.loads(g_path.read_text(encoding='utf-8'))
    if gor_output:
        last_hist = hist[-1] if hist else None
        entries.append(build_entry(gor_output.get("updated", datetime.now().strftime('%Y-%m-%d 12:00')), gor_output, prev=last_hist))

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Deep-Risk-OPP · 每日宏观信号</title>
  <subtitle>One number that tells you when oil is historically cheap · 每日自动更新</subtitle>
  <link href="{SITE}/feed.xml" rel="self"/>
  <link href="{SITE}/"/>
  <id>tag:justinjchen-cornell.github.io,2026:feed</id>
  <updated>{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}</updated>
  <author><name>Justinjchen</name></author>
{''.join(entries)}
</feed>
"""
    FEED_PATH.write_text(feed, encoding='utf-8')
    return str(FEED_PATH)


if __name__ == '__main__':
    p = generate_feed()
    print('feed generated:', p)
