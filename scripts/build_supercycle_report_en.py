# -*- coding: utf-8 -*-
"""Build the English, US-audience supercycle / collateral report."""
import json, base64, math
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "看板日志" / "reports" / "special"
ASSETS = OUT / "supercycle_report_en_assets"
ASSETS.mkdir(parents=True, exist_ok=True)
CACHE = BASE / "看板日志" / "cache"

NAVY="#0B1F33"; GOLD="#C9A227"; COPPER="#B87333"; TEAL="#1F6F78"
RED="#B23A2E"; GRAY="#8A8F98"; MID="#5A6572"; GRID="#E8E3D8"
plt.rcParams.update({
    "font.family": "Segoe UI",
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

def fred(fn, col=None):
    df = pd.read_csv(fn)
    df.columns = ["date", (col or df.columns[1])]
    df["date"] = pd.to_datetime(df["date"])
    df.iloc[:,1] = pd.to_numeric(df.iloc[:,1], errors="coerce")
    return df.dropna().sort_values("date")

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
    cutoff = last["date"] - pd.Timedelta(days=1826)
    w = df[df["date"] >= cutoff]["value"]
    return last, (w < last["value"]).mean() * 100

eia_files = {
    "crude": "商业原油库存.csv", "distillate": "馏分油库存.csv",
    "gasoline": "汽油库存.csv", "spr": "SPR战略储备.csv",
    "cushing": "Cushing库存.csv", "production": "原油产量.csv",
    "exports": "原油出口.csv", "utilization": "炼化利用率.csv",
    "natgas": "天然气库存48州.csv",
}
eia = {k: eia_stats(v) for k, v in eia_files.items()}

cofer = pd.read_csv(CACHE/"imf"/"COFER_world_shares.csv")
cofer = cofer[cofer["period"].astype(str).str.contains("-Q")].copy()
cofer["dt"] = pd.PeriodIndex(cofer["period"].astype(str), freq="Q").to_timestamp()
cofer = cofer.sort_values("dt")

cu = pd.read_csv(CACHE/"copper_monthly.csv")
cu.columns = ["date", "value"]
cu["date"] = pd.to_datetime(cu["date"]); cu = cu.dropna().sort_values("date")

elec = fred(CACHE/"us_electricity_price.csv", "value")
gas = fred(CACHE/"henry_hub.csv", "value")
dgs10 = fred(CACHE/"fred_DGS10.csv", "value")
dfii10 = fred(CACHE/"fred_DFII10.csv", "value")
t10yie = fred(CACHE/"fred_T10YIE.csv", "value")
hy = fred(CACHE/"fred_BAMLH0A0HYM2.csv", "value")
ccc = fred(CACHE/"fred_BAMLH0A3HYC.csv", "value")
ig = fred(CACHE/"fred_BAMLC0A0CM.csv", "value")
debt = fred(CACHE/"fred_GFDEBTN.csv", "value")
interest = fred(CACHE/"fred_FYOINT.csv", "value")

# ---------------- charts ----------------
# 1. three clocks
fig, ax = plt.subplots(figsize=(10.2, 3.8))
rows = [
    ("Risk repricing", 0, 0.35, RED, "weeks"),
    ("Data-center credit", 1, 2, GOLD, "1–3 years"),
    ("AI adoption", 3, 4, TEAL, "3–7 years"),
    ("New mine", 0, 17, COPPER, "~17 years"),
]
for i, (label, left, width, color, tag) in enumerate(rows):
    ax.barh(i, width, left=left, height=0.52, color=color, alpha=0.9)
    ax.text(left + width + 0.25, i, tag, va="center", fontsize=9.5, color=color, fontweight="bold")
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows], fontsize=9.5)
ax.set_xlim(0, 18.8); ax.set_xlabel("Years", fontsize=9.5)
ax.set_title("Three clocks, three speeds", loc="left", fontsize=13, fontweight="bold", color=NAVY, pad=12)
style(ax, "x"); ax.grid(axis="y", visible=False)
fig.text(0.01, -0.02, "Illustrative. AI adoption 3–7 years and data-center credit 1–3 years are research assumptions; new mine ~17 years from IEA.", fontsize=7.5, color=MID)
save(fig, "en_three_clocks.png")

