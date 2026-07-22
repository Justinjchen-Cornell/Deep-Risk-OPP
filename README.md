# Deep-Risk-OPP

<p align="center">
  <img src="logo.svg" alt="Deep-Risk-OPP" width="600">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/data-FRED%20%7C%20akshare%20%7C%20yfinance-orange" alt="Data">
  <img src="https://img.shields.io/badge/Claude%20Code-skill-6A46D1" alt="Claude Code">
  <img src="https://img.shields.io/badge/backtest-2020%E2%80%932026-ffa500" alt="Backtest">
</p>

> **See the crisis before the surface moves. Find the opportunity before the crowd arrives.**

Acknowledgments: The theoretical foundation regarding the gold-to-oil ratio within this framework is derived from Mr. Lu Qiyuan’s macroeconomic analysis system. The "Three Capital Flows" framework draws upon liquidity analysis models developed by various analysts. The "Six Masters Mapping" represents the author's synthesis of public statements made by six investment masters. The hard stop-loss rules, risk modifiers, Python automation pipeline, and Claude Code integration were independently developed by the author. All data is sourced from public APIs (FRED, akshare, yfinance).
```
GOR Seismograph → Capital Flow Fault-Line Scan → 11 Frameworks → 6 Masters → 1 Decision Card

```

---

## What Is Deep-Risk-OPP?

**Deep-Risk-OPP** is an open-source macro early-warning system built for Claude Code. It answers one question:

> *"What structural risk is building beneath the surface — and where is the opportunity hiding inside it?"*

Most investors watch prices. Deep-Risk-OPP watches the **fractures beneath prices**. It treats the Gold/Oil Ratio (GOR) as a **seismograph** for systemic stress, maps global capital flows as **fault-line scans**, and orchestrates 11 decision frameworks through a priority engine to produce a single, actionable signal card.

**OPP** stands for **Opportunity** — because deep risk, correctly read, is where the deepest opportunities are buried.

---

## The Core Metaphor

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   SURFACE LAYER (what everyone sees)                         │
│   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   │
│   Prices. Headlines. CPI prints. Fed minutes.               │
│                                                              │
│   ──────────────────── ⚡ FRACTURE ⚡ ────────────────────    │
│                                                              │
│   DEEP LAYER (what Deep-Risk-OPP sees)                      │
│   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   │
│   GOR divergence. Capital centripetal collapse.             │
│   Supply-chain severance. Liquidity freeze.                 │
│                                                              │
│   The system detects stress accumulating in the deep layer  │
│   BEFORE it erupts through the surface.                     │
│                                                              │
│   Seismograph: GOR ratio (Gold/Oil)                         │
│   Fault scan:  Capital Three-Flows (Total/Direction/Speed)  │
│   Analysts:    11 frameworks + 6 investment masters         │
│   Output:      1 early-warning decision card                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Justinjchen-Cornell/Deep-Risk-OPP.git
cd Deep-Risk-OPP

# Install dependencies
pip install -r requirements.txt

# Run the daily signal engine
python run.py --mode daily

# Or ask Claude Code directly
# "Run Deep-Risk. What's today's signal?"
```

**Prerequisites**: Claude Code with MCP server access. Python >= 3.11.

---

## Architecture

```
User: "What's the macro risk today?"
          │
          ▼
