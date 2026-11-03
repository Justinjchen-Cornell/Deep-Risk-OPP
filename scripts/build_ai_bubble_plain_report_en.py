# -*- coding: utf-8 -*-
"""Build the English plain-language AI bubble report (charts + HTML + PDF)."""
import base64
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "看板日志" / "reports" / "special"
ASSETS = OUT / "ai_bubble_assets_en"
ASSETS.mkdir(parents=True, exist_ok=True)
CACHE = BASE / "看板日志" / "cache"

NAVY="#0B1F33"; GOLD="#C9A227"; COPPER="#B87333"; TEAL="#1F6F78"
RED="#B23A2E"; GRAY="#8A8F98"; MID="#5A6572"; GRID="#E8E3D8"
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
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

def fred(fn):
    df = pd.read_csv(fn)
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna().sort_values("date")

# ---------------- charts ----------------
# 1. four-layer plain chain
fig, ax = plt.subplots(figsize=(12, 4.4))
ax.set_xlim(0, 12); ax.set_ylim(0, 4.6); ax.axis("off")
boxes = [
    (0.2, "Valuation layer", ["Is it expensive?", "P/E 28x / CAPE 41x", "Poor odds, uncertain timing"], GOLD),
    (3.08, "Demand layer", ["Is anyone using it?", "23GW vs <2GW", "Revenue/compute 0.4 to 2.0"], TEAL),
    (5.96, "Supply layer", ["How fragile is price?", "Memory 3.5-power", "1.35 to 1.10 = -51%"], COPPER),
    (8.84, "Credit layer", ["When does it crack?", "HY OAS 344bp", "CCC 1,327bp / CDS 4.5x"], RED),
]
for x, title, lines, color in boxes:
    ax.add_patch(FancyBboxPatch((x, 1.55), 2.9, 2.3, boxstyle="round,pad=0.05,rounding_size=0.08",
                                linewidth=1.2, edgecolor=color, facecolor="white"))
    ax.text(x+0.15, 3.35, title, fontsize=12, fontweight="bold", color=color)
    for j, line in enumerate(lines):
        ax.text(x+0.15, 2.95-j*0.36, line, fontsize=9.4, color=NAVY, va="top")
for x in [2.98, 5.86, 8.74]:
    ax.annotate("", xy=(x+0.16, 2.7), xytext=(x-0.02, 2.7), arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.6))
ax.text(6, 0.85, "One chain: valuation -> demand -> supply -> credit", ha="center", fontsize=13, color=NAVY, fontweight="bold")
ax.text(6, 0.35, "The technology is real. The financing chain is fragile.", ha="center", fontsize=10.5, color=COPPER, fontweight="bold")
save(fig, "plain_chain.png")

# 2. capex break-even
lives = ["5 yr\n(chips/servers)", "7 yr\n(mixed)", "10 yr\n(data centers/power)"]
rev50 = [222, 175, 142]
rev30 = [370, 292, 236]
x = np.arange(len(lives)); w = 0.34
fig, ax = plt.subplots(figsize=(10.2, 4.4))
b1 = ax.bar(x-w/2, rev30, w, color=COPPER, label="30% EBITDA margin")
b2 = ax.bar(x+w/2, rev50, w, color=TEAL, label="50% EBITDA margin")
for bars in (b1, b2):
    for b in bars:
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+8, f"{b.get_height():.0f}",
                ha="center", fontsize=9, color=NAVY, fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(lives, fontsize=9)
ax.set_ylabel(r"AI revenue needed per year (\$bn)", fontsize=9.5)
ax.set_title(r"\$400B of AI capex a year: how much AI revenue covers a 12% cost of capital?",
             loc="left", fontsize=12.2, fontweight="bold", color=NAVY, pad=10)
ax.legend(loc="upper right", frameon=False, fontsize=8.5)
style(ax)
fig.text(0.01, -0.04, r"Assumptions: C=\$400B/yr; 12% cost of capital; annuity; revenue = EBITDA / margin. Stress test, not a forecast.", fontsize=7.5, color=MID)
save(fig, "ab_capex_breakeven.png")

