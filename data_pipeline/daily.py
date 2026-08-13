"""
Deep-Risk-OPP — 每日管道入口 (P1-2 拆分)
"""
import datetime
from data_pipeline.common import (BASE_DIR, log, fetch_all, compute_gor, save_gor_json,
    save_capital_flows_json, update_wti_history, generate_alerts,
    update_html_data_blocks, redraw_gor_chart)

def run_daily():
    from data_pipeline.config_schema import validate_config
    problems = validate_config()
    if problems:
        for msg in problems:
            log("  CONFIG VIOLATION: " + msg)
        log("  FATAL: config schema failed — refusing to run pipeline.")
        raise SystemExit(1)
    log("=" * 50)
    log(f"  📡 Justinjchen投资决策框架 · 自动化数据更新启动")
    log(f"  📅 {datetime.date.today().strftime('%Y-%m-%d')}")
    log("=" * 50)

    log("⏳ Step 1/6: 拉取市场数据...")
    data = fetch_all()

    log("⏳ Step 2/6: 计算 GOR + 仓位分配...")
    gor = compute_gor(data)
    log(f"  GOR(Brent)={gor['gor_brent']} GOR(WTI)={gor['gor_wti']} 仓位={gor['final_position']}%")
    log(f"  油气={gor['allocation']['油气']}% 黄金={gor['allocation']['黄金']}% 现金={gor['allocation']['现金']}%")

    log("⏳ Step 3/6: 保存 JSON 数据文件...")
    gor_output = save_gor_json(data, gor)
    cf_output = save_capital_flows_json(data)

    log("⏳ Step 4/6: 更新 WTI 历史 (动态硬止损)...")
    update_wti_history(gor_output)

    log("⏳ Step 5/6: 熔断器检查...")
    alerts = generate_alerts(gor_output)

    log("⏳ Step 6/6: 更新 HTML 数据+文本 + 重绘图表...")
    update_html_data_blocks(gor_output, cf_output)
    redraw_gor_chart()

    # P3: 自动信号流水账（证伪条款的月度复核数据源）
    try:
        import datetime as _dt
        sig_path = BASE_DIR / "看板日志" / "signal_log_auto.md"
        header = ""
        if not sig_path.exists():
            header = (
                "# 自动信号流水账（证伪条款数据源）" + chr(10) + chr(10) +
                "> 由每日管道自动追加。证伪条款见 docs/track-record.md。" + chr(10) + chr(10) +
                "| 日期 | GOR(WTI) | WTI | 基线$69.87涨幅 | 区间 | 仓位 | 距$107.60 |" + chr(10) +
                "|---|---:|---:|---:|---|---|---:|---|" + chr(10)
            )
        wti_now = gor_output['data']['WTI原油']['price']
        target = 107.60
        pct = (wti_now / 69.87 - 1) * 100 if wti_now else 0
        gap = target - wti_now if wti_now else None
        row = ("| " + _dt.date.today().strftime('%Y-%m-%d') + " | " + f"{gor_output['gor_wti']:.1f} "
               + "| " + f"{wti_now:.2f} | " + f"{pct:+.1f}% | " + gor_output['regime']
               + " | " + f"{gor_output['final_position']}% | " + f"{gap:+.2f} |" + chr(10))
        with open(sig_path, 'a', encoding='utf-8') as f:
            f.write(header + row)
        log("  Signal log appended: 看板日志/signal_log_auto.md")
    except Exception as e:
        log(f"  Signal log append failed: {e}")

    log("✅ 全部更新完成！")
    log("=" * 50)

if __name__ == '__main__':
    run_daily()
