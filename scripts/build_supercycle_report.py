# -*- coding: utf-8 -*-
"""Build the supercycle / collateral re-anchor PDF report (charts + HTML + PDF)."""
import json, base64
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "看板日志" / "reports" / "special"
ASSETS = OUT / "supercycle_report_assets"
ASSETS.mkdir(parents=True, exist_ok=True)
CACHE = BASE / "看板日志" / "cache"

NAVY="#0B1F33"; GOLD="#C9A227"; COPPER="#B87333"; TEAL="#1F6F78"
RED="#B23A2E"; GRAY="#8A8F98"; LIGHT="#F4F1EA"; MID="#5A6572"; GRID="#E8E3D8"
plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei"],
    "axes.unicode_minus": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#D9D4C7",
    "axes.labelcolor": NAVY,
    "xtick.color": MID, "ytick.color": MID,
    "text.color": NAVY,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 10,
})

def style(ax, grid_axis="y"):
    ax.grid(axis=grid_axis, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#D9D4C7")
    ax.spines["bottom"].set_color("#D9D4C7")
    ax.tick_params(labelsize=9)

def save(fig, name):
    p = ASSETS / name
    fig.savefig(p, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p

# ---------------- data ----------------
hist = pd.DataFrame(json.load(open(BASE/"history.json", encoding="utf-8"))["rows"])
hist["date"] = pd.to_datetime(hist["date"])
hist = hist.sort_values("date").reset_index(drop=True)
hist["contract"] = ((hist["wti"] - 69.87) / (107.60 - 69.87) * 100).clip(0, 130)
hist["oil_gold"] = hist["wti"] / hist["gold"]

def eia_stats(fn):
    df = pd.read_csv(CACHE/"eia"/fn)
    df["date"] = pd.to_datetime(df["date"]); df = df.dropna().sort_values("date")
    last = df.iloc[-1]
    cutoff = last["date"] - pd.Timedelta(days=365*5)
    w = df[df["date"] >= cutoff]["value"]
    return last, (w < last["value"]).mean() * 100

eia_files = {
    "商业原油库存": "商业原油库存.csv", "馏分油库存": "馏分油库存.csv",
    "汽油库存": "汽油库存.csv", "SPR": "SPR战略储备.csv",
    "Cushing": "Cushing库存.csv", "原油产量": "原油产量.csv",
    "原油出口": "原油出口.csv", "炼化利用率": "炼化利用率.csv",
}
eia = {k: eia_stats(v) for k, v in eia_files.items()}

cofer = pd.read_csv(CACHE/"imf"/"COFER_world_shares.csv")
cofer = cofer[cofer["period"].astype(str).str.contains("-Q")].copy()
cofer["dt"] = pd.PeriodIndex(cofer["period"].astype(str), freq="Q").to_timestamp()
cofer = cofer.sort_values("dt")

cu = pd.read_csv(CACHE/"copper_monthly.csv")
cu.columns = ["date", "value"]
cu["date"] = pd.to_datetime(cu["date"]); cu = cu.dropna().sort_values("date")

# ---------------- charts ----------------
# 1. three clocks
fig, ax = plt.subplots(figsize=(10.2, 4.2))
rows = [
    ("风险重定价\nRisk repricing", 0, 0.35, RED, "weeks"),
    ("数据中心信用\nData-center credit", 1, 2, GOLD, "1–3 years"),
    ("AI 采用\nAI adoption", 3, 4, TEAL, "3–7 years"),
    ("新矿投产\nNew mine", 0, 17, COPPER, "~17 years"),
]
for i, (label, left, width, color, tag) in enumerate(rows):
    ax.barh(i, width, left=left, height=0.52, color=color, alpha=0.9)
    ax.text(left + width + 0.25, i, tag, va="center", fontsize=9.5, color=color, fontweight="bold")
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows], fontsize=9.5)
ax.set_xlim(0, 18.8); ax.set_xlabel("年 / Years", fontsize=9.5)
ax.set_title("三个周期，三种速度：超级周期发生在它们重叠的时候", loc="left", fontsize=13, fontweight="bold", color=NAVY, pad=12)
style(ax, "x")
ax.grid(axis="x", color=GRID, lw=0.8); ax.grid(axis="y", visible=False)
fig.text(0.01, -0.02, "示意图；AI 采用 3–7 年、数据中心信用 1–3 年为研究假设；新矿 17 年来自 IEA。", fontsize=7.5, color=MID)
save(fig, "fig_three_clocks.png")

