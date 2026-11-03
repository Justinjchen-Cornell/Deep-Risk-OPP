# -*- coding: utf-8 -*-
"""Regenerate Chinese charts for the plain-language edition (data to 2026-10-30)."""
import json, base64
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "看板日志" / "reports" / "special"
ASSETS = OUT / "ai_bubble_assets"
ASSETS.mkdir(parents=True, exist_ok=True)
CACHE = BASE / "看板日志" / "cache"

NAVY="#0B1F33"; GOLD="#C9A227"; COPPER="#B87333"; TEAL="#1F6F78"
RED="#B23A2E"; GRAY="#8A8F98"; MID="#5A6572"; GRID="#E8E3D8"
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

def fred(fn):
    df = pd.read_csv(fn)
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna().sort_values("date")

# ---------------- charts ----------------
# 1. four reports as one chain
fig, ax = plt.subplots(figsize=(12, 4.8))
ax.set_xlim(0, 12); ax.set_ylim(0, 5); ax.axis("off")
boxes = [
    (0.3, "材料 1 · 估值层", "PE 28x / CAPE 41x\n赔率差，时机不确定", GOLD),
    (3.15, "材料 2 · 需求层", "算力 23GW\nAnthropic <2GW\n收入/算力 0.4→2.0", TEAL),
    (6.0, "材料 3 · 供给层", "内存 3.5 次方\n需求/产能 1.35→1.10\n价格 −50%", COPPER),
    (8.85, "材料 4 · 信用层", "AI HY +55bp/周\nCDS 4.5x\n2028–30 到期墙", RED),
]
for x, title, body, color in boxes:
    ax.add_patch(FancyBboxPatch((x, 2.2), 2.65, 2.0, boxstyle="round,pad=0.05,rounding_size=0.08",
                                linewidth=1.2, edgecolor=color, facecolor="white"))
    ax.text(x+0.14, 3.85, title, fontsize=10.5, fontweight="bold", color=color)
    ax.text(x+0.14, 3.25, body, fontsize=9.2, color=NAVY, va="top", linespacing=1.45)
for x in [2.96, 5.81, 8.66]:
    ax.annotate("", xy=(x+0.17, 3.2), xytext=(x-0.02, 3.2),
                arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.6))
ax.text(6, 1.42, "同一枚硬币的四层：赔率 → 需求 → 供给弹性 → 触发器",
        ha="center", fontsize=12, color=NAVY, fontweight="bold")
ax.text(6, 0.78, "技术是真的；融资链条是脆的。",
        ha="center", fontsize=10.5, color=COPPER, fontweight="bold")
ax.text(6, 0.28, "四份材料不是四篇独立报告，而是一条链的四层。",
        ha="center", fontsize=9.2, color=MID)
save(fig, "ab_report_logic.png")

# 2. capex break-even
lives = ["5 年\n(芯片/服务器)", "7 年\n(混合)", "10 年\n(数据中心/电力)"]
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
ax.set_ylabel("每年所需 AI 收入（十亿美元）", fontsize=9.5)
ax.set_title("每年 $400B AI 资本开支，需要多少 AI 收入才能覆盖 12% 资金成本？",
             loc="left", fontsize=12.5, fontweight="bold", color=NAVY, pad=10)
ax.legend(loc="upper right", frameon=False, fontsize=8.5)
style(ax)
fig.text(0.01, -0.04, "假设：C=$400B/年；资金成本 12%；按年金法折算；收入=EBITDA/利润率。仅为压力测试，不是预测。", fontsize=7.5, color=MID)
save(fig, "ab_capex_breakeven.png")

