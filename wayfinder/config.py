"""
Wayfinder — Configuration
==========================
Thresholds for the three-flow compass.
"""

# ─── TOTAL ─────────────────────────────────────────────────────
FED_BS_CONTRACTING = 7.5    # Trillion USD: below = QT/contracting
SOFR_STRESS = 5.0           # %: above = repo market stress

# ─── DIRECTION ─────────────────────────────────────────────────
DXY_CENTRIPETAL = 99        # DXY above = capital flowing to USD
DXY_CENTRIFUGAL = 98        # DXY below = capital flowing away
US10Y_STRESS = 4.5          # %: above = rate pressure severe

# ─── SPEED ─────────────────────────────────────────────────────
VIX_CALM = 17               # Below = volatility compressed (straddle window)
VIX_ELEVATED = 20           # Above = stress rising
VIX_PANIC = 25              # Above = panic mode
HY_SPREAD_STRESS = 500      # bp: above = credit stress
HY_SPREAD_CRISIS = 800      # bp: above = credit crisis
IG_SPREAD_STRESS = 200      # bp: above = IG stress

# ─── COMPASS LABELS ────────────────────────────────────────────
COMPASS_STATES = {
    "centripetal_collapse": "CENTRIPETAL COLLAPSE — Cash is king.",
    "centrifugal_diffusion": "CENTRIFUGAL DIFFUSION — Risk-on.",
    "drain_phase": "DRAIN PHASE — USD accumulating.",
    "transition": "TRANSITION — Mixed signals.",
}