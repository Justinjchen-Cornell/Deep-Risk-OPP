# -*- coding: utf-8 -*-
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("看板日志/reports/special/linkedin_assets")
OUT.mkdir(parents=True, exist_ok=True)

HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box} body{margin:0;background:#fff;font-family:'Segoe UI',Arial,sans-serif}
.card{width:1200px;height:627px;position:relative;overflow:hidden;background:
 radial-gradient(circle at 82% 16%, rgba(201,162,39,.18) 0%, rgba(201,162,39,0) 42%),
 radial-gradient(circle at 6% 92%, rgba(31,111,120,.18) 0%, rgba(31,111,120,0) 45%),
 linear-gradient(145deg,#0B1F33 0%,#0A1A2B 60%,#081522 100%);color:#fff;padding:52px 60px;display:flex;flex-direction:column;justify-content:space-between}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:52px 52px;mask-image:linear-gradient(to bottom,rgba(0,0,0,.8),rgba(0,0,0,.15))}
.top{display:flex;justify-content:space-between;align-items:center;font-size:15px;letter-spacing:2.2px;color:#C9A227;position:relative}
.top .r{color:#8FA0B3;letter-spacing:1.6px;font-size:13px}
.rule{height:2px;background:linear-gradient(90deg,#C9A227,rgba(201,162,39,.05));margin:14px 0 0 0;position:relative}
.mid{position:relative;max-width:980px}
.kicker{font-size:15px;letter-spacing:3.2px;color:#C9A227;margin-bottom:14px}
h1{font-family:Georgia,'Times New Roman',serif;font-size:66px;line-height:1.08;margin:0 0 16px 0;font-weight:700;letter-spacing:-1.2px}
h1 .gold{color:#C9A227}
p{font-size:24px;line-height:1.45;color:#CFC7B7;margin:0;max-width:880px}
.bottom{position:relative;display:flex;justify-content:space-between;align-items:flex-end;border-top:1px solid rgba(255,255,255,.18);padding-top:16px}
.bottom .l{font-size:18px;color:#CFC7B7}.bottom .l b{color:#C9A227}
.bottom .r{font-size:14px;color:#6F8296;text-align:right;line-height:1.5}
.badge{display:inline-block;background:#C9A227;color:#0B1F33;font-size:15px;font-weight:700;letter-spacing:1.4px;padding:8px 16px;border-radius:4px;margin-bottom:22px}
.goldcard{background:linear-gradient(145deg,#F7F1E1 0%,#EFE3C4 100%);color:#0B1F33}
.goldcard .top{color:#8A6D1F}.goldcard .top .r{color:#8A6D1F}
.goldcard h1{color:#0B1F33}.goldcard h1 .gold{color:#B87333}
.goldcard p{color:#3A4552}.goldcard .kicker{color:#B87333}
.goldcard .bottom{border-top-color:rgba(11,31,51,.18)}.goldcard .bottom .l{color:#3A4552}.goldcard .bottom .l b{color:#B87333}.goldcard .bottom .r{color:#6B7280}
.goldcard .badge{background:#0B1F33;color:#C9A227}
</style></head><body>
<div class="card" id="c1"><div class="grid"></div>
<div><div class="top"><span>DEEP-RISK-OPP</span><span class="r">START HERE</span></div><div class="rule"></div></div>
<div class="mid"><div class="badge">START HERE</div><h1>The daily card<br>+ the <span class="gold">Q4 checklist</span></h1><p>One ratio. One card. One discipline. Free, public, updated daily.</p></div>
<div class="bottom"><div class="l"><b>Deep-Risk-OPP</b> · daily GOR card + 10-item crisis checklist</div><div class="r">Research framework<br>not investment advice</div></div></div>

<div class="card" id="c2" style="display:none"><div class="grid"></div>
<div><div class="top"><span>DEEP-RISK-OPP · SPECIAL REPORT</span><span class="r">2026</span></div><div class="rule"></div></div>
<div class="mid"><div class="kicker">AI CAPEX · POWER · COPPER · CREDIT</div><h1>The Next Supercycle<br>Is a <span class="gold">Collateral</span> Story</h1><p>AI capex, power, copper, and the re-anchoring of US credit. 22 pages.</p></div>
<div class="bottom"><div class="l"><b>22-page PDF</b> · data as of 2026-10-25</div><div class="r">Research framework<br>not investment advice</div></div></div>

<div class="card goldcard" id="c3" style="display:none"><div class="grid"></div>
<div><div class="top"><span>DEEP-RISK-OPP · FREE PDF</span><span class="r">Q4 2026</span></div><div class="rule"></div></div>
<div class="mid"><div class="badge">FREE PDF</div><h1>The Q4<br><span class="gold">Crisis Checklist</span></h1><p>10 pre-registered signals I score every quarter — gold, oil, credit, dollar.</p></div>
<div class="bottom"><div class="l"><b>10 signals</b> · pre-registered, falsifiable</div><div class="r">Research framework<br>not investment advice</div></div></div>
</body></html>"""

html = OUT / "_featured_cards.html"
html.write_text(HTML, encoding="utf-8")
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width":1200,"height":627}, device_scale_factor=2)
    pg.goto(html.resolve().as_uri())
    for cid, name in [("c1","featured_start_here.png"),("c2","featured_supercycle.png"),("c3","featured_checklist.png")]:
        pg.eval_on_selector_all(".card", "(els) => els.forEach(e => e.style.display='none')")
        pg.eval_on_selector("#"+cid, "e => e.style.display='flex'")
        pg.locator("#"+cid).screenshot(path=str(OUT/name))
        print("saved", OUT/name)
    b.close()
html.unlink()
