"""Exp 04 — Automatic Failover RTO"""
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

BG, PANEL = '#ffffff', '#f6f8fa'
TEXT, MUTED, BORDER = '#1f2328', '#636c76', '#d0d7de'
GREEN, RED, ORANGE = '#3fb950', '#f78166', '#ffa657'

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

records = []
run_ids = ['Run 1', 'Run 2', 'Run 3']
docker  = [486, 534, 481]
ipt_tot = [7150, 7137, 6936]
ipt_net = [514, 615, 478]

for run, d, it, in_ in zip(run_ids, docker, ipt_tot, ipt_net):
    records += [
        {'Run': run, 'RTO (ms)': d,   'Scenario': 'docker stop\n(process crash)'},
        {'Run': run, 'RTO (ms)': it,  'Scenario': 'iptables total\n(incl. detection)'},
        {'Run': run, 'RTO (ms)': in_, 'Scenario': 'iptables net\n(recovery only)'},
    ]
df = pd.DataFrame(records)

fig, axes = plt.subplots(1, 3, figsize=(16, 9), facecolor=BG)
fig.text(0.5, 0.96, 'Exp 04  |  Automatic Failover RTO',
         ha='center', fontsize=19, fontweight='bold', color=TEXT)
fig.text(0.5, 0.915, 'Process Crash vs Network Partition  |  3 Runs',
         ha='center', fontsize=13, color=MUTED)

scenarios = [
    ('docker stop\n(process crash)',      docker,   GREEN,  'Process Crash\ndocker stop yb-4'),
    ('iptables total\n(incl. detection)', ipt_tot,  RED,    'Partition Total RTO\n(detection + recovery)'),
    ('iptables net\n(recovery only)',     ipt_net,  ORANGE, 'Partition Net RTO\n(pure recovery window)'),
]

for ax, (scen, vals, color, title) in zip(axes, scenarios):
    ax.set_facecolor(PANEL)
    for sp in ax.spines.values(): sp.set_edgecolor(BORDER)
    sub = df[df['Scenario'] == scen].copy()
    sns.barplot(data=sub, x='Run', y='RTO (ms)', ax=ax,
                color=color, alpha=0.75, errorbar=None, width=0.5)
    avg = np.mean(vals)
    ax.axhline(avg, color='white', lw=2, ls='--', alpha=0.85, zorder=5)
    ax.text(2.4, avg * 1.04, f'avg\n{avg:.0f} ms', ha='right', fontsize=9.5,
            color='white', fontweight='bold')
    for p, v in zip(ax.patches, vals):
        ax.text(p.get_x() + p.get_width() / 2, p.get_height() + max(vals) * 0.015,
                f'{v}', ha='center', fontsize=11, color=color, fontweight='bold')
    ax.set_ylim(0, max(vals) * 1.4)
    ax.set_xlabel('Run', color=MUTED, fontsize=10)
    ax.set_ylabel('RTO (ms)', color=MUTED, fontsize=11)
    ax.set_title(title, color=TEXT, fontsize=12, pad=8)

fig.text(0.5, 0.03,
    'Process crash RTO ~0.5s  |  Partition total ~7s (detection overhead)  |  Partition net ~0.5s  |  RPO=0',
    ha='center', fontsize=9, color=MUTED)

plt.tight_layout(rect=[0, 0.05, 1, 0.89])
plt.savefig('phase4_failover_rto_light.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.show()
print("Saved: phase4_failover_rto_light.png")
