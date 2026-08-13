"""
Deep-Risk-OPP — 每日管道入口 (P1-2 拆分)
"""
import datetime
from data_pipeline.common import (log, fetch_all, compute_gor, save_gor_json,
    save_capital_flows_json, update_wti_history, generate_alerts,
    update_html_data_blocks, redraw_gor_chart)

def run_daily():
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

    log("✅ 全部更新完成！")
    log("=" * 50)

if __name__ == '__main__':
    run_daily()