┌─────────────────────────────────────────────────────┐
│             DEEP-RISK-OPP PIPELINE                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  [1] SEISMOGRAPH                                     │
│      GOR = Gold($/oz) / WTI($/bbl)                  │
│      Reads: extreme opportunity / recovery / bubble  │
│                                                      │
│  [2] FAULT-LINE SCAN                                 │
│      Capital Three-Flows: Total × Direction × Speed  │
│      Reads: centripetal collapse / centrifugal       │
│                                                      │
│  [3] FRAMEWORK ORCHESTRATION                         │
│      11 frameworks loaded. Priority chain resolves   │
│      conflicts. Signal consensus computed.           │
│                                                      │
│  [4] MASTER CONSULTATION                             │
│      6 legendary investor mindsets mapped to data.   │
│      Buffett says hold cash? Burry says hedge?       │
│      Li Ka-shing says wait for forced sellers?       │
│                                                      │
│  [5] SIGNAL OUTPUT                                    │
│      1 decision card. 6 lines. Zero ambiguity.       │
│                                                      │
└─────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────┐
│   EARLY-WARNING CARD │
│   Date: 2026-07-15   │
│   GOR:   50.85       │
│   Risk:  ELEVATED    │
│   Oil:   ACCUMULATE  │
│   Gold:  HOLD 15%    │
│   Cash:  50%+        │
│   Alert: Warsh hawk  │
└──────────────────────┘
```

---

## The 11 Frameworks

Every framework answers one question. Together they form a 360-degree risk assessment.

| # | Framework | Core Question | Trigger | File |
|:-:|-----------|--------------|:------:|------|
| 01 | **GOR Direction** | What to allocate today? | Daily | [01-GOR方向框架.md](01-GOR方向框架.md) |
| 02 | **Deep Diligence** | Which specific asset? | On-demand | [02-个股四维研判.md](02-个股四维研判.md) |
| 03 | **Bagholder Theory** | What market phase are we in? | Event | [03-接盘论框架.md](03-接盘论框架.md) |
| 04 | **Token Dollar** | Where is USD hegemony? | Monthly | [04-Token美元进度.md](04-Token美元进度.md) |
| 05 | **Hedging Strategy** | How to protect positions? | Per position | [05-对冲策略选择.md](05-对冲策略选择.md) |
| 06 | **Risk Calendar** | What time nodes lie ahead? | Weekly | [06-风控日历.md](06-风控日历.md) |
| 07 | **Decision Audit** | Was that luck or skill? | Monthly | [07-决策审计框架.md](07-决策审计框架.md) |
| 08 | **Six Masters** | What would the legends say? | Events | [08-六大师映射.md](08-六大师映射.md) |
| 09 | **Capacity Cycle** | Where in the industrial cycle? | On-demand | [09-产能周期框架.md](09-产能周期框架.md) |
| 10 | **Catalyst Calendar** | What events will move markets? | On-demand | [10-催化剂日历框架.md](10-催化剂日历框架.md) |
| 11 | **Capital Three Flows** | Where is money flowing? | Daily+Weekly | [11-资本三流框架.md](11-资本三流框架.md) |

### Priority Chain (When Frameworks Conflict)

```
Level 1: Circuit Breaker      — WTI < $75 → oil forced ≤ 5%
Level 2: Risk Calendar Node   — FOMC / OPEC+ / election overrides
Level 3: Bagholder >= 7       — All positions × 0.7
Level 4: Capital Flow Signal  — Centripetal → raise cash ≥ 40%
Level 5: GOR Direction        — Default allocation baseline
Level 6: Master Consensus     — Advisory only, does not override
```

Lower number = higher priority. Circuit breakers always win.

---

## The 6 Masters

Not predictions. **Risk philosophies.** Each master's framework is mapped onto current data to produce a risk posture.

| Master | Risk Philosophy | Current Posture (Jul 2026) | Signal |
|--------|----------------|---------------------------|:------:|
| **Buffett** | "Be fearful when others are greedy." $397B in cash. | Cash is the position. Energy is the watchlist. | DEFENSIVE |
| **Burry** | "The bond market is screaming." 30Y at 5.15%. | Systemic credit event brewing. | DEFENSIVE |
| **Druckenmiller** | "Liquidity drives everything." Three CBs tightening. | Tactical oil long. Strategic cash. | SELECTIVE |
| **Damodaran** | "Price is what you pay. Value is what you get." | Energy majors 40% undervalued. Gold 32% overvalued. | BULLISH ENERGY |
| **Taleb** | "The tails are fat." Hallmuz + BOJ + US auction risks. | Barbell: 90% ultra-safe + 10% convex bets. | HEDGED |
| **Li Ka-shing** | "未买先想卖." 90% of brain on what can go wrong. | Direction is right. Sweetest fruit already picked at GOR=78. Wait for forced sellers. | PATIENT |

For detailed master mappings, see [08-六大师映射.md](08-六大师映射.md).

---

## Usage Examples

```bash
# Daily macro risk scan
python run.py --mode daily
# Output: early-warning card with GOR, flows, allocation, alerts

