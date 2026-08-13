"""
Deep-Risk-OPP — 配置 schema 校验 (P2)
管道启动时调用；发现违规立即返回清单（由调用方决定 fail-fast）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


def validate_config():
    """校验 config.py 的阈值/区间/分配表。返回问题列表（空=通过）。"""
    problems = []

    # 1. GOR 区间：数值、边界、覆盖
    zones = getattr(config, 'GOR_ZONES', None)
    if not isinstance(zones, dict) or len(zones) != 4:
        problems.append('GOR_ZONES 必须包含 4 个区间')
    else:
        for name, z in zones.items():
            lo, hi = z.get('min'), z.get('max')
            if not isinstance(lo, (int, float)) or not isinstance(hi, (int, float)):
                problems.append(f'GOR_ZONES.{name} 的 min/max 必须是数字')
            elif lo >= hi:
                problems.append(f'GOR_ZONES.{name} min({lo}) >= max({hi})')
        # 连续性: extreme.min=45 → recovery.max=45 等
        if 'extreme' in zones and 'recovery' in zones:
            if zones['extreme']['min'] != zones['recovery']['max']:
                problems.append('GOR_ZONES: extreme.min 必须等于 recovery.max (边界共享)')
        if 'recovery' in zones and 'fair_value' in zones:
            if zones['recovery']['min'] != zones['fair_value']['max']:
                problems.append('GOR_ZONES: recovery.min 必须等于 fair_value.max')
        if 'fair_value' in zones and 'oil_bubble' in zones:
            if zones['fair_value']['min'] != zones['oil_bubble']['max']:
                problems.append('GOR_ZONES: fair_value.min 必须等于 oil_bubble.max')

    # 2. 阈值关系
    checks = [
        ('GOR_EXTREME', 'GOR_RECOVERY', lambda a, b: a > b, 'GOR_EXTREME 必须大于 GOR_RECOVERY'),
        ('GOR_RECOVERY', 'GOR_FAIR_VALUE', lambda a, b: a > b, 'GOR_RECOVERY 必须大于 GOR_FAIR_VALUE'),
        ('WTI_ABSOLUTE_FLOOR', 'WTI_HARD_STOP', lambda a, b: a < b, 'WTI_ABSOLUTE_FLOOR 必须小于 WTI_HARD_STOP'),
    ]
    for ka, kb, pred, msg in checks:
        a = getattr(config, ka, None)
        b = getattr(config, kb, None)
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            problems.append(f'{ka}/{kb} 必须是数字')
        elif not pred(a, b):
            problems.append(f'{msg} (当前 {ka}={a}, {kb}={b})')

    # 3. 动态止损参数
    if not 0 < getattr(config, 'HARD_STOP_MA_MULTIPLIER', 0) < 1:
        problems.append('HARD_STOP_MA_MULTIPLIER 必须在 (0,1) 区间')
    if getattr(config, 'HARD_STOP_MA_PERIOD', 0) < 20:
        problems.append('HARD_STOP_MA_PERIOD 至少为 20')
    if not 0 <= getattr(config, 'GOR_SUPPLY_SHOCK_RISE', -1) <= 1:
        problems.append('GOR_SUPPLY_SHOCK_RISE 必须在 [0,1] 区间')

    # 4. 基准分配表
    base = getattr(config, 'BASE_ALLOCATION', None)
    required_keys = {'total', 'oil', 'gold', 'cash'}
    if not isinstance(base, dict):
        problems.append('BASE_ALLOCATION 必须是字典')
    else:
        for zone, alloc in base.items():
            if not isinstance(alloc, dict):
                problems.append(f'BASE_ALLOCATION.{zone} 必须是字典')
                continue
            missing = required_keys - set(alloc)
            if missing:
                problems.append(f'BASE_ALLOCATION.{zone} 缺字段: {missing}')
            for k, v in alloc.items():
                if not isinstance(v, (int, float)) or not (0 <= v <= 100):
                    problems.append(f'BASE_ALLOCATION.{zone}.{k}={v} 超出 [0,100]')
            if 'total' in alloc and alloc['total'] > 100:
                problems.append(f'BASE_ALLOCATION.{zone}.total={alloc["total"]} 超过 100')

    # 5. 修正器阈值
    for k in ['DXY_THRESHOLD', 'YIELD_THRESHOLD', 'VIX_PANIC']:
        v = getattr(config, k, None)
        if not isinstance(v, (int, float)):
            problems.append(f'{k} 必须是数字')

    return problems


def assert_config_valid():
    """校验并输出结果。返回 True/False。"""
    problems = validate_config()
    if problems:
        print('!! CONFIG SCHEMA VIOLATIONS:')
        for msg in problems:
            print('   -', msg)
        return False
    print('  Config schema: OK')
    return True


if __name__ == '__main__':
    sys.exit(0 if assert_config_valid() else 1)
