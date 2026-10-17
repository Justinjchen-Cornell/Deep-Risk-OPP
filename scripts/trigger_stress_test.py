# -*- coding: utf-8 -*-
"""
Trigger stress test — VIX >= 22.5 AND oil <= 25th percentile of trailing 10y.
Reads docs/data/trigger_test_input.csv (date,wti,gold,vix), prints episode table + stats.
Optionally rewrites docs/data/trigger_episodes.csv.

Usage: python scripts/trigger_stress_test.py [--write]
"""
import os
import argparse
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT = os.path.join(BASE, 'docs', 'data', 'trigger_test_input.csv')
OUT = os.path.join(BASE, 'docs', 'data', 'trigger_episodes.csv')

VIX_GATE = 22.5
OIL_PCTL = 0.25
LOOKBACK = 2520      # ~10 years of trading days
MIN_PERIODS = 504    # at least ~2 years
GAP_DAYS = 30
HORIZONS = [(63, '3m'), (126, '6m'), (252, '12m')]


def load():
    df = pd.read_csv(INPUT, parse_dates=['date']).set_index('date').sort_index()
    df = df[df['wti'] > 0].copy()
    df['gor'] = df['gold'] / df['wti']
    df['pctl'] = df['wti'].rolling(LOOKBACK, min_periods=MIN_PERIODS).apply(
        lambda x: (x <= x[-1]).mean(), raw=True)
    for h, lab in HORIZONS:
        df[f'w_{lab}'] = df['wti'].shift(-h) / df['wti'] - 1
        df[f'g_{lab}'] = df['gold'].shift(-h) / df['gold'] - 1
        df[f'r_{lab}'] = df['gor'].shift(-h) / df['gor'] - 1
    return df


def episodes(df):
    ev = df[(df['vix'] >= VIX_GATE) & (df['pctl'] <= OIL_PCTL)]
    eps, last = [], None
    for d in ev.index:
        if last is None or (d - last).days > GAP_DAYS:
            eps.append([d])
        else:
            eps[-1].append(d)
        last = d
    return eps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help='rewrite docs/data/trigger_episodes.csv')
    args = ap.parse_args()

    df = load()
    eps = episodes(df)
    rows = []
    for e in eps:
        d = e[0]
        row = {'start': d.date(), 'end': e[-1].date(), 'days': len(e),
               'vix': round(df.loc[d, 'vix'], 1),
               'oil_pctl': round(df.loc[d, 'pctl'], 2),
               'wti': round(df.loc[d, 'wti'], 1)}
        for _, lab in HORIZONS:
            for src, dst in [('w', 'wti'), ('g', 'gold'), ('r', 'gor')]:
                v = df.loc[d, f'{src}_{lab}']
                row[f'{dst}_{lab}'] = round(v * 100, 1) if pd.notna(v) else None
        rows.append(row)
    out = pd.DataFrame(rows)
    print(f'data: {df.index.min().date()} -> {df.index.max().date()}  rows={len(df)}')
    print(f'episodes: {len(out)}  event days: {int(((df["vix"] >= VIX_GATE) & (df["pctl"] <= OIL_PCTL)).sum())}')
    print(out.to_string(index=False))

    print('\nepisode-level forward returns:')
    for _, lab in HORIZONS:
        s = out[f'wti_{lab}'].dropna()
        if len(s):
            print(f'  {lab}: N={len(s)} median={s.median():+.1f}% mean={s.mean():+.1f}% hit={(s > 0).mean() * 100:.0f}%')

    if args.write:
        out.to_csv(OUT, index=False, encoding='utf-8-sig')
        print(f'\nwrote {OUT}')


if __name__ == '__main__':
    main()
