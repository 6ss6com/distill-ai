"""
JoinQuant 数据 + 仿真交易接口
聚宽 (JoinQuant) - 国内最全量化数据平台

注册: https://www.joinquant.com
开通: https://www.joinquant.com/default/index/sdk
数据权限: 2025-01-27 ~ 2026-02-03 (试用版时间范围)
"""

import jqdatasdk as jq
from datetime import datetime, timedelta
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from minimax_client import structured_chat, chat

# 聚宽账号
JQ_USERNAME = "15868328768"
JQ_PASSWORD = "Jfl@1222"


def auth():
    """连接聚宽"""
    try:
        jq.auth(JQ_USERNAME, JQ_PASSWORD)
        print(f"[JoinQuant] 已连接: {JQ_USERNAME}")
        return True
    except Exception as e:
        print(f"[JoinQuant] 连接失败: {e}")
        return False


def get_stock_price(stock_code: str, days: int = 30) -> pd.DataFrame:
    """
    获取股票历史价格
    stock_code: '600519.XSHG' (上证) 或 '399001.XSHE' (深证)
    """
    try:
        end = datetime.now()
        # 数据范围限制: 2025-01-27 ~ 2026-02-03
        # 试用版数据范围: 2025-01-27 ~ 2026-02-03
        end_str = '2026-02-03'
        start = (datetime(2026, 2, 3) - timedelta(days=days*2)).strftime('%Y-%m-%d')
        if start < '2025-01-27':
            start = '2025-01-27'
        
        df = jq.get_price(stock_code, start_date=start, end_date=end_str,
                         frequency='daily', fq='pre')
        
        # 技术指标
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma10'] = df['close'].rolling(10).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        df['pct'] = df['close'].pct_change() * 100
        df['volume_pct'] = df['volume'].pct_change() * 100
        
        return df.tail(days)
    except Exception as e:
        print(f"[JoinQuant] 获取 {stock_code} 失败: {e}")
        return pd.DataFrame()


def get_valuation(stock_code: str) -> dict:
    """获取估值数据"""
    try:
        q = jq.query(jq.valuation).filter(jq.valuation.code == stock_code)
        fd = jq.get_fundamentals(q, date='2026-02-03')
        if fd is not None and len(fd) > 0:
            row = fd.iloc[0]
            return {
                'pe': row.get('pe_ratio', 0),
                'pb': row.get('pb_ratio', 0),
                'dividend': row.get('dividend_ratio', 0),
                'ps': row.get('ps_ratio', 0),
            }
    except Exception as e:
        print(f"[JoinQuant] 估值查询失败: {e}")
    return {}


def get_financials(stock_code: str) -> dict:
    """获取财务指标"""
    try:
        q = jq.query(jq.indicator).filter(jq.indicator.code == stock_code)
        fd = jq.get_fundamentals(q, date='2026-02-03')
        if fd is not None and len(fd) > 0:
            row = fd.iloc[0]
            return {
                'roe': row.get('roe', 0),
                'gross_margin': row.get('gross_profit_margin', 0),
                'net_margin': row.get('net_profit_margin', 0),
                'eps': row.get('eps', 0),
            }
    except Exception as e:
        print(f"[JoinQuant] 财务查询失败: {e}")
    return {}


def screen_value_stocks() -> pd.DataFrame:
    """
    价值投资选股: 低PE + 高股息 + 高ROE
    聚焦: 银行、电力、煤炭、交通运输
    """
    # 已知高股息股票池
    candidates = {
        '601088.XSHG': '中国神华',   # 煤炭龙头,股息高
        '600036.XSHG': '招商银行',   # 银行龙头,稳健
        '601166.XSHG': '兴业银行',   # 银行,股息高
        '601398.XSHG': '工商银行',   # 国有行,稳定
        '601318.XSHG': '中国平安',   # 保险龙头
        '601288.XSHG': '农业银行',   # 国有行,稳定
        '601939.XSHG': '建设银行',   # 国有行
        '600019.XSHG': '宝钢股份',   # 钢铁
        '600028.XSHG': '中国石化',   # 石化
        '600900.XSHG': '长江电力',   # 电力,稳定高股息
        '601088.XSHG': '中国神华',
        '601818.XSHG': '光大银行',
        '600900.XSHG': '长江电力',
        '601985.XSHG': '中国核电',
        '600795.XSHG': '国电电力',
        '600690.XSHG': '海尔智家',
        '601668.XSHG': '中国建筑',
        '600585.XSHG': '海螺水泥',
    }
    
    try:
        codes = list(candidates.keys())
        q = jq.query(
            jq.valuation.code,
            jq.valuation.pe_ratio,
            jq.valuation.pb_ratio,
            jq.valuation.dividend_ratio,
        ).filter(
            jq.valuation.code.in_(codes),
            jq.valuation.pe_ratio > 0,
            jq.valuation.pe_ratio < 20,
            jq.valuation.dividend_ratio > 3,
        ).order_by(jq.valuation.dividend_ratio.desc())

        fd = jq.get_fundamentals(q, date='2026-02-03')
        if fd is not None and len(fd) > 0:
            fd['name'] = fd['code'].map(candidates)
            return fd
    except Exception as e:
        print(f"[JoinQuant] 选股失败: {e}")
    return pd.DataFrame()


