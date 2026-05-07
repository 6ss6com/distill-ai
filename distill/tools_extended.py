"""
DistillAI Extended Tools - 第二批人格专属工具

基于用户反馈（"补充更多人格的专业工具"）新增：
- code_interpreter: Python代码执行（幽灵黑客/禅师）
- unit_converter: 单位换算（距离/重量/货币）
- translate: 简易翻译（CN/EN/JP）
- health_check: 健康检查（BMI/基础代谢等）
- timer_info: 计时器/番茄钟信息
- habit_suggest: 习惯建议
- wisdom_lookup: 名人名言/智慧金句
- schedule_helper: 日程安排建议
- emoji_mood: 情绪emoji生成
"""
from distill.tools import Tool, execute_tool, TOOL_REGISTRY, get_tool, list_tools
import json, re, random, math
from datetime import datetime, timedelta


# ===== 代码执行工具 =====
def _code_run(code: str, language: str = "python") -> str:
    """执行Python代码（安全沙箱，仅限简单计算）"""
    try:
        safe_builtins = {
            'abs': abs, 'min': min, 'max': max, 'len': len,
            'range': range, 'int': int, 'float': float, 'str': str,
            'bool': bool, 'list': list, 'dict': dict, 'tuple': tuple,
            'sum': sum, 'round': round, 'sorted': sorted, 'enumerate': enumerate,
            'zip': zip, 'map': map, 'filter': filter,
            'math': math,
        }
        # 只允许简单表达式，禁用import/os/exec/eval
        dangerous = ['import', 'os', 'sys', 'exec', 'eval', 'open', 'file', '__', 'lambda']
        if any(d in code for d in dangerous):
            return json.dumps({"status": "error", "msg": "禁止使用该关键字"})

        result = eval(code, {"__builtins__": safe_builtins})
        return json.dumps({"status": "ok", "result": str(result), "language": language})
    except Exception as e:
        return json.dumps({"status": "error", "msg": str(e)})


# ===== 单位换算 =====
def _unit_convert(value: float, from_unit: str, to_unit: str) -> str:
    """单位换算"""
    conversions = {
        # 长度
        "km_mile": 0.621371, "mile_km": 1.60934,
        "m_ft": 3.28084, "ft_m": 0.3048,
        "cm_inch": 0.393701, "inch_cm": 2.54,
        "kg_lb": 2.20462, "lb_kg": 0.453592,
        "g_oz": 0.035274, "oz_g": 28.3495,
        # 温度
        "c_f": lambda c: c * 9/5 + 32,
        "f_c": lambda f: (f - 32) * 5/9,
        # 货币（粗略）
        "cny_usd": 0.14, "usd_cny": 7.24,
        "cny_jpy": 21.5, "jpy_cny": 0.046,
    }
    key = f"{from_unit}_{to_unit}"
    if key in conversions:
        fn = conversions[key]
        if callable(fn):
            result = fn(value)
        else:
            result = value * fn
        return json.dumps({"from": f"{value}{from_unit}", "to": round(result, 4), "status": "ok"})
    return json.dumps({"status": "error", "msg": f"不支持的换算: {from_unit}->{to_unit}"})


# ===== 翻译工具 =====
def _translate(text: str, target_lang: str = "en") -> str:
    """简易翻译（基于简单规则+词典）"""
    # 简单中英词典
    simple_dict = {
        "你好": "hello", "谢谢": "thank you", "再见": "goodbye",
        "我": "I", "你": "you", "是": "is", "不": "not",
        "今天": "today", "明天": "tomorrow", "昨天": "yesterday",
        "开心": "happy", "难过": "sad", "好的": "ok",
    }
    # 如果文本包含中文字符，尝试翻译
    has_cn = any('\u4e00' <= c <= '\u9fff' for c in text)
    if has_cn and target_lang == "en":
        result = []
        for word, eng in simple_dict.items():
            if word in text:
                result.append(eng)
        if result:
            return json.dumps({"original": text, "translated": " ".join(result), "status": "ok"})
        return json.dumps({"original": text, "translated": text, "status": "partial", "note": "部分翻译"})
    return json.dumps({"original": text, "status": "ok"})


