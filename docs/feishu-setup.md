# 飞书告警接入（1 分钟）

> 二维码页面：[feishu-setup.html](feishu-setup.html)（手机扫码打开）
> 安全边界：**webhook 是密钥，不会编进二维码、不会入库。**

## 方式 A · 手动（3 步）

1. **飞书群 → 设置 → 群机器人 → 添加机器人 → 自定义机器人**，复制 Webhook。
2. 打开 [GitHub Secret 页面](https://github.com/Justinjchen-Cornell/Deep-Risk-OPP/settings/secrets/actions/new)：
   - Name: `FEISHU_WEBHOOK`
   - Secret: 粘贴上一步的 Webhook
3. 打开 [Feishu Test](https://github.com/Justinjchen-Cornell/Deep-Risk-OPP/actions/workflows/feishu-test.yml) → **Run workflow**。收到测试消息即接通。

## 方式 B · 一条命令（本机，推荐）

```bash
python scripts/feishu_setup.py
```

向导会：发一条测试消息 → 通过 `gh` 自动写入 GitHub Secret → 提示下一步。
可选：`--save-local` 同时写入本地 `.env`（仅本机，gitignored）。

## 接入后的通道

| 通道 | 用途 | 配置 |
|---|---|---|
| 飞书 | P0/P1 主通道 | `FEISHU_WEBHOOK` |
| GitHub Issue | 零配置兜底（P0/P1 也会开 Issue） | 自动（`GITHUB_TOKEN`） |
| Telegram / 钉钉 / ServerChan | 备用 | 对应 Secrets |

告警只在**状态跃迁**时发送：硬止损、投降签名、合同目标、区间/仓位/裁决变化。设计见 [v3.0-alerting-design.md](v3.0-alerting-design.md)。
