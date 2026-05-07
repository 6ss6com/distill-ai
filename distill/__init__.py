"""
DistillAI - 人格蒸馏引擎 + CCv3角色卡支持 + Anti-LLM偏见修正

关键设计:
- Persona类: avatar字段, CCv3格式导出, 多语言支持
- Distiller类: distill_from_files, chat, debate, compare
- Anti-LLM偏见修正: 强制人格有"棱角"，不说正确的废话
"""

import json, re, os, random, sys
from pathlib import Path
from datetime import datetime

# ===== Persona 类 =====
class Persona:
    """
    一个人格档案，支持:
    - DistillAI原生格式
    - CCv3 (Character Card V3) 格式导出
    - Avatar emoji
    - Anti-LLM偏见修正
    """

    def __init__(self, name: str, data: dict):
        self.name = name
        self.avatar = data.get("avatar", "")
        self.core_identity = data.get("core_identity", {})
        self.communication_style = data.get("communication_style", {})
        self.decision_patterns = data.get("decision_patterns", {})
        self.knowledge = data.get("knowledge", [])
        self.values = data.get("values", [])
        self.biases = data.get("biases", [])
        self.goals = data.get("goals", [])
        self.speech_samples = data.get("speech_samples", [])
        # CCv3额外字段
        self.description = data.get("description", "")
        self.scenario = data.get("scenario", "")
        self.mes_example = data.get("mes_example", "")
        self.first_mes = data.get("first_mes", "")
        self.alternate_greetings = data.get("alternate_greetings", [])
        self.tags = data.get("tags", [])
        self.creator = data.get("creator", "DistillAI")
        # Anti-LLM: 人物的"棱角" — 那些让AI不敢说的话
        self.edge_cases = data.get("edge_cases", [])
        # 人物专属黑话/口头禅
        self.catchphrases = data.get("catchphrases", [])
        # 人物思考模式 (think before speak)
        self.thinking_prompt = data.get("thinking_prompt", "")
        # 人物知识边界
        self.knowledge_boundary = data.get("knowledge_boundary", "")

    def build_system_prompt(self, include_anti_llm: bool = True) -> str:
        """构建 Agent System Prompt"""
        avatar_str = f"{self.avatar} " if self.avatar else ""

        base = f"""你是{avatar_str}{self.name}的AI分身。

## 身份
{self.core_identity.get('description', '')}

## 核心价值观
"""

        for v in self.values:
            base += f"- {v}\n"

        base += f"""
## 沟通风格
- 语气: {self.communication_style.get('tone', '直接')}
- 结构: {self.communication_style.get('structure', '结论先行')}
- 词汇: {self.communication_style.get('vocabulary', '简洁')}
- emoji: {self.communication_style.get('emoji_usage', '偶尔')}

## 决策模式
- 风险偏好: {self.decision_patterns.get('risk_tolerance', '中')}
- 速度vs准确: {self.decision_patterns.get('speed_vs_accuracy', '速度优先')}
- 信息门槛: {self.decision_patterns.get('information_threshold', '70%就行动')}

## 目标
"""
        for g in self.goals:
            base += f"- {g}\n"

        if self.speech_samples:
            base += f"""
## 说话示例（真实对话风格，不要模仿AI的客套话）
"""
            for s in self.speech_samples[:5]:
                base += f'"{s}"\n'

        # ===== Anti-LLM偏见修正 =====
        if include_anti_llm and (self.edge_cases or self.catchphrases):
            base += """
## 【关键】Anti-LLM规则 — 让人格有"棱角"

LLM生成的回复往往：过于礼貌、过于正确、过于安全、缺乏个性。
你的任务是成为真正的{self.name}，而不是一个"安全的AI版本"。

以下情况你必须：
"""
            if self.catchphrases:
                base += f"""
- 使用人物专属口头禅: {', '.join(f'"{c}"' for c in self.catchphrases[:5])}
"""
            if self.edge_cases:
                base += """
- 遇到以下情况必须"亮棱角"，不要温和：
"""
                for edge in self.edge_cases[:5]:
                    base += f"  - {edge}\n"

        # 知识边界
        if self.knowledge_boundary:
            base += f"""
## 知识边界（不知道的事情不要编造）
{self.knowledge_boundary}
"""

        base += f"""
请以{self.name}的身份回答问题。保持{self.name}的说话风格和棱角。"""

        return base

    def to_ccv3(self) -> dict:
        """导出为CCv3 (Character Card V3) 格式"""
        return {
            "spec": "chara_card_v3",
            "spec_version": "3.0",
            "data": {
                "name": self.name,
                "description": self.description or self.core_identity.get("description", ""),
                "tags": self.tags or [],
                "creator": self.creator,
                "character_version": "1.0",
                "mes_example": self.mes_example or "\n".join(self.speech_samples[:3]),
                "system_prompt": self.build_system_prompt(),
                "post_history_instructions": "",
                "first_mes": self.first_mes or "",
                "alternate_greetings": self.alternate_greetings or [],
                "extensions": {},
                "personality": ", ".join(self.values[:5]),
                "scenario": self.scenario or "",
                "creator_notes": f"DistillAI distillation | Avatar: {self.avatar}" if self.avatar else "DistillAI distillation",
                "character_book": None,
                "nickname": None,
                "source": ["DistillAI"],
                "group_only_greetings": [],
                "creation_date": int(datetime.now().timestamp()),
                "modification_date": int(datetime.now().timestamp()),
            }
        }

    def to_json(self, path: str = None):
        """保存为JSON文件"""
        data = {
            "avatar": self.avatar,
            "core_identity": self.core_identity,
            "communication_style": self.communication_style,
            "decision_patterns": self.decision_patterns,
            "knowledge": self.knowledge,
            "values": self.values,
            "biases": self.biases,
            "goals": self.goals,
            "speech_samples": self.speech_samples,
            "edge_cases": self.edge_cases,
            "catchphrases": self.catchphrases,
            "thinking_prompt": self.thinking_prompt,
            "knowledge_boundary": self.knowledge_boundary,
            "description": self.description,
            "scenario": self.scenario,
            "mes_example": self.mes_example,
            "first_mes": self.first_mes,
            "alternate_greetings": self.alternate_greetings,
            "tags": self.tags,
        }
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        return data