# 2. GOR + contract
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10.2, 5.6), sharex=True, gridspec_kw={"height_ratios":[1.35,1]})
ax1.plot(hist["date"], hist["gor_wti"], color=NAVY, lw=2.0, label="GOR (WTI)")
for y, lab in [(45,"45"),(42,"42"),(40,"40")]:
    ax1.axhline(y, color=GRAY, lw=0.9, ls="--")
    ax1.text(hist["date"].iloc[-1], y+0.25, lab, ha="right", va="bottom", fontsize=8, color=GRAY)
ax1.scatter([hist["date"].iloc[0], hist["date"].iloc[-1]], [hist["gor_wti"].iloc[0], hist["gor_wti"].iloc[-1]], color=GOLD, s=26, zorder=5)
ax1.annotate(f"{hist['gor_wti'].iloc[0]:.2f}", (hist["date"].iloc[0], hist["gor_wti"].iloc[0]), textcoords="offset points", xytext=(6,8), fontsize=9, color=GOLD, fontweight="bold")
ax1.annotate(f"{hist['gor_wti'].iloc[-1]:.2f}", (hist["date"].iloc[-1], hist["gor_wti"].iloc[-1]), textcoords="offset points", xytext=(-6,-18), fontsize=9, color=GOLD, fontweight="bold", ha="right")
ax1.axvspan(pd.Timestamp("2026-10-14"), pd.Timestamp("2026-10-18"), color=COPPER, alpha=0.10)
ax1.text(pd.Timestamp("2026-10-16"), 50.5, "10/15 流动性事件", fontsize=8, color=COPPER, ha="center")
ax1.set_ylabel("金油比 GOR (WTI)", fontsize=9.5)
ax1.set_title("金油比：从 55 到 38.77，油接过了接力棒", loc="left", fontsize=13, fontweight="bold", color=NAVY, pad=10)
style(ax1)

ax2.plot(hist["date"], hist["contract"], color=GOLD, lw=2.0)
ax2.fill_between(hist["date"], hist["contract"], color=GOLD, alpha=0.10)
ax2.axhline(100, color=GRAY, lw=0.9, ls="--")
ax2.text(hist["date"].iloc[-1], 101, "契约目标 107.60", ha="right", va="bottom", fontsize=8, color=GRAY)
ax2.annotate(f"{hist['contract'].iloc[-1]:.1f}%", (hist["date"].iloc[-1], hist["contract"].iloc[-1]), textcoords="offset points", xytext=(-48,5), fontsize=9, color=GOLD, fontweight="bold", ha="right")
ax2.set_ylim(0, 115); ax2.set_ylabel("契约完成度 %", fontsize=9.5)
style(ax2)
ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
fig.text(0.01, -0.01, "数据：Deep-Risk-OPP 日卡/历史；契约基线 WTI \\$69.87（2026-06-19），目标 \\$107.60。", fontsize=7.5, color=MID)
save(fig, "fig_gor_contract.png")

# 3. oil in gold terms
base = hist.iloc[0]
idx_wti = hist["wti"]/base["wti"]*100
idx_gold = hist["gold"]/base["gold"]*100
idx_og = hist["oil_gold"]/base["oil_gold"]*100
fig, ax = plt.subplots(figsize=(10.2, 4.4))
ax.plot(hist["date"], idx_wti, color=TEAL, lw=2.0, label="WTI（美元计价）")
ax.plot(hist["date"], idx_gold, color=GRAY, lw=1.8, label="黄金（美元计价）")
ax.plot(hist["date"], idx_og, color=COPPER, lw=2.4, label="油/金（以黄金计价的油）")
for s, c, lab in [(idx_wti, TEAL, f"{idx_wti.iloc[-1]-100:+.1f}%"), (idx_gold, GRAY, f"{idx_gold.iloc[-1]-100:+.1f}%"), (idx_og, COPPER, f"{idx_og.iloc[-1]-100:+.1f}%")]:
    ax.annotate(lab, (hist["date"].iloc[-1], s.iloc[-1]), textcoords="offset points", xytext=(-6,6) if c != GRAY else (-6,-16), ha="right", fontsize=9.5, color=c, fontweight="bold")
