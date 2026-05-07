"""
DistillAI Memory System - 人格记忆 + 对话历史
每个Persona都有独立的记忆，跨session持续
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import hashlib


class PersonaMemory:
    """
    单个人格的记忆系统

    层级:
    1. 对话历史 (最近N轮对话)
    2. 重要事件 (跨session记住的关键信息)
    3. 用户画像 (和这个人格对话过的用户偏好)
    """

    def __init__(self, persona_name: str, memory_dir: str = None):
        self.persona_name = persona_name
        base = Path(memory_dir) if memory_dir else Path.home() / ".openclaw" / "workspace" / "distill-ai" / "memory"
        self.memory_dir = base / persona_name
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.memory_dir / "history.json"
        self.events_file = self.memory_dir / "events.json"
        self.user_file = self.memory_dir / "users.json"
        self._history: List[Dict] = self._load(self.history_file, [])
        self._events: List[Dict] = self._load(self.events_file, [])
        self._users: Dict[str, Dict] = self._load(self.user_file, {})

    def _load(self, path: Path, default):
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return default

    def _save(self, path: Path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ===== 对话历史 =====
    def add_turn(self, user: str, message: str, reply: str, metadata: dict = None):
        """添加一轮对话"""
        self._history.append({
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "user_msg": message,
            "reply": reply,
            "metadata": metadata or {}
        })
        # 保留最近50轮
        if len(self._history) > 50:
            self._history = self._history[-50:]
        self._save(self.history_file, self._history)

    def get_history(self, last_n: int = 10) -> List[Dict]:
        """获取最近N轮对话"""
        return self._history[-last_n:]

    def get_history_prompt(self, last_n: int = 10) -> str:
        """生成历史对话字符串（用于填充context window）"""
        history = self.get_history(last_n)
        if not history:
            return ""
        lines = []
        for turn in history:
            lines.append(f"用户: {turn['user_msg']}")
            lines.append(f"{self.persona_name}: {turn['reply']}")
        return "\n".join(lines[-last_n * 2:])

    # ===== 重要事件 =====
    def add_event(self, event_type: str, content: str, importance: int = 1):
        """记录重要事件"""
        self._events.append({
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "content": content,
            "importance": importance
        })
        self._events.sort(key=lambda x: x["importance"], reverse=True)
        if len(self._events) > 100:
            self._events = self._events[:100]
        self._save(self.events_file, self._events)

    def get_events(self, types: List[str] = None) -> List[Dict]:
        """获取事件，可按类型过滤"""
        if not types:
            return self._events
        return [e for e in self._events if e["type"] in types]

    # ===== 用户画像 =====
    def update_user(self, user_id: str, preferences: dict):
        """更新用户画像"""
        if user_id not in self._users:
            self._users[user_id] = {"first_seen": datetime.now().isoformat()}
        self._users[user_id].update(preferences)
        self._users[user_id]["last_seen"] = datetime.now().isoformat()
        self._save(self.user_file, self._users)

    def get_user(self, user_id: str) -> Optional[Dict]:
        return self._users.get(user_id)

    # ===== 记忆摘要 =====
    def summarize(self) -> str:
        """生成记忆摘要（用于system prompt）"""
        events = self.get_events()[:5]
        history = self.get_history()[-3:]
        summary_parts = []

        if events:
            summary_parts.append("## 这个角色记得的重要事件\n")
            for e in events:
                summary_parts.append(f"- [{e['timestamp'][:10]}] {e['content']}")

        if history:
            summary_parts.append("\n## 最近对话\n")
            for h in history:
                summary_parts.append(f"用户: {h['user_msg'][:60]}...")
                summary_parts.append(f"{self.persona_name}: {h['reply'][:60]}...")

        return "\n".join(summary_parts) if summary_parts else ""


class ConversationContext:
    """
    单次对话的上下文管理器

    管理: 历史消息 + 工具调用 + 思考追踪 + 情感状态
    """

    def __init__(self, persona: str, user_id: str = "default", max_turns: int = 20):
        self.persona = persona
        self.user_id = user_id
        self.max_turns = max_turns
        self.messages: List[Dict] = []  # {"role": "user"/"assistant", "content": str}
        self.tool_calls: List[Dict] = []
        self.thinking_steps: List[str] = []
        self.emotion: Optional[str] = None
        self._memory = PersonaMemory(persona)

    def add_message(self, role: str, content: str, metadata: dict = None):
        """添加消息"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
        if len(self.messages) > self.max_turns * 2:
            # 保留system + 最近N轮
            self.messages = self.messages[:2] + self.messages[-(self.max_turns * 2):]

    def add_tool_call(self, tool: str, args: dict, result: str):
        """记录工具调用"""
        self.tool_calls.append({
            "tool": tool,
            "args": args,
            "result": result[:200] if result else "",  # 截断
            "timestamp": datetime.now().isoformat()
        })

    def add_thinking(self, step: str):
        self.thinking_steps.append(step)

    def set_emotion(self, emotion: str):
        self.emotion = emotion

    def get_messages_for_llm(self) -> List[Dict]:
        """获取用于LLM的历史消息（不包含工具调用细节）"""
        return [{"role": m["role"], "content": m["content"]} for m in self.messages]

    def save_to_memory(self):
        """保存到持久化记忆"""
        if self.messages:
            last = self.messages[-1]
            if last["role"] == "assistant":
                # 保存最后一轮
                prev = self.messages[-2] if len(self.messages) >= 2 else None
                if prev and prev["role"] == "user":
                    self._memory.add_turn(
                        user=self.user_id,
                        message=prev["content"],
                        reply=last["content"],
                        metadata={"tool_calls": len(self.tool_calls)}
                    )

    def full_summary(self) -> str:
        """生成完整上下文摘要"""
        parts = []
        if self.tool_calls:
            parts.append("工具调用记录: " + ", ".join(t["tool"] for t in self.tool_calls[-3:]))
        if self.thinking_steps:
            parts.append("思考: " + " -> ".join(self.thinking_steps[-3:]))
        if self.emotion:
            parts.append(f"用户情绪: {self.emotion}")
        return " | ".join(parts) if parts else ""


def memory_summary(persona: str) -> str:
    """快速获取某人格的记忆摘要"""
    m = PersonaMemory(persona)
    return m.summarize()