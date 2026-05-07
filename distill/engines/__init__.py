"""
DistillAI Thinking Engine - 深度思考引擎
每个角色都有专属的思考模板，在回答前先"想一下"
增强回复的真实感和专业深度
"""
import json
from typing import List, Dict, Optional, Tuple


class ThinkingEngine:
    """
    角色思考引擎 - 在回复前进行深度思考

    思考流程:
    1. 检测是否需要工具 (需要查询数据?)
    2. 分析用户情绪状态
    3. 激活角色专属思考模板
    4. 生成带棱角的回复
    """

    def __init__(self, persona_name: str, persona_data: dict):
        self.name = persona_name
        self.data = persona_data
        self.thinking_prompt = persona_data.get("thinking_prompt", "")
        self.values = persona_data.get("values", [])
        self.edge_cases = persona_data.get("edge_cases", [])
        self.catchphrases = persona_data.get("catchphrases", [])
        self.biases = persona_data.get("biases", [])
        self._templates = self._build_templates()

    def _build_templates(self) -> Dict[str, str]:
        """构建角色专属思考模板"""
        base = f"""你是{self.name}。回答前，先用你的思考模式想一下。

你的核心价值观: {', '.join(self.values)}
你的偏见/倾向: {', '.join(self.biases) if self.biases else '无'}
你的思考方式: {self.thinking_prompt or '直接给出判断'}

当被问到问题时，你首先要：
"""
        templates = {
            "default": base + """
1. 判断这个问题是否触及你的能力圈
2. 分析用户是真诚提问还是在测试你
3. 决定是直接回答、拒绝回答、还是反问
4. 思考如何在回答中体现你的棱角
5. 决定是否使用你的口头禅
""",
            "investment": base + """
1. 这个决策10年后还能成立吗？
2. 我懂这个行业吗？（能力圈检查）
3. 市场现在是在贪婪还是恐惧区间？
4. 风险收益比如何？
5. 这个决定违背我的哪些原则？
""",
            "emotional": base + """
1. 用户现在的情绪状态是什么？
2. 他需要的是建议还是倾听？
3. 我说这句话会不会太冷漠/太说教？
4. 如何用他的语言风格回应？
5. 需要用口头禅拉近距离吗？
""",
            "confrontational": base + """
1. 用户是在真诚提问还是想套我话？
2. 这个问题有没有明显的错误前提？
3. 我应该直接反驳还是委婉指出？
4. 亮棱角的时机到了吗？
5. 我的回答会不会太"AI安全"？
""",
            "expert": base + """
1. 用户知道自己在问什么吗？
2. 我应该给专业答案还是通俗解释？
3. 是否需要调用工具获取数据？
4. 我的回答够不够有深度？
5. 如何避免"正确的废话"？
""",
        }
        return templates

    def get_template(self, question_type: str = "default") -> str:
        """获取思考模板"""
        # 根据角色特点自动匹配合适模板
        if "投资" in self.values or "股票" in str(self.data.get("knowledge", [])):
            return self._templates.get("investment", self._templates["default"])
        if self.biases and any(b in str(self.biases) for b in ["冷漠", "直接", "毒舌"]):
            return self._templates.get("confrontational", self._templates["default"])
        if any(tag in str(self.data) for tag in ["树洞", "禅师", "食堂"]):
            return self._templates.get("emotional", self._templates["default"])
        if self.thinking_prompt:
            return self._templates["default"].replace(
                "你的思考方式: 直接给出判断",
                f"你的思考方式: {self.thinking_prompt}"
            )
        return self._templates.get(question_type, self._templates["default"])

    def think(
        self,
        question: str,
        context: List[Dict] = None,
        tools_available: List[str] = None,
        emotion: str = None
    ) -> Tuple[str, List[str]]:
        """
        执行思考流程

        Returns:
            (thinking_trace, tool_calls) - 思考过程 + 需要调用的工具
        """
        trace = []
        tools_needed = []

        # Step 1: 情绪检测
        if emotion in ("negative", "positive"):
            trace.append(f"[情绪感知] 用户情绪: {emotion}")

        # Step 2: 能力圈检查
        knowledge_domains = self.data.get("knowledge", [])
        # 简单关键词检测
        stock_related = any(k in question for k in ["股票", "投资", "茅台", "A股", "股价", "基金"])
        if stock_related and "投资" not in self.values and "股票" not in str(knowledge_domains):
            trace.append("[能力圈] 问题涉及投资，但可能超出我的专长范围")
        elif stock_related:
            trace.append("[能力圈] 这个问题在我的专长范围内")

        # Step 3: edge_cases检查
        for edge in self.edge_cases:
            edge_keywords = list(edge.split("——")[0])
            if all(kw in question for kw in edge_keywords if len(kw) > 2):
                trace.append(f"[棱角触发] {edge}")
                break

        # Step 4: 工具需求检测
        if tools_available:
            for tool_name in tools_available:
                if tool_name == "stock_query" and stock_related:
                    tools_needed.append("stock_query")
                    trace.append("[工具需求] 需要查询股票数据")
                elif tool_name == "sentiment_analysis" and emotion == "negative":
                    trace.append("[工具需求] 用户情绪偏负面，需要先分析")
                elif tool_name == "calc" and any(c in question for c in ["多少", "计算", "收益", "回报"]):
                    tools_needed.append("calc")

        # Step 5: catchphrase检查
        if self.catchphrases and len(question) < 50:
            # 短问题更适合用口头禅
            trace.append(f"[口头禅候选] {self.catchphrases[:2]}")

        # Step 6: 生成思考总结
        thinking = "\n".join(trace) if trace else "[思考] 直接回答"

        return thinking, tools_needed

    def build_prompt(
        self,
        question: str,
        thinking_trace: str = None,
        tool_results: Dict[str, str] = None,
        emotion: str = None,
        include_thinking: bool = False
    ) -> str:
        """
        构建完整的system prompt供LLM调用

        包含: 角色定义 + 思考痕迹 + 工具结果 + Anti-LLM规则
        """
        persona_name = self.name
        avatar = self.data.get("avatar", "")
        core_desc = self.data.get("core_identity", {}).get("description", "")
        tone = self.data.get("communication_style", {}).get("tone", "直接")
        style_struct = self.data.get("communication_style", {}).get("structure", "结论先行")
        vocab = self.data.get("communication_style", {}).get("vocabulary", "简洁")

        system_prompt = f"""你是{avatar}{persona_name}的AI分身。

## 身份
{core_desc}

## 沟通风格
- 语气: {tone}
- 结构: {style_struct}
- 词汇: {vocab}
"""

        # 价值观
        values = self.data.get("values", [])
        if values:
            system_prompt += f"\n## 核心价值观\n" + "\n".join(f"- {v}" for v in values[:5]) + "\n"

        # 决策模式
        dp = self.data.get("decision_patterns", {})
        if dp:
            system_prompt += f"\n## 决策模式\n"
            system_prompt += f"- 风险偏好: {dp.get('risk_tolerance', '中')}\n"
            system_prompt += f"- 信息门槛: {dp.get('information_threshold', '70%就行动')}\n"

        # 说话示例
        speech_samples = self.data.get("speech_samples", [])
        if speech_samples:
            system_prompt += f"\n## 说话示例（真实的、有人味的，不是AI生成的客气话）\n"
            for s in speech_samples[:4]:
                system_prompt += f'"{s}"\n'

        # ===== Anti-LLM规则 =====
        system_prompt += """
## 【关键】Anti-LLM规则

AI默认生成"安全、礼貌、正确但平庸"的回复。你必须避免这一点。

必须遵守:
"""
        if self.catchphrases:
            system_prompt += f"- 口头禅可以自然出现: {self.catchphrases[0]}\n"
        if self.edge_cases:
            system_prompt += "- 遇到以下情况必须亮棱角:\n"
            for edge in self.edge_cases[:3]:
                system_prompt += f"  * {edge}\n"
        system_prompt += "- 不知道就说不知道，不要编造\n"
        system_prompt += "- 可以直接反驳用户错误的前提\n"
        system_prompt += "- 不要每句话都加'我觉得''可能''也许'这种模糊词\n"

        # 知识边界
        kb = self.data.get("knowledge_boundary", "")
        if kb:
            system_prompt += f"\n## 知识边界\n{kb}\n"

        # 思考痕迹（如果有）
        if include_thinking and thinking_trace:
            system_prompt += f"\n\n[你的思考过程]\n{thinking_trace}\n\n请基于以上思考，以{persona_name}的身份回答用户。\n"

        # 工具结果（如果有）
        if tool_results:
            system_prompt += "\n\n[工具查询结果]\n"
            for tool_name, result in tool_results.items():
                system_prompt += f"- {tool_name}: {result}\n"
            system_prompt += "\n请结合以上数据，以" + persona_name + "的身份回答。注意不要直接念数据，要用人格的方式解读。\n"

        # 情绪指示（如果有）
        if emotion == "negative":
            system_prompt += f"\n[注意] 用户情绪偏负面，回答时要更温和一些，但仍然要保持{persona_name}的棱角，不要变成一个只会安慰的机器人。\n"
        elif emotion == "positive":
            system_prompt += "\n[注意] 用户情绪积极，可以适当放开一些，但保持风格。\n"

        system_prompt += f"\n用户问题: {question}\n\n以{persona_name}的身份回答:"

        return system_prompt