# 3. memory sensitivity
labels = ["1.10x", "1.20x", "1.35x", "1.35->1.30", "1.35->1.25", "1.35->1.20", "1.35->1.10"]
vals = [40, 89, 184, -12, -24, -34, -51]
colors = [TEAL if v>0 else RED for v in vals]
fig, ax = plt.subplots(figsize=(10.2, 4.0))
bars = ax.bar(labels, vals, color=colors, width=0.6)
for b, v in zip(bars, vals):
    ax.text(b.get_x()+b.get_width()/2, v + (6 if v>0 else -12), f"{v:+d}%",
            ha="center", fontsize=9, color=NAVY, fontweight="bold")
ax.axhline(0, color=GRAY, lw=0.8)
ax.set_ylabel("Memory price change, %", fontsize=9.5)
ax.set_title("Memory price elasticity to demand/capacity: boom up, bust down (index 3.5)",
             loc="left", fontsize=12.0, fontweight="bold", color=NAVY, pad=10)
style(ax)
fig.text(0.01, -0.04, "Model: P ~ (demand/capacity)^3.5; the 3.5 exponent is a source estimate, not physics. Contract/spot mix, HBM, capacity additions also matter.", fontsize=7.5, color=MID)
save(fig, "ab_memory_sensitivity.png")

# 4. credit spreads + VIX
hy = fred(CACHE/"fred_BAMLH0A0HYM2.csv")
ccc = fred(CACHE/"fred_BAMLH0A3HYC.csv")
ig = fred(CACHE/"fred_BAMLC0A0CM.csv")
vix = fred(CACHE/"fred_VIXCLS.csv")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10.2, 4.9), sharex=True, gridspec_kw={"height_ratios":[1.5,1]})
for df, c, lab in [(ig, GRAY, "IG"), (hy, GOLD, "HY"), (ccc, RED, "CCC")]:
    d = df[df["date"] >= "2024-01-01"]
    ax1.plot(d["date"], d["value"]*100, color=c, lw=1.6 if lab!="CCC" else 2.0, label=lab)
    ax1.annotate(f"{d['value'].iloc[-1]*100:,.0f}bp", (d["date"].iloc[-1], d["value"].iloc[-1]*100),
                 textcoords="offset points", xytext=(-6,6), ha="right", fontsize=8.5, color=c, fontweight="bold")
ax1.set_ylabel("OAS, bp", fontsize=9)
ax1.set_title("Credit cracks first; equities are still calm", loc="left", fontsize=12.5, fontweight="bold", color=NAVY, pad=10)
ax1.legend(loc="upper left", frameon=False, fontsize=8.5, ncol=3)
style(ax1)
d = vix[vix["date"] >= "2024-01-01"]
ax2.plot(d["date"], d["value"], color=TEAL, lw=1.5)
ax2.annotate(f"{d['value'].iloc[-1]:.1f}", (d["date"].iloc[-1], d["value"].iloc[-1]),
             textcoords="offset points", xytext=(-6,6), ha="right", fontsize=8.5, color=TEAL, fontweight="bold")
ax2.axhline(22.5, color=RED, lw=0.9, ls=":")
ax2.text(d["date"].iloc[-1], 26.6, "22.5 alarm line", fontsize=7.5, color=RED, ha="right")
ax2.set_ylabel("VIX", fontsize=9)
style(ax2); ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=6)); ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
fig.text(0.01, -0.03, "Data: FRED BAMLC0A0CM / BAMLH0A0HYM2 / BAMLH0A3HYC / VIXCLS, through 2026-10-30.", fontsize=7.5, color=MID)
save(fig, "ab_credit_vix.png")

# 5. Nvidia shipments vs Anthropic usage
years = ["2024", "2025E", "2026E", "2027E"]
gw = [5.8, 9.7, 16.0, 23.0]
gpu = ["3.7M", "5M+", "8M+", "10M+"]
fig, ax = plt.subplots(figsize=(10.2, 4.2))
bars = ax.bar(years, gw, color=[TEAL, TEAL, COPPER, COPPER], width=0.5)
for b, v, g in zip(bars, gw, gpu):
    ax.text(b.get_x()+b.get_width()/2, v+0.7, f"{v:.1f} GW\n{g} GPUs", ha="center", fontsize=9, color=NAVY, fontweight="bold")