# 3. memory sensitivity
labels = ["1.10x", "1.20x", "1.35x", "1.35→1.30", "1.35→1.25", "1.35→1.20", "1.35→1.10"]
vals = [40, 89, 184, -12, -24, -34, -51]
colors = [TEAL if v>0 else RED for v in vals]
fig, ax = plt.subplots(figsize=(10.2, 4.0))
bars = ax.bar(labels, vals, color=colors, width=0.6)
for b, v in zip(bars, vals):
    ax.text(b.get_x()+b.get_width()/2, v + (6 if v>0 else -12), f"{v:+d}%",
            ha="center", fontsize=9, color=NAVY, fontweight="bold")
ax.axhline(0, color=GRAY, lw=0.8)
ax.set_ylabel("内存价格相对变化 %", fontsize=9.5)
ax.set_title("内存价格对需求/产能比的弹性：上行暴利，下行灾难（假设指数 3.5）",
             loc="left", fontsize=12.2, fontweight="bold", color=NAVY, pad=10)
style(ax)
fig.text(0.01, -0.04, "模型：P ∝ (需求/产能)^3.5；指数 3.5 为材料 3 的估算，不是物理定律。实际价格还受合约/现货、HBM 结构、产能投放影响。", fontsize=7.5, color=MID)
save(fig, "ab_memory_sensitivity.png")

# 4. credit spreads + VIX
hy = fred(CACHE/"fred_BAMLH0A0HYM2.csv")
ccc = fred(CACHE/"fred_BAMLH0A3HYC.csv")
ig = fred(CACHE/"fred_BAMLC0A0CM.csv")
vix = fred(CACHE/"fred_VIXCLS.csv")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10.2, 5.6), sharex=True, gridspec_kw={"height_ratios":[1.5,1]})
for df, c, lab in [(ig, GRAY, "IG"), (hy, GOLD, "HY"), (ccc, RED, "CCC")]:
    d = df[df["date"] >= "2024-01-01"]
    ax1.plot(d["date"], d["value"]*100, color=c, lw=1.6 if lab!="CCC" else 2.0, label=lab)
    ax1.annotate(f"{d['value'].iloc[-1]*100:,.0f}bp", (d["date"].iloc[-1], d["value"].iloc[-1]*100),
                 textcoords="offset points", xytext=(-6,6), ha="right", fontsize=8.5, color=c, fontweight="bold")
ax1.set_ylabel("OAS，bp", fontsize=9)
ax1.set_title("信用市场先裂，股票市场还平静", loc="left", fontsize=12.5, fontweight="bold", color=NAVY, pad=10)
ax1.legend(loc="upper left", frameon=False, fontsize=8.5, ncol=3)
style(ax1)
d = vix[vix["date"] >= "2024-01-01"]
ax2.plot(d["date"], d["value"], color=TEAL, lw=1.5)
ax2.annotate(f"{d['value'].iloc[-1]:.1f}", (d["date"].iloc[-1], d["value"].iloc[-1]),
             textcoords="offset points", xytext=(-6,6), ha="right", fontsize=8.5, color=TEAL, fontweight="bold")
ax2.axhline(22.5, color=RED, lw=0.9, ls=":")
ax2.text(d["date"].iloc[-1], 26.6, "22.5 恐慌线", fontsize=7.5, color=RED, ha="right")
ax2.set_ylabel("VIX", fontsize=9)
style(ax2); ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=6)); ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
fig.text(0.01, -0.03, "数据：FRED BAMLC0A0CM / BAMLH0A0HYM2 / BAMLH0A3HYC / VIXCLS，截至 2026-10-30。", fontsize=7.5, color=MID)
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
ax.text(0.02, 26.0, "虚线：Anthropic 实际占用 <2GW（材料 2 估算）", fontsize=8.3, color=RED, fontweight="bold")
ax.set_ylim(0, 28); ax.set_ylabel("英伟达出货对应的算力，GW", fontsize=9.5)
ax.set_title("算力供给 23GW vs 头部租户 <2GW：闲置不是意外", loc="left", fontsize=12.5, fontweight="bold", color=NAVY, pad=10)
style(ax)
fig.text(0.01, -0.04, "来源：材料 2 对英伟达出货量与等效功率的估算；Anthropic 按 S-1 算力支出与租赁价折算。均为发言人口径，非官方统计。", fontsize=7.5, color=MID)
save(fig, "ab_nvidia_gw.png")

