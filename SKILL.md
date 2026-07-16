# Deep-Risk-OPP — Claude Code Skill

## Metadata

- **Name**: `deep-risk-opp`
- **Version**: `2.0.0`
- **Author**: Justin Chen
- **Description**: Macro systemic risk early-warning framework. GOR seismograph + capital flow fault-line scan + 11 decision frameworks + 6 investment masters → 1 decision card.

## Activation

This skill activates automatically when the user asks about:
- Macro risk assessment ("what's the risk today?", "macro posture")
- GOR / Gold-Oil Ratio ("金油比", "GOR", "gold oil ratio")
- Asset allocation direction ("what to allocate", "gold or oil")
- Capital flows ("资本三流", "capital flows", "centripetal collapse")
- Market regime ("extreme opportunity", "market phase")
- Circuit breakers ("hard stop", "defense mode")

Or explicitly: `Run Deep-Risk`, `Deep-Risk-OPP`

## Core Capabilities

### 1. Daily Risk Scan
Read `gor_latest.json` and `capital_flows_latest.json`. Output a 6-line decision card:
1. GOR value + regime zone
2. Framework position (%)
3. Oil directive (accumulate / hold / reduce / hard stop)
4. Gold directive (hold / trim / accumulate)
5. A-share / commodity directive
6. Key alerts + this week's triggers

### 2. Framework Cross-Reference
When user asks a specific question, load the relevant framework(s):
- "should I hedge?" → `05-对冲策略选择.md`
- "is this a top?" → `03-接盘论框架.md`
- "what would Buffett say?" → `08-六大师映射.md`
- "where is USD going?" → `04-Token美元进度.md` + `11-资本三流框架.md`

### 3. Data Refresh
`python run.py --mode daily` to pull fresh data and regenerate the decision card.

### 4. Backtest
`python run.py --mode backtest --from 2020-01-01 --to 2026-07-16` for historical regime-switching performance.

## Priority Chain (Non-Negotiable)

When frameworks conflict, resolve in this order:
1. **Circuit Breaker** (WTI < $75 → oil ≤ 5%)
2. **Risk Calendar Node** (FOMC / OPEC+ / election override)
3. **Bagholder ≥ 7** (all positions × 0.7)
4. **Capital Flow Signal** (centripetal → cash ≥ 40%)
5. **GOR Direction** (default allocation baseline)
6. **Master Consensus** (advisory only)

## Tone & Constraints

- **Zero predictions.** Use "the framework indicates" / "historically" / "the signal shows"
- **No ticker recommendations.** Use sector/theme language (e.g. "offshore oil leaders" not "0883.HK")
- **Always include risk context.** Every bullish signal must note the bear case.
- **Disclaimer at end.** "Research framework. Not investment advice."
- **Chinese responses** when user writes in Chinese. Bilingual capability.

## Data Sources

- `gor_latest.json` — GOR, allocation, alerts (updated daily)
- `capital_flows_latest.json` — Capital three-flows readings
- Framework `.md` files in project root — decision logic

## Example Prompt

```
User: "Deep-Risk: 今天宏观风险怎么样？"

Response:
[Loads gor_latest.json + capital_flows_latest.json]
[Cross-checks with 06-风控日历.md for upcoming events]
[Applies priority chain]
[Outputs 6-line decision card in Chinese]
```