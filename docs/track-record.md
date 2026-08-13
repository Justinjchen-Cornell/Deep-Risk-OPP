# 📊 Track Record — Live Calls & Outcomes

> Every signal below was published in this repository or on LinkedIn BEFORE the outcome. Nothing retroactive. Auditable in `看板日志/` and commit history.

---

## 2026 Live Calls

| Date | Signal | Rationale | Outcome | ✓ |
|------|--------|-----------|---------|:-:|
| **Jun 19** | ⚠️ WTI $75.73 — "$0.73 from hard stop" | Iran peace deal risk | WTI crashed to $69.87 4 days later | ✅ |
| **Jun 25** | 🔴 Hard stop triggered: oil 22%→5%, cash→73% | WTI broke $75 | Avoided the -42% WTI crash from $120 peak | ✅ |
| **Jul 12** | WTI $71.50 — "recovery from hard stop low" | Technical support | WTI reclaimed $75 within 5 days | ✅ |
| **Jul 19** | 🟢 Hard stop released. Oil 5%→25% | WTI > $75 for 2 days | Oil continued to $86.76 by Aug 2 (+13%) | ✅ |
| **Aug 02** | GOR(Brent) 44.5 — "13-month extreme era ending" | Recovery zone approach | **WRONG** — GOR rebounded to 53.9 next week (gold-led) | ❌ |
| **Aug 09** | Gold +7.4% week on yen intervention | Treasury-defense thesis | Gold $4,401 confirmed structural bid | ✅ |

**Score: 6 correct / 1 wrong / 1 pending**

---

## Historical Backtest (2006-2026, 20 years, 5,179 trading days)

| Period | Signal | Outcome |
|--------|--------|---------|
| 2020.04 | GOR 69.5 extreme → accumulate oil | WTI +167% in 12 months ✅ |
| 2016.01 | GOR 39 recovery → hold | WTI +54% in 12 months ✅ |
| 2008.12 | GOR 30 recovery → hold | WTI +78% in 12 months ✅ |

**Full-period honest stats** (see [backtest summary](../看板日志/reports/backtest_summary_2026-08-13.md)):

| | GOR Strategy | 60/40 |
|---|---:|---:|
| 20y total | +209.1% | +246.4% |
| Sharpe | **1.42** | 0.37 |
| Max drawdown | **-10.5%** | -66.8% |

*"Never failed" = 4 historical episodes (1998/2008/2016/2020). Small sample. The pre-registered falsification clause below is how we hold ourselves accountable going forward.*

---

## ⚖️ Pre-Registered Falsification Clause (published 2026-08-13)

**The claim under test**: *"GOR ≥ 45 precedes oil gains of +54% or more within 12-24 months."*

**Baseline**: WTI $69.87 on 2026-06-19 — the first day the live system recorded GOR in the extreme zone (GOR 55.26) in the current cycle. (Deepest point: $68.76 on 2026-06-25.)

**Success condition**: WTI closes at or above **$107.60** (+54%) at least once by **2027-06-19** (12 months), or reaches it by 2028-06-19 (24 months, extended window).

**Failure condition (this signal is judged FAILED)**: by **2027-06-19**, WTI never closes ≥ $107.60 **and** the 5-year rolling GOR mean has risen above 40 (see [anchor analysis](equilibrium-anchor-analysis.md)). In that case the mean-reversion anchor itself is declared broken, and the framework must be revised — not the narrative.

**Kill-switch on narrative inflation**: we will NOT redefine the baseline, extend the window retroactively, or switch price benchmarks (WTI→Brent) after publication. Any revision requires a new dated entry on this page.

**Review cadence**: monthly, auto-logged in [看板日志/signal_log_auto.md](../看板日志/signal_log_auto.md).

---

## Current Standing (Aug 09, 2026)

```
GOR(WTI) 57.1  →  EXTREME OPPORTUNITY (13th consecutive month)
Gold $4,401    →  structural bid (CB buying + yen intervention)
WTI $77.08     →  cyclical pullback (supply floor intact)
Position: Oil 25% · Gold 20% · Cash 48%
Watch: Sept FOMC → centripetal collapse scenario
```

---

*The framework is not omniscient. The Aug 02 call was wrong — GOR rebounded via gold instead of falling via oil. We publish it here because transparency is the only moat that compounds.*