# 6. transmission chain
fig, ax = plt.subplots(figsize=(11, 6.2))
ax.set_xlim(0, 11); ax.set_ylim(0, 7); ax.axis("off")
steps = [
    ("① 资本开支增速见顶", "capex 从 +50% 降到 +20%\n订单增速先下修", GOLD),
    ("② 供应商恶化", "库存/应收上升\n供应商融资收紧", COPPER),
    ("③ 信用先裂", "AI HY/CCC 走阔\nCDS 放量、项目融资收紧", RED),
    ("④ 巨头削减 capex", "英伟达/内存收入转负\n科技股杀估值", RED),
    ("⑤ 财富效应/信用收缩", "高收益债违约↑\n私募信贷/BDC 赎回", NAVY),
    ("⑥ 政策响应", "Fed 降息/流动性\n有现金流者存活", TEAL),
]
for i, (title, body, color) in enumerate(steps):
    y = 6.0 - i*1.02
    ax.add_patch(FancyBboxPatch((0.8, y), 5.2, 0.84, boxstyle="round,pad=0.04,rounding_size=0.06",
                                linewidth=1.1, edgecolor=color, facecolor="white"))
    ax.text(1.0, y+0.66, title, fontsize=9.6, fontweight="bold", color=color)
    ax.text(1.0, y+0.40, body, fontsize=7.4, color=NAVY, va="top", linespacing=1.3)
    if i < len(steps)-1:
        ax.annotate("", xy=(3.4, y-0.22), xytext=(3.4, y-0.02),
                    arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.5))
ax.text(7.2, 5.2, "风险从下往上爆", fontsize=13, color=RED, fontweight="bold")
ax.text(7.2, 4.75, "先死的是杠杆供应商，\n不是微软/谷歌。", fontsize=9.5, color=NAVY)
ax.text(7.2, 3.2, "技术留下，\n融资链条断掉。", fontsize=13, color=COPPER, fontweight="bold")
ax.text(7.2, 2.55, "铁路泡沫破了，铁轨留下来；\n郁金香破了，什么都没有。", fontsize=9.2, color=MID)
save(fig, "ab_transmission.png")

# 7. fragility score
components = ["估值\nCAPE 41x", "Capex / 收入缺口", "算力利用率", "内存周期", "信用利差 / CDS"]
scores = [80, 70, 65, 80, 75]
weights = [15, 25, 20, 15, 25]
fig, ax = plt.subplots(figsize=(10.2, 4.2))
colors = [GOLD, COPPER, TEAL, GOLD, RED]
bars = ax.barh(components, scores, color=colors, height=0.55)
for b, s, w in zip(bars, scores, weights):
    ax.text(s+1.5, b.get_y()+b.get_height()/2, f"{s}/100  ·  权重 {w}%", va="center", fontsize=8.8, color=NAVY)
ax.set_xlim(0, 100); ax.set_xlabel("脆弱性评分（0 = 无压力，100 = 危机）", fontsize=9)
ax.set_title("AI 泡沫脆弱性评分：73/100（脆弱，未破）", loc="left", fontsize=12.5, fontweight="bold", color=NAVY, pad=10)
ax.invert_yaxis(); style(ax, "x")
fig.text(0.01, -0.04, "评分是框架判断，不是概率；权重可调。估值 15%、Capex/收入缺口 25%、算力利用率 20%、内存周期 15%、信用 25%。", fontsize=7.5, color=MID)
save(fig, "ab_fragility_score.png")

print("charts done:", sorted(p.name for p in ASSETS.glob("*.png")))

