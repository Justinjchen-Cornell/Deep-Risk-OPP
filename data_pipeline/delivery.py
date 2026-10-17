# -*- coding: utf-8 -*-
"""Alert delivery — Feishu / Telegram / DingTalk / ServerChan (v3.0).

No secrets in code. Returns per-channel status; never logs tokens/URLs.
GitHub Issue is a FALLBACK only (created when every primary channel fails).
Buttondown is intentionally NOT used for real-time alerts.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

CARD_URL = "https://justinjchen-cornell.github.io/Deep-Risk-OPP"


def configured_channels():
    out = []
    if os.environ.get("GITHUB_TOKEN") and os.environ.get("GITHUB_REPOSITORY"):
        out.append("github_issue")
    if os.environ.get("FEISHU_WEBHOOK"):
        out.append("feishu")
    if os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        out.append("telegram")
    if os.environ.get("DINGTALK_WEBHOOK"):
        out.append("dingtalk")
    if os.environ.get("SERVERCHAN_SENDKEY"):
        out.append("serverchan")
    return out


def format_message(a):
    cur = a.get("current") or {}
    return "\n".join([
        "[" + a.get("severity", "?") + "] " + a.get("title", a.get("rule", "")),
        a.get("message", ""),
        "GOR(WTI) " + str(cur.get("gor_wti")) + " · WTI " + str(cur.get("wti")) +
        " · VIX " + str(cur.get("vix")) + " · 仓位 " + str(cur.get("position")) + "%",
        "卡片: " + CARD_URL,
        "ID: " + a.get("id", ""),
    ])


def _post_json(url, payload, timeout=10):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", "replace")
        try:
            return r.status, json.loads(body)
        except Exception:
            return r.status, {}


def _get(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "deep-risk-alert"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status


def _dispatch(text, title="Deep-Risk-OPP", severity="P2", alert_id=""):
    results = {}
    feishu = os.environ.get("FEISHU_WEBHOOK")
    if feishu:
        try:
            status, obj = _post_json(feishu, {"msg_type": "text", "content": {"text": text}})
            if status in (200, 201) and obj.get("code", 0) in (0, None):
                results["feishu"] = "ok"
            else:
                results["feishu"] = "error: feishu code " + str(obj.get("code"))
        except Exception as e:
            results["feishu"] = "error: " + type(e).__name__
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat:
        try:
            status, obj = _post_json("https://api.telegram.org/bot" + token + "/sendMessage",
                                     {"chat_id": chat, "text": text, "disable_web_page_preview": True})
            if status in (200, 201) and obj.get("ok"):
                results["telegram"] = "ok"
            else:
                results["telegram"] = "error: telegram not ok"
        except Exception as e:
            results["telegram"] = "error: " + type(e).__name__
    ding = os.environ.get("DINGTALK_WEBHOOK")
    if ding:
        try:
            status, obj = _post_json(ding, {"msgtype": "text", "text": {"content": text}})
            if status in (200, 201) and obj.get("errcode", 0) == 0:
                results["dingtalk"] = "ok"
            else:
                results["dingtalk"] = "error: dingtalk code " + str(obj.get("errcode"))
        except Exception as e:
            results["dingtalk"] = "error: " + type(e).__name__
    sc = os.environ.get("SERVERCHAN_SENDKEY")
    if sc:
        try:
            url = ("https://sctapi.ftqq.com/" + sc + ".send?title=" +
                   urllib.parse.quote(title) + "&desp=" + urllib.parse.quote(text))
            _get(url)
            results["serverchan"] = "ok"
        except Exception as e:
            results["serverchan"] = "error: " + type(e).__name__

    # GitHub Issue: fallback only, when every primary channel failed.
    gh_token = os.environ.get("GITHUB_TOKEN")
    gh_repo = os.environ.get("GITHUB_REPOSITORY")
    if gh_token and gh_repo and not any(v == "ok" for v in results.values()):
        try:
            payload = {"title": "[" + severity + "] " + title, "body": text}
            req = urllib.request.Request(
                "https://api.github.com/repos/" + gh_repo + "/issues",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json",
                         "Accept": "application/vnd.github+json",
                         "Authorization": "Bearer " + gh_token})
            with urllib.request.urlopen(req, timeout=10) as r:
                results["github_issue"] = "ok" if r.status in (200, 201) else "error: HTTP " + str(r.status)
        except Exception as e:
            results["github_issue"] = "error: " + type(e).__name__
    return results


def send_alert(a):
    return _dispatch(format_message(a), a.get("title", a.get("rule", "")),
                     a.get("severity", "?"), a.get("id", ""))


def send_text(text, title="Deep-Risk-OPP", severity="P2", alert_id=""):
    return _dispatch(text, title, severity, alert_id)


def has_any_success(results):
    return any(v == "ok" for v in results.values())
