"""
DistillAI Tool System - 人格专属工具箱
每个工具包含: name, description, args, result_format, persona_tags

人格使用工具时，保持说话风格和棱角。
"""
from typing import Callable, Dict, List, Any, Optional
import json, re

# ===== 工具基类 =====
class Tool:
    """一个可执行工具"""

    def __init__(
        self,
        name: str,
        description: str,
        args_schema: str = "",
        result_format: str = "",
        persona_tags: List[str] = None,  # 哪些人格适合用这个工具
        emotional: bool = False,  # 是否需要情感化输出
    ):
        self.name = name
        self.description = description
        self.args_schema = args_schema  # JSON格式参数描述
        self.result_format = result_format  # 结果应该如何呈现
        self.persona_tags = persona_tags or []  # e.g. ["巴菲特", "禅师", "沙雕网友"]
        self.emotional = emotional
        self._fn: Optional[Callable] = None

    def register(self, fn: Callable):
        self._fn = fn
        return self

    def execute(self, **kwargs) -> str:
        if not self._fn:
            return f"[Tool '{self.name}' not implemented]"
        try:
            result = self._fn(**kwargs)
            if self.emotional and self.result_format:
                return self.result_format.format(**kwargs, result=result)
            return str(result)
        except Exception as e:
            return f"[Tool error: {e}]"

    def __str__(self):
        return f"Tool({self.name}, tags={self.persona_tags})"


# ===== 内置工具实现 =====
def _stock_query(code: str, name: str = None) -> str:
    """查询股票当前价格和涨跌"""
    try:
        import urllib.request
        # 腾讯行情API
        url = f"https://qt.gtimg.cn/q=sz{code}" if code.startswith("00") else f"https://qt.gtimg.cn/q=sh{code}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = r.read().decode("gbk", errors="replace")
        # 解析数据
        parts = data.split("~")
        if len(parts) > 10:
            price = parts[3]
            change = parts[31]
            pct = parts[32]
            vol = parts[36]
            name_val = parts[1]
            return json.dumps({
                "name": name or name_val,
                "price": price,
                "change": change,
                "change_pct": pct,
                "volume": vol,
                "status": "ok"
            })
        return json.dumps({"status": "error", "msg": "数据解析失败"})
    except Exception as e:
        return json.dumps({"status": "error", "msg": str(e)})


def _news_search(query: str) -> str:
    """搜索新闻/热点"""
    try:
        import urllib.request, json, urllib.parse
        q = urllib.parse.quote(query)
        # 用wttr风格的简单API，或者直接用搜索
        # 这里用 DuckDuckGo instant answer
        url = f"https://api.duckduckgo.com/?q={q}&format=json&no_html=1"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        results = []
        for topic in data.get("RelatedTopics", [])[:5]:
            if "Text" in topic:
                results.append(topic["Text"])
        return json.dumps({"query": query, "results": results[:5], "status": "ok"})
    except Exception as e:
        return json.dumps({"status": "error", "msg": str(e)})


def _calc(expression: str) -> str:
    """数学计算"""
    try:
        # 安全计算（只允许数字和运算符）
        safe_expr = re.sub(r'[^\d\+\-\*\/\.\(\)\s]', '', expression)
        result = eval(safe_expr, {"__builtins__": {}})
        return json.dumps({"expression": safe_expr, "result": result, "status": "ok"})
    except Exception as e:
        return json.dumps({"status": "error", "msg": f"计算错误: {e}"})


def _date_info() -> str:
    """获取当前日期时间信息"""
    from datetime import datetime
    now = datetime.now()
    return json.dumps({
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "weekday": now.strftime("%A"),
        "is_weekend": now.weekday() >= 5,
        "timestamp": now.timestamp()
    })


def _weather(location: str = "Jiaxing") -> str:
    """查询天气"""
    try:
        import urllib.request, json
        url = f"https://wttr.in/{urllib.parse.quote(location)}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        current = data.get("current_condition", [{}])[0]
        return json.dumps({
            "location": location,
            "temp": current.get("temp_C", "?"),
            "condition": current.get("weatherDesc", [{}])[0].get("value", "?"),
            "humidity": current.get("humidity", "?"),
            "status": "ok"
        })
    except Exception as e:
        return json.dumps({"status": "error", "msg": str(e)})


def _web_page(url: str) -> str:
    """获取网页内容摘要"""
    try:
        import urllib.request, re
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
        # 提取纯文本
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:1000]  # 限制长度
    except Exception as e:
        return f"[Error fetching {url}: {e}]"


def _stock_news(stock_code: str = "") -> str:
    """获取个股/市场新闻"""
    try:
        import urllib.request, json, urllib.parse
        q = urllib.parse.quote(stock_code or "A股")
        url = f"https://api.每股收益.com/api/news?keyword={q}&limit=5"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        articles = data.get("data", {}).get("list", [])[:5]
        results = [{"title": a.get("title",""), "time": a.get("time",""), "src": a.get("source","")} for a in articles]
        return json.dumps({"news": results, "status": "ok"})
    except:
        # Fallback: 搜索新闻
        return _news_search(stock_code + " 股票 新闻" if stock_code else "A股 市场")