# ===== 健康检查 =====
def _health_check(age: int = None, weight_kg: float = None, height_cm: float = None, gender: str = "male") -> str:
    """BMI/基础代谢计算"""
    if not all([weight_kg, height_cm]):
        return json.dumps({"status": "error", "msg": "需要提供体重(kg)和身高(cm)"})
    try:
        h_m = height_cm / 100
        bmi = weight_kg / (h_m * h_m)
        # BMI分类
        if bmi < 18.5:
            cat = "偏瘦"
        elif bmi < 24:
            cat = "正常"
        elif bmi < 28:
            cat = "偏胖"
        else:
            cat = "肥胖"
        # 基础代谢 (Mifflin-St Jeor)
        if gender == "male":
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
        return json.dumps({
            "bmi": round(bmi, 1),
            "category": cat,
            "bmr_kcal": round(bmr),
            "weight": weight_kg, "height": height_cm,
            "status": "ok"
        })
    except Exception as e:
        return json.dumps({"status": "error", "msg": str(e)})


# ===== 计时器 =====
def _timer_info(focus_minutes: int = 25, break_minutes: int = 5) -> str:
    """番茄钟/计时器信息"""
    now = datetime.now()
    focus_end = now + timedelta(minutes=focus_minutes)
    break_end = focus_end + timedelta(minutes=break_minutes)
    return json.dumps({
        "session_duration_min": focus_minutes,
        "break_duration_min": break_minutes,
        "focus_end": focus_end.strftime("%H:%M"),
        "break_end": break_end.strftime("%H:%M"),
        "tip": "专注25分钟，休息5分钟，这是最科学的番茄工作法",
        "status": "ok"
    })


# ===== 习惯建议 =====
def _habit_suggest(goal: str = None) -> str:
    """根据目标给出习惯建议"""
    suggestions = {
        "早起": ["每天同一时间起床（包括周末）", "睡前不看手机", "早晨喝一杯水", "做5分钟拉伸"],
        "健康": ["每天走8000步", "不喝含糖饮料", "晚上7点后不进食", "每天7小时睡眠"],
        "学习": ["每天阅读30分钟", "做笔记输出", "教别人是最好的学习", "间隔复习"],
        "投资": ["每月固定日期投资", "只投闲钱", "分散投资", "不天天看账户"],
        "冥想": ["每天同一时间", "从5分钟开始", "关注呼吸", "不要评判自己"],
    }
    if not goal:
        goal = random.choice(list(suggestions.keys()))
    tips = suggestions.get(goal, suggestions["健康"])
    return json.dumps({"goal": goal, "suggestions": tips, "status": "ok"})


# ===== 名人名言 =====
WISDOM_DB = [
    {"text": "别人贪婪时恐惧，别人恐惧时贪婪", "author": "巴菲特", "topic": "投资"},
    {"text": "知道和悟到之间，隔着一场生活", "author": "禅师", "topic": "成长"},
    {"text": "第一性原理，不要偷懒", "author": "马斯克", "topic": "创新"},
    {"text": "Stay hungry, stay foolish", "author": "乔布斯", "topic": "人生"},
    {"text": "好生意是好价格的基础", "author": "巴菲特", "topic": "投资"},
    {"text": "山还是山，水还是水", "author": "禅师", "topic": "禅"},
    {"text": "知行合一", "author": "王阳明", "topic": "哲学"},
    {"text": "人间真实，吃瓜第一", "author": "沙雕网友", "topic": "生活"},
]

def _wisdom_lookup(topic: str = None) -> str:
    """名人名言/智慧金句查询"""
    if topic:
        matches = [w for w in WISDOM_DB if topic in w["topic"]]
        if matches:
            w = random.choice(matches)
            return json.dumps({"text": w["text"], "author": w["author"], "topic": w["topic"], "status": "ok"})
    w = random.choice(WISDOM_DB)
    return json.dumps({"text": w["text"], "author": w["author"], "topic": w["topic"], "status": "ok"})


# ===== 日程建议 =====
def _schedule_suggest(time_available: int = 60) -> str:
    """根据可用时间给出日程安排建议"""
    now = datetime.now()
    schedule = []
    remaining = time_available
    if remaining >= 60:
        schedule.append({"activity": "深度工作", "minutes": 45, "end": (now + timedelta(minutes=45)).strftime("%H:%M")})
        remaining -= 50  # 含休息
    if remaining >= 25:
        schedule.append({"activity": "快速处理", "minutes": 20, "end": (now + timedelta(minutes=remaining)).strftime("%H:%M")})
    return json.dumps({"available_minutes": time_available, "schedule": schedule, "status": "ok"})