# Run with specific frameworks
python run.py --mode daily --frameworks 01,05,11

# What would the masters say about current data?
python run.py --mode masters --masters buffett,burry,taleb

# Generate a weekly change report
python run.py --mode weekly --compare last-week

# Run a historical backtest
python run.py --mode backtest --from 2020-01 --to 2026-07

# Export the decision card as JSON
python run.py --mode daily --output signal.json
```

### Natural Language (via Claude Code)

```
User: "Deep-Risk: what's the macro risk posture today?"
→ Loads GOR + Capital Flows + Risk Calendar. Outputs card.

User: "Hedge my oil position."
→ Loads Hedging + Risk Calendar. Recommends WTI $75 Put.

User: "Is this a market top?"
→ Loads Bagholder. Scores 10-point checklist.

User: "Should I rotate from gold to oil?"
→ Loads GOR + Six Masters + Capital Flows. Cross-validates.

User: "What did we get right and wrong last month?"
→ Loads Decision Audit. Scores framework accuracy.
```

---

## The Seismograph: GOR Zones

| Zone | GOR Range | Risk Signal | Action |
|------|:---------:|-------------|--------|
| 🔴 **Extreme Opportunity** | ≥ 45 | Oil deeply undervalued. Structural mean-reversion building. | Accumulate energy. Reduce gold. |
| 🟠 **Recovery Cycle** | 30–45 | Ratio normalizing. Crisis abating. | Hold. Let the trade work. |
| 🟢 **Fair Value** | 20–30 | Historical equilibrium. No structural mispricing. | Light positions. Wait. |
| 🔵 **Oil Bubble** | < 20 | Gold cheap. Oil expensive. Inflation fear peaked. | Cash + gold. No energy exposure. |

### Circuit Breakers (Non-Negotiable)

| Breaker | Condition | Action |
|---------|:--------:|--------|
| WTI Hard Stop | WTI < $75 | Oil forced ≤ 5% |
| DXY Surge | DXY > 99 | Total position -10% |
| Rate Spike | 10Y > 4.3% | Total position -10% |
| Vol Explosion | VIX > 25 | All risk positions -50% |
| PBoC Floor | Monthly gold buy ≥ 2T | Gold floor locked ≥ 15% |

---

## The Fault-Line Scan: Capital Three-Flows

| Dimension | What It Measures | Current (Jul 2026) |
|-----------|-----------------|--------------------|
| **Total** | Global liquidity: expanding or contracting? | 🔴 Contracting (Fed QT $7.3T) |
| **Direction** | Capital flowing to USD or away? | 🔴 Centripetal (DXY 100.96) |
| **Speed** | Panic or calm? | 🟡 Slowing (VIX 15.03) |

**Centripetal Collapse Alert**: When Total contracts + Direction pulls inward + Speed accelerates → systemic liquidity event is imminent.

---

## Configuration

```python
# config.py — Shared parameters for all frameworks

# GOR Seismograph
GOR_EXTREME = 45          # Extreme opportunity threshold
GOR_RECOVERY = 30         # Recovery cycle floor
GOR_FAIR_VALUE = 20       # Fair value floor

# Circuit Breakers
WTI_HARD_STOP = 75        # Oil forced ≤ 5% below this
DXY_THRESHOLD = 99        # Strong USD: total position -10%
YIELD_THRESHOLD = 4.3     # High rates: total position -10%
VIX_PANIC = 25            # Vol explosion: risk positions -50%

# Priority Weights
CIRCUIT_BREAKER_PRIORITY = 1    # Always wins
RISK_CALENDAR_PRIORITY = 2
BAGHOLDER_PRIORITY = 3
CAPITAL_FLOW_PRIORITY = 4
GOR_DIRECTION_PRIORITY = 5
MASTER_CONSENSUS_PRIORITY = 6