def analyze_stock(stock_code: str, stock_name: str = None) -> dict:
    """
    完整股票分析: 价格 + 估值 + 财务 + AI综合判断
    """
    # 获取数据
    price_df = get_stock_price(stock_code, 20)
    val = get_valuation(stock_code)
    fin = get_financials(stock_code)
    
    if price_df.empty:
        return {"error": "无法获取数据"}
    
    latest = price_df.iloc[-1]
    name = stock_name or stock_code
    
    # AI 综合分析
    prompt = f"""你是专业股票分析师。请分析 {name}({stock_code}) 的投资价值。

【近期价格走势】
{price_df[['close','ma5','ma10','pct']].tail(10).round(2).to_string()}

【最新价】{latest['close']:.2f}
【5日均线】{latest['ma5']:.2f} | 【10日均线】{latest['ma10']:.2f}
【涨跌幅】{latest['pct']:.2f}%

【估值数据】
PE={val.get('pe', 'N/A'):.1f} | PB={val.get('pb', 'N/A'):.2f} | 股息率={val.get('dividend', 'N/A'):.2f}%

【财务数据】
ROE={fin.get('roe', 'N/A'):.1f}% | 毛利率={fin.get('gross_margin', 'N/A'):.1f}% | 净利率={fin.get('net_margin', 'N/A'):.1f}%

请给出JSON格式分析:
{{
  "signal": "强烈看多/看多/中性/看空/强烈看空",
  "score": 1-10,
  "trend": "上升/下降/震荡",
  "style": "短线/波段/长线",
  "key_levels": {{"支撑": "价格", "阻力": "价格"}},
  "risks": ["风险1", "风险2"],
  "summary": "30字以内总结"
}}"""

    result = structured_chat(prompt, {
        "signal": "信号",
        "score": "评分",
        "trend": "趋势",
        "style": "投资风格",
        "key_levels": "关键价位",
        "risks": "风险",
        "summary": "总结"
    })
    
    result['price_data'] = {
        'latest': float(latest['close']),
        'ma5': float(latest['ma5']) if pd.notna(latest['ma5']) else None,
        'ma10': float(latest['ma10']) if pd.notna(latest['ma10']) else None,
        'pct': float(latest['pct']),
    }
    result['valuation'] = val
    result['financials'] = fin
    
    return result


def full_workflow(stock_codes: list = None) -> dict:
    """
    完整选股+分析工作流
    """
    if not auth():
        return {"error": "聚宽连接失败"}
    
    results = {}
    
    # 1. 筛选高股息价值股
    print("\n=== 价值股筛选 ===")
    df = screen_value_stocks()
    if not df.empty:
        print(df.to_string(index=False))
        results['screened'] = df.to_dict('records')
    
    # 2. 分析候选股票
    targets = stock_codes or ['600519.XSHG', '601088.XSHG', '600036.XSHG']
    print(f"\n=== AI 个股分析 ===")
    
    for code in targets:
        name_map = {
            '600519.XSHG': '贵州茅台',
            '601088.XSHG': '中国神华',
            '600036.XSHG': '招商银行',
            '601166.XSHG': '兴业银行',
            '601398.XSHG': '工商银行',
            '600900.XSHG': '长江电力',
        }
        name = name_map.get(code, code)
        print(f"\n--- {name}({code}) ---")
        r = analyze_stock(code, name)
        if 'error' not in r:
            print(f"  信号: {r.get('signal')} | 评分: {r.get('score')}/10 | 趋势: {r.get('trend')}")
            print(f"  估值: PE={r['valuation'].get('pe', 'N/A')} | 股息={r['valuation'].get('dividend', 'N/A')}%")
            print(f"  财务: ROE={r['financials'].get('roe', 'N/A')}% | 毛利率={r['financials'].get('gross_margin', 'N/A')}%")
            print(f"  总结: {r.get('summary')}")
            results[code] = r
    
    return results


if __name__ == "__main__":
    print("=== JoinQuant 完整工作流 ===\n")
    r = full_workflow()
    print("\n\n=== 工作流完成 ===")