"""
Deep-Risk-OPP — Shared Configuration
=====================================
All framework parameters, circuit breakers, and data source definitions.
Modify thresholds only with strong historical evidence.
"""

# ============================================================
# GOR SEISMOGRAPH
# ============================================================

# GOR = Gold($/oz) / WTI($/bbl)
GOR_EXTREME = 45          # Extreme opportunity: oil deeply undervalued
GOR_RECOVERY = 30         # Recovery cycle floor
GOR_FAIR_VALUE = 20       # Fair value: historical equilibrium (15-25)

GOR_ZONES = {
    "extreme":     {"min": 45, "max": 999, "label": "Extreme Opportunity", "color": "#ff4444"},
    "recovery":    {"min": 30, "max": 45,  "label": "Recovery Cycle",      "color": "#ffaa00"},
    "fair_value":  {"min": 20, "max": 30,  "label": "Fair Value",          "color": "#00cc66"},
    "oil_bubble":  {"min": 0,  "max": 20,  "label": "Oil Bubble",          "color": "#4488ff"},
}

# ============================================================
# CIRCUIT BREAKERS (Non-Negotiable)
# ============================================================

WTI_HARD_STOP = 75        # Oil forced <= 5% below this
DXY_THRESHOLD = 99        # Strong USD: total position -10%
YIELD_THRESHOLD = 4.3     # High rates (10Y): total position -10%
VIX_PANIC = 25            # Vol explosion: all risk positions -50%
PBOC_GOLD_FLOOR = 2       # PBoC monthly gold buy (tons): gold floor >= 15%

# ============================================================
# ALLOCATION BASELINE (by GOR zone, before risk corrections)
# ============================================================

BASE_ALLOCATION = {
    "extreme": {
        "total": 70,
        "oil": 38,
        "gold": 10,
        "a_shares": 12,
        "copper": 3,
        "cash": 37,
    },
    "recovery": {
        "total": 50,
        "oil": 20,
        "gold": 15,
        "a_shares": 15,
        "copper": 0,
        "cash": 50,
    },
    "fair_value": {
        "total": 30,
        "oil": 0,
        "gold": 15,
        "a_shares": 20,
        "copper": 0,
        "cash": 65,
    },
    "oil_bubble": {
        "total": 10,
        "oil": 0,
        "gold": 7,
        "a_shares": 3,
        "copper": 0,
        "cash": 90,
    },
}

# ============================================================
# PRIORITY CHAIN (lower number = higher priority)
# ============================================================

CIRCUIT_BREAKER_PRIORITY = 1     # Always wins
RISK_CALENDAR_PRIORITY = 2       # FOMC / OPEC+ / election overrides
BAGHOLDER_PRIORITY = 3           # Bagholder >= 7: all positions x 0.7
CAPITAL_FLOW_PRIORITY = 4        # Centripetal collapse: cash >= 40%
GOR_DIRECTION_PRIORITY = 5       # Default allocation baseline
MASTER_CONSENSUS_PRIORITY = 6    # Advisory only, does not override

# ============================================================
# OIL TARGET / STOP ZONES
# ============================================================

OIL_ACCUMULATION_ZONE = (75, 85)    # WTI range for low-absorb
OIL_TARGET_ZONE = (95, 105)         # WTI take-profit range
OIL_HARD_STOP = 75                  # WTI: forced reduce to 5%

# ============================================================
# CAPITAL THREE-FLOWS THRESHOLDS
# ============================================================

DXY_CENTRIPETAL = 99     # DXY above this = centripetal
DXY_CENTRIFUGAL = 98     # DXY below this = centrifugal
VIX_ACCELERATING = 20    # VIX above this = flow speed accelerating
VIX_PANIC = 25           # VIX above this = panic

# ============================================================
# DATA SOURCES
# ============================================================

GOLD_SOURCE = "Yahoo Finance (GC=F)"
WTI_SOURCE = "Yahoo Finance (CL=F)"
BRENT_SOURCE = "Yahoo Finance (BZ=F)"
DXY_SOURCE = "ICE (DX-Y.NYB) + FRED (DTWEXBGS)"
YIELD_10Y_SOURCE = "CBOE (^TNX) + FRED (DGS10)"
YIELD_30Y_SOURCE = "CBOE (^TYX) + FRED (DGS30)"
VIX_SOURCE = "CBOE (^VIX)"
COPPER_SOURCE = "COMEX (HG=F)"

# API endpoints for gor_daily.py
API_ENDPOINTS = {
    "gold": "GC=F",
    "wti": "CL=F",
    "brent": "BZ=F",
    "dxy": "DX-Y.NYB",
    "ten_year": "^TNX",
    "vix": "^VIX",
    "copper": "HG=F",
}

# ============================================================
# FRED API CONFIGURATION (Federal Reserve Economic Data)
# ============================================================

# FRED API key loaded from .env file (never committed to repo)
# See .env.example for setup instructions

FRED_SERIES = {
    "DGS10": "10-Year Treasury Constant Maturity Rate",
    "DGS30": "30-Year Treasury Constant Maturity Rate",
    "DFF": "Federal Funds Effective Rate",
    "DTWEXBGS": "Trade Weighted U.S. Dollar Index (Broad)",
    "CPIAUCSL": "Consumer Price Index (All Urban Consumers)",
    "PCEPILFE": "Core PCE Price Index (excl. Food & Energy)",
    "WALCL": "Federal Reserve Total Assets",
    "M2SL": "M2 Money Supply",
    "GFDEBTN": "Federal Debt: Total Public Debt",
    "VIXCLS": "CBOE Volatility Index (VIX)",
    "DCOILWTICO": "WTI Crude Oil Spot Price",
    "GOLDAMGBD228NLBR": "Gold Fixing Price (London, USD/oz)",
}

# ============================================================
# FILE PATHS
# ============================================================

OUTPUT_DIR = "./看板日志"
GOR_LATEST = "./gor_latest.json"
CAPITAL_FLOWS_LATEST = "./capital_flows_latest.json"
DECISION_CARD_TEMPLATE = "./每日资讯/📊 GOR 今日决策卡.md"

# ============================================================
# MCP / CLAUDE CODE INTEGRATION
# ============================================================

SKILL_NAME = "Deep-Risk-OPP"
SKILL_VERSION = "2.0.0"
SKILL_TRIGGERS = [
    "macro risk",
    "GOR",
    "gold oil ratio",
    "capital flows",
    "what to allocate",
    "Deep-Risk",
]

if __name__ == "__main__":
    print(f"Deep-Risk-OPP v{SKILL_VERSION}")
    print(f"GOR Extreme threshold: >= {GOR_EXTREME}")
    print(f"WTI Hard Stop: ${WTI_HARD_STOP}")
    print(f"Priority levels: {CIRCUIT_BREAKER_PRIORITY} (breaker) to {MASTER_CONSENSUS_PRIORITY} (masters)")