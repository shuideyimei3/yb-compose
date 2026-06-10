"""Exp 08 — Clock Skew & Hybrid Logical Clock (HLC)"""
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

BG, PANEL = '#ffffff', '#f6f8fa'
TEXT, MUTED, BORDER = '#1f2328', '#636c76', '#d0d7de'
GREEN, RED, BLUE, PURPLE = '#3fb950', '#f78166', '#58a6ff', '#d2a8ff'

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

t = np.linspace(0, 10, 300)
physical = np.where(t < 5, t, np.where(t < 6, t - (t - 5) * 0.85, t - 0.85 + (t - 6) * 1.0))
hlc = np.maximum.accumulate(physical + 0.01)
clock_df = pd.DataFrame({
    'Time': np.concatenate([t, t]),
    'Timestamp': np.concatenate([physical, hlc]),
    'Clock': ['Physical Clock'] * 300 + ['HLC (monotone)'] * 300,
})

steps  = ['Step1\nBaseline', 'Step2\n+2s fwd', 'Step3\n-4s back', 'Step4\nPartition\n+skew']
metrics = ['Cluster\nhealthy', 'SQL conn\naccept', 'HLC stays\nmonotone', 'Write\nsucceeds']
status = np.array([[1,1,1,1],[1,1,1,0],[1,1,1,1],[1,1,1,0]], dtype=float)
status_df = pd.DataFrame(status, index=metrics, columns=steps)

fig = plt.figure(figsize=(16, 9), facecolor=BG)
fig.text(0.5, 0.96, 'Exp 08  |  Clock Skew & Hybrid Logical Clock (HLC)',
         ha='center', fontsize=19, fontweight='bold', color=TEXT)
fig.text(0.5, 0.915, 'Monotonicity Guarantee Under Clock Anomalies  |  HLC vs Spanner TrueTime',
         ha='center', fontsize=13, color=MUTED)

ax1 = fig.add_axes([0.05, 0.50, 0.42, 0.36])
ax1.set_facecolor(PANEL)
for sp in ax1.spines.values(): sp.set_edgecolor(BORDER)
sns.lineplot(data=clock_df, x='Time', y='Timestamp', hue='Clock',
             palette=[RED, GREEN], linewidth=2.2, ax=ax1)
ax1.axvspan(4.8, 6.2, color=RED, alpha=0.08)
ax1.text(5.5, 8.6, 'Clock rollback\n-4s', ha='center', fontsize=9, color=RED, style='italic')
ax1.set_title('HLC Monotonicity vs Physical Clock Rollback', color=TEXT, fontsize=11, pad=6)
ax1.set_xlabel('Time', color=MUTED, fontsize=10)
ax1.set_ylabel('Timestamp', color=MUTED, fontsize=10)
ax1.legend(title='Clock Type', fontsize=8.5, title_fontsize=8.5)

ax2 = fig.add_axes([0.05, 0.09, 0.42, 0.32])
sns.heatmap(status_df, ax=ax2, annot=True, fmt='.0f', linewidths=2, linecolor=BG,
            cmap=[RED, GREEN], vmin=0, vmax=1, cbar=False,
            annot_kws={'size': 18, 'weight': 'bold', 'color': 'white'})
ax2.set_title('Behavior Matrix  (1=OK, 0=Fail)', color=TEXT, fontsize=11, pad=6)
ax2.tick_params(colors=MUTED, labelsize=9, rotation=0)

compare = pd.DataFrame({
    'HLC (YugabyteDB)': [1, 0, 1, 0.5, 1, 1],
    'TrueTime (Spanner)': [0, 1, 0, 1, 1, 0.5],
}, index=['Hardware req.', 'Precision guar.', 'SW-layer impl.',
          'Wait interval', 'Rollback handle', 'Partition safe'])

ax3 = fig.add_axes([0.54, 0.09, 0.43, 0.76])
sns.heatmap(compare, ax=ax3, annot=True, fmt='.1f', linewidths=2, linecolor=BG,
            cmap=sns.diverging_palette(10, 130, s=80, l=40, as_cmap=True),
            vmin=0, vmax=1, cbar=True,
            annot_kws={'size': 14, 'weight': 'bold', 'color': 'white'},
            cbar_kws={'label': 'Capability Score', 'shrink': 0.7})
ax3.set_title('HLC vs Spanner TrueTime', color=TEXT, fontsize=12, pad=8)
ax3.tick_params(colors=MUTED, labelsize=9.5, rotation=0)
ax3.set_xticklabels(ax3.get_xticklabels(), rotation=15, ha='right')

fig.text(0.5, 0.03,
    'HLC = physical time + logical counter  |  No GPS/atomic clock  |  Partition+skew: write rejected (no quorum)',
    ha='center', fontsize=9, color=MUTED)

plt.savefig('phase8_clock_skew_light.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.show()
print("Saved: phase8_clock_skew_light.png")
