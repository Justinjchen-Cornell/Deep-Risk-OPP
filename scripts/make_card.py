# -*- coding: utf-8 -*-
"""Deep-Risk-OPP — 前向注册卡生成器（v2.2 配套，源自延伸研究 #03）

用法: python scripts/make_card.py
输出: 注册卡/注册卡-YYYY-MM-DD-GOR.md（待填写；填完 git commit 即冻结）
"""
import datetime
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from data_pipeline.screener import load_and_compute  # noqa: E402


def plus_days(days):
    return (datetime.date.today() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")


def main():
    gl = json.loads((BASE_DIR / "gor_latest.json").read_text(encoding="utf-8"))
    d = gl.get("data", {})
    gold = d.get("黄金期货", {}).get("price")
    wti = d.get("WTI原油", {}).get("price")
    vix = d.get("VIX恐慌指数", {}).get("price")
    scr = load_and_compute(current_gold=gold, current_oil=wti, current_vix=vix)

    today = datetime.date.today().strftime("%Y-%m-%d")
    cap = int((scr.get("oil_cap_factor") or 0) * 100)
    card = f"""# 前向注册卡 · GOR ／ 编号 GOR-{today} · v2.2

> 规则：**只写一次、提交即冻结**（git commit 即签署）；到期只读对账，不得修改本卡。
> 背景：GOR≥45 = 极端报警器而非概率规律（延伸研究 #01/#02）；恐惧是分水岭。

## 状态（自动填充 ｜ 数据 {gl.get('updated')}）

| 指标 | 数值 |
|---|---|
| GOR(Brent / WTI) | **{gl.get('gor_brent')} / {gl.get('gor_wti')}** ｜ 区间：{gl.get('regime')} |
| 机制筛选器 | **{scr.get('verdict')}**（{scr.get('npass')}/3）→ 油气腿上限 {cap}% |
| 拆腿 | 金 {scr.get('d_gold')} ／ 油 {scr.get('d_oil')} → {scr.get('leg')} |
| 恐慌签名 | VIX {scr.get('vix')} vs 阈值 {scr.get('vix_thr')} → {'恐慌' if scr.get('s2') else '平静'} |
| 油分位（滚动 10 年） | {scr.get('oil_pctl')} |

## 我的预测（待填写 ｜ 提交前写完）

- **P1**：未来 12 个月末，GOR 落在 ____ 至 ____ 区间，把握 ____%；
- **P2**：若未来 6 个月内 GOR 回落至 <40，主因预计是（油涨／金跌／两者）：____；
- **P3**：对「油回归」逻辑，我的行动是（参与／观察／放弃）：____。

## 判据

- 命中条件：____ ｜ 失败条件：____

## 签署与对账

- 签署方式：填完预测后 `git commit`（提交即冻结，之后不得修改本文件）
- 对账日：6 个月后（{plus_days(183)}）、12 个月后（{plus_days(365)}）
- 对账规则：只读本卡；结果写入 `注册卡/对账记录.md`
"""
    out = BASE_DIR / "注册卡" / f"注册卡-{today}-GOR.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(card, encoding="utf-8")
    print(f"注册卡已生成: {out.name}")
    print(f"  筛选器: {scr.get('verdict')} ({scr.get('npass')}/3) ｜ 油气腿上限: {cap}% ｜ leg={scr.get('leg')}")


if __name__ == "__main__":
    main()