# plain-language four-layer chain
fig, ax = plt.subplots(figsize=(12, 4.4))
ax.set_xlim(0, 12); ax.set_ylim(0, 4.6); ax.axis("off")
boxes = [
    (0.3, "估值层", ["贵不贵？", "PE 28x / CAPE 41x", "赔率差，时机不确定"], GOLD),
    (3.15, "需求层", ["有没有人用？", "23GW vs <2GW", "收入/算力 0.4→2.0"], TEAL),
    (6.0, "供给层", ["价格脆不脆？", "内存 3.5 次方", "1.35→1.10 = −51%"], COPPER),
    (8.85, "信用层", ["什么时候裂？", "HY OAS 344bp", "CCC 1,327bp / CDS 4.5x"], RED),
]
for x, title, lines, color in boxes:
    ax.add_patch(FancyBboxPatch((x, 1.55), 2.65, 2.3, boxstyle="round,pad=0.05,rounding_size=0.08",
                                linewidth=1.2, edgecolor=color, facecolor="white"))
    ax.text(x+0.14, 3.35, title, fontsize=12, fontweight="bold", color=color)
    for j, line in enumerate(lines):
        ax.text(x+0.14, 2.95-j*0.34, line, fontsize=9.2, color=NAVY, va="top")
for x in [2.96, 5.81, 8.66]:
    ax.annotate("", xy=(x+0.17, 2.7), xytext=(x-0.02, 2.7), arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.6))
ax.text(6, 0.85, "一条链：估值 → 需求 → 供给 → 信用", ha="center", fontsize=13, color=NAVY, fontweight="bold")
ax.text(6, 0.35, "技术是真的；融资链条是脆的。", ha="center", fontsize=10.5, color=COPPER, fontweight="bold")
save(fig, "plain_chain.png")

# 8. GPU purchase price ranges
gens = ["H100", "H200", "B200", "GB200", "GB300", "Rubin"]
low = [25, 30, 35, 35, 45, 55]
high = [40, 40, 50, 50, 60, 75]
fig, ax = plt.subplots(figsize=(10.2, 4.2))
for i, (g, l, h) in enumerate(zip(gens, low, high)):
    ax.plot([l, h], [i, i], color=COPPER, lw=7, solid_capstyle="round", alpha=0.85)
    ax.text(h+1.2, i, f"${l}k–{h}k", va="center", fontsize=9, color=NAVY, fontweight="bold")
ax.set_yticks(range(len(gens))); ax.set_yticklabels(gens, fontsize=9.5)
ax.set_xlim(0, 85); ax.set_xlabel("单卡购买价，千美元（渠道/合同价区间）", fontsize=9)
ax.set_title("GPU 购买价：新代溢价，旧代折旧", loc="left", fontsize=12.5, fontweight="bold", color=NAVY, pad=10)
ax.invert_yaxis(); style(ax, "x")
fig.text(0.01, -0.04, "价格为公开渠道/合同价区间，受采购量、保修、网络、交付时间影响；Rubin 为 2027–28 估算。不是官方报价。", fontsize=7.5, color=MID)
save(fig, "ab_gpu_purchase.png")

# 9. GPU rental price
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
            ax.annotate(f"${y:.1f}", (x, y), textcoords="offset points", xytext=(0,8), ha="center", fontsize=8, color=c)
ax.set_xticks(years); ax.set_xticklabels(["2023", "2024", "2025", "2026", "2027E", "2028E"])
ax.set_ylabel("GPU 租赁价，美元/卡/小时", fontsize=9.5)
ax.set_title("GPU 租赁价：从 2023 年的 \$9/小时，到 2028E 的 \$1–2/小时", loc="left", fontsize=12.2, fontweight="bold", color=NAVY, pad=10)
ax.legend(loc="upper right", frameon=False, fontsize=8.5)
style(ax)
fig.text(0.01, -0.04, "价格为公开云报价/渠道调研的中位区间；2026–2028 为情景预测（阴影区）。实际价格受合同期限、批量、网络、电力、利用率影响。", fontsize=7.5, color=MID)
save(fig, "ab_gpu_rental.png")

print("GPU charts done")

