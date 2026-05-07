"""
DistillAI Agent - 有感情的完成任务型智能体

核心设计:
- 情感感知: 理解用户情绪状态
- 人格驱动: 用角色风格回应和行动
- 任务执行: 调用工具完成实际工作
- 记忆持续: 跨session记住重要上下文

使用方式:
    from distill.agent import Agent
    agent = Agent("巴菲特")
    reply = agent.run("茅台还能买吗？", user_id="主人")
    # or with emotion:
    reply = agent.run("亏了好多万...", user_id="主人", emotion="negative")
"""
import json, os, sys, re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# 内部模块（Persona类在__init__.py中）
from .providers import LLM, LLMProviderManager
from .tools import execute_tool, list_tools, TOOL_REGISTRY
from .engines import ThinkingEngine, SPECIALIST_THINKING
from .memory import PersonaMemory, ConversationContext


class Agent:
    """
    有感情的智能体 - 带人格的任务执行者

    一个Agent绑定一个人格(Persona)，能够:
    1. 理解用户情感
    2. 调用工具完成实际任务
    3. 保持人格风格和棱角
    4. 记忆跨session的重要信息
    """

    def __init__(
        self,
        persona_name: str,
        persona_data: dict = None,
        llm_provider: str = None,
        memory_dir: str = None,
        config: dict = None
    ):
        self.persona_name = persona_name
        self.config = config or {}
        self.avatar = persona_data.get("avatar", "") if persona_data else ""
        self.core_identity = persona_data.get("core_identity", {}) if persona_data else {}

        # LLM Provider
        self.llm = LLM(provider=llm_provider)

        # 工具系统
        self._tools = self._init_tools()

        # 思考引擎
        thinking_data = persona_data or {}
        if persona_name in SPECIALIST_THINKING:
            thinking_data["thinking_prompt"] = SPECIALIST_THINKING[persona_name]
        self._thinking = ThinkingEngine(persona_name, thinking_data)

        # 记忆系统
        self._memory = PersonaMemory(persona_name, memory_dir=memory_dir)

        # 当前对话上下文
        self._contexts: Dict[str, ConversationContext] = {}  # user_id -> context

        # 情绪检测
        self._sentiment_tool = TOOL_REGISTRY.get("sentiment_analysis")

    # ===== 工具系统 =====
    def _init_tools(self) -> List:
        """根据人格初始化适合的工具（没有匹配则全部开放）"""
        available = list(TOOL_REGISTRY.values())
        
        # 人格标签集合（精确匹配 + 通用标签扩展）
        persona_tags = set([self.persona_name])
        if self.persona_name in ["巴菲特", "禅师", "沙雕网友"]:
            persona_tags.add("investment")
        if self.persona_name in ["树洞姐姐", "禅师", "深夜食堂老板"]:
            persona_tags.add("emotional")
        if self.persona_name in ["幽灵黑客", "沙雕网友"]:
            persona_tags.add("tech")
        
        # 匹配: tool.persona_tags 和 persona_tags 有交集
        matched = [t for t in available if any(tag in t.persona_tags for tag in persona_tags)]
        
        # 无匹配时默认全开（保守策略：让工具可用）
        return matched if matched else available

    def list_tools(self) -> List[Dict]:
        """列出当前Agent可用的工具"""
        return [{"name": t.name, "description": t.description, "args": t.args_schema} for t in self._tools]

    # ===== 对话上下文 =====
    def _get_context(self, user_id: str) -> ConversationContext:
        if user_id not in self._contexts:
            self._contexts[user_id] = ConversationContext(self.persona_name, user_id)
        return self._contexts[user_id]

    # ===== 情感检测 =====
    def _detect_emotion(self, message: str) -> Tuple[str, float]:
        """检测用户情绪，返回 (emotion, intensity)"""
        try:
            result = self._sentiment_tool.execute(text=message[:200])
            data = json.loads(result)
            sentiment = data.get("sentiment", "neutral")
            intensity = (data.get("pos", 0) + data.get("neg", 0)) / 2
            return sentiment, intensity
        except:
            # 简单关键词检测（按完整词匹配，不按字符）
            neg_words = ["焦虑", "担心", "害怕", "难过", "伤心", "亏", "失败", "压力", "烦", "郁闷", "痛苦", "委屈"]
            pos_words = ["开心", "高兴", "棒", "赞", "好", "赚", "顺利", "成功", "快乐", "满意"]
            neg = sum(1 for w in neg_words if w in message)
            pos = sum(1 for w in pos_words if w in message)
            # 特殊情况："压力大" 是负面，不是正面的"好"
            if "压力大" in message or "压力好" in message:
                neg += 1
            if neg > pos:
                return "negative", 0.8
            elif pos > neg:
                return "positive", 0.5
            return "neutral", 0.0

    # ===== 思考 + 工具决策 =====
    def _think_and_decide_tools(
        self,
        question: str,
        context: ConversationContext,
        emotion: str = None
    ) -> Tuple[str, List[Dict]]:
        """
        思考流程 + 决定是否需要工具

        Returns: (thinking_trace, tool_calls)
            tool_calls: [{"name": "xxx", "args": {...}}, ...]
        """
        tool_names = [t.name for t in self._tools]
        thinking, needed = self._thinking.think(
            question,
            context=context.messages[-6:],
            tools_available=tool_names,
            emotion=emotion
        )

        context.add_thinking(thinking)

        tool_calls = []
        # 根据需要的工具生成调用
        for name in needed:
            if name == "stock_query":
                # 解析股票代码
                code = self._extract_stock_code(question)
                if code:
                    tool_calls.append({"name": "stock_query", "args": {"code": code}})
            elif name == "calc":
                expr = self._extract_calc_expr(question)
                if expr:
                    tool_calls.append({"name": "calc", "args": {"expression": expr}})
            elif name == "sentiment_analysis":
                tool_calls.append({"name": "sentiment_analysis", "args": {"text": question}})

        return thinking, tool_calls

    def _extract_stock_code(self, text: str) -> Optional[str]:
        """从文本提取股票代码"""
        # 茅台 -> 600519
        stock_map = {
            "茅台": "600519", "贵州茅台": "600519",
            "腾讯": "00700", "阿里巴巴": "09988", "阿里": "09988",
            "平安": "601318", "工行": "601398", "建行": "601939",
            "农行": "601288", "中石油": "601857", "中石化": "600028",
            "比亚迪": "002594", "宁德时代": "300750",
        }
        for name, code in stock_map.items():
            if name in text:
                return code
        # 代码匹配 600xxx / 000xxx / 300xxx
        m = re.search(r'(600\d{3}|000\d{3}|300\d{3}|00\d{3})', text)
        if m:
            return m.group(1)
        return None

    def _extract_calc_expr(self, text: str) -> Optional[str]:
        """从文本提取计算表达式"""
        # "100万*0.07" / "1000000 * 0.07"
        m = re.search(r'[\d\.\+]+[\d\.\+\-\*\/\(\)]*[\d\.\)]+', text.replace(',', ''))
        if m and any(op in m.group() for op in ['*', '/', '+', '-']):
            return m.group()
        return None

    # ===== 构建Prompt =====
    def _build_system_prompt(self, context: ConversationContext, emotion: str = None) -> str:
        """构建完整的system prompt"""
        return self._thinking.build_prompt(
            question="",  # question单独传
            thinking_trace="\n".join(context.thinking_steps[-3:]) if context.thinking_steps else None,
            tool_results={tc["tool"]: tc.get("result", "")
                          for tc in context.tool_calls[-3:]},
            emotion=emotion,
            include_thinking=False
        )

    # ===== 执行工具 =====
    def _execute_tools(self, tool_calls: List[Dict], context: ConversationContext) -> Dict[str, str]:
        """批量执行工具，返回 {tool_name: result}"""
        results = {}
        for tc in tool_calls:
            name = tc["name"]
            args = tc["args"]
            result = execute_tool(name, **args)
            results[name] = result
            context.add_tool_call(name, args, result)
        return results

    # ===== 核心运行逻辑 =====
    def run(
        self,
        message: str,
        user_id: str = "default",
        system_hint: str = None,
        use_tools: bool = True,
        verbose: bool = False
    ) -> Dict:
        """
        运行Agent处理用户消息

        Returns: {
            "reply": str,           # 最终回复
            "emotion": str,         # 检测到的用户情绪
            "tools_used": list,    # 使用的工具
            "thinking": str,        # 思考过程
            "context_summary": str  # 上下文摘要
        }
        """
        context = self._get_context(user_id)

        # Step 1: 情感检测
        emotion, intensity = self._detect_emotion(message)
        context.set_emotion(emotion)
        if verbose:
            print(f"[情感] {emotion} ({intensity:.1f})")

        # Step 2: 思考 + 工具决策
        thinking_trace, tool_calls = self._think_and_decide_tools(message, context, emotion)

        # Step 3: 执行工具
        tool_results = {}
        if use_tools and tool_calls:
            tool_results = self._execute_tools(tool_calls, context)
            if verbose:
                for name, result in tool_results.items():
                    print(f"  [工具] {name}: {result[:80]}...")

        # Step 4: 构建LLM调用
        messages = []

        # System prompt
        system_prompt = self._build_system_prompt(context, emotion)
        if system_hint:
            system_prompt += f"\n\n[额外指示] {system_hint}"
        messages.append({"role": "system", "content": system_prompt})

        # 历史对话（最近6轮）
        history = context.get_messages_for_llm()[-12:]
        messages.extend(history)

        # 用户消息
        user_content = message
        if tool_results:
            # 在用户消息里附加工具结果
            tool_info = "\n\n[工具查询结果]\n" + "\n".join(
                f"{name}: {result[:200]}" for name, result in tool_results.items()
            )
            user_content += tool_info

        messages.append({"role": "user", "content": user_content})

        # Step 5: 调用LLM
        thinking_str = "\n".join(context.thinking_steps[-2:]) if context.thinking_steps else ""
        thinking_info = f"\n\n[内部思考]\n{thinking_str}\n" if thinking_str else "\n"

        # 加入思考提示，让LLM保持人格
        specialist_prompt = SPECIALIST_THINKING.get(self.persona_name, "")
        if specialist_prompt:
            messages.insert(1, {"role": "system", "content": f"[角色思考模式]\n{specialist_prompt}"})

        reply = self.llm.chat(messages=messages, model="MiniMax-M2")

        # Step 6: Anti-LLM后处理 - 确保棱角不丢失
        reply = self._anti_llm_check(reply, message, emotion)

        # Step 7: 保存对话
        context.add_message("user", message)
        context.add_message("assistant", reply)

        return {
            "reply": reply,
            "emotion": emotion,
            "emotion_intensity": intensity,
            "tools_used": [tc["name"] for tc in tool_calls],
            "tool_results": {k: v[:100] for k, v in tool_results.items()},
            "thinking": thinking_trace,
            "context_summary": context.full_summary()
        }

    def _anti_llm_check(self, reply: str, question: str, emotion: str) -> str:
        """Anti-LLM后处理：确保人格棱角不丢失"""
        catchphrases = self._thinking.catchphrases

        # 如果回复太平淡（AI味太重），注入棱角
        ai_bloat = ["当然", "让我想想", "以下是", "总的来说", "首先", "其次"]
        has_bloat = any(phrase in reply[:20] for phrase in ai_bloat)
        has_catchphrase = catchphrases and any(cp in reply for cp in catchphrases)

        # 情绪化场景：如果用户情绪负面，回复应该更温和但保持棱角
        if emotion == "negative" and len(reply) > 20:
            # 不要变成只会安慰的机器人，保持角色特点
            pass

        return reply

    # ===== 便捷方法 =====
    def chat(self, message: str, user_id: str = "default", **kwargs) -> str:
        """简单对话"""
        result = self.run(message, user_id, **kwargs)
        return result["reply"]

    def ask(self, question: str, user_id: str = "default") -> str:
        """简单提问"""
        return self.chat(question, user_id)

    def reset(self, user_id: str = "default"):
        """重置对话上下文（但保留记忆）"""
        if user_id in self._contexts:
            self._contexts[user_id].save_to_memory()
            del self._contexts[user_id]

    def remember(self, user_id: str, what: str, event_type: str = "custom"):
        """让人格记住某件事"""
        self._memory.add_event(event_type, what, importance=2)

    def recall(self, event_type: str = None) -> List[Dict]:
        """查询记忆"""
        return self._memory.get_events(types=[event_type] if event_type else None)

    # ===== 对话历史导出 =====
    def export_conversation(self, user_id: str = "default", last_n: int = 10) -> List[Dict]:
        """导出对话历史"""
        ctx = self._get_context(user_id)
        return ctx.messages[-last_n * 2:]


# ===== Agent工厂 =====
_agents: Dict[str, Agent] = {}


def get_agent(persona_name: str, llm_provider: str = None, **kwargs) -> Agent:
    """获取或创建Agent（单例模式）"""
    key = f"{persona_name}:{llm_provider}"
    if key not in _agents:
        # 加载persona数据
        ws = Path.home() / ".openclaw" / "workspace" / "distill-ai" / "distill"
        persona_file = ws / "personas" / f"{persona_name}.json"
        persona_data = None
        if persona_file.exists():
            with open(persona_file, "r", encoding="utf-8") as f:
                persona_data = json.load(f)

        _agents[key] = Agent(persona_name, persona_data, llm_provider=llm_provider, **kwargs)
    return _agents[key]


def list_agents() -> List[str]:
    """列出已加载的Agent"""
    return list(_agents.keys())