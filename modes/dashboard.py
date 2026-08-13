"""
Deep-Risk-OPP — mode dashboard (P1-1 拆分自 run.py)
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from modes.common import get_gor_zone, get_gor_blend, check_dynamic_hard_stop, get_allocation

def mode_dashboard():
    """Launch interactive dashboard."""
    print("Interactive dashboard — launching...")
    try:
        import streamlit as st
        print("Streamlit available. Run: streamlit run dashboard.py")
    except ImportError:
        print("Streamlit not installed. pip install streamlit")