ax.axhline(100, color=GRAY, lw=0.8, ls=":")
ax.set_ylabel("2026-06-19 = 100", fontsize=9.5)
ax.set_title("“尺子”没有掩盖油价：以黄金计价的油价涨得更快", loc="left", fontsize=13, fontweight="bold", color=NAVY, pad=10)
ax.legend(loc="upper left", frameon=False, fontsize=8.5, ncol=3)
style(ax)
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
fig.text(0.01, -0.02, "数据：Deep-Risk-OPP 日卡/历史。油/金 = WTI / 黄金；指数化仅为比较相对涨幅。", fontsize=7.5, color=MID)
save(fig, "fig_oil_gold.png")

# 4. EIA percentiles
stocks = [("SPR", eia["SPR"]), ("汽油", eia["汽油库存"]), ("商业原油", eia["商业原油库存"]), ("馏分油", eia["馏分油库存"]), ("Cushing", eia["Cushing"])]
stocks = sorted(stocks, key=lambda x: x[1][1])
fig, ax = plt.subplots(figsize=(10.2, 3.9))
labels = [s[0] for s in stocks]; vals = [s[1][1] for s in stocks]
colors = [RED if v < 10 else (GOLD if v < 50 else GRAY) for v in vals]
bars = ax.barh(labels, vals, color=colors, height=0.55)
for b, v, (name, (last, pct)) in zip(bars, vals, stocks):
    ax.text(max(v+2.0, 2.0), b.get_y()+b.get_height()/2, f"{v:.1f}%  ·  {last['value']:,.0f}", va="center", fontsize=9, color=NAVY)
ax.set_xlim(0, 100); ax.set_xlabel("过去 5 年分位（0 = 最低）", fontsize=9.5)
ax.set_title("库存分位：四个品种在 7% 以下，Cushing 是例外", loc="left", fontsize=13, fontweight="bold", color=NAVY, pad=10)
ax.invert_yaxis(); style(ax, "x")
fig.text(0.01, -0.03, "数据：EIA Weekly Petroleum Status Report，2026-10-16；库存单位千桶；分位为 261 周滚动。Cushing 27.6 百万桶，分位 63.6%。", fontsize=7.5, color=MID)
save(fig, "fig_eia_percentiles.png")