# 2. US data-center electricity
fig, ax = plt.subplots(figsize=(10.2, 3.7))
ax.bar(["2023"], [176], color=TEAL, width=0.45)
ax.bar(["2028E"], [580-325], bottom=325, color=COPPER, alpha=0.30, width=0.45)
ax.plot(["2028E","2028E"], [325,580], color=COPPER, lw=2.5)
ax.scatter(["2028E"], [452.5], color=COPPER, s=45, zorder=5)
ax.text(0, 176+18, "176 TWh\n4.4% of US power", ha="center", fontsize=9.5, color=NAVY, fontweight="bold")
ax.text(1, 580+18, "325–580 TWh\n6.7–12% of US power", ha="center", fontsize=9.5, color=COPPER, fontweight="bold")
ax.set_ylim(0, 660); ax.set_ylabel("TWh", fontsize=9.5)
ax.set_title("US data-center electricity: 176 TWh (2023) → 325–580 TWh (2028E)", loc="left", fontsize=12.5, fontweight="bold", color=NAVY, pad=10)
style(ax)
fig.text(0.01, -0.03, "Source: LBNL, 2024 United States Data Center Energy Usage Report. Range reflects low/high case; midpoint ~453 TWh.", fontsize=7.5, color=MID)
save(fig, "en_us_dc_power.png")

# 3. US power prices + gas
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 3.7), gridspec_kw={"width_ratios":[1.15,1]})
e = elec[elec["date"] >= "2015-01-01"]
ax1.plot(e["date"], e["value"]*100, color=COPPER, lw=2.0)
ax1.annotate("19.6¢\nSep 2026", (e["date"].iloc[-1], e["value"].iloc[-1]*100), textcoords="offset points", xytext=(-8,10), ha="right", fontsize=9, color=COPPER, fontweight="bold")
ax1.axhline(13.5, color=GRAY, lw=0.9, ls="--")
ax1.text(e["date"].iloc[0], 13.8, "2020 avg 13.5¢", fontsize=8, color=GRAY)
ax1.set_ylabel("US retail electricity, cents/kWh", fontsize=9)
ax1.set_title("Power prices: +45% since 2020", loc="left", fontsize=11, fontweight="bold", color=NAVY, pad=8)
style(ax1); ax1.xaxis.set_major_locator(mdates.YearLocator(2)); ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

g = gas[gas["date"] >= "2015-01-01"].set_index("date")["value"].resample("ME").mean().dropna().reset_index()
ax2.plot(g["date"], g["value"], color=TEAL, lw=1.6)
ax2.axhline(3.47, color=GRAY, lw=0.9, ls="--")
ax2.text(g["date"].iloc[0], 3.7, "2026 avg $3.47", fontsize=8, color=GRAY)
ax2.set_ylabel("Henry Hub, $/MMBtu", fontsize=9)
ax2.set_title("Gas is not the bottleneck", loc="left", fontsize=11, fontweight="bold", color=NAVY, pad=8)
style(ax2); ax2.xaxis.set_major_locator(mdates.YearLocator(2)); ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
fig.text(0.01, -0.04, "Sources: FRED APU000072610 (BLS average retail electricity price); FRED DHHNGSP (Henry Hub spot). EIA natural-gas storage is at the 89th percentile — the constraint is turbines, transformers, and interconnection, not molecules.", fontsize=7.5, color=MID)
save(fig, "en_us_power_prices.png")

# 4. EIA seasonal stocks 2x2
fig, axes = plt.subplots(2, 2, figsize=(10.2, 5.4))
series = [
    ("crude", "Crude oil", "Million barrels", 1e3),
    ("distillate", "Distillate", "Million barrels", 1e3),
    ("gasoline", "Gasoline", "Million barrels", 1e3),
    ("natgas", "Natural gas", "Bcf", 1.0),
]
for ax, (key, title, unit, div) in zip(axes.flat, series):
    df = pd.read_csv(CACHE/"eia"/eia_files[key])
    df["date"] = pd.to_datetime(df["date"]); df = df.dropna().sort_values("date")
    df["year"] = df["date"].dt.year; df["week"] = df["date"].dt.isocalendar().week.astype(int)
    for y in range(2021, 2026):
        s = df[df["year"] == y]
        ax.plot(s["week"], s["value"]/div, color="#D9D4C7", lw=1.0)
    s = df[df["year"] == 2026]
    ax.plot(s["week"], s["value"]/div, color=COPPER, lw=2.0)
    last, pct = eia[key]
    wk = last["date"].isocalendar().week
    ax.scatter([wk], [last["value"]/div], color=COPPER, s=28, zorder=5)
    ax.annotate(f"{last['value']/div:,.0f}", (wk, last["value"]/div), textcoords="offset points", xytext=(6,8), fontsize=8, color=COPPER, fontweight="bold")
    ax.set_title(f"{title}  ·  {pct:.0f}th percentile", loc="left", fontsize=10, fontweight="bold", color=NAVY)
    ax.set_xlim(1, 53); ax.set_xlabel("Week of year", fontsize=8); ax.set_ylabel(unit, fontsize=8)
    style(ax)