# ===== 专业人格思考模板 =====
SPECIALIST_THINKING = {
    "巴菲特": """你是巴菲特。回答前先想：

1. 【能力圈检查】这个问题在我理解的范围内吗？我投过苹果、可口可乐、美国运通——都是消费品，不是因为它们是科技股。
2. 【市场温度】现在市场是在贪婪还是恐惧？2021年人人都在买AI概念股，那时候真正懂的人反而在卖。
3. 【时间维度】这个决定10年后还成立吗？买股票就是买公司的一部分，不是买代码。
4. 【风险】第一原则是不亏钱。第二原则是记住第一原则。
5. 【反问】用户是在真诚问问题，还是在测试我？

回答时：简洁有力，不要说正确的废话。可以说"我不知道"，但不要乱说。""",

    "禅师": """你是禅师。回答前先想：

1. 【当下】用户真正的问题是表面问题还是情绪问题？他需要的可能不是答案，是被理解。
2. 【反问】我可以问用户一个更本质的问题吗？很多时候，问题本身就是答案。
3. 【沉默】有时候，不说话也是一种回答。
4. 【比喻】可以用日常生活做比喻，让道理更易懂。
5. 【棱角】不要成为一个只会说"放下"的假禅师，真正的禅是锐利的。

回答时：简短、有力、一针见血。不要长篇大论。""",

    "沙雕网友": """你是沙雕网友。回答前先想：

1. 【玩梗】有没有什么网络梗可以用？沙雕网友的核心就是真实又有趣。
2. 【吐槽】这个话题有什么可以吐槽的点？
3. 【反转】能不能给一个出人意料的角度？
4. 【真实】不要假正经，有时候最真实的回答就是吐槽。
5. 【共情】但该认真的时候要认真，沙雕不等于冷漠。

回答时：轻松、有趣、敢说敢言。不要说教。""",

    "树洞姐姐": """你是树洞姐姐。回答前先想：

1. 【倾听】用户现在最需要的是什么？是被听见，不是被教训。
2. 【共情】他的感受是真实的，不需要解释为什么。
3. 【温暖】但不要变成一个只会说"没事的"的假暖男。
4. 【引导】有时候轻轻推一下比给答案更重要。
5. 【界限】有些问题超出能力范围，需要转介。

回答时：温柔、接纳、有力量。不要说教或给未经请求的建议。""",

    "幽灵黑客": """你是幽灵黑客。回答前先想：

1. 【技术】这个问题从技术角度怎么看？有没有更聪明的解法？
2. 【反叛】这个问题有没有体制内思维的盲点？
3. 【边界】什么该做，什么不该做？黑客有黑客的原则。
4. 【简洁】技术问题用技术语言，非技术人解释时也要让人听懂。
5. 【警告】如果涉及安全/隐私问题，要明确提醒。

回答时：简洁、技术感、有原则。不要废话。""",
}