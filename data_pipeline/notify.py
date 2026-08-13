"""
Deep-Risk-OPP — 每日推送 (交付层 L1)
支持四通道（配置即用，密钥来自 .env 或 GitHub Secrets）：
  FEISHU_WEBHOOK      飞书群机器人
  DINGTALK_WEBHOOK    钉钉群机器人
  SERVERCHAN_SENDKEY  Server酱（微信推送）
  TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID
未配置任何通道时静默跳过。DR_PUSH_DRY_RUN=1 只打印不发送。
"""
import json
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.common import BASE_DIR, log

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except Exception:
    pass

SITE = "https://justinjchen-cornell.github.io"


def _post_json(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status


def _get(url):
    with urllib.request.urlopen(url, timeout=15) as r:
        return r.status


def build_message(gor_output):
    d = gor_output
    data = d.get('data', {})
    alloc = d.get('allocation', {})

    def price(key):
        v = (data.get(key) or {}).get('price')
        return f"{v:,.1f}" if isinstance(v, (int, float)) else "N/A"

    alerts = d.get('alerts', [])
    alert_txt = ""
    if alerts:
        alert_txt = "\n".join(f"⚠️ {a.get('title', '')} — {a.get('detail', '')}" for a in alerts[:4])
    dq = d.get('data_quality', {})
    dq_txt = ""
    if not (dq.get('ok', True)):
        dq_txt = f"\n🔧 数据源降级: {', '.join(dq.get('degraded_fields', []))}"

    msg = (
        f"📡 Deep-Risk-OPP 每日信号 · {d.get('updated', '')[:10]}\n"
        f"GOR(WTI) {d.get('gor_wti'):.1f} · {d.get('regime', '')} · 仓位 {d.get('final_position')}%\n"
        f"黄金 ${price('黄金期货')} | WTI ${price('WTI原油')} | DXY {price('美元指数DXY')} | 10Y {price('10Y美债收益率')}% | VIX {price('VIX恐慌指数')}\n"
        f"配置: 油气{alloc.get('油气', 0)}% 黄金{alloc.get('黄金', 0)}% 现金{alloc.get('现金', 0)}% A股{alloc.get('A股', 0)}%\n"
        f"{alert_txt}{dq_txt}\n"
        f"🔗 {SITE}/\n"
        f"— 研究框架，不构成投资建议"
    )
    return msg


def send_daily_push(gor_output):
    msg = build_message(gor_output)
    dry = os.environ.get('DR_PUSH_DRY_RUN') == '1'
    sent = []

    # 飞书
    url = os.environ.get('FEISHU_WEBHOOK')
    if url:
        try:
            if dry:
                print(f"  [dry] Feishu: {msg[:60]}...")
            else:
                _post_json(url, {"msg_type": "text", "content": {"text": msg}})
            sent.append('feishu')
        except Exception as e:
            log(f"  Feishu push failed: {e}")

    # 钉钉
    url = os.environ.get('DINGTALK_WEBHOOK')
    if url:
        try:
            if dry:
                print(f"  [dry] DingTalk: {msg[:60]}...")
            else:
                _post_json(url, {"msgtype": "text", "text": {"content": msg}})
            sent.append('dingtalk')
        except Exception as e:
            log(f"  DingTalk push failed: {e}")

    # Server酱
    key = os.environ.get('SERVERCHAN_SENDKEY')
    if key:
        try:
            url2 = f"https://sctapi.ftqq.com/{key}.send?title={urllib.parse.quote(msg.splitlines()[0])}&desp={urllib.parse.quote(msg)}"
            if dry:
                print(f"  [dry] ServerChan: {msg[:60]}...")
            else:
                _get(url2)
            sent.append('serverchan')
        except Exception as e:
            log(f"  ServerChan push failed: {e}")

    # Telegram
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat:
        try:
            url3 = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {"chat_id": chat, "text": msg, "disable_web_page_preview": True}
            if dry:
                print(f"  [dry] Telegram: {msg[:60]}...")
            else:
                _post_json(url3, payload)
            sent.append('telegram')
        except Exception as e:
            log(f"  Telegram push failed: {e}")

    # Buttondown 邮件
    bd_key = os.environ.get('BUTTONDOWN_API_KEY')
    if bd_key:
        try:
            subject = ("GOR " + str(gor_output.get("gor_wti")) + " · " + str(gor_output.get("regime", ""))
                       + " · 仓位 " + str(gor_output.get("final_position")) + "% · " + str(gor_output.get("updated", ""))[:10])
            bd_body = msg.replace(chr(10), chr(10) + chr(10))
            req = urllib.request.Request(
                'https://api.buttondown.com/v1/emails',
                data=json.dumps({'subject': subject, 'body': bd_body}).encode('utf-8'),
                headers={'Content-Type': 'application/json', 'Authorization': f'Token {bd_key}'})
            if dry:
                print(f"  [dry] Buttondown: {subject}")
            else:
                with urllib.request.urlopen(req, timeout=20) as r:
                    if r.status in (200, 201):
                        sent.append('buttondown')
        except Exception as e:
            log(f"  Buttondown push failed: {e}")

    if sent:
        log(f"  Push sent via: {', '.join(sent)}")
    elif dry:
        log("  Push dry-run complete (no channels configured for real send)")
    else:
        log("  No push channels configured — skipping (set FEISHU_WEBHOOK / DINGTALK_WEBHOOK / SERVERCHAN_SENDKEY / TELEGRAM_BOT_TOKEN)")
    return sent


if __name__ == '__main__':
    import json as _j
    g = _j.load(open('gor_latest.json', encoding='utf-8'))
    send_daily_push(g)
