"""Exp 01 — Cluster Architecture & Health Dashboard"""
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

BG, PANEL = '#0d1117', '#161b22'
TEXT, MUTED, BORDER = '#e6edf3', '#8b949e', '#30363d'
BLUE, GREEN, PURPLE, ORANGE, RED = '#58a6ff', '#3fb950', '#d2a8ff', '#ffa657', '#f78166'
PALETTE = [BLUE, GREEN, PURPLE, ORANGE, RED]

RC = {
    'axes.facecolor': PANEL, 'figure.facecolor': BG,
    'axes.edgecolor': BORDER, 'grid.color': '#21262d',
    'text.color': TEXT, 'axes.labelcolor': MUTED,
    'xtick.color': MUTED, 'ytick.color': MUTED,
    'legend.facecolor': PANEL, 'legend.edgecolor': BORDER,
    'legend.labelcolor': TEXT, 'axes.unicode_minus': False,
    'font.family': 'monospace', 'font.size': 11,
}
sns.set_theme(style='darkgrid', palette=PALETTE, rc=RC)

avail_df = pd.DataFrame(
    np.ones((5, 3), dtype=int),
    index=['yb-1  region1', 'yb-2  region2', 'yb-3  region3',
           'yb-4  region4', 'yb-5  region5'],
    columns=['Run 1\n082336Z', 'Run 2\n085229Z', 'Run 3\n093857Z'],
)
config_df = pd.DataFrame({
    'Metric': ['Nodes', 'Masters', 'TServers', 'Regions'],
    'Count': [5, 3, 5, 5],
})
hlc_df = pd.DataFrame({'Run': ['Run 1', 'Run 2', 'Run 3'], 'Drift (ms)': [0.0, 0.0, 0.0]})

fig = plt.figure(figsize=(16, 9), facecolor=BG)
fig.text(0.5, 0.96, 'Exp 01  |  Cluster Architecture & Health Dashboard',
         ha='center', fontsize=19, fontweight='bold', color=TEXT)
fig.text(0.5, 0.915, 'YugabyteDB  5-Node RF=3  3 Reproducible Runs',
         ha='center', fontsize=13, color=MUTED)

ax1 = fig.add_axes([0.04, 0.08, 0.44, 0.74])
cmap = sns.light_palette(GREEN, as_cmap=True, n_colors=12)
sns.heatmap(avail_df, ax=ax1, annot=True, fmt='d', cmap=cmap,
            linewidths=3, linecolor=BG, cbar=False,
            annot_kws={'size': 28, 'weight': 'bold', 'color': '#093d1a'})
ax1.set_title('Node Availability  (1 = PASS)', color=TEXT, fontsize=13, pad=10)
ax1.tick_params(colors=MUTED, labelsize=10, rotation=0)

ax2 = fig.add_axes([0.55, 0.52, 0.41, 0.30])
sns.barplot(data=config_df, x='Metric', y='Count', hue='Metric',
            palette=[BLUE, PURPLE, ORANGE, GREEN], ax=ax2,
            dodge=False, legend=False, width=0.55)
for p in ax2.patches:
    ax2.text(p.get_x() + p.get_width() / 2, p.get_height() + 0.1,
             f'{int(p.get_height())}', ha='center', fontsize=15,
             fontweight='bold', color=TEXT)
ax2.set_ylim(0, 7.5)
ax2.set_xlabel('')
ax2.set_ylabel('Count', color=MUTED, fontsize=10)
ax2.set_title('Cluster Config (Stable Across 3 Runs)', color=TEXT, fontsize=11, pad=6)

ax3 = fig.add_axes([0.55, 0.10, 0.41, 0.30])
sns.lineplot(data=hlc_df, x='Run', y='Drift (ms)', ax=ax3,
             color=GREEN, marker='o', markersize=12, linewidth=2.5)
ax3.fill_between(hlc_df['Run'], hlc_df['Drift (ms)'], color=GREEN, alpha=0.12)
ax3.set_ylim(-0.5, 1.0)
ax3.set_xlabel('')
ax3.set_ylabel('Drift (ms)', color=MUTED, fontsize=10)
ax3.set_title('HLC Clock Drift  now() Across Nodes', color=TEXT, fontsize=11, pad=6)
ax3.text(1, 0.42, '0.000 ms  shared host clock (expected)',
         ha='center', fontsize=9, color=GREEN, style='italic')

fig.text(0.5, 0.03,
    'RF=3: 3-Master Raft quorum  |  5 TServers simulate 5 regions  |  Single-host Docker: zero HLC drift',
    ha='center', fontsize=9, color=MUTED)

plt.savefig('phase1_architecture.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.show()
print("Saved: phase1_architecture.png")
