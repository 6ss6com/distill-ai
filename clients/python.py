#!/usr/bin/env python3
"""
DistillAI Client SDK - Python

pip install requests

Usage:
    from distill_client import DistillAIClient
    client = DistillAIClient("http://localhost:5000")
    reply = client.chat("巴菲特", "最近AI很火该投资吗")
"""
import requests
from typing import Optional, List, Dict, Any


class DistillAIClient:
    """
    DistillAI Multi-Language Client - Python版本

    支持:
    - REST API (http://localhost:5000)
    - Webhook模式 (http://localhost:5001)
    - 任意自定义base_url
    """

    def __init__(self, base_url: str = "http://localhost:5000", timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "DistillAI-Python-SDK/2.0"})

    # ===== 基础API =====

    def health(self) -> dict:
        return self.session.get(f"{self.base_url}/health", timeout=5).json()

    # ===== 聊天 =====

    def chat(self, persona: str, message: str, user_id: str = "default") -> str:
        """简单聊天"""
        r = self.session.post(
            f"{self.base_url}/api/chat",
            json={"persona": persona, "message": message, "user_id": user_id},
            timeout=self.timeout
        )
        return r.json().get("reply", "")

    def agent_chat(self, persona: str, message: str, user_id: str = "default") -> dict:
        """
        Agent聊天（带工具+情感+思考）
        返回完整结果: {reply, emotion, tools_used, thinking}
        """
        r = self.session.post(
            f"{self.base_url}/api/agent/chat",
            json={"persona": persona, "message": message, "user_id": user_id},
            timeout=self.timeout
        )
        return r.json()

    # ===== 分身管理 =====

    def spawn_info(self, persona: str) -> dict:
        return self.session.get(f"{self.base_url}/api/spawn/{persona}", timeout=10).json()

    def reset_spawn(self, persona: str, user_id: str = "default") -> dict:
        return self.session.post(
            f"{self.base_url}/api/spawn/{persona}/reset",
            json={"user_id": user_id}, timeout=10
        ).json()

    def clone_persona(self, source: str, new_name: str) -> dict:
        return self.session.post(
            f"{self.base_url}/api/clone",
            json={"source": source, "new_name": new_name}, timeout=10
        ).json()

    def merge_personas(self, name1: str, name2: str, new_name: str) -> dict:
        return self.session.post(
            f"{self.base_url}/api/merge",
            json={"name1": name1, "name2": name2, "new_name": new_name}, timeout=10
        ).json()

    def share_persona(self, persona: str) -> str:
        return self.session.get(f"{self.base_url}/api/share/{persona}", timeout=10).json().get("share_link", "")

    def import_persona(self, link: str, new_name: str = None) -> dict:
        payload = {"link": link}
        if new_name:
            payload["new_name"] = new_name
        return self.session.post(f"{self.base_url}/api/import", json=payload, timeout=10).json()

    # ===== 记忆 =====

    def get_memory(self, persona: str) -> dict:
        return self.session.get(f"{self.base_url}/api/memory/{persona}", timeout=10).json()

    def add_memory(self, persona: str, content: str, event_type: str = "custom", importance: int = 2) -> dict:
        return self.session.post(
            f"{self.base_url}/api/memory/{persona}",
            json={"content": content, "event_type": event_type, "importance": importance},
            timeout=10
        ).json()

    # ===== 市场 =====

    def market_list(self) -> List[dict]:
        return self.session.get(f"{self.base_url}/api/market/list", timeout=10).json().get("listings", [])

    def market_publish(self, persona: str, description: str = "", tags: List[str] = None) -> dict:
        return self.session.post(
            f"{self.base_url}/api/market/publish",
            json={"persona": persona, "description": description, "tags": tags or []},
            timeout=10
        ).json()

    # ===== 对比/辩论 =====

    def compare(self, personas: List[str], question: str) -> dict:
        return self.session.post(
            f"{self.base_url}/api/compare",
            json={"personas": personas, "question": question},
            timeout=self.timeout
        ).json()

    def debate(self, persona1: str, persona2: str, topic: str) -> dict:
        return self.session.post(
            f"{self.base_url}/api/debate",
            json={"persona1": persona1, "persona2": persona2, "topic": topic},
            timeout=self.timeout
        ).json()

    # ===== CCv3 =====

    def export_ccv3(self, persona: str) -> dict:
        return self.session.get(f"{self.base_url}/api/ccv3/{persona}", timeout=10).json()

    # ===== 人格列表 =====

    def list_personas(self) -> List[str]:
        return self.session.get(f"{self.base_url}/api/personas", timeout=10).json().get("personas", [])


# ===== Webhook客户端 =====

class DistillAIWebhook:
    """飞书/Telegram/Discord Webhook客户端"""

    def __init__(self, webhook_url: str = "http://localhost:5001"):
        self.base_url = webhook_url.rstrip("/")
        self.session = requests.Session()

    def feishu(self, text: str, persona: str = "沙雕网友", user_id: str = "feishu_user") -> dict:
        return self.session.post(
            f"{self.base_url}/webhook/feishu",
            json={"content": text, "persona": persona, "sender": {"sender_id": {"open_id": user_id}}},
            timeout=30
        ).json()

    def feishu_receive(self, message: dict, persona: str = "沙雕网友") -> dict:
        """飞书消息接收模式"""
        return self.session.post(
            f"{self.base_url}/webhook/feishu/receive",
            json={"message": message, "persona": persona},
            timeout=30
        ).json()

    def telegram(self, text: str, chat_id: str = None, persona: str = "沙雕网友") -> dict:
        return self.session.post(
            f"{self.base_url}/webhook/telegram",
            json={"message": {"text": text, "chat": {"id": chat_id}, "from": {"id": "user"}}},
            timeout=30
        ).json()

    def discord(self, content: str, user_id: str = None, persona: str = "沙雕网友") -> dict:
        return self.session.post(
            f"{self.base_url}/webhook/discord",
            json={"content": content, "author": {"id": user_id}, "persona": persona},
            timeout=30
        ).json()

    def generic(self, message: str, persona: str = "沙雕网友", user_id: str = "generic") -> dict:
        return self.session.post(
            f"{self.base_url}/webhook/generic",
            json={"message": message, "persona": persona, "user_id": user_id},
            timeout=30
        ).json()


if __name__ == "__main__":
    # Demo
    client = DistillAIClient()
    print("Health:", client.health())
    print("Personas:", client.list_personas()[:5])
    print("Chat:", client.chat("沙雕网友", "你好")[:50])