#!/usr/bin/env python3
"""
周度变化报告 — 薄包装 (P1-2)
实现见 data_pipeline/weekly.py + data_pipeline/common.py
用法: python scripts/weekly_data_pull.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.weekly import run_weekly

if __name__ == '__main__':
    run_weekly()