# 5. copper
cu15 = cu[cu["date"] >= "2015-01-01"]
fig, ax = plt.subplots(figsize=(10.2, 3.9))
ax.plot(cu15["date"], cu15["value"], color=COPPER, lw=1.8)
ax.fill_between(cu15["date"], cu15["value"], color=COPPER, alpha=0.08)
last_cu = cu15.iloc[-1]
ax.scatter([last_cu["date"]], [last_cu["value"]], color=COPPER, s=30, zorder=5)
ax.annotate(f"2026-09\n${last_cu['value']:,.0f}/t", (last_cu["date"], last_cu["value"]), textcoords="offset points", xytext=(-8,12), ha="right", fontsize=9, color=COPPER, fontweight="bold")
ax.set_ylabel("铜价，美元/吨", fontsize=9.5)
ax.set_title("铜：价格在涨，但供给的回答要 17 年", loc="left", fontsize=13, fontweight="bold", color=NAVY, pad=10)
style(ax)
ax.xaxis.set_major_locator(mdates.YearLocator(2)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
fig.text(0.01, -0.03, "数据：FRED PCOPPUSDM（月度，全球铜价）。供给事实：IEA（品位 1991 年以来 -40%，新矿约 17 年）；S&P Global（2026 年铜勘探预算 +32% 至约 43 亿美元）。", fontsize=7.5, color=MID)
save(fig, "fig_copper.png")

# 6. COFER
fig, ax = plt.subplots(figsize=(10.2, 4.0))
ax.plot(cofer["dt"], cofer["USD"], color=NAVY, lw=2.2, label="美元")
ax.plot(cofer["dt"], cofer["EUR"], color=TEAL, lw=1.4, alpha=0.85, label="欧元")
ax.plot(cofer["dt"], cofer["CNY"], color=GOLD, lw=1.4, alpha=0.9, label="人民币")
ax.axhline(60, color=GRAY, lw=0.8, ls="--")
ax.text(cofer["dt"].iloc[0], 60.8, "60%", fontsize=8, color=GRAY)
for d, lab in [("1999-Q1", "71.2%"), ("2026-Q2", "56.7%")]:
    row = cofer[cofer["period"] == d].iloc[0]
    ax.scatter([row["dt"]], [row["USD"]], color=GOLD, s=26, zorder=5)
    ax.annotate(lab, (row["dt"], row["USD"]), textcoords="offset points", xytext=(6,8) if d=="1999-Q1" else (-6,8), ha="left" if d=="1999-Q1" else "right", fontsize=9, color=GOLD, fontweight="bold")
ax.set_ylabel("占全球储备份额 %", fontsize=9.5)
ax.set_title("美元份额：27 年 -14.5pt，是慢迁移，不是断崖", loc="left", fontsize=13, fontweight="bold", color=NAVY, pad=10)
ax.legend(loc="upper right", frameon=False, fontsize=8.5, ncol=3)
style(ax)
ax.xaxis.set_major_locator(mdates.YearLocator(5)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
fig.text(0.01, -0.03, "数据：IMF COFER，2026Q2；份额为季度末已分配储备。2026Q2 美元储备 7.495 万亿美元，总储备 13.217 万亿美元。", fontsize=7.5, color=MID)
save(fig, "fig_cofer.png")

# 7. China compute power
fig, ax = plt.subplots(figsize=(10.2, 3.9))
x = ["2025", "2030E"]; y = [170, 800]
bars = ax.bar(x, y, color=[TEAL, COPPER], width=0.45)
for b, v in zip(bars, y):
    ax.text(b.get_x()+b.get_width()/2, v+25, f"{v} TWh", ha="center", fontsize=11, color=NAVY, fontweight="bold")
ax.annotate("", xy=(1, 790), xytext=(0, 180), arrowprops=dict(arrowstyle="->", color=GOLD, lw=1.6))
ax.text(0.5, 520, "+371%", ha="center", fontsize=14, color=GOLD, fontweight="bold")
ax.set_ylim(0, 900); ax.set_ylabel("数据中心用电，TWh", fontsize=9.5)
ax.set_title("中国数据中心用电：2025 年 1,700 亿 kWh → 2030E 8,000 亿 kWh", loc="left", fontsize=13, fontweight="bold", color=NAVY, pad=10)
style(ax)
fig.text(0.01, -0.03, "数据：国家能源局援引中电联《中国电力行业年度发展报告 2026》；2030 为预测值。", fontsize=7.5, color=MID)
save(fig, "fig_china_power.png")

# 8. property vs data center investment
fig, ax = plt.subplots(figsize=(10.2, 3.6))
labels = ["房地产峰值年投资\n2021", "东数西算累计规划\n2022–2025"]
vals = [14.8, 0.4]
bars = ax.barh(labels, vals, color=[GRAY, COPPER], height=0.5)
for b, v in zip(bars, vals):
    ax.text(v+0.25, b.get_y()+b.get_height()/2, f"{v:.1f} 万亿元" + ("+" if v==0.4 else ""), va="center", fontsize=10.5, color=NAVY, fontweight="bold")
ax.set_xlim(0, 17); ax.set_xlabel("万亿元人民币（不同口径，仅作量级对比）", fontsize=9.5)
ax.set_title("“新房地产”不是旧房地产：算力投资只有房地产峰值的约 3%", loc="left", fontsize=13, fontweight="bold", color=NAVY, pad=10)
ax.invert_yaxis(); style(ax, "x")
fig.text(0.01, -0.04, "数据：国家统计局（房地产投资 2021 年峰值约 14.8 万亿元）；国家发改委/公开报道（东数西算 8 枢纽 10 集群，累计规划投资 4,000 亿元以上）。口径不同，仅作量级示意。", fontsize=7.5, color=MID)
save(fig, "fig_property_vs_dc.png")

# 9. credit tail + DC finance
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 3.8), gridspec_kw={"width_ratios":[1.35,1]})
names = ["IG", "HY", "AI HY", "CCC"]
vals = [89, 340, 360, 1340]
colors = [GRAY, GOLD, COPPER, RED]
bars = ax1.bar(names, vals, color=colors, width=0.55)
for b, v in zip(bars, vals):
    ax1.text(b.get_x()+b.get_width()/2, v+25, f"{v:,}", ha="center", fontsize=10, color=NAVY, fontweight="bold")
