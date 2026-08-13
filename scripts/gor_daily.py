#!/usr/bin/env python3
"""
每日GOR决策卡引擎 — 薄包装 (P1-2)
实现见 data_pipeline/daily.py + data_pipeline/common.py
用法: python scripts/gor_daily.py （GitHub Actions daily.yml 调用入口）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.daily import run_daily

if __name__ == '__main__':
    run_daily()
