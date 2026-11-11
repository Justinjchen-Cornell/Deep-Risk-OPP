# -*- coding: utf-8 -*-
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

BASE=Path(__file__).resolve().parent.parent
OUT=BASE/"看板日志"/"reports"/"special"/"linkedin_assets"
rows=json.load(open(BASE/"history.json",encoding="utf-8"))["rows"]
rows=[r for r in rows if r.get("gor_wti") and r.get("gor_brent") and r["date"]>="2026-09-01"]
dates=[datetime.strptime(r["date"],"%Y-%m-%d") for r in rows]
gw=[r["gor_wti"] for r in rows]; gb=[r["gor_brent"] for r in rows]

NAVY="#0B1F33"; GOLD="#C9A227"; COPPER="#B87333"; RED="#B23A2E"; GRAY="#8A8F98"; MID="#5A6572"; LINE="#E3DED2"
plt.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Segoe UI","Arial"],
    "axes.unicode_minus":False,"figure.facecolor":"white","text.color":NAVY})

fig, ax = plt.subplots(figsize=(12,6.75))
ax.plot(dates, gw, color=COPPER, lw=2.2, label="GOR (WTI)")
ax.plot(dates, gb, color=NAVY, lw=2.2, label="GOR (Brent)")
ax.axhline(45, color=RED, lw=1.0, ls=(0,(4,3)))
# annotations
ax.annotate("Oct 12\n46.8", (datetime(2026,10,12), 46.8), xytext=(-8,22), textcoords="offset points", fontsize=9, color=COPPER, ha="center")
ax.annotate("Oct 31" + chr(10) + "37.7", (datetime(2026,10,31), 37.73), xytext=(-54,-20), textcoords="offset points", fontsize=9, color=COPPER, ha="right")
ax.annotate("Nov 10" + chr(10) + "48.0", (datetime(2026,11,10), 48.0), xytext=(0,12), textcoords="offset points", fontsize=9, color=COPPER, fontweight="bold", ha="center")
ax.annotate("46.6", (dates[-1]+timedelta(days=2), gw[-1]), fontsize=9, color=COPPER, fontweight="bold", ha="left", va="center")
ax.annotate("43.8", (dates[-1]+timedelta(days=2), gb[-1]), fontsize=9, color=NAVY, fontweight="bold", ha="left", va="center")
ax.set_ylim(33, 50.5)
ax.set_xlim(dates[0]-timedelta(days=1), dates[-1]+timedelta(days=8))
ax.legend(loc="lower left", frameon=False, fontsize=9.5)
ax.set_ylabel("Gold / oil ratio", fontsize=10, color=MID)
ax.xaxis.set_major_locator(mdates.MonthLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
ax.tick_params(labelsize=9, colors=MID)
for s in ("top","right"): ax.spines[s].set_visible(False)
ax.spines["left"].set_color(LINE); ax.spines["bottom"].set_color(LINE)
ax.grid(axis="y", color="#F0ECE2", lw=0.8); ax.set_axisbelow(True)
fig.text(0.06, 0.925, "Gold/oil: 46.8 → 37.7 → 48.0 in a month", fontsize=18, fontweight="bold", color=NAVY)
fig.text(0.06, 0.878, "GOR (WTI) and GOR (Brent), Sep–Nov 2026 · daily card data", fontsize=10.5, color=MID)
fig.text(0.06, 0.045, "45 is the framework's extreme-alarm line. An alarm means run the mechanism checklist, not buy oil.", fontsize=9.2, color=NAVY)
fig.text(0.06, 0.012, "Source: GOR daily card (gold, WTI, Brent). Gold/oil = gold $/oz ÷ crude $/bbl.", fontsize=7.6, color=GRAY)
fig.subplots_adjust(left=0.08, right=0.97, top=0.83, bottom=0.13)
p=OUT/"gor_four_week_roundtrip.png"; fig.savefig(p,dpi=200,facecolor="white"); print(p, p.stat().st_size)