# Data Sources (3-layer: FRED primary → yfinance → web fallback)
GOLD_SOURCE = "akshare (GC=F)"
WTI_SOURCE = "akshare (CL=F)"
DXY_SOURCE = "yfinance (DX-Y.NYB) + web fallback"
YIELD_10Y_SOURCE = "FRED (DGS10) + akshare fallback"
YIELD_30Y_SOURCE = "FRED (DGS30)"
VIX_SOURCE = "FRED (VIXCLS) + TradingView/CBOE fallback"
FED_SOURCE = "FRED (DFF/WALCL/M2SL/CPIAUCSL/PCEPILFE/GFDEBTN)"
```

Full configuration guide: [config.py](config.py)

---

## Data Pipeline

```
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│  FRED (Fed)  │    │   Yahoo Finance  │    │    akshare    │
│  DGS10/30    │    │   DX-Y.NYB (DXY) │    │  Gold, WTI,   │
│  VIXCLS, DFF │    │                  │    │  Brent, Copper│
│  WALCL, M2SL │    │                  │    │               │
│  CPIAUCSL     │    │                  │    │               │
│  PCEPILFE     │    │                  │    │               │
│  GFDEBTN      │    │                  │    │               │
└──────┬───────┘    └────────┬─────────┘    └───────┬───────┘
       │                     │                      │
       └─────────────────────┼──────────────────────┘
                             │
                             ▼
                   ┌─────────────────┐
                   │  gor_daily.py   │
                   │  weekly_data_   │
                   │  pull.py        │
                   │  Pull→Compute   │
                   │  →Classify→     │
                   │  Output JSON     │
                   └────────┬────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  Decision Engine (run.py)      │
            │  Load frameworks → Check      │
            │  priority → Output card       │
            └───────────────┬───────────────┘
                            │
                            ▼
                 ┌──────────────────┐
                 │  Signal Output    │
                 │  ├─ JSON          │
                 │  ├─ Markdown Card │
                 │  └─ Log Archive   │
                 └──────────────────┘