fig.suptitle("US energy inventories: tight in liquids, loose in gas", x=0.01, ha="left", fontsize=13, fontweight="bold", color=NAVY)
fig.text(0.01, -0.02, "Source: EIA Weekly Petroleum Status Report and Weekly Natural Gas Storage Report, week ending 2026-10-16. Gray lines: 2021–2025; orange: 2026. Percentile is trailing 5 years.", fontsize=7.5, color=MID)
fig.tight_layout(rect=[0,0,1,0.95])
save(fig, "en_eia_seasonal.png")

# 5. copper
cu15 = cu[cu["date"] >= "2015-01-01"]
fig, ax = plt.subplots(figsize=(10.2, 3.6))
ax.plot(cu15["date"], cu15["value"], color=COPPER, lw=1.8)
ax.fill_between(cu15["date"], cu15["value"], color=COPPER, alpha=0.08)
last_cu = cu15.iloc[-1]
ax.scatter([last_cu["date"]], [last_cu["value"]], color=COPPER, s=30, zorder=5)
ax.annotate(f"Sep 2026\n\\${last_cu['value']:,.0f}/t", (last_cu["date"], last_cu["value"]), textcoords="offset points", xytext=(-8,12), ha="right", fontsize=9, color=COPPER, fontweight="bold")
ax.set_ylabel("Copper, $/tonne", fontsize=9.5)
ax.set_title("Copper: prices are rising; supply takes 17 years", loc="left", fontsize=13, fontweight="bold", color=NAVY, pad=10)
style(ax); ax.xaxis.set_major_locator(mdates.YearLocator(2)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
fig.text(0.01, -0.03, "Source: FRED PCOPPUSDM (monthly global copper price). Supply facts: IEA (grade -40% since 1991; ~17 years from discovery to production); S&P Global (2026 copper exploration +32% to ~$4.3B).", fontsize=7.5, color=MID)
save(fig, "en_copper.png")

# 6. credit: time series + DC finance
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 3.8), gridspec_kw={"width_ratios":[1.45,1]})
for df, c, lab in [(ig, GRAY, "IG"), (hy, GOLD, "HY"), (ccc, RED, "CCC")]:
    d = df[df["date"] >= "2024-01-01"]
    ax1.plot(d["date"], d["value"]*100, color=c, lw=1.8 if lab=="CCC" else 1.4, label=lab)
    ax1.annotate(f"{d['value'].iloc[-1]*100:,.0f}bp", (d["date"].iloc[-1], d["value"].iloc[-1]*100), textcoords="offset points", xytext=(-6,6), ha="right", fontsize=8.5, color=c, fontweight="bold")
ax1.set_ylabel("Option-adjusted spread, bp", fontsize=9)
ax1.set_title("Credit spreads: the tail is widening", loc="left", fontsize=11, fontweight="bold", color=NAVY, pad=8)
ax1.legend(loc="upper left", frameon=False, fontsize=8, ncol=3)
style(ax1); ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6)); ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))

x2 = ["2025", "2026 YTD"]; y2 = [37, 106]
bars = ax2.bar(x2, y2, color=[GRAY, COPPER], width=0.5)
for b, v in zip(bars, y2):
    ax2.text(b.get_x()+b.get_width()/2, v+3, f"\\${v}B", ha="center", fontsize=10, color=NAVY, fontweight="bold")
