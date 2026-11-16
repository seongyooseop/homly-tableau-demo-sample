"""HOMLY (fictional Korean home-living brand, ~120 employees) - synthetic daily sales by channel x category.
Planted stories for the first-meeting demo:
  1) Coupang is the #1 channel by net sales but has the lowest online contribution margin (discount + fee).
  2) Own Mall repeat-customer share rises after a subscription launch in Mar 2026.
  3) Bedding returns jump on Coupang/Naver from Jul 2026 (supplier change) - an alert to drill into.
"""
import sys, numpy as np, pandas as pd

out = sys.argv[1]
rng = np.random.default_rng(1116)
dates = pd.date_range("2025-01-01", "2026-10-31", freq="D")

channels = {
    #            share  aov    disc  fee   ship  ad
    "Own Mall":        (0.25, 48000, 0.06, 0.03, 3000, 0.10),
    "Coupang":         (0.40, 32000, 0.12, 0.11, 2500, 0.09),
    "Naver SmartStore":(0.25, 38000, 0.08, 0.06, 3000, 0.07),
    "Offline Pop-up":  (0.10, 65000, 0.05, 0.28, 0,    0.03),
}
cats = {  # share, cogs ratio
    "Towels": (0.26, 0.40), "Bedding": (0.24, 0.45), "Kitchen": (0.20, 0.38),
    "Bath": (0.18, 0.42), "Home Fragrance": (0.12, 0.30),
}
DAILY_NET = 68_000_000  # ~KRW 25B a year at start

month_season = {1: 1.0, 2: 0.9, 3: 1.0, 4: 1.0, 5: 1.05, 6: 0.95, 7: 0.95, 8: 0.95, 9: 1.05, 10: 1.05, 11: 1.35, 12: 1.2}
rows = []
for d in dates:
    t = (d - dates[0]).days / 365.0
    base = DAILY_NET * (1.15 ** t) * month_season[d.month] * (1.12 if d.dayofweek >= 5 else 0.97)
    for ch, (sh, aov, disc, fee, ship, ad) in channels.items():
        ch_sh = sh
        if ch == "Own Mall" and d >= pd.Timestamp("2026-03-01"):
            ch_sh = sh * 1.10  # subscription lifts own-mall sales
        for ct, (csh, cogs_r) in cats.items():
            net = base * ch_sh * csh * rng.normal(1, 0.08)
            if ch == "Offline Pop-up" and d.dayofweek < 4:
                net *= 0.6
            net = max(net, 0)
            gross = net / (1 - disc)
            orders = max(int(round(net / (aov * rng.normal(1, 0.05)))), 0)
            units = int(round(orders * rng.normal(1.6, 0.1)))
            ret_r = 0.03
            if ct == "Bedding" and ch in ("Coupang", "Naver SmartStore") and d >= pd.Timestamp("2026-07-01"):
                ret_r = 0.09
            if ch == "Offline Pop-up":
                new_c, rep_c = None, None
            else:
                if ch == "Own Mall":
                    rep_share = 0.30 if d < pd.Timestamp("2026-03-01") else min(0.30 + 0.025 * ((d - pd.Timestamp("2026-03-01")).days / 30), 0.48)
                elif ch == "Coupang":
                    rep_share = 0.12
                else:
                    rep_share = 0.22
                cust = int(round(orders * 0.93))
                rep_c = int(round(cust * rep_share * rng.normal(1, 0.05)))
                new_c = max(cust - rep_c, 0)
            rows.append({
                "date": d.date().isoformat(), "channel": ch, "category": ct,
                "orders": orders, "units": units,
                "gross_sales_krw": round(gross), "discount_krw": round(gross - net), "net_sales_krw": round(net),
                "channel_fee_krw": round(net * fee), "cogs_krw": round(net * cogs_r),
                "shipping_krw": orders * ship, "ad_spend_krw": round(net * ad * rng.normal(1, 0.1)),
                "returns_krw": round(net * ret_r * rng.normal(1, 0.15)),
                "new_customers": new_c, "repeat_customers": rep_c,
            })

df = pd.DataFrame(rows)
df["new_customers"] = df["new_customers"].astype("Int64")
df["repeat_customers"] = df["repeat_customers"].astype("Int64")
df.to_csv(out, index=False, encoding="utf-8-sig")

# ---- facts for the demo plan ----
df["contribution_krw"] = df.net_sales_krw - df.channel_fee_krw - df.cogs_krw - df.shipping_krw - df.ad_spend_krw - df.returns_krw
last12 = df[df.date >= "2025-11-01"]
g = last12.groupby("channel")[["net_sales_krw", "contribution_krw", "discount_krw", "gross_sales_krw", "channel_fee_krw"]].sum()
g["share"] = g.net_sales_krw / g.net_sales_krw.sum()
g["cm_rate"] = g.contribution_krw / g.net_sales_krw
g["disc_rate"] = g.discount_krw / g.gross_sales_krw
g["fee_rate"] = g.channel_fee_krw / g.net_sales_krw
print("rows", len(df), "last-12m net sales KRW B", round(g.net_sales_krw.sum() / 1e9, 1))
print(g[["share", "cm_rate", "disc_rate", "fee_rate"]].round(3))
own = df[df.channel == "Own Mall"].copy(); own["m"] = own.date.str[:7]
om = own.groupby("m")[["new_customers", "repeat_customers"]].sum()
om["rep_share"] = om.repeat_customers / (om.new_customers + om.repeat_customers)
print(om.rep_share.loc[["2025-12", "2026-02", "2026-06", "2026-10"]].round(3))
bed = df[(df.category == "Bedding") & (df.channel.isin(["Coupang", "Naver SmartStore"]))].copy(); bed["m"] = bed.date.str[:7]
bm = bed.groupby("m")[["returns_krw", "net_sales_krw"]].sum(); bm["rr"] = bm.returns_krw / bm.net_sales_krw
print(bm.rr.loc[["2026-05", "2026-06", "2026-07", "2026-08"]].round(3))
