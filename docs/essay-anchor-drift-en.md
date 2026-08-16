# "The 15-25 GOR equilibrium? It already drifted." — 20 years of daily data

> LinkedIn / Substack candidate #2. Based on docs/equilibrium-anchor-analysis.md.

---

**Gold/Oil Ratio = gold price ÷ oil price. Every commentary says: "the historical equilibrium is 15-25; at 54 it's an extreme of historic proportions."**

I ran the daily data for the past 20 years (2006-2026, 5,179 trading days). The finding is more interesting:

**That equilibrium may have already moved.**

## 1. Over the full sample, 15-25 holds

The median GOR since 2006 is 21.0; interquartile range 15.2-27.4. Over 20 years, "15-25" is statistically fine.

## 2. But broken into regimes, the anchor has been drifting up

5-year rolling mean:

```
2011: 12.9
2016: 16.6
2021: 29.1
2026: 35.4
```

| Period | Mean | Median | Days above 45 |
|---|---:|---:|---:|
| 2006-2012 | 13.7 | 14.2 | **0.0%** |
| 2012-2018 | 21.0 | 21.0 | 0.1% |
| 2018-2026 | **34.2** | 27.7 | **23.7%** |

**In six years (2006-2012), GOR never crossed 45 once. Since 2018, it has been above 45 nearly a quarter of the time.**

## 3. Why would it drift? Three structural forces

1. **Central bank gold buying** — 19 consecutive months of PBoC accumulation; demand curve shifted up structurally.
2. **Shale supply + EV adoption** — more supply elasticity, slower demand growth; the oil price ceiling moved down.
3. **Dollar debasement** — fiat purchasing power erodes; hard-asset premium rises systematically.

These are not cyclical. They are slow, structural variables. The drift is likely permanent, not temporary.

## 4. What this means for "extreme" calls

- The 45 threshold still equals the P90 of the full sample — "extreme" remains statistically defensible. **Keep it.**
- But "54 is the most extreme since 1986" is measured against the *old* anchor. Against the 2018-2026 anchor (28-34), 54 sits around P92 — still extreme, just not apocalyptic.
- If the anchor keeps drifting, "45" will stop being extreme a decade from now. The framework must re-check percentiles quarterly instead of worshipping a fixed number.

## 5. The rules I published for myself (in the repo)

1. Always date the claim: not "historical equilibrium 15-25", but "full-sample median 21; the center of gravity has moved from ~14 (2006-2012) to ~28-34 (2018-2026)".
2. Re-baseline the 45 threshold quarterly against percentiles; recalibrate if the full-sample P90 crosses 45.
3. My public falsifiable claim (WTI ≥ $107.60 by 2027-06-19) carries a failure clause: **if oil misses AND the 5-year GOR mean breaks 40, I declare the mean-reversion framework broken — and fix the framework, not the narrative.**

---

Data: Sina XAU/CL daily, 2006-08 → 2026-08. Code and cache open-source & reproducible: github.com/Justinjchen-Cornell/Deep-Risk-OPP

Research framework. Not investment advice.