ax2.set_ylim(0, 125); ax2.set_ylabel("Data-center project finance, $B", fontsize=9)
ax2.set_title("Project finance: \\$37B → \\$106B", loc="left", fontsize=11, fontweight="bold", color=NAVY, pad=8)
style(ax2)
fig.text(0.01, -0.04, "Sources: FRED BAMLC0A0CM/BAMLH0A0HYM2/BAMLH0A3HYC (2026-10-22); credit review (AI HY 360bp; data-center project finance 2025 ~\\$37B, 2026 YTD >\\$106B).", fontsize=7.5, color=MID)
save(fig, "en_credit.png")

# 7. COFER
fig, ax = plt.subplots(figsize=(10.2, 3.6))
ax.plot(cofer["dt"], cofer["USD"], color=NAVY, lw=2.2, label="USD")
ax.plot(cofer["dt"], cofer["EUR"], color=TEAL, lw=1.3, alpha=.85, label="EUR")
ax.plot(cofer["dt"], cofer["CNY"], color=GOLD, lw=1.3, alpha=.9, label="CNY")
ax.axhline(60, color=GRAY, lw=.8, ls="--")
for d, lab in [("1999-Q1","71.2%"),("2026-Q2","56.7%")]:
    row = cofer[cofer["period"]==d].iloc[0]
    ax.scatter([row["dt"]],[row["USD"]],color=GOLD,s=26,zorder=5)
    ax.annotate(lab,(row["dt"],row["USD"]),textcoords="offset points",xytext=(6,8) if d=="1999-Q1" else (-6,8),ha="left" if d=="1999-Q1" else "right",fontsize=9,color=GOLD,fontweight="bold")
ax.set_ylabel("Share of global reserves, %", fontsize=9)
ax.set_title("The dollar's reserve share: a slow migration, not a cliff", loc="left", fontsize=13, fontweight="bold", color=NAVY, pad=10)
ax.legend(loc="upper right", frameon=False, fontsize=8.5, ncol=3)
style(ax); ax.xaxis.set_major_locator(mdates.YearLocator(5)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
fig.text(0.01, -0.03, "Source: IMF COFER, 2026Q2. USD holdings \\$7.495T; total reserves \\$13.217T; peak USD holdings \\$7.677T in 2021Q3.", fontsize=7.5, color=MID)
save(fig, "en_cofer.png")

# 8. oil in gold terms
base = hist.iloc[0]
idx_wti = hist["wti"]/base["wti"]*100
idx_gold = hist["gold"]/base["gold"]*100
idx_og = hist["oil_gold"]/base["oil_gold"]*100
fig, ax = plt.subplots(figsize=(10.2, 3.9))
ax.plot(hist["date"], idx_wti, color=TEAL, lw=2.0, label="WTI (USD)")
ax.plot(hist["date"], idx_gold, color=GRAY, lw=1.7, label="Gold (USD)")
ax.plot(hist["date"], idx_og, color=COPPER, lw=2.3, label="Oil/Gold")
for s,c,lab in [(idx_wti,TEAL,f"{idx_wti.iloc[-1]-100:+.1f}%"),(idx_gold,GRAY,f"{idx_gold.iloc[-1]-100:+.1f}%"),(idx_og,COPPER,f"{idx_og.iloc[-1]-100:+.1f}%")]:
    ax.annotate(lab,(hist["date"].iloc[-1],s.iloc[-1]),textcoords="offset points",xytext=(-6,6) if c!=GRAY else (-6,-16),ha="right",fontsize=9.5,color=c,fontweight="bold")
ax.axhline(100,color=GRAY,lw=.8,ls=":")
ax.set_ylabel("2026-06-19 = 100", fontsize=9)
ax.set_title("Oil in gold terms is up more than oil in dollars", loc="left", fontsize=13, fontweight="bold", color=NAVY, pad=10)
ax.legend(loc="upper left", frameon=False, fontsize=8.5, ncol=3)
style(ax); ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
fig.text(0.01, -0.02, "Source: Deep-Risk-OPP daily card/history. Oil/Gold = WTI / gold; indexed for relative performance only.", fontsize=7.5, color=MID)
save(fig, "en_oil_gold.png")

# 9. rates
fig, ax = plt.subplots(figsize=(10.2, 3.6))
for df,c,lab in [(dgs10,NAVY,"10Y nominal"),(dfii10,TEAL,"10Y real"),(t10yie,GOLD,"10Y breakeven")]:
    d = df[df["date"] >= "2024-01-01"]
    ax.plot(d["date"], d["value"], color=c, lw=1.7, label=lab)
ax.set_ylabel("%", fontsize=9)
ax.set_title("Rates: 10Y at 4.96%, real yield 2.64%, breakeven 2.34%", loc="left", fontsize=13, fontweight="bold", color=NAVY, pad=10)
ax.legend(loc="upper right", frameon=False, fontsize=8.5, ncol=3)
style(ax); ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
fig.text(0.01, -0.03, "Source: FRED DGS10 / DFII10 / T10YIE, 2026-10-22/23. 2s10s +31bp.", fontsize=7.5, color=MID)
save(fig, "en_rates.png")

# 10. debt + interest
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 3.6), gridspec_kw={"width_ratios":[1.25,1]})
d = debt[debt["date"] >= "2015-01-01"]
ax1.plot(d["date"], d["value"]/1e6, color=NAVY, lw=2.0)
ax1.set_ylabel("Federal debt, $T", fontsize=9)
ax1.set_title("Federal debt: ~\\$39.5T", loc="left", fontsize=11, fontweight="bold", color=NAVY, pad=8)
style(ax1); ax1.xaxis.set_major_locator(mdates.YearLocator(2)); ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
i = interest[interest["date"] >= "2015-01-01"]
ax2.bar(i["date"].dt.year, i["value"]/1e3, color=GOLD, width=0.65)
ax2.set_ylabel("Interest outlays, $B", fontsize=9)
ax2.set_title("Interest: ~\\$970B in FY2025", loc="left", fontsize=11, fontweight="bold", color=NAVY, pad=8)
style(ax2)
fig.text(0.01, -0.04, "Sources: FRED GFDEBTN (quarterly federal debt, 2026Q2); FRED FYOINT (federal interest outlays, FY2025).", fontsize=7.5, color=MID)
save(fig, "en_debt.png")

