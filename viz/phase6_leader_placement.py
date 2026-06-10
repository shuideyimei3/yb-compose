"""Exp 06 — Asymmetric Delay & Leader Placement"""
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

BG, PANEL = '#0d1117', '#161b22'
TEXT, MUTED, BORDER = '#e6edf3', '#8b949e', '#30363d'
PALETTE5 = ['#58a6ff', '#3fb950', '#d2a8ff', '#ffa657', '#f78166']
GOLD = '#e3b341'

RC = {
    'axes.facecolor': PANEL, 'figure.facecolor': BG,
    'axes.edgecolor': BORDER, 'grid.color': '#21262d',
    'text.color': TEXT, 'axes.labelcolor': MUTED,
    'xtick.color': MUTED, 'ytick.color': MUTED,
    'legend.facecolor': PANEL, 'legend.edgecolor': BORDER,
    'legend.labelcolor': TEXT, 'axes.unicode_minus': False,
    'font.family': 'monospace', 'font.size': 11,
}
sns.set_theme(style='darkgrid', palette=PALETTE5, rc=RC)

nodes  = ['yb-1', 'yb-2', 'yb-3', 'yb-4', 'yb-5']
delays = [10, 25, 50, 75, 100]
df = pd.DataFrame({'Node': nodes, 'Delay (ms)': delays})

fig, (ax_bar, ax_top) = plt.subplots(1, 2, figsize=(16, 9), facecolor=BG,
                                      gridspec_kw={'width_ratios': [1, 1.1]})
fig.text(0.5, 0.96, 'Exp 06  |  Asymmetric Delay & Leader Placement',
         ha='center', fontsize=19, fontweight='bold', color=TEXT)
fig.text(0.5, 0.915, 'Raft Master Leader Does NOT Auto-Migrate to Lowest-Latency Node',
         ha='center', fontsize=13, color=MUTED)

ax_bar.set_facecolor(PANEL)
for sp in ax_bar.spines.values(): sp.set_edgecolor(BORDER)
sns.barplot(data=df, x='Node', y='Delay (ms)', hue='Node',
            palette=PALETTE5, ax=ax_bar, dodge=False, legend=False, width=0.6)
for p, d, c in zip(ax_bar.patches, delays, PALETTE5):
    ax_bar.text(p.get_x() + p.get_width() / 2, d + 1.5,
                f'{d} ms', ha='center', fontsize=13, fontweight='bold', color=c)
ax_bar.annotate('Lowest Delay', xy=(0, 10), xytext=(0.5, 65),
                arrowprops=dict(arrowstyle='->', color=PALETTE5[0], lw=2),
                ha='center', fontsize=10, color=PALETTE5[0])
ax_bar.set_ylim(0, 135)
ax_bar.set_xlabel('Node', color=MUTED, fontsize=11)
ax_bar.set_ylabel('Injected Egress Delay (ms)', color=MUTED, fontsize=11)
ax_bar.set_title('Per-Node Injected Delay Gradient', color=TEXT, fontsize=12, pad=8)

ax_top.set_facecolor(PANEL)
for sp in ax_top.spines.values(): sp.set_edgecolor(BORDER)
ax_top.set_xlim(0, 10); ax_top.set_ylim(0, 10)
ax_top.axis('off')
ax_top.set_title('Leader Placement Across 3 Runs', color=TEXT, fontsize=12, pad=8)

angles = np.linspace(np.pi / 2, np.pi / 2 + 2 * np.pi, 5, endpoint=False)
cx, cy, r = 5, 5, 3.1
nxy = [(cx + r * np.cos(a), cy + r * np.sin(a)) for a in angles]

for i, j in [(i, j) for i in range(5) for j in range(i + 1, 5)]:
    ax_top.plot([nxy[i][0], nxy[j][0]], [nxy[i][1], nxy[j][1]],
                '-', color=BORDER, lw=0.8, alpha=0.45, zorder=0)

for i, ((nx, ny), c, nd, dl) in enumerate(zip(nxy, PALETTE5, nodes, delays)):
    ax_top.add_patch(plt.Circle((nx, ny), 0.72, color=c, alpha=0.18))
    ax_top.add_patch(plt.Circle((nx, ny), 0.72, fill=False, edgecolor=c, lw=2))
    ax_top.text(nx, ny + 0.1, nd, ha='center', va='center',
                fontsize=12, fontweight='bold', color=c)
    ax_top.text(nx, ny - 0.32, f'{dl}ms', ha='center', fontsize=9, color=MUTED)

lx, ly = nxy[0]
ax_top.add_patch(plt.Circle((lx, ly), 0.88, fill=False, edgecolor=GOLD, lw=2.5, ls='--'))
ax_top.text(lx, ly + 1.25, 'MASTER LEADER', ha='center',
            fontsize=12, color=GOLD, fontweight='bold')
ax_top.text(lx, ly + 0.98, 'All 3 Runs', ha='center', fontsize=9, color=GOLD)
ax_top.text(5, 0.55, 'Leader stays by historical election, not by latency',
            ha='center', fontsize=9, color=MUTED, style='italic')

fig.text(0.5, 0.03,
    'Existing leader keeps quorum: no auto-migration  |  To optimize: Geo-Partitioning + Leader Preference required',
    ha='center', fontsize=9, color=MUTED)

plt.tight_layout(rect=[0, 0.05, 1, 0.89])
plt.savefig('phase6_leader_placement.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.show()
print("Saved: phase6_leader_placement.png")
