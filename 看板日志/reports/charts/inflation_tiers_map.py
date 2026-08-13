import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

fig, ax = plt.subplots(figsize=(18, 10), dpi=150, facecolor='#f0f2f5')
ax.set_facecolor('#f0f2f5')
ax.set_xlim(0, 18); ax.set_ylim(0, 10)
ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values(): s.set_visible(False)

# ─── Concentric rings ───
cx, cy = 9, 5
for r, color, lw, ls, alpha in [(1.6,'#ccd0d5',1.5,'-',1),(2.8,'#ccd0d5',1.5,'-',1),(4.2,'#ccd0d5',1,'--',0.7),(5.5,'#dde0e5',0.8,'-.',0.5)]:
    ax.add_patch(plt.Circle((cx,cy), r, fill=False, edgecolor=color, linewidth=lw, linestyle=ls, alpha=alpha))

# ─── TIER 3: Center (Green) ───
t3 = [
    ('US', 0.40, '#22c55e'), ('China', 0.45, '#22c55e'), ('Russia', 0.18, '#22c55e'),
    ('Canada', 0.14, '#22c55e'), ('Saudi', 0.12, '#22c55e'), ('UAE', 0.07, '#22c55e'),
    ('Qatar', 0.05, '#22c55e'), ('Kuwait', 0.04, '#22c55e'),
]
for i, (name, size, color) in enumerate(t3):
    a = (i/len(t3))*np.pi*2 - np.pi/2
    r = 0.6 + size*2.5
    x, y = cx+np.cos(a)*r, cy+np.sin(a)*r
    ax.scatter(x, y, s=size*1500, color=color, alpha=0.85, edgecolors='#fff', linewidth=1.5, zorder=3)
    ax.text(x, y, name, fontsize=8, color='#222' if size>0.1 else '#fff', ha='center', va='center', fontweight='bold')

# Tier 3 zone label
ax.add_patch(mpatches.FancyBboxPatch((cx-2.2,cy-1.8),4.4,3.6,boxstyle='round,pad=8',facecolor='#22c55e08',edgecolor='#22c55e33',lw=1.5))
ax.text(cx, cy+1.5, 'TIER 3', fontsize=13, color='#22c55e', ha='center', fontweight='bold')
ax.text(cx, cy+1.05, 'INFLATION SAFE ZONE', fontsize=10, color='#22c55e', ha='center', fontweight='bold')
ax.text(cx, cy+0.65, 'Energy self-sufficient  ·  CPI ~2%', fontsize=8, color='#447744', ha='center')
ax.text(cx, cy+0.3, 'Capital INFLOW destination', fontsize=8, color='#446644', ha='center')

# ─── TIER 1: Middle ring (Orange) ───
t1 = [
    ('Eurozone',0.32,'#f59e0b'),('Japan',0.28,'#f59e0b'),('Korea',0.18,'#f59e0b'),
    ('UK',0.14,'#f59e0b'),('Australia',0.10,'#f59e0b'),('Taiwan',0.07,'#f59e0b'),
    ('Singapore',0.05,'#f59e0b'),
]
for i,(name,size,color) in enumerate(t1):
    a = (i/len(t1))*np.pi*2 + 0.4
    r = 2.4 + size*2
    x,y = cx+np.cos(a)*r, cy+np.sin(a)*r
    ax.scatter(x,y,s=size*1000,color=color,alpha=0.75,edgecolors='#fff',lw=1,zorder=3)
    ax.text(x,y,name,fontsize=8,color='#0a0e1a' if size>0.1 else '#fff',ha='center',va='center',fontweight='bold')

# Tier 1 ring
ax.add_patch(plt.Circle((cx,cy),2.6,fill=False,edgecolor='#f59e0b55',lw=1.5,ls='--'))
# Tier 1 label box
ax.text(cx+3.0, cy+2.0, 'TIER 1', fontsize=12, color='#f59e0b', ha='center', fontweight='bold')
ax.text(cx+3.0, cy+1.65, 'STAGFLATION TRAP', fontsize=9, color='#f59e0b', ha='center', fontweight='bold')
ax.text(cx+3.0, cy+1.3, 'CPI 12-18%', fontsize=8, color='#666', ha='center')
ax.text(cx+3.0, cy+1.0, 'Capital OUTFLOW → USD', fontsize=7.5, color='#555', ha='center')

