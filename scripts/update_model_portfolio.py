#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update the public model portfolio (paper) from the daily card.

Method: fixed NAV, weights from card allocation; oil/gold daily returns;
cash/A-shares/copper = 0 (conservative until feeds are added).
No costs, no tax, no leverage. Appends history + rebalance log.
"""
import json
import os
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PF = os.path.join(BASE, 'model_portfolio.json')
CARD = os.path.join(BASE, 'gor_latest.json')

def bj_today():
    return datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d')

def main():
    pf = json.load(open(PF, encoding='utf-8'))
    card = json.load(open(CARD, encoding='utf-8'))
    d = card.get('data') or {}
    wti = (d.get('WTI原油') or {}).get('price')
    gold = (d.get('黄金期货') or {}).get('price')
    alloc = card.get('allocation') or {}
    today = bj_today()

    last = pf.get('history', [])[-1] if pf.get('history') else None
    last_prices = pf.get('last_prices') or {}
    nav = float(pf.get('nav') or pf.get('base_nav') or 100)
    changed = False

    if last and last.get('date') == today:
        # same-day rerun: do not double count
        pass
    else:
        wo = float(pf.get('weights', {}).get('油气', 0)) / 100.0
        wg = float(pf.get('weights', {}).get('黄金', 0)) / 100.0
        r_oil = (wti / last_prices['wti'] - 1.0) if (wti and last_prices.get('wti')) else 0.0
        r_gold = (gold / last_prices['gold'] - 1.0) if (gold and last_prices.get('gold')) else 0.0
        nav = nav * (1.0 + wo * r_oil + wg * r_gold)
        pf.setdefault('history', []).append({
            'date': today,
            'nav': round(nav, 4),
            'note': 'oil %.2f%% / gold %.2f%%' % (r_oil * 100, r_gold * 100),
        })
        changed = True

    new_weights = {k: alloc.get(k, 0) for k in ('油气', '黄金', '现金', 'A股', '铜')}
    old_weights = pf.get('weights') or {}
    diff = max(abs(float(new_weights.get(k, 0)) - float(old_weights.get(k, 0))) for k in new_weights)
    if diff >= 1:
        pf.setdefault('trades', []).append({
            'date': today,
            'action': 'rebalance',
            'nav': round(nav, 2),
            'note': 'weights %s -> %s' % (old_weights, new_weights),
        })
        pf['weights'] = new_weights
        changed = True

    pf['nav'] = round(nav, 4)
    pf['last_prices'] = {'wti': wti, 'gold': gold}
    pf['updated'] = today
    pf.setdefault('history', [])
    pf['history'] = pf['history'][-500:]
    if changed:
        json.dump(pf, open(PF, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('model portfolio updated:', today, 'NAV', pf['nav'])
    else:
        print('model portfolio unchanged:', today, 'NAV', pf['nav'])

if __name__ == '__main__':
    main()