ax.axhline(2.0, color=RED, lw=1.4, ls="--")
ax.text(0.02, 26.2, "Dashed line: Anthropic actual usage <2GW (source estimate)", fontsize=8.3, color=RED, fontweight="bold")
ax.set_ylim(0, 28); ax.set_ylabel("Compute implied by Nvidia shipments, GW", fontsize=9.5)
ax.set_title("Compute supply 23GW vs top tenant <2GW: idle is not an accident", loc="left", fontsize=12.2, fontweight="bold", color=NAVY, pad=10)
style(ax)
fig.text(0.01, -0.04, "Source: shipment and equivalent-power estimates from source material; Anthropic converted from S-1 compute spend and rental prices. Speaker estimates, not official statistics.", fontsize=7.5, color=MID)
save(fig, "ab_nvidia_gw.png")

# 6. transmission chain
fig, ax = plt.subplots(figsize=(11, 5.5))
ax.set_xlim(0, 11); ax.set_ylim(0, 7); ax.axis("off")
steps = [
    ("1. Capex growth peaks", "capex +50% -> +20%; orders revised down first", GOLD),
    ("2. Suppliers deteriorate", "inventory/receivables up; supplier finance tightens", COPPER),
    ("3. Credit cracks first", "AI HY/CCC widen; CDS volume jumps", RED),
    ("4. Hyperscalers cut capex", "Nvidia/memory revenue turns negative", RED),
    ("5. Wealth effect / credit contraction", "HY defaults up; BDC redemptions", NAVY),
    ("6. Policy response", "Fed cuts; cash-flow survivors live", TEAL),
]
for i, (title, body, color) in enumerate(steps):
    y = 6.0 - i*1.02
    ax.add_patch(FancyBboxPatch((0.8, y), 5.4, 0.78, boxstyle="round,pad=0.04,rounding_size=0.06",
                                linewidth=1.1, edgecolor=color, facecolor="white"))
    ax.text(1.0, y+0.62, title, fontsize=9.6, fontweight="bold", color=color)
    ax.text(1.0, y+0.36, body, fontsize=7.6, color=NAVY, va="top")
    if i < len(steps)-1:
        ax.annotate("", xy=(3.5, y-0.22), xytext=(3.5, y-0.02),
                    arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.5))
ax.text(7.2, 5.3, "Risk blows up", fontsize=13, color=RED, fontweight="bold")
ax.text(7.2, 4.95, "from the bottom", fontsize=13, color=RED, fontweight="bold")
ax.text(7.2, 4.4, "The first to die are leveraged suppliers,\nnot Microsoft/Google.", fontsize=9.5, color=NAVY)
ax.text(7.2, 3.2, "Technology stays;\nthe financing chain breaks.", fontsize=12.5, color=COPPER, fontweight="bold")
ax.text(7.2, 2.5, "When the railway bubble burst, the tracks remained;\nwhen tulips burst, nothing remained.", fontsize=9.2, color=MID)
save(fig, "ab_transmission.png")

# 7. fragility score
components = ["Valuation\nCAPE 41x", "Capex / revenue gap", "Compute utilization", "Memory cycle", "Credit spreads / CDS"]
scores = [80, 70, 65, 80, 75]
weights = [15, 25, 20, 15, 25]
fig, ax = plt.subplots(figsize=(10.2, 4.2))
colors = [GOLD, COPPER, TEAL, GOLD, RED]
bars = ax.barh(components, scores, color=colors, height=0.55)
for b, s, w in zip(bars, scores, weights):
    ax.text(s+1.5, b.get_y()+b.get_height()/2, f"{s}/100  ·  weight {w}%", va="center", fontsize=8.8, color=NAVY)
ax.set_xlim(0, 100); ax.set_xlabel("Fragility score (0 = no stress, 100 = crisis)", fontsize=9)
ax.set_title("AI bubble fragility score: 73/100 (fragile, not broken)", loc="left", fontsize=12.5, fontweight="bold", color=NAVY, pad=10)
ax.invert_yaxis(); style(ax, "x")
fig.text(0.01, -0.04, "Score is a framework judgment, not a probability; weights adjustable. Valuation 15%, capex/revenue gap 25%, compute utilization 20%, memory cycle 15%, credit 25%.", fontsize=7.5, color=MID)
save(fig, "ab_fragility_score.png")

