"""Exp 07 — Dynamic Network Partition"""
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

BG, PANEL = '#ffffff', '#f6f8fa'
TEXT, MUTED, BORDER = '#1f2328', '#636c76', '#d0d7de'
PALETTE3 = ['#58a6ff', '#3fb950', '#d2a8ff']

RC = {
    'axes.facecolor': PANEL, 'figure.facecolor': BG,
    'axes.edgecolor': BORDER, 'grid.color': '#d8dee4',
    'text.color': TEXT, 'axes.labelcolor': MUTED,
    'xtick.color': MUTED, 'ytick.color': MUTED,
    'legend.facecolor': PANEL, 'legend.edgecolor': BORDER,
    'legend.labelcolor': TEXT, 'axes.unicode_minus': False,
    'font.family': 'monospace', 'font.size': 11,
}
sns.set_theme(style='darkgrid', rc=RC)

raw = {
    'Run 1': [245, 214, 285, 297, 289],
    'Run 2': [204, 246, 276, 500, 263],
    'Run 3': [371, 534, 222, 713, 238],
}
rows = []
for run, vals in raw.items():
    for attempt, v in enumerate(vals, 1):
        rows.append({'Run': run, 'Attempt': attempt, 'Latency (ms)': v})
df = pd.DataFrame(rows)

fig, (ax_scatter, ax_box) = plt.subplots(1, 2, figsize=(16, 9), facecolor=BG)
fig.text(0.5, 0.96, 'Exp 07  |  Dynamic Network Partition — Recovery Read Latency',
         ha='center', fontsize=19, fontweight='bold', color=TEXT)
fig.text(0.5, 0.915, 'Post-Recovery Read Latency Distribution  (5 reads x 3 runs)',
         ha='center', fontsize=13, color=MUTED)

ax_scatter.set_facecolor(PANEL)
for sp in ax_scatter.spines.values(): sp.set_edgecolor(BORDER)
sns.lineplot(data=df, x='Attempt', y='Latency (ms)', hue='Run',
             palette=PALETTE3, marker='o', markersize=10, linewidth=2, ax=ax_scatter)
for run, vals, c in zip(raw.keys(), raw.values(), PALETTE3):
    mx, mx_i = max(vals), vals.index(max(vals))
    ax_scatter.annotate(f'peak {mx}ms', xy=(mx_i + 1, mx),
                        xytext=(mx_i + 1.2, mx + 22), fontsize=8.5, color=c,
                        arrowprops=dict(arrowstyle='->', color=c, lw=1.2))
ax_scatter.axhline(300, color=MUTED, lw=1.2, ls='--', alpha=0.5)
ax_scatter.text(0.8, 318, '300ms ref', fontsize=8, color=MUTED)
ax_scatter.set_xlabel('Attempt # after Recovery', color=MUTED, fontsize=11)
ax_scatter.set_ylabel('Latency (ms)', color=MUTED, fontsize=11)
ax_scatter.set_title('Per-Attempt Read Latency Post-Recovery', color=TEXT, fontsize=12, pad=8)
ax_scatter.legend(title='Run', fontsize=10, title_fontsize=9)
ax_scatter.set_ylim(100, 850)

ax_box.set_facecolor(PANEL)
for sp in ax_box.spines.values(): sp.set_edgecolor(BORDER)
sns.boxplot(data=df, x='Run', y='Latency (ms)', palette=PALETTE3,
            ax=ax_box, width=0.45, fliersize=0, linewidth=1.5,
            medianprops=dict(color='white', lw=2.5),
            whiskerprops=dict(color=MUTED, lw=1.5),
            capprops=dict(color=MUTED, lw=1.5),
            boxprops=dict(alpha=0.3))
sns.stripplot(data=df, x='Run', y='Latency (ms)', palette=PALETTE3,
              ax=ax_box, size=9, alpha=0.9, jitter=0.08, zorder=4)
ax_box.set_xlabel('Run', color=MUTED, fontsize=11)
ax_box.set_ylabel('Latency (ms)', color=MUTED, fontsize=11)
ax_box.set_title('Distribution per Run (Box + Strip)', color=TEXT, fontsize=12, pad=8)
ax_box.set_ylim(100, 850)

fig.text(0.5, 0.03,
    'Single-region partition (RF=3 majority intact)  |  RPO=0  |  Recovery != immediate baseline (routing cache lag)',
    ha='center', fontsize=9, color=MUTED)

plt.tight_layout(rect=[0, 0.05, 1, 0.89])
plt.savefig('phase7_partition_light.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.show()
print("Saved: phase7_partition_light.png")
