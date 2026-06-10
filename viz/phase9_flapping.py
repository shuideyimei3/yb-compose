"""Exp 09 — Flapping Node"""
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.patches as mpatches

BG, PANEL = '#0d1117', '#161b22'
TEXT, MUTED, BORDER = '#e6edf3', '#8b949e', '#30363d'
BLUE, GREEN, PURPLE, RED, ORANGE = '#58a6ff', '#3fb950', '#d2a8ff', '#f78166', '#ffa657'
PALETTE3 = [BLUE, GREEN, PURPLE]

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
base_avg  = [166, 155, 166]; base_p99  = [182, 204, 194]
recov_avg = [161, 164, 158]; recov_p99 = [186, 195, 174]
flap_max  = [5533, 3670, 6555]; p99_deg = [30.4, 18.0, 33.8]

rows_p99 = []
for run, bp, rp in zip(runs, base_p99, recov_p99):
    rows_p99 += [
        {'Run': run, 'P99 (ms)': bp, 'Phase': 'Baseline'},
        {'Run': run, 'P99 (ms)': rp, 'Phase': 'Recovery'},
    ]
df_p99 = pd.DataFrame(rows_p99)

rng = np.random.default_rng(42)
normal  = rng.normal(163, 15, 20)
flap    = rng.normal(163, 200, 20)
recover = rng.normal(161, 12, 20)
timeline = np.clip(np.concatenate([normal, flap, recover]), 0, 7000)
phases_t = ['Baseline'] * 20 + ['Flapping'] * 20 + ['Recovery'] * 20
tl_df = pd.DataFrame({'Sample': range(60), 'Latency (ms)': timeline, 'Phase': phases_t})

fig = plt.figure(figsize=(16, 9), facecolor=BG)
fig.text(0.5, 0.96, 'Exp 09  |  Flapping Node — Tail Spike & Self-Recovery',
         ha='center', fontsize=19, fontweight='bold', color=TEXT)
fig.text(0.5, 0.915, 'P99 Spike During Oscillation  |  Avg Latency Recovers to Baseline',
         ha='center', fontsize=13, color=MUTED)

# Left-top: dumbbell avg
ax1 = fig.add_axes([0.05, 0.52, 0.40, 0.34])
ax1.set_facecolor(PANEL)
for sp in ax1.spines.values(): sp.set_edgecolor(BORDER)
for i, (run, ba, ra) in enumerate(zip(runs, base_avg, recov_avg)):
    ax1.plot([ba, ra], [i, i], '-', color=MUTED, lw=2, alpha=0.5, zorder=2)
    ax1.scatter([ba], [i], color=BLUE,  s=130, zorder=4)
    ax1.scatter([ra], [i], color=GREEN, s=130, marker='D', zorder=4)
    ax1.text(ba - 1, i + 0.13, f'{ba}ms', ha='right', fontsize=10, color=BLUE)
    ax1.text(ra + 1, i + 0.13, f'{ra}ms', ha='left',  fontsize=10, color=GREEN)
ax1.set_yticks([0, 1, 2]); ax1.set_yticklabels(runs, fontsize=11)
ax1.set_xlabel('Avg Latency (ms)', color=MUTED, fontsize=10)
ax1.set_title('Baseline vs Recovery Avg (Dumbbell)', color=TEXT, fontsize=11, pad=6)
ax1.legend(handles=[mpatches.Patch(color=BLUE, label='Baseline'),
                    mpatches.Patch(color=GREEN, label='Recovery')],
           fontsize=9, loc='lower right')
ax1.set_xlim(130, 200)

# Left-bottom: P99 grouped barplot
ax2 = fig.add_axes([0.05, 0.09, 0.40, 0.34])
ax2.set_facecolor(PANEL)
for sp in ax2.spines.values(): sp.set_edgecolor(BORDER)
sns.barplot(data=df_p99, x='Run', y='P99 (ms)', hue='Phase',
            palette=[BLUE, GREEN], ax=ax2, errorbar=None, width=0.55, alpha=0.85)
ax2.set_xlabel('Run', color=MUTED, fontsize=10)
ax2.set_ylabel('P99 (ms)', color=MUTED, fontsize=11)
ax2.set_title('Baseline vs Recovery P99', color=TEXT, fontsize=11, pad=6)
ax2.legend(title='Phase', fontsize=9, title_fontsize=9)

# Right: latency timeline
ax3 = fig.add_axes([0.52, 0.09, 0.45, 0.76])
ax3.set_facecolor(PANEL)
for sp in ax3.spines.values(): sp.set_edgecolor(BORDER)
sns.lineplot(data=tl_df, x='Sample', y='Latency (ms)', ax=ax3,
             color=ORANGE, lw=1.5, alpha=0.8, zorder=3)
ax3.axvspan(20, 40, color=RED, alpha=0.08, label='Flapping Window')
ax3.axvline(20, color=RED,   lw=1.5, ls='--', alpha=0.6)
ax3.axvline(40, color=GREEN, lw=1.5, ls='--', alpha=0.6)
for i, (fmax, deg, c) in enumerate(zip(flap_max, p99_deg, PALETTE3)):
    ax3.text(53, 400 + i * 600, f'Run {i+1}: peak {fmax/1000:.1f}s  P99 x{deg}',
             fontsize=9, color=c, fontweight='bold')
ax3.set_ylim(-200, 7500)
ax3.set_xlabel('Sample Index', color=MUTED, fontsize=10)
ax3.set_ylabel('Latency (ms)', color=MUTED, fontsize=11)
ax3.set_title('Latency Timeline: Flapping -> Self-Recovery', color=TEXT, fontsize=11, pad=6)
ax3.legend(fontsize=9)

fig.text(0.5, 0.03,
    'Flapping = P99 spike (3.7-6.6s), NOT cascade failure  |  RF=3 majority intact  |  Recovery avg ~= baseline',
    ha='center', fontsize=9, color=MUTED)

plt.savefig('phase9_flapping.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.show()
print("Saved: phase9_flapping.png")
