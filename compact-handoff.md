# 交接摘要 · 2026-08-13 · Deep-Risk-OPP

---

## 1. 当前目标与阶段

**阶段**: 产品化完成 → 进入推广期

**核心目标**: 将GOR金油比框架从"个人研究工具"转变为"有影响力的公开产品"。

**产品现状**:
- 线上站点已上线: `justinjchen-cornell.github.io/Deep-Risk-OPP/`
- 结构: 语言选择页 → zh/ + en/ 双语Hub → 6个功能页
- Dashboard每日自动更新（GitHub Actions → 数据管道 → 推送JSON → Pages自动刷新）
- GitHub仓库已重构（frameworks/ + docs/ + scripts/ 分层）
- 品牌统一: Justinjchen（陈嘉已全部替换）

**市场定位**（关键战略决策）: 独立宏观研究品牌，对标Tavi Costa / Lyn Alden，**不做**散户选股工具（daily_stock_analysis的赛道）。

---

## 2. 关键技术决策与已排除方案

| 决策 | 选择 | 排除的方案 |
|------|------|-----------|
| 产品形态 | GitHub Pages静态站 | 自建服务器/Streamlit云部署 |
| 设计系统 | Cyberpunk Terminal HUD (ui-ux-pro-max输出) | Light mode、渐变卡片风格 |
| 语言方案 | 独立zh//en/双Hub | 单页i18n切换（有重复问题）、机器翻译全部框架 |
| Logo | 决策看板风格截图 | 抽象SVG图形（旧logo.svg已弃用） |
| 硬止损逻辑 | v2.1动态止损（60日SMA×0.85+供需冲击区分） | 静态$75规则（已废弃但保留fallback） |
| 赛道 | 宏观研究品牌 | 个股分析工具（学DSA会死——不同市场） |
| 数据源 | FRED+akshare+yfinance+Adanos四源 | Alpha Vantage（已排除，多余） |
| 框架翻译 | 只翻4个核心框架英文版 | 全部翻译（维护成本过高） |
| 文档组织 | frameworks//docs/分层 | 根目录平铺（已重构） |

---

## 3. 重要文件改动

### 代码核心
- `run.py` (1272行) — 修复3个BUG: ①分配比例缩放(components sum=100%) ②GOR 43-47过渡带(消除18%仓位跳变) ③get_gor_blend()新增
- `config.py` — v2.1动态止损参数（HARD_STOP_MA_PERIOD=60, MULTIPLIER=0.85, GOR_SUPPLY_SHOCK_RISE=0.05, WTI_ABSOLUTE_FLOOR=60）
- `wti_history.json` — 回溯填充至11天（原3天），动态止损需30+天数据
- `dashboard.html` — 重建（Cyberpunk风格+Fira Code+霓虹光晕），fetch gor_latest.json实时渲染

### 站点
- `index.html` — 语言选择落地页
- `zh/index.html` / `en/index.html` — 分离的6卡片Hub
- `en/decision-board.html` / `capital-flows.html` / `hedge-playbook.html` — 英文三页（新建，~6KB each）

### 文档
- `README.md` — 重构（一句话定位+Live Site链接+新文件结构树）
- `docs/track-record.md` — 实盘记录（6对1错1待定，含认错）
- `docs/promo-pack.md` — 四平台首发文案
- `docs/system_dissection_v3.md` — 系统解剖（给deepseek的审查简报）
- `docs/code_review_2026-08.md` — 首轮审查报告（4BUG+3ISSUE）
- `handoff-2026-08-13.md` — 完整交接文档

### 品牌
- `logo.png` — 决策看板风格（三卡片：GOR 57.1/仓位条/资本流）
- 38处"陈嘉"→"Justinjchen"（18文件）

### 工作流
- `.github/workflows/pages.yml` — Pages自动部署
- `.github/workflows/daily.yml` — 每日数据更新（已存在）

---

## 4. 未决问题与风险

### 风险
1. **动态止损尚未生效** — wti_history仅11天，需积累到30+天（约8月底）。此前系统走$75静态fallback。
2. **run.py单文件1272行** — 待拆分为modes/包（P1）
3. **gor_daily与weekly_data_pull重复70%** — 待合并（P1）
4. **风控日历节点过期** — SpaceX IPO窗口(2026.06)等节点未更新
5. **无单元测试** — 任何改动可能悄悄破坏逻辑
6. **yfinance限速** — DXY偶发缺失（有fallback）
7. **中文HTML页面** — 含大量硬编码中文，维护成本高

### 安全
- 旧PAT（github_pat_11BK...）在聊天中出现过 → **建议立即在GitHub撤销**
- 所有API key仅存本地.env，不入库（GitHub推保护已验证拦截）

---

## 5. 下一步任务

### 本周（推广启动）
1. 🔴 **撤销旧PAT** → 生成最小权限新PAT
2. 🔴 **雪球首发** — 文案在docs/promo-pack.md，标题《金油比57.1：一个数字告诉你油什么时候便宜》
3. 🟠 **LinkedIn发布GOR Pulse #004** — linkedin/GOR_Pulse_Weekly_004_short.md（2,728字符）
4. 🟠 **HelloGitHub提交自荐** — hellogithub.com免费

### 后续（技术进化）
5. run.py拆分为modes/包（deepseek-v4-pro可接手，审查简报已备好）
6. 单元测试pytest（3个纯函数：get_gor_zone / check_dynamic_hard_stop / get_allocation）
7. 回测覆盖2000-2026全周期
8. 情绪数据(Adanos)并入主JSON

### 给deepseek-v4-pro的输入
- 读 `docs/code_review_2026-08.md`（4BUG已修复，验证修复质量）
- 读 `docs/system_dissection_v3.md`（v3.0架构方案）
- 按handoff第八节启动提示词执行

---

**关键约束**: 不改GOR单比率哲学（品牌核心）；数据契约gor_latest.json结构不变；所有输出中英双语。