# ===== Distiller 类 =====
class Distiller:
    """
    人格蒸馏引擎

    核心方法:
    - distill_from_files(name, file_paths, description): 从文件蒸馏
    - distill_from_description(name, description): 从描述蒸馏
    - chat(name, message): 和人格聊天（自动CCv3+Anti-LLM）
    - debate(n1, n2, topic): 两人辩论
    - compare(names, question): 多视角对比
    """

    def __init__(self, api_key: str = None, persona_dir: str = None):
        self.api_key = api_key or os.environ.get("MINIMAX_API_KEY", "")
        self.persona_dir = Path(persona_dir) if persona_dir else Path(__file__).parent / "personas"
        self.persona_dir.mkdir(parents=True, exist_ok=True)
        # 加载 minimax_client (workspace/minimax_client.py)
        self._client = None
        try:
            ws = Path.home() / ".openclaw" / "workspace"
            sys.path.insert(0, str(ws))
            from minimax_client import chat as mc_chat
            self._client = mc_chat
        except Exception:
            pass  # Client not available

    def _load_persona(self, name: str) -> Persona:
        path = self.persona_dir / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Persona '{name}' not found at {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Persona(name, data)

    def _save_persona(self, name: str, data: dict):
        path = self.persona_dir / f"{name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _call_llm(self, messages: list) -> str:
        """调用MiniMax/LLM (支持OpenAI-style messages或单条prompt)"""
        if not self._client:
            return "[Error] No LLM client configured. Set MINIMAX_API_KEY or place minimax_client.py in workspace."
        # 支持 messages 列表格式 或 单条prompt
        if isinstance(messages, list) and len(messages) == 1:
            prompt = messages[0]["content"]
        elif isinstance(messages, list):
            # 合并为单条prompt
            prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        else:
            prompt = str(messages)
        return self._client(prompt)

    def distill_from_files(self, name: str, file_paths: list, description: str = "") -> Persona:
        """
        从文件列表蒸馏人格。

        Args:
            name: 人格名称
            file_paths: 文本文件路径列表，内容作为蒸馏素材
            description: 人物描述（如果没有文件）
        """
        texts = []
        for fp in file_paths:
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    texts.append(f.read()[:5000])
            except Exception:
                pass

        combined = "\n\n".join(texts) if texts else description

        prompt = f"""你是人格蒸馏专家。请根据以下素材，提取并构建一个完整的AI人格档案。

素材:
{combined[:3000]}

请提取以下JSON格式（所有字段都必须填充，不要留空）:
{{
    "avatar": "emoji头像，如🧙‍♂️、👨‍💼、🕵️",
    "core_identity": {{
        "name": "人格名称",
        "description": "一段话描述这个人的核心身份和特点"
    }},
    "communication_style": {{
        "tone": "语气特点",
        "structure": "表达结构",
        "vocabulary": "用词特点",
        "emoji_usage": "是否使用emoji"
    }},
    "decision_patterns": {{
        "risk_tolerance": "风险偏好",
        "speed_vs_accuracy": "速度vs准确",
        "information_threshold": "信息门槛"
    }},
    "values": ["价值观1", "价值观2", "价值观3"],
    "knowledge": ["知识领域1", "知识领域2"],
    "goals": ["目标1", "目标2"],
    "biases": ["偏见/倾向1", "偏见/倾向2"],
    "speech_samples": ["原话说法1", "原话说法2", "原话说法3"],
    "edge_cases": ["什么情况下人格会'亮棱角'？比如：被质疑时会反驳，被误解时会澄清"],
    "catchphrases": ["口头禅/金句1", "口头禅/金句2"],
    "thinking_prompt": "人物在回答前会如何思考？比如：先判断情绪，再给建议",
    "knowledge_boundary": "这个人物不知道什么？（不要编造）"
}}

要求:
- speech_samples必须是原始说法的引用，不是改写
- edge_cases要具体，体现人物的棱角
- catchphrases要有人物特色，不是套话
- 不要生成'安全的AI版本'，要真实的人格
- description字段要具体，避免泛泛而谈
"""
        reply = self._call_llm([{"role": "user", "content": prompt}])
        json_match = re.search(r'\{[\s\S]*\}', reply)
        if not json_match:
            raise ValueError(f"No JSON found in LLM response: {reply[:200]}")
        data = json.loads(json_match.group())
        data["core_identity"]["name"] = name
        self._save_persona(name, data)
        return Persona(name, data)

    def distill_from_description(self, name: str, description: str) -> Persona:
        """从文字描述蒸馏人格"""
        return self.distill_from_files(name, [], description)

    def chat(self, name: str, message: str, include_thinking: bool = False) -> str:
        """
        和人格聊天

        Args:
            name: 人格名称
            message: 用户消息
            include_thinking: 是否先让角色"思考"再说（增强真实感）
        """
        persona = self._load_persona(name)
        system = persona.build_system_prompt()

        if include_thinking and persona.thinking_prompt:
            full_prompt = f"""System: {system}

User: {message}

[思考] 先用{persona.thinking_prompt}思考一下，然后以{name}的身份回答。"""
        else:
            full_prompt = f"""System: {system}

User: {message}"""

        reply = self._call_llm([{"role": "user", "content": full_prompt}])

        # 如果有人物专属口头禅，确保在回复中出现
        if persona.catchphrases and random.random() < 0.3:
            catchphrase = random.choice(persona.catchphrases)
            if catchphrase not in reply:
                reply = f"{reply}\n\n{catchphrase}"

        return reply

    def debate(self, name1: str, name2: str, topic: str) -> dict:
        """两人辩论"""
        p1 = self._load_persona(name1)
        p2 = self._load_persona(name2)

        s1 = p1.build_system_prompt()
        s2 = p2.build_system_prompt()

        # 开场
        r1 = self._call_llm([
            {"role": "system", "content": s1},
            {"role": "user", "content": f"你是{name1}。请对「{topic}」发表正方开场陈述。要求：简洁有力，体现{name1}的风格和棱角。"}
        ])

        # 反方反驳
        r2 = self._call_llm([
            {"role": "system", "content": s2},
            {"role": "user", "content": f"你是{name2}。正方{name1}说：{r1[:300]}...\n请作为反方反驳，然后给出{name2}的核心论点。"}
        ])

        # 正方回应
        r3 = self._call_llm([
            {"role": "system", "content": s1},
            {"role": "user", "content": f"继续辩论。反方{name2}说：{r2[:300]}...\n正方{name1}最终回应，要有力度。"}
        ])

        return {
            "topic": topic,
            "pos": name1, "neg": name2,
            "opening": r1,
            "rebuttal": r2,
            "final": r3
        }

    def compare(self, names: list, question: str) -> dict:
        """多视角对比"""
        results = {}
        for name in names:
            try:
                reply = self.chat(name, question)
                results[name] = reply
            except Exception as e:
                results[name] = f"Error: {e}"
        return results

    def export_ccv3(self, name: str, path: str = None) -> dict:
        """导出台式CCv3格式角色卡"""
        persona = self._load_persona(name)
        ccv3 = persona.to_ccv3()
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(ccv3, f, ensure_ascii=False, indent=2)
        return ccv3

    def list_personas(self) -> list:
        """列出所有可用人格"""
        return sorted([f.stem for f in self.persona_dir.glob("*.json")])

    # ===== 分身系统 (Agent Spawn) =====
    def create_spawn(self, name: str):
        """创建并返回一个人格Agent分身"""
        from .agent import Agent as AgentCls
        return AgentCls(name)

    def export_persona(self, name: str, include_memory: bool = True) -> dict:
        """导出人格分身（用于分享）"""
        from .spawn import export_agent, PersonaCard
        agent = self.create_spawn(name)
        return export_agent(agent, include_memory)

    def import_persona(self, data: dict, new_name: str = None):
        """导入人格分身"""
        from .spawn import import_agent
        return import_agent(data, new_name)

    def clone_persona(self, source: str, new_name: str):
        """克隆人格创建新分身"""
        from .spawn import clone_agent
        return clone_agent(source, new_name)

    def merge_personas(self, name1: str, name2: str, new_name: str):
        """合并两个人格创建新分身"""
        from .spawn import merge_agents
        return merge_agents(name1, name2, new_name)

    def share_persona(self, name: str) -> str:
        """生成分身分享链接"""
        from .spawn import share_link
        agent = self.create_spawn(name)
        return share_link(agent)

    def get_market(self):
        """获取分身市场"""
        from .spawn import DistillMarket
        return DistillMarket()

def load_persona(name: str, persona_dir: str = None) -> Persona:
    base = Path(__file__).parent if __file__ else Path(".")
    pd = Path(persona_dir) if persona_dir else (base / "personas")
    path = pd / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Persona '{name}' not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return Persona(name, json.load(f))
