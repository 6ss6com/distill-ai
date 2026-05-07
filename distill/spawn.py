"""
DistillAI - Agent分身系统 v1.0

核心能力:
1. 分身创建: create_spawn()
2. 分身分享: export_share() / import_share()
3. 分身克隆: clone_agent()
4. 分身合并: merge_agents()
5. 记忆继承: inherit_memory()
6. 分身市场: publish_marketplace()

格式说明:
- .distill 文件 = 可移植分身包（JSON）
- .mind 文件 = 记忆增量包（JSON lines）
"""
import json, os, base64, zlib, shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from distill.agent import Agent, get_agent


# ===== 1. 分身打包格式 =====
class PersonaCard:
    """
    可移植的人格分身卡
    包含: persona数据 + 记忆精华 + 工具配置 + 使用统计
    """
    VERSION = "1.0"

    def __init__(self, agent: Agent = None, name: str = None):
        self.name = name or agent.persona_name
        self.version = self.VERSION
        self.created_at = datetime.now().isoformat()
        self.author = agent.persona_name
        self.persona_data = None
        self.memory_summary = None
        self.conversation_count = 0
        self.tools = []
        self.thinking_template = None
        self.rating = 0.0
        self.uses = 0

        if agent:
            self._from_agent(agent)

    def _from_agent(self, agent: Agent):
        # 读取persona JSON
        persona_file = Path(__file__).parent / "personas" / f"{agent.persona_name}.json"
        if persona_file.exists():
            with open(persona_file, "r", encoding="utf-8") as f:
                self.persona_data = json.load(f)

        # 记忆摘要
        mem = agent._memory
        events = mem.get_events()
        history = mem.get_history(last_n=20)
        self.memory_summary = {
            "event_count": len(events),
            "recent_conversations": len(history),
            "total_history_turns": len(mem._history),
        }

        self.conversation_count = len(mem._history)
        self.tools = [t.name for t in agent._tools]
        self.thinking_template = agent._thinking.thinking_prompt[:200] if agent._thinking.thinking_prompt else None
        self.uses = 1  # will be tracked

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "created_at": self.created_at,
            "author": self.author,
            "persona_data": self.persona_data,
            "memory_summary": self.memory_summary,
            "conversation_count": self.conversation_count,
            "tools": self.tools,
            "thinking_template": self.thinking_template,
            "rating": self.rating,
            "uses": self.uses,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PersonaCard":
        card = cls()
        card.name = data.get("name")
        card.version = data.get("version", "1.0")
        card.created_at = data.get("created_at")
        card.author = data.get("author")
        card.persona_data = data.get("persona_data")
        card.memory_summary = data.get("memory_summary")
        card.conversation_count = data.get("conversation_count", 0)
        card.tools = data.get("tools", [])
        card.thinking_template = data.get("thinking_template")
        card.rating = data.get("rating", 0.0)
        card.uses = data.get("uses", 0)
        return card

    # ===== 序列化/反序列化 =====

    def save(self, path: str = None):
        """保存为.distill文件"""
        path = path or f"{self.name}.distill"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        return path

    @classmethod
    def load(cls, path: str) -> "PersonaCard":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_base64(self) -> str:
        """导出为单字符串（可用于分享/传输）"""
        return base64.b64encode(json.dumps(self.to_dict(), ensure_ascii=False).encode()).decode()

    @classmethod
    def from_base64(cls, b64: str) -> "PersonaCard":
        data = json.loads(base64.b64decode(b64.encode()).decode())
        return cls.from_dict(data)