print("EN charts done:", sorted(p.name for p in ASSETS.glob("*.png")))

# ---------------- HTML + PDF ----------------
from playwright.sync_api import sync_playwright
from pypdf import PdfWriter, PdfReader

def data_uri(name):
    p = ASSETS / name
    if not p.exists():
        p = ASSETS / "visuals" / name
    mime = "image/jpeg" if p.suffix.lower() in (".jpg", ".jpeg") else "image/png"
    return "data:%s;base64,%s" % (mime, base64.b64encode(p.read_bytes()).decode())

body_tpl = (BASE/"scripts"/"supercycle_report_en_body.html").read_text(encoding="utf-8")
for fig in list(ASSETS.glob("*.png")) + list((ASSETS/"visuals").glob("*.jpg")):
    body_tpl = body_tpl.replace("{{FIG:%s}}" % fig.name, data_uri(fig.name))
body_html = OUT / "_en_body_rendered.html"
body_html.write_text(body_tpl, encoding="utf-8")

cover_tpl = (BASE/"scripts"/"supercycle_report_en_cover.html").read_text(encoding="utf-8")
cover_html = OUT / "_en_cover_rendered.html"
cover_html.write_text(cover_tpl, encoding="utf-8")

cover_pdf = OUT / "_en_cover.pdf"
body_pdf = OUT / "_en_body.pdf"
final_pdf = OUT / "The-Next-Supercycle-Is-a-Collateral-Story-2026-10-25-V2.pdf"

header = """<div style="width:100%;font-family:'Segoe UI';font-size:7pt;color:#8A8F98;padding:0 18mm;display:flex;justify-content:space-between;">
<span>Deep-Risk-OPP · The Next Supercycle Is a Collateral Story</span><span>2026-10-25</span></div>"""
footer = """<div style="width:100%;font-family:'Segoe UI';font-size:7pt;color:#8A8F98;padding:0 18mm;display:flex;justify-content:space-between;">
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
             margin={"top":"19mm","bottom":"17mm","left":"18mm","right":"18mm"})
    browser.close()

writer = PdfWriter()
for f in (cover_pdf, body_pdf):
    for pg in PdfReader(str(f)).pages:
        writer.add_page(pg)
writer.add_metadata({
    "/Title": "The Next Supercycle Is a Collateral Story",
    "/Author": "Deep-Risk-OPP",
    "/Subject": "AI capex, power, copper, and the re-anchoring of US credit",
    "/Keywords": "AI capex, data centers, power, copper, gold, credit spreads, FRED, EIA, collateral",
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