# ─── TIER 2: Outer ring (Red) ───
t2 = [
    ('Turkey',0.14,'#ef4444'),('Argentina',0.12,'#ef4444'),('Egypt',0.10,'#ef4444'),
    ('Pakistan',0.10,'#ef4444'),('Nigeria',0.08,'#ef4444'),('Vietnam',0.06,'#ef4444'),
    ('Sri Lanka',0.05,'#ef4444'),('Bangladesh',0.05,'#ef4444'),('Lebanon',0.03,'#ef4444'),
]
for i,(name,size,color) in enumerate(t2):
    a = (i/len(t2))*np.pi*2 + 1.2
    r = 4.2 + size*3
    x,y = cx+np.cos(a)*r, cy+np.sin(a)*r
    ax.scatter(x,y,s=size*600,color=color,alpha=0.6,edgecolors='#fff',lw=0.5,zorder=3)
    ax.text(x,y,name,fontsize=7,color='#ddd' if size>0.06 else '#999',ha='center',va='center')

# Tier 2 ring
ax.add_patch(plt.Circle((cx,cy),4.5,fill=False,edgecolor='#ef444444',lw=1,ls='--'))
ax.text(cx+5.2, cy+0.5, 'TIER 2', fontsize=12, color='#ef4444', ha='center', fontweight='bold')
ax.text(cx+5.2, cy+0.15, 'CURRENCY COLLAPSE', fontsize=9, color='#ef4444', ha='center', fontweight='bold')
ax.text(cx+5.2, cy-0.2, 'CPI >50%', fontsize=8, color='#666', ha='center')
ax.text(cx+5.2, cy-0.5, 'FX + Bonds + Stocks', fontsize=7.5, color='#663333', ha='center')
ax.text(cx+5.2, cy-0.75, 'triple kill', fontsize=7.5, color='#663333', ha='center')

# ─── Capital flow arrows (Tier 1 → Center) ───
for name in ['Eurozone','Japan','Korea','UK']:
    for lst, r0 in [(t1, 2.6)]:
        for cn, size, _ in lst:
            if cn == name:
                idx = [c[0] for c in lst].index(name)
                a = (idx/len(lst))*np.pi*2 + 0.4
                sx = cx+np.cos(a)*(r0+size*1.5)
                sy = cy+np.sin(a)*(r0+size*1.5)
                ex = cx+np.cos(a)*1.0
                ey = cy+np.sin(a)*1.0
                ax.annotate('',xy=(ex,ey),xytext=(sx,sy),arrowprops=dict(arrowstyle='->',color='#f59e0b33',lw=1.2))
                break

# ─── Title ───
fig.text(0.5, 0.97, 'GLOBAL INFLATION APARTHEID', fontsize=22, color='#1a1a2e', fontweight='bold', ha='center')
fig.text(0.5, 0.94, 'One Oil Shock   ·   Three Completely Different Worlds   ·   H2 2026', fontsize=11, color='#666', ha='center')

# ─── Bottom legend ───
ly = 0.035
items = [
    (0.18, '#22c55e', 'Tier 3: Safe (~2% CPI) — Capital INFLOW destination'),
    (0.48, '#f59e0b', 'Tier 1: Stagflation (12-18%) — Capital OUTFLOW, blood banks'),
    (0.78, '#ef4444', 'Tier 2: Collapse (>50%) — Triple kill, distressed prey'),
]
for lx, color, label in items:
    fig.text(lx, ly, '●', fontsize=14, color=color, ha='center')
    fig.text(lx+0.02, ly, label, fontsize=8.5, color='#555', va='center')

fig.text(0.5, 0.008, 'Deep-Risk-OPP  ·  Research Framework  ·  Not Investment Advice', fontsize=7.5, color='#aaa', ha='center')

out = r'c:\Users\Admin\Documents\陈嘉-资料备份\08.投资决策框架\看板日志\reports\charts\inflation_tiers_map.png'
fig.savefig(out, dpi=150, facecolor='#0a0e1a', bbox_inches='tight', pad_inches=0.3)
print('SAVED')

