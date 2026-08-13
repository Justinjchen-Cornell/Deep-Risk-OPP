"""
Deep-Risk-OPP — mode weekly (P1-1 拆分自 run.py)
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from modes.common import get_gor_zone, get_gor_blend, check_dynamic_hard_stop, get_allocation

def mode_weekly():
    """Generate weekly change report."""
    print("Weekly change report — compare with last week's data.")
    print("Run: python run.py --mode weekly --compare last-week")
    # Placeholder for weekly report generation
    pass