def _random_choice(options: str) -> str:
    """随机选择（用于决策辅助）"""
    opts = [o.strip() for o in options.split(",") if o.strip()]
    if not opts:
        return json.dumps({"status": "error", "msg": "没有可选项"})
    import random
    chosen = random.choice(opts)
    return json.dumps({"chosen": chosen, "all": opts, "status": "ok"})


def _sentiment_analysis(text: str) -> str:
    """情感分析（用于理解用户情绪）"""
    # 简单的关键词情感判断
    positive = ["开心", "高兴", "喜欢", "满意", "棒", "好", "赞", "感谢", "谢谢", "太好了"]
    negative = ["难过", "伤心", "焦虑", "担心", "害怕", "生气", "讨厌", "失望", "郁闷", "烦"]
    pos_count = sum(1 for w in positive if w in text)
    neg_count = sum(1 for w in negative if w in text)
    if pos_count > neg_count:
        sentiment = "positive"
    elif neg_count > pos_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    return json.dumps({"text": text[:50], "sentiment": sentiment, "pos": pos_count, "neg": neg_count, "status": "ok"})


# ===== 内置工具注册表 =====
def get_tool(name: str) -> Optional[Tool]:
    """获取工具实例"""
    tools = {
        "stock_query": Tool(
            name="stock_query",
            description="查询股票当前价格、涨跌幅、成交量",
            args_schema='{"code": "股票代码，如000001", "name": "股票名称(可选)"}',
            result_format="当前{name}价格: {result}",
            persona_tags=["巴菲特", "禅师", "沙雕网友"],
            emotional=False
        ).register(_stock_query),

        "news_search": Tool(
            name="news_search",
            description="搜索最新新闻和热点事件",
            args_schema='{"query": "搜索关键词"}',
            result_format="最新消息: {result}",
            persona_tags=["沙雕网友", "禅师", "巴菲特"],
            emotional=False
        ).register(_news_search),

        "calc": Tool(
            name="calc",
            description="数学计算（支持+-\\*/和括号）",
            args_schema='{"expression": "算术表达式，如 100*0.07*365"}',
            result_format="计算结果: {result}",
            persona_tags=["巴菲特"],
            emotional=False
        ).register(_calc),

        "date_info": Tool(
            name="date_info",
            description="获取当前日期、时间和星期",
            args_schema="{}",
            result_format="今天是 {result}",
            persona_tags=["沙雕网友", "禅师", "巴菲特"],
            emotional=True
        ).register(_date_info),

        "weather": Tool(
            name="weather",
            description="查询天气",
            args_schema='{"location": "城市名(默认嘉兴)"}',
            result_format="{result}",
            persona_tags=["沙雕网友", "禅师", "树洞姐姐"],
            emotional=True
        ).register(_weather),

        "web_page": Tool(
            name="web_page",
            description="获取网页内容摘要",
            args_schema='{"url": "网页URL"}',
            result_format="[网页内容摘要]\n{result}",
            persona_tags=["巴菲特", "幽灵黑客", "沙雕网友"],
            emotional=False
        ).register(_web_page),

        "stock_news": Tool(
            name="stock_news",
            description="获取股票相关新闻",
            args_schema='{"stock_code": "股票代码(可选)"}',
            result_format="相关新闻: {result}",
            persona_tags=["巴菲特", "禅师"],
            emotional=False
        ).register(_stock_news),

        "random_choice": Tool(
            name="random_choice",
            description="随机选择（用于决策参考）",
            args_schema='{"options": "选项列表，逗号分隔"}',
            result_format="{result}",
            persona_tags=["沙雕网友", "禅师"],
            emotional=True
        ).register(_random_choice),

        "sentiment_analysis": Tool(
            name="sentiment_analysis",
            description="分析用户情感状态",
            args_schema='{"text": "用户说的话"}',
            result_format="[情绪分析] {result}",
            persona_tags=["树洞姐姐", "禅师", "深夜食堂老板"],
            emotional=True
        ).register(_sentiment_analysis),
    }
    return tools.get(name)


# ===== 工具注册表 =====
TOOL_REGISTRY: Dict[str, Tool] = {
    name: get_tool(name) for name in [
        "stock_query", "news_search", "calc", "date_info",
        "weather", "web_page", "stock_news", "random_choice", "sentiment_analysis"
    ]
}


def list_tools(persona_tags: List[str] = None) -> List[Tool]:
    """列出工具，可选按人格标签过滤"""
    tools = list(TOOL_REGISTRY.values())
    if persona_tags:
        tools = [t for t in tools if any(tag in t.persona_tags for tag in persona_tags)]
    return tools


def execute_tool(name: str, **kwargs) -> str:
    """执行工具"""
    tool = TOOL_REGISTRY.get(name)
    if not tool:
        return f"[Unknown tool: {name}]"
    return tool.execute(**kwargs)