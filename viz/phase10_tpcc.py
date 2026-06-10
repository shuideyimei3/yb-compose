"""Exp 10 — TPC-C Benchmark Throughput"""
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

BG, PANEL = '#0d1117', '#161b22'
TEXT, MUTED, BORDER = '#e6edf3', '#8b949e', '#30363d'
BLUE, GREEN, ORANGE, PURPLE = '#58a6ff', '#3fb950', '#ffa657', '#d2a8ff'

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

runs      = ['Run 1', 'Run 2', 'Run 3']
tpmc      = [14784.6, 15196.0, 14864.4]
tpm_total = [32706.6, 33774.6, 32963.8]
avg_tpmc  = np.mean(tpmc)
avg_total = np.mean(tpm_total)

rows = []
for run, tc, tt in zip(runs, tpmc, tpm_total):
    rows += [
        {'Run': run, 'Value': tc, 'Metric': 'tpmC'},
        {'Run': run, 'Value': tt, 'Metric': 'tpmTotal'},
    ]
df = pd.DataFrame(rows)

fig, (ax_main, ax_info) = plt.subplots(1, 2, figsize=(16, 9), facecolor=BG,
                                        gridspec_kw={'width_ratios': [3, 1.4]})
fig.text(0.5, 0.96, 'Exp 10  |  TPC-C Benchmark Throughput',
         ha='center', fontsize=19, fontweight='bold', color=TEXT)
fig.text(0.5, 0.915, '5-Node RF=3  |  10 Warehouses  |  8 Threads  |  5 min',
         ha='center', fontsize=13, color=MUTED)

ax_main.set_facecolor(PANEL)
for sp in ax_main.spines.values(): sp.set_edgecolor(BORDER)
sns.barplot(data=df, x='Run', y='Value', hue='Metric',
            palette=[BLUE, GREEN], ax=ax_main,
            errorbar=None, width=0.6, alpha=0.82)
sns.stripplot(data=df[df['Metric'] == 'tpmC'], x='Run', y='Value',
              ax=ax_main, color='white', size=7, alpha=0.9, zorder=5,
              jitter=False, dodge=True)
ax_main.axhline(avg_tpmc,  color=BLUE,  lw=2,   ls='--', alpha=0.8, zorder=4)
ax_main.axhline(avg_total, color=GREEN, lw=1.5, ls='--', alpha=0.6, zorder=4)
ax_main.text(2.45, avg_tpmc  + 300, f'tpmC avg {avg_tpmc:,.0f}',
             ha='right', fontsize=9.5, color=BLUE, fontweight='bold')
ax_main.text(2.45, avg_total + 300, f'tpmTotal avg {avg_total:,.0f}',
             ha='right', fontsize=9.5, color=GREEN)
for p in ax_main.patches:
    h = p.get_height()
    if h > 1000:
        ax_main.text(p.get_x() + p.get_width() / 2, h + 400,
                     f'{h:,.0f}', ha='center', fontsize=9.5,
                     color=BLUE if h < 25000 else GREEN)
ax_main.set_ylim(0, 42000)
ax_main.set_xlabel('Run', color=MUTED, fontsize=11)
ax_main.set_ylabel('Transactions per Minute', color=MUTED, fontsize=11)
ax_main.set_title('tpmC vs tpmTotal Across 3 Runs', color=TEXT, fontsize=13, pad=8)
ax_main.legend(title='Metric', fontsize=10, title_fontsize=9)

ax_info.set_facecolor(PANEL)
for sp in ax_info.spines.values(): sp.set_edgecolor(BORDER)
ax_info.axis('off')
ax_info.set_title('Benchmark Config', color=TEXT, fontsize=12, pad=8)
config = [
    ('Tool', 'go-tpc', BLUE),
    ('Warehouses', '10', ORANGE),
    ('Threads', '8', ORANGE),
    ('Duration', '5 min', ORANGE),
    ('Nodes', '5 (RF=3)', PURPLE),
    ('WAN delay', 'None', GREEN),
    ('tpmC avg', f'{avg_tpmc:,.0f}', BLUE),
    ('tpmTotal avg', f'{avg_total:,.0f}', GREEN),
    ('Variance', '+-2.8%', ORANGE),
]
for i, (k, v, c) in enumerate(config):
    y = 0.93 - i * 0.1
    ax_info.add_patch(plt.Rectangle((0.03, y - 0.055), 0.94, 0.09,
        facecolor=c, alpha=0.07, edgecolor=c, lw=0.8, transform=ax_info.transAxes))
    ax_info.text(0.07, y, k, fontsize=9, color=MUTED, transform=ax_info.transAxes)
    ax_info.text(0.95, y, v, fontsize=10, color=c, fontweight='bold',
                 ha='right', transform=ax_info.transAxes)

fig.text(0.5, 0.03,
    'Efficiency >100% = go-tpc relative metric (not TPC-C audit)  |  No WAN delay; see Exp 03 for cross-region impact',
    ha='center', fontsize=9, color=MUTED)

plt.tight_layout(rect=[0, 0.05, 1, 0.89])
plt.savefig('phase10_tpcc.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.show()
print("Saved: phase10_tpcc.png")