ax1.set_ylim(0, 1500); ax1.set_ylabel("OAS，bp", fontsize=9.5)
ax1.set_title("信用尾部：指数平静，CCC 已 1,340bp", loc="left", fontsize=11.5, fontweight="bold", color=NAVY, pad=8)
style(ax1)

x2 = ["2025 全年", "2026 YTD"]
y2 = [37, 106]
bars = ax2.bar(x2, y2, color=[GRAY, COPPER], width=0.5)
for b, v in zip(bars, y2):
    ax2.text(b.get_x()+b.get_width()/2, v+3, f"${v}B", ha="center", fontsize=10, color=NAVY, fontweight="bold")
ax2.set_ylim(0, 125); ax2.set_ylabel("数据中心项目融资，十亿美元", fontsize=9.5)
ax2.set_title("项目融资：\\$37B → \\$106B", loc="left", fontsize=11.5, fontweight="bold", color=NAVY, pad=8)
style(ax2)
fig.text(0.01, -0.04, "数据：FRED（IG/HY/CCC，2026-10-22）；信用展望汇总（AI HY 360bp；数据中心项目融资 2025 年 ~\\$37B、2026 YTD >\\$106B）。", fontsize=7.5, color=MID)
save(fig, "fig_credit_tail.png")

print("charts done:", sorted(p.name for p in ASSETS.glob("*.png")))

# ---------------- HTML + PDF ----------------
from playwright.sync_api import sync_playwright
from pypdf import PdfWriter, PdfReader

def data_uri(name):
    p = ASSETS / name
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()

body_tpl = (BASE/"scripts"/"supercycle_report_body.html").read_text(encoding="utf-8")
for fig in ASSETS.glob("*.png"):
    body_tpl = body_tpl.replace("{{FIG:%s}}" % fig.name, data_uri(fig.name))
body_html = OUT / "supercycle_report_body_rendered.html"
body_html.write_text(body_tpl, encoding="utf-8")

cover_tpl = (BASE/"scripts"/"supercycle_report_cover.html").read_text(encoding="utf-8")
cover_html = OUT / "supercycle_report_cover_rendered.html"
cover_html.write_text(cover_tpl, encoding="utf-8")

cover_pdf = OUT / "_cover.pdf"
body_pdf = OUT / "_body.pdf"
final_pdf = OUT / "大宗商品超级周期与中美抵押品换锚-2026-10-25.pdf"

header = """<div style="width:100%;font-family:'Microsoft YaHei';font-size:7pt;color:#8A8F98;padding:0 18mm;display:flex;justify-content:space-between;">
<span>Deep-Risk-OPP · 大宗商品超级周期与抵押品换锚</span><span>2026-10-25</span></div>"""
footer = """<div style="width:100%;font-family:'Microsoft YaHei';font-size:7pt;color:#8A8F98;padding:0 18mm;display:flex;justify-content:space-between;">
<span>Research framework, not investment advice.</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>"""

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page()
    page.goto(cover_html.resolve().as_uri())
    page.pdf(path=str(cover_pdf), format="A4", print_background=True,
             margin={"top":"0","bottom":"0","left":"0","right":"0"})
    page.goto(body_html.resolve().as_uri())
    page.pdf(path=str(body_pdf), format="A4", print_background=True,
             display_header_footer=True, header_template=header, footer_template=footer,
             margin={"top":"20mm","bottom":"18mm","left":"18mm","right":"18mm"})
    browser.close()

writer = PdfWriter()
for f in (cover_pdf, body_pdf):
    for pg in PdfReader(str(f)).pages:
        writer.add_page(pg)
writer.add_metadata({
    "/Title": "下一轮超级周期，是抵押品的故事",
    "/Author": "Deep-Risk-OPP",
    "/Subject": "大宗商品超级周期、算力资本开支与中美抵押品换锚",
    "/Keywords": "commodity supercycle, AI capex, data centers, copper, gold, collateral, China, US",
})
with open(final_pdf, "wb") as fh:
    writer.write(fh)
print("PDF:", final_pdf, final_pdf.stat().st_size, "bytes")
print("body pages:", len(PdfReader(str(body_pdf)).pages), "cover pages:", len(PdfReader(str(cover_pdf)).pages))
for f in (cover_pdf, body_pdf, body_html, cover_html):
    try:
        f.unlink()
    except Exception:
        pass
