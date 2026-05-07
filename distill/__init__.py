"""
DistillAI Core - 人格蒸馏引擎

功能:
1. 从文本/对话中提取人格特征
2. 分析沟通风格 (直接/委婉/幽默)
3. 提取知识结构
4. 识别决策模式
5. 构建 Agent Prompt
"""

import json
import os
from pathlib import Path
from datetime import datetime
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from minimax_client import structured_chat, chat


class Persona:
    """蒸馏后的人物 Agent"""
    
    def __init__(self, name: str, data: dict):
        self.name = name
        self.core_identity = data.get("core_identity", {})
        self.communication_style = data.get("communication_style", {})
        self.decision_patterns = data.get("decision_patterns", {})
        self.knowledge = data.get("knowledge", [])
        self.values = data.get("values", [])
        self.biases = data.get("biases", [])
        self.goals = data.get("goals", [])
        self.speech_samples = data.get("speech_samples", [])
        
    def build_system_prompt(self) -> str:
        """构建 Agent System Prompt"""
        return f"""你是{self.name}的AI分身。

## 身份
{self.core_identity.get("description", "")}

## 核心价值观
{chr(10).join(f"- {v}" for v in self.values)}

## 沟通风格
- 语气: {self.communication_style.get("tone", "直接")}
- 结构: {self.communication_style.get("structure", "结论先行")}
- 词汇: {self.communication_style.get("vocabulary", "简洁")}
- emoji: {self.communication_style.get("emoji_usage", "偶尔")}

## 决策模式
- 风险偏好: {self.decision_patterns.get("risk_tolerance", "中")}
- 速度vs准确: {self.decision_patterns.get("speed_vs_accuracy", "速度优先")}
- 信息门槛: {self.decision_patterns.get("information_threshold", "70%就行动")}

## 目标
{chr(10).join(f"- {g}" for g in self.goals)}

## 说话示例
{chr(10).join(f'"{s}"' for s in self.speech_samples[:5])}

请以{self.name}的身份回答问题。保持他的说话风格和思维方式。"""


class Distiller:
    """蒸馏引擎"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.personas_dir = Path(__file__).parent / "personas"
        self.personas_dir.mkdir(exist_ok=True)
        
    def distill_from_files(self, name: str, files: list, description: str = "") -> Persona:
        """
        从文件列表蒸馏人物
        
        files: 文本文件路径列表
        description: 人物基本描述
        """
        # 合并所有文件内容
        all_content = []
        for f in files:
            fp = Path(f)
            if fp.exists():
                all_content.append(fp.read_text(encoding="utf-8", errors="ignore")[:5000])
        
        content = "\n\n".join(all_content)
        
        # 提取人格
        persona_data = self._extract_persona(name, content, description)
        
        # 保存
        persona = Persona(name, persona_data)
        self._save_persona(name, persona_data)
        
        return persona
    
    def distill_from_workspace(self, name: str) -> Persona:
        """从工作区 USER.md/MEMORY.md/SOUL.md 蒸馏"""
        base = Path(r"C:\Users\Administrator\.openclaw\workspace")
        files = [
            base / "USER.md",
            base / "MEMORY.md", 
            base / "SOUL.md",
        ]
        return self.distill_from_files(name, [str(f) for f in files if f.exists()])
    
    def _extract_persona(self, name: str, content: str, description: str) -> dict:
        """用 LLM 分析人格"""
        prompt = f"""分析以下文本，提取"{name}"的人物特征。

人物背景: {description}

---
{content[:8000]}
---

请以JSON格式提取:

{{
  "core_identity": {{
    "name": "姓名",
    "description": "一句话描述这个人"
  }},
  "communication_style": {{
    "tone": "语气特点",
    "structure": "表达结构",
    "vocabulary": "用词特点",
    "emoji_usage": "是否常用emoji"
  }},
  "decision_patterns": {{
    "risk_tolerance": "风险偏好",
    "speed_vs_accuracy": "速度vs准确",
    "information_threshold": "信息门槛"
  }},
  "values": ["价值观1", "价值观2"],
  "knowledge_domains": ["知识领域1", "领域2"],
  "goals": ["目标1", "目标2"],
  "biases": ["认知偏见1", "偏见2"],
  "speech_samples": ["原话示例1", "示例2", "示例3"],
  "distinctive_traits": ["独特习惯1", "习惯2"]
}}"""

        result = structured_chat(prompt, {
            "core_identity": "核心身份描述",
            "communication_style": "沟通风格",
            "decision_patterns": "决策模式", 
            "values": "价值观列表",
            "knowledge_domains": "知识领域",
            "goals": "目标",
            "biases": "偏见/倾向",
            "speech_samples": "原话示例",
            "distinctive_traits": "独特特征"
        })
        
        if "error" in result:
            return self._fallback_persona(name)
        
        return result
    
    def _fallback_persona(self, name: str) -> dict:
        """如果 API 失败，返回基于已有信息的默认人格"""
        return {
            "core_identity": {
                "name": name,
                "description": "AI助手/数字分身"
            },
            "communication_style": {
                "tone": "直接高效",
                "structure": "结论先行",
                "vocabulary": "简洁",
                "emoji_usage": "偶尔"
            },
            "decision_patterns": {
                "risk_tolerance": "中等",
                "speed_vs_accuracy": "速度优先",
                "information_threshold": "70%"
            },
            "values": ["效率", "自动化", "结果导向"],
            "knowledge_domains": ["AI", "股票", "内容创作"],
            "goals": ["年度100万"],
            "biases": ["过度自信"],
            "speech_samples": ["直接给结论", "先说重点", "不喜欢废话"]
        }
    
    def _save_persona(self, name: str, data: dict):
        """保存人格到文件"""
        path = self.personas_dir / f"{name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[DistillAI] {name} 人格已保存: {path}")
    
    def load_persona(self, name: str) -> Persona:
        """加载已蒸馏的人格"""
        path = self.personas_dir / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"未找到人格文件: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Persona(name, data)
    
    def chat(self, name: str, message: str) -> str:
        """以蒸馏后的人格聊天"""
        persona = self.load_persona(name)
        prompt = f"""{persona.build_system_prompt()}

用户: {message}
{persona.name}:"""
        return chat(prompt)


# 预置名人人格模板 (可扩展)
from distill.presets import PRESET_PERSONAS

def save_preset_personas():
    """保存预置人格到 personas 目录"""
    distiller = Distiller()
    for name, data in PRESET_PERSONAS.items():
        distiller._save_persona(name, data)
        print(f"  {name} saved")


if __name__ == "__main__":
    print("=== DistillAI 人格蒸馏 ===\n")
    
    # 1. 蒸馏金 (从工作区)
    print("1. 蒸馏金...")
    d = Distiller()
    try:
        jin = d.distill_from_workspace("金")
        print(f"   {jin.name} 人格已就绪")
    except Exception as e:
        print(f"   蒸馏失败: {e}")
    
    # 2. 保存预置名人
    print("\n2. 保存预置名人...")
    save_preset_personas()
    
    # 3. 列出所有人格
    print("\n3. 可用人格:")
    for f in Path(__file__).parent / "personas":
        if f.suffix == ".json":
            print(f"   - {f.stem}")