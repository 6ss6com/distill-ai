"""
每日股票分析 Cron Job 脚本
每天 8:30 自动跑 → 飞书推送信号

用法:
  python stock_report.py
  (由 OpenClaw Cron 调用)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

import joinquant_api as jq

def build_report(results: dict) -> str:
    """构建飞书消息"""
    lines = ["📊 **每日A股信号晨报**\n"]
    
    # 筛选结果
    if 'screened' in results:
        lines.append("🔥 **价值股筛选 Top5**\n")
        lines.append("| 股票 | PE | 股息率 |")
        lines.append("|------|-----|--------|")
        for s in results['screened'][:5]:
            name = s.get('name', s.get('code', ''))
            pe = f"{s.get('pe_ratio', 0):.1f}"
            div = f"{s.get('dividend_ratio', 0):.2f}%"
            lines.append(f"| {name} | {pe} | {div} |")
        lines.append("")
    
    # AI 分析
    skip_codes = ['screened']
    for code, r in results.items():
        if code in skip_codes:
            continue
        name_map = {
            '600519.XSHG': '贵州茅台', '601088.XSHG': '中国神华',
            '600036.XSHG': '招商银行', '601166.XSHG': '兴业银行',
            '601398.XSHG': '工商银行', '600900.XSHG': '长江电力',
        }
        name = name_map.get(code, code)
        signal = r.get('signal', 'N/A')
        score = r.get('score', 0)
        trend = r.get('trend', 'N/A')
        summary = r.get('summary', '')
        val = r.get('valuation', {})
        pe = f"{val.get('pe', 'N/A')}"
        div = f"{val.get('dividend', 'N/A')}%"
        
        emoji = '🟢' if '看多' in signal else ('🔴' if '看空' in signal else '🟡')
        lines.append(f"{emoji} **{name}** ({code})\n"
                    f"   信号:{signal} {score}/10 | 趋势:{trend}\n"
                    f"   PE={pe} | 股息={div}\n"
                    f"   {summary}\n")
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("=== 每日股票分析 ===")
    
    # 跑分析
    results = jq.full_workflow()
    
    # 构建报告
    report = build_report(results)
    print("\n" + report)
    
    # 保存到文件，供 Cron 投递
    report_path = Path(__file__).parent / "distill_ai" / "stock_report.md"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"\n报告已保存: {report_path}")
    
    # 打印原始文本（供飞书投递读取）
    with open(report_path, "r", encoding="utf-8") as f:
        print("\n--- REPORT START ---")
        print(f.read())
        print("--- REPORT END ---")