# ===== 情绪emoji =====
def _emoji_mood(emotion: str = None) -> str:
    """根据情绪返回emoji"""
    emoji_map = {
        "happy": ["😊", "😄", "🙌", "🥳", "✨"],
        "sad": ["😢", "😔", "🥺", "💔", "😞"],
        "angry": ["😠", "😤", "💢", "🤬", "😡"],
        "anxious": ["😰", "😥", "😓", "💫", "😵"],
        "excited": ["🤩", "😆", "🎉", "🔥", "💥"],
        "calm": ["😌", "🧘", "🍃", "☮️", "🌿"],
        "neutral": ["😐", "🤔", "💭", "👀", "😐"],
        "default": ["💬", "👋", "🤝", "✨", "🌟"],
    }
    if not emotion:
        emotion = random.choice(list(emoji_map.keys()))
    emojis = emoji_map.get(emotion, emoji_map["default"])
    return json.dumps({"emotion": emotion, "emoji": random.choice(emojis), "alternatives": emojis[:3], "status": "ok"})


# ===== 注册扩展工具 =====
def register_extended_tools():
    """将扩展工具注册到TOOL_REGISTRY"""
    new_tools = {
        "code_run": Tool(
            name="code_run",
            description="执行Python代码（仅限安全计算，禁止import/os/exec）",
            args_schema='{"code": "Python代码，如 abs(-5) + 10", "language": "python"}',
            result_format="执行结果: {result}",
            persona_tags=["幽灵黑客", "禅师", "巴菲特"],
            emotional=False
        ).register(_code_run),

        "unit_convert": Tool(
            name="unit_convert",
            description="单位换算（长度/重量/温度/货币）",
            args_schema='{"value": 100, "from_unit": "km", "to_unit": "mile"}',
            result_format="换算结果: {result}",
            persona_tags=["沙雕网友", "幽灵黑客"],
            emotional=False
        ).register(_unit_convert),

        "translate": Tool(
            name="translate",
            description="简易翻译（CN/EN/JP）",
            args_schema='{"text": "要翻译的文本", "target_lang": "en"}',
            result_format="翻译: {result}",
            persona_tags=["沙雕网友", "银发法师"],
            emotional=False
        ).register(_translate),

        "health_check": Tool(
            name="health_check",
            description="健康检查（BMI计算+基础代谢）",
            args_schema='{"age": 30, "weight_kg": 70, "height_cm": 175, "gender": "male"}',
            result_format="BMI: {result}",
            persona_tags=["树洞姐姐", "深夜食堂老板"],
            emotional=True
        ).register(_health_check),

        "timer_info": Tool(
            name="timer_info",
            description="番茄钟/计时器信息",
            args_schema='{"focus_minutes": 25, "break_minutes": 5}',
            result_format="{result}",
            persona_tags=["禅师", "巴菲特"],
            emotional=True
        ).register(_timer_info),

        "habit_suggest": Tool(
            name="habit_suggest",
            description="习惯建议（早起/健康/学习/投资/冥想）",
            args_schema='{"goal": "早起"}',
            result_format="建议: {result}",
            persona_tags=["禅师", "树洞姐姐", "深夜食堂老板"],
            emotional=True
        ).register(_habit_suggest),

        "wisdom_lookup": Tool(
            name="wisdom_lookup",
            description="名人名言/智慧金句查询",
            args_schema='{"topic": "投资"}',
            result_format="{result}",
            persona_tags=["巴菲特", "禅师", "Ancient Philosopher"],
            emotional=True
        ).register(_wisdom_lookup),

        "schedule_helper": Tool(
            name="schedule_helper",
            description="日程安排建议（根据可用时间）",
            args_schema='{"time_available": 60}',
            result_format="日程: {result}",
            persona_tags=["巴菲特", "禅师", "沙雕网友"],
            emotional=False
        ).register(_schedule_suggest),

        "emoji_mood": Tool(
            name="emoji_mood",
            description="情绪emoji生成",
            args_schema='{"emotion": "happy"}',
            result_format="{result}",
            persona_tags=["沙雕网友", "树洞姐姐", "九尾灵狐"],
            emotional=True
        ).register(_emoji_mood),
    }

    for name, tool in new_tools.items():
        TOOL_REGISTRY[name] = tool

    return new_tools


# 自动注册
register_extended_tools()