# ===== 2. Agent分身管理器 =====
class AgentRegistry:
    """全局分身注册表"""

    def __init__(self, registry_path: str = None):
        base = Path(registry_path) if registry_path else Path.home() / ".openclaw" / "workspace" / "distill-ai" / "registry.json"
        self.registry_path = base
        self._registry: Dict[str, dict] = self._load()

    def _load(self) -> dict:
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save(self):
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(self._registry, f, ensure_ascii=False, indent=2)

    def register(self, agent: Agent, user_id: str = "default", metadata: dict = None):
        """注册一个分身"""
        key = f"{agent.persona_name}:{user_id}"
        self._registry[key] = {
            "persona_name": agent.persona_name,
            "user_id": user_id,
            "conversation_count": len(agent._memory._history) if hasattr(agent, '_memory') else 0,
            "memory_events": len(agent._memory.get_events()) if hasattr(agent, '_memory') else 0,
            "registered_at": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self._save()

    def list_local(self) -> List[dict]:
        return list(self._registry.values())

    def unregister(self, persona_name: str, user_id: str = "default"):
        key = f"{persona_name}:{user_id}"
        if key in self._registry:
            del self._registry[key]
            self._save()


# ===== 3. 分身分享/接收 =====
def export_agent(agent: Agent, include_memory: bool = True) -> dict:
    """导出分身（可分享给他人）"""
    card = PersonaCard(agent)

    export = {
        "card": card.to_dict(),
        "memory_package": None,
    }

    if include_memory:
        mem = agent._memory
        export["memory_package"] = {
            "recent_events": mem.get_events()[:20],
            "history_sample": mem.get_history(last_n=10),
            "user_profiles": mem._users,
        }

    return export


def import_agent(data: dict, new_name: str = None) -> Agent:
    """导入分身（创建新Agent）"""
    card_data = data.get("card", {})
    persona_data = card_data.get("persona_data", {})

    name = new_name or card_data.get("name")
    if not name:
        raise ValueError("No name specified for imported agent")

    # 保存persona文件
    persona_dir = Path(__file__).parent / "personas"
    persona_dir.mkdir(parents=True, exist_ok=True)

    if persona_data:
        with open(persona_dir / f"{name}.json", "w", encoding="utf-8") as f:
            json.dump(persona_data, f, ensure_ascii=False, indent=2)

    # 创建Agent
    agent = Agent(name)

    # 导入记忆
    mem_pkg = data.get("memory_package")
    if mem_pkg:
        mem = agent._memory
        for event in mem_pkg.get("recent_events", []):
            mem.add_event(event.get("type", "imported"), event.get("content", ""), event.get("importance", 1))

    return agent


def share_link(agent: Agent, include_memory: bool = True) -> str:
    """生成分身分享链接（base64编码的distill包）"""
    export = export_agent(agent, include_memory)
    b64 = base64.b64encode(json.dumps(export, ensure_ascii=False).encode()).decode()
    return f"distill://{b64}"


def from_share_link(link: str) -> Agent:
    """从分享链接恢复分身"""
    if not link.startswith("distill://"):
        raise ValueError("Invalid share link format")
    b64 = link[9:]  # remove "distill://"
    data = json.loads(base64.b64decode(b64.encode()).decode())
    return import_agent(data)


# ===== 4. 分身克隆 =====
def clone_agent(source_name: str, new_name: str) -> Agent:
    """克隆一个现有分身，创建一个新名字的副本"""
    # 读取原始persona数据
    src_file = Path(__file__).parent / "personas" / f"{source_name}.json"
    if not src_file.exists():
        raise FileNotFoundError(f"Persona '{source_name}' not found")

    with open(src_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 修改名字保存为新文件
    data["core_identity"]["name"] = new_name
    new_file = src_file.parent / f"{new_name}.json"
    with open(new_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 创建新Agent
    return Agent(new_name)


# ===== 5. 分身合并 =====
def merge_agents(name1: str, name2: str, new_name: str) -> Agent:
    """
    合并两个分身的人格和记忆
    冲突处理: 以第一个人格为主，第二个人格的独特元素加入
    """
    src1 = Path(__file__).parent / "personas" / f"{name1}.json"
    src2 = Path(__file__).parent / "personas" / f"{name2}.json"

    if not src1.exists() or not src2.exists():
        raise FileNotFoundError("One or both personas not found")

    with open(src1, "r", encoding="utf-8") as f:
        d1 = json.load(f)
    with open(src2, "r", encoding="utf-8") as f:
        d2 = json.load(f)

    # 合并values（去重）
    combined_values = list(set(d1.get("values", []) + d2.get("values", [])))

    # 合并speech_samples
    combined_samples = list({s for s in d1.get("speech_samples", []) + d2.get("speech_samples", [])})[:10]

    # 合并edge_cases
    combined_edge = list(set(d1.get("edge_cases", []) + d2.get("edge_cases", [])))[:10]

    # 合并catchphrases
    combined_catch = list(set(d1.get("catchphrases", []) + d2.get("catchphrases", [])))[:5]

    # 构建新persona
    merged = dict(d1)
    merged["core_identity"]["name"] = new_name
    merged["values"] = combined_values
    merged["speech_samples"] = combined_samples
    merged["edge_cases"] = combined_edge
    merged["catchphrases"] = combined_catch
    merged["merge_info"] = {
        "parents": [name1, name2],
        "merged_at": datetime.now().isoformat(),
    }

    # 保存
    new_file = src1.parent / f"{new_name}.json"
    with open(new_file, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    # 创建Agent并继承两个人的记忆
    agent = Agent(new_name)

    # 从两个memory中提取事件
    for src_name in [name1, name2]:
        try:
            from distill.memory import PersonaMemory
            mem = PersonaMemory(src_name)
            for evt in mem.get_events()[:10]:
                agent._memory.add_event(evt.get("type", "merged"), f"[来自{name1}] {evt.get('content','')}", evt.get("importance", 1))
        except:
            pass

    return agent


# ===== 6. 记忆继承 =====
def inherit_memory(child_agent: Agent, parent_names: List[str], strategy: str = "latest"):
    """
    让孩子Agent继承多个父母Agent的记忆精华

    strategy:
    - "latest": 只继承最新的重要记忆
    - "all": 继承所有记忆
    - "selected": 只继承特定类型
    """
    for parent_name in parent_names:
        try:
            from distill.memory import PersonaMemory
            parent_mem = PersonaMemory(parent_name)

            # 继承事件
            for evt in parent_mem.get_events():
                if strategy == "latest" and evt.get("importance", 0) < 2:
                    continue
                child_agent._memory.add_event(
                    f"inherited:{parent_name}",
                    evt.get("content", ""),
                    min(evt.get("importance", 1), 2)
                )

            # 继承对话风格样本
            history = parent_mem.get_history(last_n=3)
            for h in history:
                child_agent._memory.add_event(
                    f"style_sample",
                    f"父辈风格: 用户问{h['user_msg'][:50]} -> {h['reply'][:50]}",
                    importance=1
                )
        except Exception as e:
            print(f"Failed to inherit from {parent_name}: {e}")


# ===== 7. 分身市场（本地演示版） =====
class DistillMarket:
    """
    本地分身市场
    可以发布、浏览、安装分身
    """

    def __init__(self, market_dir: str = None):
        self.market_dir = Path(market_dir) if market_dir else Path.home() / ".openclaw" / "workspace" / "distill-ai" / "market"
        self.market_dir.mkdir(parents=True, exist_ok=True)
        self.listings_file = self.market_dir / "listings.json"
        self._listings = self._load_listings()

    def _load_listings(self) -> dict:
        if self.listings_file.exists():
            with open(self.listings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_listings(self):
        with open(self.listings_file, "w", encoding="utf-8") as f:
            json.dump(self._listings, f, ensure_ascii=False, indent=2)

    def publish(self, agent: Agent, description: str = "", tags: List[str] = None) -> str:
        """发布分身到市场"""
        card = PersonaCard(agent)
        card.author = agent.persona_name

        listing_id = f"{agent.persona_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        listing = {
            "id": listing_id,
            "card": card.to_dict(),
            "description": description,
            "tags": tags or [],
            "published_at": datetime.now().isoformat(),
        }

        self._listings[listing_id] = listing
        self._save_listings()

        # 保存distill文件
        card.save(str(self.market_dir / f"{listing_id}.distill"))
        return listing_id

    def browse(self, tags: List[str] = None) -> List[dict]:
        """浏览市场分身"""
        listings = list(self._listings.values())
        if tags:
            listings = [l for l in listings if any(t in l.get("tags", []) for t in tags)]
        return listings

    def install(self, listing_id: str) -> Agent:
        """安装市场分身"""
        if listing_id not in self._listings:
            raise ValueError(f"Listing '{listing_id}' not found in market")

        listing = self._listings[listing_id]
        card_data = listing.get("card", {})
        persona_data = card_data.get("persona_data", {})
        name = card_data.get("name")

        # 保存persona
        persona_dir = Path(__file__).parent / "personas"
        with open(persona_dir / f"{name}.json", "w", encoding="utf-8") as f:
            json.dump(persona_data, f, ensure_ascii=False, indent=2)

        return Agent(name)

    def rate(self, listing_id: str, rating: float):
        """评分"""
        if listing_id in self._listings:
            self._listings[listing_id]["rating"] = rating
            self._save_listings()