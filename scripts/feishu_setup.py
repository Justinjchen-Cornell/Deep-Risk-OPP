#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Feishu custom-bot setup wizard.

3 steps: create a custom bot in a Feishu group -> paste webhook -> test + store
as a GitHub Actions secret. The webhook is never printed in full and never
written into a QR code.

Usage:
  python scripts/feishu_setup.py                 # interactive wizard
  python scripts/feishu_setup.py --webhook URL   # non-interactive
  python scripts/feishu_setup.py --test-only     # CI: read FEISHU_WEBHOOK env
"""
import argparse
import getpass
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

REPO = "Justinjchen-Cornell/Deep-Risk-OPP"
SECRET_NAME = "FEISHU_WEBHOOK"
SECRET_PAGE = "https://github.com/" + REPO + "/settings/secrets/actions/new"
VALID_PREFIXES = ("https://open.feishu.cn/open-apis/bot/v2/hook/",
                  "https://open.larksuite.com/open-apis/bot/v2/hook/")


def mask(url):
    if not url:
        return "(empty)"
    tail = url[-4:] if len(url) >= 4 else "****"
    return url.split("/hook/")[0] + "/hook/****" + tail


def validate(url):
    if not url or not url.startswith(VALID_PREFIXES):
        raise SystemExit("Invalid Feishu webhook. It must start with:\n  " +
                         "\n  ".join(VALID_PREFIXES))


def send_test(url):
    text = ("🧪 Deep-Risk-OPP · Feishu 连接测试\n"
            "如果你看到这条消息，飞书告警通道已打通。\n"
            "下一步：Actions → Feishu Test → Run workflow。")
    payload = {"msg_type": "text", "content": {"text": text}}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        body = r.read().decode("utf-8", "replace")
        try:
            obj = json.loads(body)
        except Exception:
            obj = {}
        if r.status not in (200, 201) or (obj.get("code") not in (None, 0)):
            raise SystemExit("Feishu test failed: HTTP %s %s" % (r.status, body[:200]))
    print("✅ 测试消息已发送（%s）" % mask(url))


def gh_ready():
    try:
        subprocess.run(["gh", "auth", "status"], capture_output=True, check=True)
        return True
    except Exception:
        return False


def set_github_secret(url, repo):
    p = subprocess.run(["gh", "secret", "set", SECRET_NAME, "-R", repo],
                       input=url + "\n", text=True, capture_output=True)
    if p.returncode == 0:
        print("✅ 已写入 GitHub Actions Secret: %s (%s)" % (SECRET_NAME, repo))
        return True
    print("⚠️ 自动写入失败：%s" % (p.stderr.strip()[:160] or "gh 未登录"))
    print("   手动方式：打开 %s" % SECRET_PAGE)
    print("   名称：%s；值：你刚粘贴的 webhook" % SECRET_NAME)
    return False


def save_local(url):
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    try:
        old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        if "FEISHU_WEBHOOK=" in old:
            print("ℹ️ .env 已有 FEISHU_WEBHOOK，未覆盖")
            return
        with open(path, "a", encoding="utf-8") as f:
            if old and not old.endswith("\n"):
                f.write("\n")
            f.write("FEISHU_WEBHOOK=" + url + "\n")
        print("✅ 已写入本地 .env（gitignored，仅本机使用）")
    except Exception as e:
        print("⚠️ 写入 .env 失败：%s" % e)


def main():
    ap = argparse.ArgumentParser(description="Feishu custom-bot setup wizard")
    ap.add_argument("--webhook", default=None, help="Feishu custom bot webhook URL")
    ap.add_argument("--repo", default=REPO, help="GitHub repo (owner/name)")
    ap.add_argument("--test-only", action="store_true", help="send a test and exit (CI)")
    ap.add_argument("--no-github", action="store_true", help="do not write the GitHub secret")
    ap.add_argument("--save-local", action="store_true", help="also save to local .env")
    ap.add_argument("--skip-test", action="store_true", help="do not send a test message")
    args = ap.parse_args()

    url = args.webhook or os.environ.get("FEISHU_WEBHOOK")

    if args.test_only:
        if not url:
            raise SystemExit("FEISHU_WEBHOOK is not set — add the GitHub secret first")
        validate(url)
        send_test(url)
        return

    if not url:
        print("飞书接入 · 3 步\n"
              "1) 飞书群 → 设置 → 群机器人 → 添加机器人 → 自定义机器人 → 复制 Webhook\n"
              "2) 把 Webhook 粘贴到下面（输入不回显）\n"
              "3) 本脚本会发一条测试消息，并写入 GitHub Actions Secret\n")
        try:
            url = getpass.getpass("粘贴 Feishu Webhook: ").strip()
        except Exception:
            url = input("粘贴 Feishu Webhook: ").strip()

    validate(url)
    if not args.skip_test:
        send_test(url)
    if not args.no_github:
        if gh_ready():
            set_github_secret(url, args.repo)
        else:
            print("⚠️ gh 未登录或不可用。手动方式：%s" % SECRET_PAGE)
    if args.save_local:
        save_local(url)

    print("\n下一步：")
    print("  • 手动验证：GitHub → Actions → Feishu Test → Run workflow")
    print("  • 或运行：gh workflow run feishu-test.yml -R %s" % args.repo)
    print("  • 告警通道：飞书（主）+ GitHub Issue（零配置兜底）")


if __name__ == "__main__":
    main()