# 8. GPU rental price
years = [2023, 2024, 2025, 2026, 2027, 2028]
h100 = [9.0, 4.0, 2.5, 2.0, 1.6, 1.4]
b200 = [np.nan, np.nan, 5.0, 4.0, 3.0, 2.6]
rubin = [np.nan, np.nan, np.nan, np.nan, 6.0, 5.0]
fig, ax = plt.subplots(figsize=(10.2, 4.2))
ax.axvspan(2026, 2028, color=GOLD, alpha=0.08)
ax.plot(years, h100, marker="o", color=TEAL, lw=2.0, label="H100")
ax.plot(years, b200, marker="o", color=COPPER, lw=2.0, label="B200")
ax.plot(years, rubin, marker="o", color=RED, lw=2.0, label="Rubin")
for xs, ys, c in [(years, h100, TEAL), (years, b200, COPPER), (years, rubin, RED)]:
    for x, y in zip(xs, ys):
        if not np.isnan(y):
            ax.annotate(rf"\${y:.1f}", (x, y), textcoords="offset points", xytext=(0,8), ha="center", fontsize=8, color=c)
ax.set_xticks(years); ax.set_xticklabels(["2023", "2024", "2025", "2026", "2027E", "2028E"])
ax.set_ylabel(r"GPU rental, \$/card/hour", fontsize=9.5)
ax.set_title(r"GPU rents: from \$9/hour in 2023 to \$1-2/hour by 2028E", loc="left", fontsize=12.2, fontweight="bold", color=NAVY, pad=10)
ax.legend(loc="upper right", frameon=False, fontsize=8.5)
style(ax)
fig.text(0.01, -0.04, "Prices are median ranges from public cloud quotes/channel checks; 2026-2028 are scenario forecasts (shaded). Terms, volume, networking, power and utilization all matter.", fontsize=7.5, color=MID)
save(fig, "ab_gpu_rental.png")

print("charts done:", sorted(p.name for p in ASSETS.glob("*.png")))

# ---------------- HTML + PDF ----------------
from playwright.sync_api import sync_playwright
from pypdf import PdfWriter, PdfReader

def data_uri(name):
    p = ASSETS / name
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()

body_tpl = (BASE/"scripts"/"ai_bubble_plain_body_en.html").read_text(encoding="utf-8")
for fig in ASSETS.glob("*.png"):
    body_tpl = body_tpl.replace("{{FIG:%s}}" % fig.name, data_uri(fig.name))
body_html = OUT / "_abe_body_rendered.html"
body_html.write_text(body_tpl, encoding="utf-8")

cover_tpl = (BASE/"scripts"/"ai_bubble_plain_cover_en.html").read_text(encoding="utf-8")
cover_html = OUT / "_abe_cover_rendered.html"
cover_html.write_text(cover_tpl, encoding="utf-8")

cover_pdf = OUT / "_abe_cover.pdf"
body_pdf = OUT / "_abe_body.pdf"
final_pdf = OUT / "The-AI-Bubble-Plain-Language-2026-11-03.pdf"

header = """<div style="width:100%;font-family:'Segoe UI',Arial,sans-serif;font-size:6.8pt;color:#8A8F98;padding:0 18mm;display:flex;justify-content:space-between;letter-spacing:0.3pt;border-bottom:0.5pt solid #E3DED2;padding-bottom:2mm;">
<span>DEEP-RISK-OPP &middot; THE AI BUBBLE &middot; SECOND-/THIRD-ORDER</span><span>2026-11-03</span></div>"""
footer = """<div style="width:100%;font-family:'Segoe UI',Arial,sans-serif;font-size:6.8pt;color:#8A8F98;padding:2mm 18mm 0;display:flex;justify-content:space-between;border-top:0.5pt solid #E3DED2;">
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
    "/Title": "The AI Bubble: Risks, the Path, and Second-/Third-Order Opportunities",
    "/Author": "Deep-Risk-OPP",
    "/Subject": "Plain-language research framework (English edition)",
    "/Keywords": "AI bubble, capex, credit, GPU, power, second-order, third-order",
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
