"""Exp 03 — Cross-Region Delay Injection"""
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

BG, PANEL = '#ffffff', '#f6f8fa'
TEXT, MUTED, BORDER = '#1f2328', '#636c76', '#d0d7de'
PALETTE5 = ['#58a6ff', '#3fb950', '#d2a8ff', '#ffa657', '#f78166']

RC = {
    'axes.facecolor': PANEL, 'figure.facecolor': BG,
    'axes.edgecolor': BORDER, 'grid.color': '#d8dee4',
    'text.color': TEXT, 'axes.labelcolor': MUTED,
    'xtick.color': MUTED, 'ytick.color': MUTED,
    'legend.facecolor': PANEL, 'legend.edgecolor': BORDER,
    'legend.labelcolor': TEXT, 'axes.unicode_minus': False,
    'font.family': 'monospace', 'font.size': 11,
}
sns.set_theme(style='darkgrid', palette=PALETTE5, rc=RC)

nodes   = ['yb-1 (30ms)', 'yb-2 (60ms)', 'yb-3 (90ms)', 'yb-4 (120ms)', 'yb-5 (150ms)']
base_r  = [89.77, 90.75, 90.61, 88.44, 89.19]
delay_r = [128.16, 160.30, 189.89, 220.67, 249.83]
base_w  = [89.76, 91.27, 89.06, 88.64, 90.30]
delay_w = [127.15, 155.73, 187.89, 218.94, 248.24]
mult    = [1.43, 1.77, 2.10, 2.50, 2.80]

rows = []
for node, b, d, bw, dw in zip(nodes, base_r, delay_r, base_w, delay_w):
    rows += [
        {'Node': node, 'Latency (ms)': b,  'Stage': 'Baseline', 'Op': 'Read'},
        {'Node': node, 'Latency (ms)': d,  'Stage': 'Injected', 'Op': 'Read'},
        {'Node': node, 'Latency (ms)': bw, 'Stage': 'Baseline', 'Op': 'Write'},
        {'Node': node, 'Latency (ms)': dw, 'Stage': 'Injected', 'Op': 'Write'},
    ]
df = pd.DataFrame(rows)

fig, (ax_r, ax_w) = plt.subplots(1, 2, figsize=(16, 9), facecolor=BG)
fig.text(0.5, 0.96, 'Exp 03  |  Cross-Region Delay Injection',
         ha='center', fontsize=19, fontweight='bold', color=TEXT)
fig.text(0.5, 0.915, 'Baseline vs Injected Latency per Node  |  3-Run Average',
         ha='center', fontsize=13, color=MUTED)

for ax, op, title in [(ax_r, 'Read', 'Read Latency'), (ax_w, 'Write', 'Write Latency')]:
    ax.set_facecolor(PANEL)
    for sp in ax.spines.values(): sp.set_edgecolor(BORDER)
    sub = df[df['Op'] == op].copy()
    sns.lineplot(data=sub, x='Stage', y='Latency (ms)', hue='Node',
                 palette=PALETTE5, marker='o', markersize=10,
                 linewidth=2.2, ax=ax, legend=(ax is ax_r))
    injected = delay_r if op == 'Read' else delay_w
    for i, (node, d_val, m) in enumerate(zip(nodes, injected, mult)):
        ax.text(1.04, d_val, f'x{m}', va='center', fontsize=9,
                color=PALETTE5[i], fontweight='bold')
    ax.set_xlim(-0.25, 1.35)
    ax.set_ylim(70, 280)
    ax.set_xlabel('Stage', color=MUTED, fontsize=11)
    ax.set_ylabel('Latency (ms)', color=MUTED, fontsize=11)
    ax.set_title(title, color=TEXT, fontsize=13, pad=8)

ax_r.legend(title='Node', fontsize=9, title_fontsize=9, loc='upper left')

fig.text(0.5, 0.03,
    'Latency grows ~linearly with egress delay  |  Read ~= Write  |  RTT ~ src_egress + dst_egress',
    ha='center', fontsize=9, color=MUTED)

plt.tight_layout(rect=[0, 0.05, 1, 0.89])
plt.savefig('phase3_delay_injection_light.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.show()
print("Saved: phase3_delay_injection_light.png")
