# Code Review #001 · Deep-Risk-OPP v2.1

**审查日期**: 2026-08-13 | **审查范围**: run.py / config.py / scripts | **审查方式**: 静态分析+逻辑推演

---

## 🔴 BUG-1 (P0): 动态硬止损永远不生效

**位置**: `config.py` + `run.py:check_dynamic_hard_stop()` + `wti_history.json`

**证据**: wti_history.json 只有 **3条**记录（需要60条）

```json
[{"date":"2026-07-31"...}, {"date":"2026-08-02"...}, {"date":"2026-08-09"...}]
```

**逻辑链**:
```
check_dynamic_hard_stop() 要求 len(wti_history) >= 30 才计算60日均线
实际只有3条 → 永远走 static_fallback 分支
→ v2.1动态止损形同虚设，系统实际仍在用已废弃的$75静态规则
```

**影响**: 若9月向心坍缩爆发，动态止损的"供给/需求冲击区分"能力不会启动。系统会按旧规则处理——而这正是v2.1升级想要解决的问题。

**修复**: wti_history需要从历史gor-data.json回溯填充（我们有13天历史数据可立即回溯）。或把MA周期降为10天直到积累够60天。

---

## 🔴 BUG-2 (P0): 分配数字不自洽

**位置**: `config.py:BASE_ALLOCATION`

**证据**:
```
"extreme": total=70, oil=38, gold=10, a_shares=12, copper=3, cash=37
求和: 38+10+12+3+37 = 100 ✅ 这个对

但 get_allocation() 中:
  alloc["total"] 被DXY/10Y修正(-10/-10)
  但 oil/gold/cash 的绝对数没有按比例缩放

结果: total=50% 时, oil仍=38% (绝对数)
→ "总仓位50%"与"油38%金10%股12%铜3%现金37%=100%"矛盾
```

**影响**: 决策卡上显示的 total 和 分项加总不一致。框架输出的仓位建议在数学上不可信。

**修复**: total修正后，各分项按比例缩放。或明确 total 是"风险敞口上限"而非"配置之和"。

---

## 🟠 BUG-3 (P1): GOR区间边界仓位跳变

**位置**: `config.py:GOR_ZONES` + `get_allocation()`

**证据**: GOR从44.99→45.01 (0.02的微变):
```
oil: 20% → 38% (跳变+18%)
total: 50% → 70% (跳变+20%)
```

**影响**: 当前GOR(WTI)=57.1、GOR(Brent)=53.9，若Brent向45回归，仓位会在一天内巨幅跳变，造成实际交易中的追涨杀跌。

**修复**: 过渡带设计。例如:
```
GOR 43-47: oil = 20% + (GOR-43)/4 × 18%  (线性过渡)
```

---

## 🟠 BUG-4 (P1): mode_daily读取gor_latest.json，但脚本写的是最新日期文件

**位置**: `run.py:mode_daily()` vs `scripts/gor_daily.py:save_gor_json()`

**证据**: gor_daily.py 同时写 `gor_latest.json` 和 `看板日志/{today}-gor-data.json`。mode_daily 只读 `gor_latest.json`。数据一致 ✅ 无bug。

但 mode_daily 中:
```
gor_data.get("capital_three_flows", {}) 从未被使用
wti_history 读取用 config.WTI_HISTORY = "./wti_history.json"
```
而 gor_daily.py 是否在写wti_history？**未找到写入逻辑**。

**影响**: wti_history只能靠手动/其他脚本维护（当前3条可能是外部模型加的）。

**修复**: gor_daily.py 的 save_gor_json() 应同步 append 到 wti_history.json。

---

## 🟡 ISSUE-5 (P2): 异常吞噬

**位置**: run.py多处 `except: pass` / `except Exception: pass`

**证据**:
```python
try:
    with open(config.WTI_HISTORY, "r", encoding="utf-8") as f:
        wti_history = json.load(f)
except Exception:
    pass   # ← 静默失败
```

**影响**: 数据文件损坏时无任何告警，系统静默降级。

**修复**: 加日志(logging模块)或至少print警告。

---

## 🟡 ISSUE-6 (P2): 硬编码的已过时数据

**位置**: `scripts/gor_daily.py:save_capital_flows_json()`

**证据**:
```python
"ecb": {"balance_sheet": "€3.4万亿", "trend": "6月已加息25bp至2.40%", ...}
"boj": {"balance_sheet": "¥760万亿", "trend": "6月16日加息至1.00%", ...}
"gold_flows": {"2024_total": "1,037吨", ...}
```

**影响**: 8月的数据文件里写着6月的手工数据。与FRED自动拉取的Fed数据形成对比——一半自动一半手工。

**修复**: ECB/BOJ数据接入FRED系列，或明确标注"manual_stale"。

---

## 🟡 ISSUE-7 (P2): 无单元测试

**证据**: 全仓库0个test文件。

**风险**: 任何一次修改都可能悄悄破坏动态止损/GOR判定/分配逻辑而无人知晓。

**修复**: 为以下纯函数建pytest:
- get_gor_zone() — 边界值44.99/45.0/45.01
- check_dynamic_hard_stop() — 供给/需求冲击区分
- get_allocation() — 修正逻辑

---

## 🟢 做得好的地方

1. **config.py 单一配置源** — 所有阈值集中管理，可审计
2. **动态硬止损的设计思想** — 供给/需求冲击区分是正确的进化方向
3. **优先级链明确** — 6层决策逻辑清晰
4. **FRED集成** — 从网页抓取升级到官方API
5. **数据管道三层容错** — FRED→yfinance→web fallback

---

## 📋 审查结论

| 等级 | 数量 | 状态 |
|------|:---:|------|
| 🔴 P0 必须修复 | 2 | BUG-1, BUG-2 |
| 🟠 P1 应该修复 | 2 | BUG-3, BUG-4 |
| 🟡 P2 建议修复 | 3 | ISSUE-5,6,7 |

**系统可用性**: ✅ 可用（日常决策卡能正常输出）
**代码成熟度**: 3/5（快速迭代产物，缺测试和边界处理）
**v3.0进化就绪度**: ✅ 架构清晰，问题已明确定位

---

## 给deepseek-v4-pro的修复优先清单

```
1. 修复BUG-1: wti_history回溯填充（13天历史立即可用）
2. 修复BUG-2: total与分项加总一致
3. 修复BUG-3: GOR过渡带(43-47线性)
4. 修复BUG-4: gor_daily.py追加写wti_history
5. 补pytest测试(3个纯函数)
6. 然后才是模块化重构(run.py拆分)
```
