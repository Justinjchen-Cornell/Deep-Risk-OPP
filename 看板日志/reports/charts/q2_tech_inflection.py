import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig = plt.figure(figsize=(14, 7), dpi=150, facecolor='#fff')
gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.25, left=0.05, right=0.97, top=0.88, bottom=0.08)

signals = [
    ('AAPL', 'Upstream Squeeze', 'Storage makers at 60%+ margins\nsqueeze Apple. Tipping point\nreached. Supply chain conflict\nsignals cycle maturity.', '#c0392b'),
    ('GOOGL', 'Free Cash Flow -> 0', 'Q2: FCF evaporated. 2024:\n"spending = visionary." 2026:\n"where is the ROI?" Same\nnumbers. Opposite reaction.', '#e67e22'),
    ('NVDA', 'CDS Spike', 'Credit default swaps surging\nsince late June. Market now\nprices circular financing as\ncredit risk, not innovation.', '#c0392b'),
]

for idx, (ticker, title, body, color) in enumerate(signals):
    ax = fig.add_subplot(gs[0, idx])
    ax.set_xlim(0,10); ax.set_ylim(0,10)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)
    ax.add_patch(mpatches.FancyBboxPatch((0.3,0.3),9.4,9.4,boxstyle='round,pad=10',facecolor='#fafafa',edgecolor=color,lw=2.5))
    ax.add_patch(mpatches.FancyBboxPatch((3.0,8.5),4.0,1.0,boxstyle='round,pad=5',facecolor=color,edgecolor='none',alpha=0.9))
    ax.text(5,9.0,ticker,fontsize=16,color='#fff',fontfamily='monospace',fontweight='bold',ha='center',va='center')
    ax.text(5,7.3,title,fontsize=13,color='#000',fontfamily='monospace',fontweight='bold',ha='center')
    ax.plot([2,8],[6.5,6.5],color=color,lw=1,alpha=0.3)
    ax.text(5,4.2,body,fontsize=8,color='#444',fontfamily='monospace',ha='center',va='center',linespacing=1.5)
    ax.annotate('',xy=(9,1.2),xytext=(1,1.2),arrowprops=dict(arrowstyle='->',color=color,lw=3))
    ax.text(5,0.5,'Q2 INFLECTION',fontsize=8,color=color,fontfamily='monospace',fontweight='bold',ha='center')

insights = [
    ('SAME DATA,\nOPPOSITE STORY','Google spending billions on AI.\n2024: bullish. 2026: bearish.\nNumbers unchanged. Narrative flipped.\nWhen interpretation changes before\ndata does — inflection point.'),
    ('CIRCULAR\nFINANCING','NVIDIA invests in AI startups.\nStartups buy NVIDIA GPUs.\nNVIDIA guarantees the loans.\nConfidence high = ecosystem.\nConfidence low = credit risk.\nThe CDS market has spoken.'),
    ('WINDOW IS\nCLOSING','Two years of massive AI capex.\nStill no killer consumer app.\nROI question gets louder.\nNot "AI is over."\n"It is time to show the money."\nGrace period for no-return\nspending is ending.'),
]

for idx, (title, body) in enumerate(insights):
    ax = fig.add_subplot(gs[1, idx])
    ax.set_xlim(0,10); ax.set_ylim(0,10)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_facecolor('#fafafa')
    ax.text(5,9.2,f'0{idx+1}',fontsize=28,color='#e0e0e0',fontfamily='monospace',fontweight='bold',ha='center')
    ax.text(5,7.6,title,fontsize=14,color='#000',fontfamily='monospace',fontweight='bold',ha='center',linespacing=1.2)
    ax.text(1,4.5,body,fontsize=8,color='#555',fontfamily='monospace',va='center',linespacing=1.6)

fig.text(0.5,0.95,'Q2 2026: THE GREAT TECH INFLECTION',fontsize=16,color='#000',fontfamily='monospace',fontweight='bold',ha='center')
fig.text(0.5,0.925,'Apple  .  Google  .  NVIDIA — Three Signals, One Story',fontsize=10,color='#888',fontfamily='monospace',ha='center')
fig.text(0.5,0.02,'Deep-Risk-OPP  |  Research Framework  |  Not Investment Advice',fontsize=7,color='#bbb',fontfamily='monospace',ha='center')

out = r'c:\Users\Admin\Documents\陈嘉-资料备份\08.投资决策框架\看板日志\reports\charts\q2_tech_inflection.png'
fig.savefig(out, dpi=150, facecolor='#fff', bbox_inches='tight', pad_inches=0.3)
print('SAVED')