```

---

## Track Record

Selected historical signals from the GOR seismograph (backtested):

| Date | GOR | Signal | Subsequent Market Move | ✓ |
|------|----:|--------|------------------------|:-:|
| 2020.04 | 69.5 | Extreme: accumulate oil | WTI +167% in 12 months | ✅ |
| 2016.01 | ~39 | Recovery: hold oil | WTI +54% in 12 months | ✅ |
| 2008.12 | ~30 | Recovery: hold oil | WTI +78% in 12 months | ✅ |
| **2026.06.25** | 53.33 | **Circuit breaker: WTI < $75 → oil 5%** | WTI fell to $68.76. Capital preserved. | ✅ |
| **2026.07.15** | 50.85 | **Hard stop released. Accumulate oil 27%.** | In progress — WTI reclaimed $79.49 in 72h. | ⏳ |

*Past signals are backtested on historical data. Real-time signals are tracked live.*

---

## Dashboard Logs

Daily snapshots, weekly change reports, and special deep-dive analyses are archived in [看板日志/](看板日志/).

| Date | Type | GOR | Event |
|------|------|----:|-------|
| 2026-07-12 | Weekly Change | 57.74 | WTI recovering from hard stop low |
| 2026-07-05 | Weekly Change | 60.89 | GOR spiking to near-record |
| 2026-06-25 | **Critical Event** | 56.88 | WTI broke $75. Circuit breaker triggered. |
| 2026-06-19 | Daily Brief | 52.69 | WTI $0.73 from hard stop |

---

## File Structure

```
Deep-Risk-OPP/
│
├── README.md                          # This file
├── config.py                          # Shared parameters
├── run.py                             # CLI entry point
├── requirements.txt                   # Dependencies
│
├── 01-GOR方向框架.md                   # Seismograph: GOR-based allocation
├── 02-个股四维研判.md                   # Deep diligence: 4D stock screening
├── 03-接盘论框架.md                     # Bagholder theory: market phase
├── 04-Token美元进度.md                  # Token dollar: USD hegemony tracker
├── 05-对冲策略选择.md                   # Hedging: position protection
├── 06-风控日历.md                       # Risk calendar: time nodes
├── 07-决策审计框架.md                   # Decision audit: luck vs skill
├── 08-六大师映射.md                     # Six masters: legendary mindsets
├── 09-产能周期框架.md                   # Capacity cycle: industrial timing
├── 10-催化剂日历框架.md                  # Catalyst calendar: event-driven
├── 11-资本三流框架.md                   # Fault-line: capital flow scan
│
├── scripts/                           # Automation scripts
│   ├── gor_daily.py                   # GOR data pipeline
│   └── risk_calendar.py               # Calendar event checker
│
├── 看板日志/                           # Dashboard archive
│   ├── 2026-06-19-每日简报.md
│   ├── 2026-06-25-变化比对报告.md
│   ├── 2026-07-05-变化比对报告.md
│   ├── 2026-07-12-变化比对报告.md
│   ├── *.json                          # Machine-readable signal data
│   └── 📋 看板日志索引.md
│
├── gor_latest.json                    # Latest GOR + allocation data
├── capital_flows_latest.json          # Latest capital flow readings
│
└── 审计记录/                           # Decision audit history
```

---

## Roadmap

| Milestone | Description | Status |
|-----------|-------------|:------:|
| v1.0 | GOR seismograph + daily signal card | ✅ Done |
| v1.1 | Capital flow fault-line scan integration | ✅ Done |
| v1.2 | Six masters mapping + consensus engine | ✅ Done |
| v1.3 | Second/third-order opportunity detection | ✅ Done |
| v2.0 | Full priority chain with circuit breakers | ✅ Done |
| v2.1 | Weekly automated change reports | ✅ Done |
| v2.2 | Historical backtest suite (2000–2026) | 🔄 In progress |
| v3.0 | Real-time alerting (email/webhook) | 📋 Planned |
| v3.1 | Interactive dashboard (HTML/JS) | 📋 Planned |
| v4.0 | Multi-asset portfolio simulation | 📋 Planned |

---

## Contributing

Deep-Risk-OPP is a personal research framework shared openly. If you want to:

- **Report a bug**: Open an issue with the signal date and framework involved.
- **Suggest a framework**: Propose a new decision framework with its core question and trigger logic.
- **Improve the backtest**: Submit a PR with verified historical data and methodology.
- **Translate**: English and Chinese are maintained. Other languages welcome.

All framework parameters are in `config.py`. Circuit breaker thresholds should only be changed with strong historical evidence.

---

## Disclaimer

```
DEEP-RISK-OPP IS A MACRO RESEARCH FRAMEWORK — NOT INVESTMENT ADVICE.

This system is a tool for structural risk awareness and scenario analysis.
It does not predict market movements. It does not recommend specific securities.
It does not guarantee outcomes. All signals are probabilistic, not deterministic.

The GOR ratio, capital flow scans, master consensus, and all framework outputs
are research artifacts. They carry no warranty of accuracy.

Past signals and backtests do not guarantee future results.
All investment decisions remain entirely your responsibility.

By using this framework, you acknowledge that you are engaging with
independent macro research — not receiving financial advice.
```

---

## License

MIT © 2026 Justin Chen (Justinjchen-Cornell)

---

## Credits

Deep-Risk-OPP synthesizes insights from:

- **Gold/Oil Ratio theory** — a single-ratio macro allocation framework
- **Capital Three-Flows theory** (资本三流) — global liquidity total/direction/speed analysis
- **The Centripetal Collapse thesis** (向心坍缩) — structural USD liquidity concentration
- **Six legendary investors** — Buffett, Burry, Druckenmiller, Damodaran, Taleb, Li Ka-shing
- **Claude Code** — the AI platform that makes multi-framework orchestration possible

Built with Python, Claude MCP, Yahoo Finance API, CBOE, FRED, and ICE data.

---

> *"The GOR ratio is the seismograph. Capital flows are the fault-line scan. The frameworks are the analysts. Deep-Risk-OPP is the early-warning system. What you do with the signal — that's yours."*
