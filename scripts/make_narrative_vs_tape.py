# -*- coding: utf-8 -*-
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path('看板日志/reports/special/linkedin_assets'); OUT.mkdir(parents=True,exist_ok=True)
HTML="""<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}body{margin:0;font-family:'Segoe UI',Arial,sans-serif}
.card{width:1200px;height:1200px;background:
 radial-gradient(circle at 82% 12%, rgba(201,162,39,.18) 0%, rgba(201,162,39,0) 42%),
 radial-gradient(circle at 8% 92%, rgba(178,58,46,.16) 0%, rgba(178,58,46,0) 45%),
 linear-gradient(145deg,#0B1F33 0%,#0A1A2B 60%,#081522 100%);color:#fff;padding:64px 64px 52px;display:flex;flex-direction:column;justify-content:flex-start;position:relative;overflow:hidden}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:52px 52px;mask-image:linear-gradient(to bottom,rgba(0,0,0,.8),rgba(0,0,0,.15))}
.top{display:flex;justify-content:space-between;font-size:15px;letter-spacing:2px;color:#C9A227;position:relative}.top .r{color:#8FA0B3;letter-spacing:1px}
.rule{height:2px;background:linear-gradient(90deg,#C9A227,rgba(201,162,39,.05));margin-top:14px}
h1{font-family:Georgia,'Times New Roman',serif;font-size:62px;line-height:1.1;margin:26px 0 8px;font-weight:700}
h1 .gold{color:#C9A227}
.sub{font-size:23px;color:#CFC7B7;margin:0 0 26px}
table{width:100%;border-collapse:collapse;position:relative;font-size:22px}
th{text-align:left;color:#8FA0B3;font-size:15px;letter-spacing:1.4px;font-weight:600;padding:0 0 10px;border-bottom:1px solid rgba(255,255,255,.18)}
td{padding:18px 0;border-bottom:1px solid rgba(255,255,255,.12);vertical-align:top}
td.n{color:#CFC7B7;width:40%}td.t{color:#fff;font-weight:600}
.tag{display:inline-block;font-size:13px;letter-spacing:1px;color:#B23A2E;border:1px solid rgba(178,58,46,.6);padding:3px 8px;border-radius:3px;margin-left:10px;vertical-align:middle}
.watch{margin-top:38px;border-left:3px solid #C9A227;padding-left:20px;font-size:20px;line-height:1.65;color:#CFC7B7;position:relative}.watch b{color:#fff}.watch .g{color:#C9A227}.score{display:grid;grid-template-columns:1fr 1fr;gap:10px 26px;margin-top:30px;font-size:18px;color:#CFC7B7;position:relative}.score .yes{color:#2E9E6B}.score .warn{color:#C9A227}.score .no{color:#B23A2E}.scoreline{margin-top:14px;font-size:19px;color:#C9A227;font-weight:700;position:relative}.bottom{border-top:1px solid rgba(255,255,255,.18);padding-top:18px;margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;position:relative}
.bottom .d{font-size:19px;color:#CFC7B7;max-width:760px}.bottom .d b{color:#C9A227}
.bottom .r{font-size:14px;color:#6F8296;text-align:right;line-height:1.5}
</style></head><body>
<div class="card"><div class="grid"></div>
<div><div class="top"><span>DEEP-RISK-OPP · MACRO NOTE</span><span class="r">2026-11-01</span></div><div class="rule"></div></div>
<div><h1>The narrative<br>vs <span class="gold">the tape</span></h1><p class="sub">The “US liquidity drain” story is half right. The mechanism is real; the script is not.</p>
<table><tr><th>NARRATIVE</th><th>WHAT THE TAPE SAYS</th></tr>
<tr><td class="n">Dollar squeeze</td><td class="t">DXY 101.83 — flat <span class="tag">NO</span></td></tr>
<tr><td class="n">Global equity crash</td><td class="t">ASHR −1.15% / FXI +1.19% — mixed <span class="tag">NO</span></td></tr>
<tr><td class="n">Gold safe-haven bid</td><td class="t">Gold −3.63% — sold for liquidity <span class="tag">NO</span></td></tr>
<tr><td class="n">Rates up</td><td class="t">10Y 4.93% — down <span class="tag">NO</span></td></tr>
</table><div class="watch"><div><b>Mechanism:</b> AI deleveraging → gold sold for cash → Treasuries bid.</div><div><b>Script:</b> not proven. No dollar squeeze, no global crash, no oil lever.</div><div><b>Watch:</b> <span class="g">VIX close &gt;22.5 · HY &gt;350/400 · CCC &gt;1,400/1,500 · DXY &gt;103–105.</span></div></div><div class="score"><div><span class="yes">✅</span> Gold + stocks fell together</div><div><span class="warn">⚠️</span> VIX touched 23.93, closed 19.42</div><div><span class="no">❌</span> HY 326 / CCC 1,325</div><div><span class="no">❌</span> DXY 101.83</div><div><span class="no">❌</span> A-shares mixed</div></div><div class="scoreline">On the close: 1 of 5. Intraday: 2 of 5. Early warning, not crisis.</div></div>
<div class="bottom"><div class="d"><b>Mechanism:</b> AI deleveraging → gold sold for cash → Treasuries bid.<br><b>Script:</b> not proven. Watch credit, VIX, and the dollar.</div><div class="r">Research framework<br>not investment advice</div></div>
</div></body></html>"""
h=OUT/'_narrative_vs_tape.html'; h.write_text(HTML,encoding='utf-8')
with sync_playwright() as p:
    b=p.chromium.launch(channel='msedge',headless=True)
    pg=b.new_page(viewport={'width':1200,'height':1200},device_scale_factor=2)
    pg.goto(h.resolve().as_uri()); pg.locator('.card').screenshot(path=str(OUT/'narrative_vs_tape.png'))
    b.close()
h.unlink(); print('saved',OUT/'narrative_vs_tape.png')
