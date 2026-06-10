"""Exp 11 — Scalability Test"""
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

BG, PANEL = '#ffffff', '#f6f8fa'
TEXT, MUTED, BORDER = '#1f2328', '#636c76', '#d0d7de'
BLUE, ORANGE, GREEN, RED = '#58a6ff', '#ffa657', '#3fb950', '#f78166'

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

tps_data = {1: [808.655, 775.855, 796.013],
            3: [435.436, 438.957, 482.148],
            5: [494.285, 479.521, 476.374]}
lat_data = {1: [19.786, 20.622, 20.100],
            3: [36.745, 36.450, 33.185],
            5: [32.370, 33.367, 33.587]}

rows = []
for n in [1, 3, 5]:
    for tps, lat in zip(tps_data[n], lat_data[n]):
        rows.append({'Nodes': str(n), 'TPS': tps, 'Latency (ms)': lat})
df = pd.DataFrame(rows)
df_avg = df.groupby('Nodes').agg({'TPS': 'mean', 'Latency (ms)': 'mean'}).reset_index()
avg_n1 = df_avg[df_avg['Nodes'] == '1']['TPS'].values[0]
ideal_y = [avg_n1 * n / 1 for n in [1, 3, 5]]

fig, ax1 = plt.subplots(figsize=(16, 9), facecolor=BG)
ax1.set_facecolor(PANEL)
for sp in ax1.spines.values(): sp.set_edgecolor(BORDER)

fig.text(0.5, 0.96, 'Exp 11  |  Scalability Test  (pgbench)',
         ha='center', fontsize=19, fontweight='bold', color=TEXT)
fig.text(0.5, 0.915, 'N=1 outperforms N=3/5 — Raft coordination overhead dominates on small dataset',
         ha='center', fontsize=13, color=MUTED)

sns.barplot(data=df, x='Nodes', y='TPS', ax=ax1,
            color=BLUE, errorbar='sd', alpha=0.75,
            capsize=0.12, err_kws={'linewidth': 2, 'color': 'white'},
            order=['1', '3', '5'], width=0.5)
sns.stripplot(data=df, x='Nodes', y='TPS', ax=ax1,
              color='white', size=8, alpha=0.85, jitter=0.08, zorder=5,
              order=['1', '3', '5'])
ax1.plot([0, 1, 2], ideal_y, '--', color=GREEN, lw=2.2, alpha=0.7,
         label='Ideal linear scaling', zorder=4)

ax2 = ax1.twinx()
ax2.set_facecolor('none')
for sp in ax2.spines.values(): sp.set_edgecolor(BORDER)
sns.lineplot(data=df_avg, x='Nodes', y='Latency (ms)', ax=ax2,
             color=ORANGE, marker='o', markersize=14, linewidth=2.5,
             zorder=6, label='Avg Latency')
ax2.tick_params(axis='y', colors=ORANGE)
ax2.set_ylabel('Avg Latency (ms)', color=ORANGE, fontsize=12)
ax2.set_ylim(0, 55)
for _, row in df_avg.iterrows():
    xi = ['1', '3', '5'].index(row['Nodes'])
    ax2.text(xi + 0.15, row['Latency (ms)'] - 1.5,
             f"{row['Latency (ms)']:.1f}ms", fontsize=10, color=ORANGE, fontweight='bold')

ax1.annotate('N=1: no Raft replication\n-> highest TPS', xy=(0, 793),
             xytext=(0.4, 680), fontsize=9, color=RED,
             arrowprops=dict(arrowstyle='->', color=RED, lw=1.5))
ax1.annotate('N=3/5: RF=3 quorum\ncoordination overhead', xy=(1, 453),
             xytext=(1.5, 620), fontsize=9, color=MUTED,
             arrowprops=dict(arrowstyle='->', color=MUTED, lw=1.2))

ax1.set_xlabel('Node Count', color=MUTED, fontsize=12)
ax1.set_ylabel('TPS (pgbench)', color=BLUE, fontsize=12)
ax1.tick_params(axis='y', colors=BLUE)
ax1.tick_params(axis='x', colors=MUTED, labelsize=12)
ax1.set_ylim(0, 1200)
ax1.set_xticklabels(['N=1\n(no replication)', 'N=3\n(RF=3, min)', 'N=5\n(RF=3, full)'])
ax1.set_title('TPS (+-SD, white dots = individual runs)  &  Avg Latency (orange)',
              color=TEXT, fontsize=13, pad=10)

h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, fontsize=10, framealpha=0.25,
           facecolor=PANEL, edgecolor=BORDER, loc='upper right')

fig.text(0.5, 0.03,
    'N=1: no Raft overhead -> highest TPS  |  N=3/5: RF=3 quorum cost  |  scale=1 dataset too small for parallel benefit',
    ha='center', fontsize=9, color=MUTED)

plt.tight_layout(rect=[0, 0.05, 1, 0.89])
plt.savefig('phase11_scalability_light.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.show()
print("Saved: phase11_scalability_light.png")
