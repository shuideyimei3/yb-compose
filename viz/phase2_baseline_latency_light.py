"""Exp 02 — Baseline Latency"""
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

BG, PANEL = '#ffffff', '#f6f8fa'
TEXT, MUTED, BORDER = '#1f2328', '#636c76', '#d0d7de'
BLUE, ORANGE = '#58a6ff', '#ffa657'

RC = {
    'axes.facecolor': PANEL, 'figure.facecolor': BG,
    'axes.edgecolor': BORDER, 'grid.color': '#d8dee4',
    'text.color': TEXT, 'axes.labelcolor': MUTED,
    'xtick.color': MUTED, 'ytick.color': MUTED,
    'legend.facecolor': PANEL, 'legend.edgecolor': BORDER,
    'legend.labelcolor': TEXT, 'axes.unicode_minus': False,
    'font.family': 'monospace', 'font.size': 11,
}
sns.set_theme(style='darkgrid', palette=[BLUE, ORANGE], rc=RC)

nodes  = ['yb-1 region1', 'yb-2 region2', 'yb-3 region3', 'yb-4 region4', 'yb-5 region5']
reads  = [89.77, 90.75, 90.61, 88.44, 89.19]
writes = [89.76, 91.27, 89.06, 88.64, 90.30]

rows = []
for node, r, w in zip(nodes, reads, writes):
    rows.append({'Node': node, 'Latency (ms)': r, 'Type': 'Read avg'})
    rows.append({'Node': node, 'Latency (ms)': w, 'Type': 'Write avg'})
df = pd.DataFrame(rows)

fig, ax = plt.subplots(figsize=(16, 9), facecolor=BG)
ax.set_facecolor(PANEL)
for sp in ax.spines.values(): sp.set_edgecolor(BORDER)

sns.barplot(data=df, y='Node', x='Latency (ms)', hue='Type',
            palette=[BLUE, ORANGE], orient='h', ax=ax,
            errorbar=None, width=0.65, alpha=0.88)

for i, p in enumerate(ax.patches):
    v = p.get_width()
    if v > 1:
        ax.text(v + 0.15, p.get_y() + p.get_height() / 2,
                f'{v:.2f}', va='center', fontsize=9.5,
                color=BLUE if i < len(nodes) else ORANGE)

avg_r, avg_w = np.mean(reads), np.mean(writes)
ax.axvline(avg_r, color=BLUE,   lw=1.8, ls='--', alpha=0.7, zorder=5)
ax.axvline(avg_w, color=ORANGE, lw=1.8, ls='--', alpha=0.7, zorder=5)
ax.text(avg_r + 0.05, 4.62, f'Read avg\n{avg_r:.2f} ms', color=BLUE,   fontsize=8.5, va='top')
ax.text(avg_w - 1.95, 4.62, f'Write avg\n{avg_w:.2f} ms', color=ORANGE, fontsize=8.5, va='top')

ax.set_xlim(83, 96)
ax.set_xlabel('Latency (ms)', color=MUTED, fontsize=12)
ax.set_ylabel('Node', color=MUTED, fontsize=12)
ax.legend(title='Operation', fontsize=11, title_fontsize=10, loc='lower right')

fig.text(0.5, 0.96, 'Exp 02  |  Baseline Latency  (No Added Delay)',
         ha='center', fontsize=19, fontweight='bold', color=TEXT)
fig.text(0.5, 0.915, '5-Node RF=3  |  3-Run Average  |  Simple read/write transactions',
         ha='center', fontsize=13, color=MUTED)
fig.text(0.5, 0.03,
    'Node-to-node variance < 3ms  |  Read ~= Write  |  Baseline ~90ms',
    ha='center', fontsize=9, color=MUTED)

plt.tight_layout(rect=[0, 0.05, 1, 0.89])
plt.savefig('phase2_baseline_latency_light.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.show()
print("Saved: phase2_baseline_latency_light.png")
