"""Exp 05 — WAN Quality: Jitter / Loss / Bandwidth"""
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

BG, PANEL = '#0d1117', '#161b22'
TEXT, MUTED, BORDER = '#e6edf3', '#8b949e', '#30363d'
BLUE, ORANGE, RED = '#58a6ff', '#ffa657', '#f78166'

RC = {
    'axes.facecolor': PANEL, 'figure.facecolor': BG,
    'axes.edgecolor': BORDER, 'grid.color': '#21262d',
    'text.color': TEXT, 'axes.labelcolor': MUTED,
    'xtick.color': MUTED, 'ytick.color': MUTED,
    'legend.facecolor': PANEL, 'legend.edgecolor': BORDER,
    'legend.labelcolor': TEXT, 'axes.unicode_minus': False,
    'font.family': 'monospace', 'font.size': 11,
}
sns.set_theme(style='darkgrid', rc=RC)

scenarios = ['r1 30ms\nbaseline', 'r3 90ms\nbaseline', 'r2 jitter\n+loss', 'r3 jitter\n+loss', 'r4 10mbit\nbw limit']
r_avg = [129, 192, 159, 217, 229]
r_p99 = [161, 280, 202, 612, 334]
w_avg = [125, 183, 193, 252, 218]
w_p99 = [151, 199, 527, 566, 232]

rows = []
for s, ra, rp, wa, wp in zip(scenarios, r_avg, r_p99, w_avg, w_p99):
    rows += [
        {'Scenario': s, 'Latency (ms)': ra, 'Metric': 'Read avg'},
        {'Scenario': s, 'Latency (ms)': rp, 'Metric': 'Read P99'},
        {'Scenario': s, 'Latency (ms)': wa, 'Metric': 'Write avg'},
        {'Scenario': s, 'Latency (ms)': wp, 'Metric': 'Write P99'},
    ]
df = pd.DataFrame(rows)

fig, (ax_r, ax_w) = plt.subplots(2, 1, figsize=(16, 9), facecolor=BG, sharex=True)
fig.text(0.5, 0.96, 'Exp 05  |  WAN Quality: Jitter / Loss / Bandwidth Limit',
         ha='center', fontsize=19, fontweight='bold', color=TEXT)
fig.text(0.5, 0.915, 'Avg vs P99 Latency — WAN Impairment Impact',
         ha='center', fontsize=13, color=MUTED)

for ax, ops, pal, title, avgs, p99s in [
    (ax_r, ['Read avg', 'Read P99'],  [BLUE, '#c0d8ff'],   'Read',  r_avg, r_p99),
    (ax_w, ['Write avg', 'Write P99'], [ORANGE, '#ffd8a0'], 'Write', w_avg, w_p99),
]:
    ax.set_facecolor(PANEL)
    for sp in ax.spines.values(): sp.set_edgecolor(BORDER)
    sub = df[df['Metric'].isin(ops)].copy()
    sns.barplot(data=sub, x='Scenario', y='Latency (ms)', hue='Metric',
                palette=pal, ax=ax, errorbar=None, width=0.65, alpha=0.88)
    for xi in [2, 3]:
        gap = p99s[xi] - avgs[xi]
        ax.annotate('', xy=(xi + 0.18, p99s[xi] + 8), xytext=(xi + 0.18, avgs[xi] + 8),
                    arrowprops=dict(arrowstyle='<->', color=RED, lw=1.6))
        ax.text(xi + 0.30, (p99s[xi] + avgs[xi]) / 2,
                f'+{gap}ms', color=RED, fontsize=8.5, va='center', fontweight='bold')
    ax.set_ylabel('Latency (ms)', color=MUTED, fontsize=11)
    ax.set_xlabel('')
    ax.set_title(title, color=TEXT, fontsize=13, pad=6)
    ax.legend(title='Metric', fontsize=9, title_fontsize=9)
    ax.axvline(1.5, color=BORDER, lw=1.5, ls='--', alpha=0.7)

ax_r.text(0.5, ax_r.get_ylim()[1] * 0.88, 'Baseline', ha='center', fontsize=9, color=MUTED)
ax_r.text(3,   ax_r.get_ylim()[1] * 0.88, 'Impairment', ha='center', fontsize=9, color=RED)
ax_w.set_xlabel('Scenario', color=MUTED, fontsize=11)

fig.text(0.5, 0.03,
    'Avg driven by RTT  |  P99 sensitive to loss+jitter (TCP retransmit x Raft retry)  |  BW limit: minor on small payloads',
    ha='center', fontsize=9, color=MUTED)

plt.tight_layout(rect=[0, 0.05, 1, 0.89])
plt.savefig('phase5_wan_quality.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.show()
print("Saved: phase5_wan_quality.png")
