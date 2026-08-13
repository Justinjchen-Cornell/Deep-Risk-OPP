#!/usr/bin/env python3
"""
Buttondown 订阅者批量导入 (审核通过后使用!)
=============================================
用法:
    python scripts/import_subscribers.py 邮箱清单.csv
    python scripts/import_subscribers.py 邮箱清单.csv --dry-run

输入格式: 每行一个邮箱（可含表头 "email"；支持 .csv / .txt）

⚠️ 使用前提:
  1. Buttondown 账号已完成人工审核
  2. 清单里每个人都明确同意订阅（否则=垃圾邮件，账号可能被封）
  3. Buttondown 会向每个地址发送确认邮件(double opt-in)，只有确认的才生效
"""
import argparse
import csv
import os
import sys
import time
import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_PATH = BASE_DIR / "看板日志" / "subscriber_import_log.txt"


def load_key():
    try:
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / '.env')
    except Exception:
        pass
    return os.environ.get('BUTTONDOWN_API_KEY')


def read_emails(path):
    p = Path(path)
    raw = p.read_text(encoding='utf-8-sig').splitlines()
    emails = []
    for line in raw:
        line = line.strip()
        if not line or line.lower() in ('email', '邮箱'):
            continue
        # 支持 "xxx@yyy.com,备注" 形式，取第一个字段
        email = line.split(',')[0].strip()
        if '@' in email and '.' in email.split('@')[-1]:
            emails.append(email.lower())
    # 去重保序
    seen, out = set(), []
    for e in emails:
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out


def add_subscriber(key, email):
    req = urllib.request.Request(
        'https://api.buttondown.com/v1/subscribers',
        data=json.dumps({'email': email}).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Authorization': f'Token {key}'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv_path', help='邮箱清单文件（每行一个邮箱）')
    ap.add_argument('--dry-run', action='store_true', help='只预览不导入')
    ap.add_argument('--delay', type=float, default=1.0, help='每封间隔秒数（默认1秒）')
    args = ap.parse_args()

    emails = read_emails(args.csv_path)
    if not emails:
        print('清单里没有有效邮箱，退出。')
        sys.exit(1)
    print(f'共 {len(emails)} 个唯一邮箱待导入:')
    for e in emails:
        print('  -', e)

    if args.dry_run:
        print(f'\n[dry-run] 未实际导入。确认无误后去掉 --dry-run 执行。')
        sys.exit(0)

    key = load_key()
    if not key:
        print('BUTTONDOWN_API_KEY 未找到（.env）。退出。')
        sys.exit(1)

    ok, skipped, failed = 0, 0, 0
    log_lines = [f'=== import {datetime.now().strftime("%Y-%m-%d %H:%M")} | file={args.csv_path} | total={len(emails)} ===']
    for i, email in enumerate(emails, 1):
        try:
            status = add_subscriber(key, email)
            print(f'[{i}/{len(emails)}] {email} -> HTTP {status} ✅')
            ok += 1
            log_lines.append(f'OK  {email}')
        except urllib.error.HTTPError as e:
            if e.code == 400:
                # 通常=已订阅
                print(f'[{i}/{len(emails)}] {email} -> 已存在/重复，跳过')
                skipped += 1
                log_lines.append(f'SKIP {email}')
            else:
                print(f'[{i}/{len(emails)}] {email} -> HTTP {e.code} ❌ {e.read().decode()[:80]}')
                failed += 1
                log_lines.append(f'FAIL {email} (HTTP {e.code})')
        except Exception as e:
            print(f'[{i}/{len(emails)}] {email} -> 异常 ❌ {e}')
            failed += 1
            log_lines.append(f'FAIL {email} ({e})')
        time.sleep(args.delay)

    summary = f'完成: 新增 {ok} | 跳过 {skipped} | 失败 {failed}'
    print('\n' + summary)
    log_lines.append(summary)
    log_lines.append('')
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write('\n'.join(log_lines) + '\n')
        print(f'日志已写入: {LOG_PATH}')
    except Exception as e:
        print(f'日志写入失败: {e}')


if __name__ == '__main__':
    main()
