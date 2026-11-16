"""Static mock of the HOMLY 'Channel Health' dashboard (design preview before building it in Tableau Public)."""
import sys, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

csv, out = sys.argv[1], sys.argv[2]
df = pd.read_csv(csv)
df["contribution_krw"] = df.net_sales_krw - df.channel_fee_krw - df.cogs_krw - df.shipping_krw - df.ad_spend_krw - df.returns_krw
df["month"] = df.date.str[:7]

INK, MUTED, GRID, SURF = "#262626", "#6b6b6b", "#e6e5e0", "#fcfcfb"
COL = {"Own Mall": "#2a78d6", "Coupang": "#eb6834", "Naver SmartStore": "#1baf7a", "Offline Pop-up": "#eda100"}
plt.rcParams.update({"font.family": "Segoe UI", "font.size": 9, "text.color": INK, "axes.edgecolor": GRID,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED})

l12 = df[df.date >= "2025-11-01"]
g = l12.groupby("channel")[["net_sales_krw", "contribution_krw"]].sum()
g["share"] = g.net_sales_krw / g.net_sales_krw.sum()
g["cm"] = g.contribution_krw / g.net_sales_krw
g = g.loc[["Coupang", "Own Mall", "Naver SmartStore", "Offline Pop-up"]]
total, cm_all = g.net_sales_krw.sum(), g.contribution_krw.sum() / g.net_sales_krw.sum()

own = df[df.channel == "Own Mall"].groupby("month")[["new_customers", "repeat_customers"]].sum()
own["rep"] = own.repeat_customers / (own.new_customers + own.repeat_customers)
mk = df[df.channel.isin(["Coupang", "Naver SmartStore"])].copy()
mk["grp"] = mk.category.where(mk.category == "Bedding", "Other categories")
bed = mk.groupby(["month", "grp"])[["returns_krw", "net_sales_krw"]].sum()
bed["rr"] = bed.returns_krw / bed.net_sales_krw
bed = bed.rr.unstack()

fig = plt.figure(figsize=(12, 7.2), facecolor=SURF)
gs = fig.add_gridspec(3, 4, height_ratios=[0.55, 1.5, 1.5], hspace=0.75, wspace=0.45, left=0.115, right=0.95, top=0.88, bottom=0.08)
fig.text(0.06, 0.95, "HOMLY  |  Channel Health (last 12 months: Nov 2025 – Oct 2026)", fontsize=15, weight="bold")
fig.text(0.06, 0.915, "Fictional company and data · design preview for a Tableau Public dashboard", fontsize=9, color=MUTED)

tiles = [("Net sales", f"KRW {total/1e9:.1f}B"), ("Contribution margin", f"{cm_all:.1%}"),
         ("Own Mall repeat share (Oct)", f"{own.rep.iloc[-1]:.0%}"), ("Bedding return rate (Oct)", f"{bed['Bedding'].iloc[-1]:.1%}")]
for i, (lab, val) in enumerate(tiles):
    ax = fig.add_subplot(gs[0, i]); ax.axis("off")
    ax.text(0, 0.95, lab, fontsize=9, color=MUTED, va="top")
    ax.text(0, 0.15, val, fontsize=20, weight="bold", va="bottom")

def style(ax, title, sub):
    ax.set_title(title, loc="left", fontsize=11, weight="bold", pad=18)
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=8.5, color=MUTED)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", color=GRID, lw=0.8); ax.set_axisbelow(True); ax.tick_params(length=0)

names = list(g.index)
ax1 = fig.add_subplot(gs[1:, 0]); ax2 = fig.add_subplot(gs[1:, 1])
for ax, col, title, sub in [(ax1, "share", "Net sales share", "by channel"), (ax2, "cm", "Contribution margin", "after discount, fees, COGS, shipping, ads, returns")]:
    vals = g[col].values
    ax.barh(names, vals, color=[COL[n] for n in names], height=0.55)
    for y, v in enumerate(vals):
        ax.text(v + 0.006, y, f"{v:.1%}", va="center", fontsize=9, color=INK)
    ax.invert_yaxis(); ax.xaxis.set_major_formatter(PercentFormatter(1, 0)); ax.set_xlim(0, max(vals) * 1.3)
    style(ax, title, sub)
ax2.set_yticklabels([])

ax3 = fig.add_subplot(gs[1, 2:])
x = range(len(own))
ax3.plot(x, own.rep.values, color=COL["Own Mall"], lw=2)
ax3.scatter([len(own) - 1], [own.rep.iloc[-1]], color=COL["Own Mall"], s=36, zorder=3)
i0 = list(own.index).index("2026-03")
ax3.axvline(i0, color=MUTED, lw=0.8, ls="--"); ax3.text(i0 + 0.3, 0.255, "Subscription launch (Mar 2026)", fontsize=8.5, color=MUTED)
ax3.set_xticks(list(x)[::3]); ax3.set_xticklabels(list(own.index)[::3], fontsize=8)
ax3.yaxis.set_major_formatter(PercentFormatter(1, 0)); ax3.set_ylim(0.2, 0.55)
style(ax3, "Own Mall repeat-customer share", "monthly"); ax3.grid(axis="y", color=GRID, lw=0.8); ax3.grid(axis="x", visible=False)

ax4 = fig.add_subplot(gs[2, 2:])
for grp, c, lw in [("Other categories", "#9b9a95", 1.5), ("Bedding", "#e87ba4", 2)]:
    ax4.plot(range(len(bed)), bed[grp].values, color=c, lw=lw)
    ax4.text(len(bed) - 0.6, bed[grp].iloc[-1], grp, fontsize=8.5, color=INK, va="center")
j0 = list(bed.index).index("2026-07")
ax4.axvline(j0, color=MUTED, lw=0.8, ls="--"); ax4.text(j0 - 0.3, 0.105, "Supplier change (Jul 2026)", fontsize=8.5, color=MUTED, ha="right")
ax4.set_xticks(list(range(len(bed)))[::3]); ax4.set_xticklabels(list(bed.index)[::3], fontsize=8)
ax4.yaxis.set_major_formatter(PercentFormatter(1, 0)); ax4.set_ylim(0, 0.12); ax4.set_xlim(-0.5, len(bed) + 4)
style(ax4, "Return rate: Bedding vs other categories", "Coupang + Naver SmartStore, monthly"); ax4.grid(axis="y", color=GRID, lw=0.8); ax4.grid(axis="x", visible=False)

fig.savefig(out, dpi=200, facecolor=SURF)
print("saved", out)
