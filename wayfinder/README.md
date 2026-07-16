# Wayfinder

> **Don't predict prices. Map the flows.**
> *不看价格。看流向。*

```
Total × Direction × Speed = Capital Flow Compass
```

---

## What Is Wayfinder?

Wayfinder is a standalone capital flow navigation system. It tracks the **three flows** of global capital — Total Volume, Direction, and Speed — and produces a real-time compass that tells you where money is going and how fast.

It is the capital-flow engine extracted from [Deep-Risk-OPP](https://github.com/Justinjchen-Cornell/Deep-Risk-OPP), rebuilt as an independent project.

**Wayfinder does not predict prices. It maps flows.**

---

## The Three Flows

```
     TOTAL                         DIRECTION                     SPEED
  Is global liquidity          Is capital flowing            Is it panic
  expanding or                 toward the USD               or calm?
  contracting?                 or away?
       │                            │                            │
       ▼                            ▼                            ▼
  ┌──────────┐               ┌──────────────┐            ┌──────────────┐
  │Fed BS    │               │ DXY          │            │ VIX           │
  │M2        │               │ TIC inflows  │            │ HY spread     │
  │ECB/BOJ   │               │ Gold flows   │            │ IG spread     │
  │SOFR      │               │ EM outflows  │            │ TED spread    │
  │Deficit   │               │ CNH deposits │            │ Swap basis    │
  └────┬─────┘               └──────┬───────┘            └──────┬───────┘
       │                            │                            │
       └────────────────────────────┼────────────────────────────┘
                                    │
                                    ▼
                         ┌──────────────────┐
                         │  FLOW COMPASS     │
                         │                   │
                         │  Centripetal      │
                         │  Collapse         │
                         │  ⬆ ACTIVE        │
                         │                   │
                         │  Cash is king.    │
                         │  Wait for signals.│
                         └──────────────────┘
```

## Quick Start

```bash
pip install -r requirements.txt
python run.py --mode scan          # Today's flow readings
python run.py --mode report        # Standalone HTML flow report
python run.py --mode history       # 6-month flow trend
```

## Data Sources

| Source | What It Provides | Series |
|--------|-----------------|--------|
| **FRED** | Fed BS, M2, SOFR, yields, spreads | WALCL, M2SL, SOFR, DGS10, DGS30, BAMLH0A0HYM2, BAMLC0A0CM, CPIAUCSL, GFDEBTN |
| **yfinance** | DXY, currency vols | DX-Y.NYB |
| **akshare** | China flows, gold reserves | macro_china_gold_reserve |

## License

MIT · Independent Research · Not Investment Advice