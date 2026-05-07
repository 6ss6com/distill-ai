"""
DistillAI Memory Layer v2 - Inspired by Mem0/OpenViking

核心设计（借鉴Mem0）:
1. Add → Learn → Retrieve  Pipeline
2. Memory Compression Engine (自动压缩长对话历史)
3. 重要性评分 + 时间衰减
4. 多用户/多Agent记忆隔离 (user_id + agent_name filters)
5. Semantic Search (基于关键词的语义检索)

对齐Mem0的核心概念:
- Mem0: user_id + messages + add() + search()
- DistillAI: user_id + agent_name + memories + add_event() + search()
"""
import json, re, time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class SemanticMemory:
    """
    语义记忆层 - 对齐Mem0的Add/Learn/Retrieve架构

    和 PersonaMemory 的区别:
    - PersonaMemory: 存储原始事件（对话历史+重要事件）
    - SemanticMemory: 存储"学习后的记忆碎片"，带重要性评分、时间戳、标签
    """

    def __init__(self, agent_name: str, user_id: str = "default"):
        self.agent_name = agent_name
        self.user_id = user_id
        base = Path.home() / ".openclaw" / "workspace" / "distill-ai" / "semantic_memory"
        self.dir = base / agent_name / user_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.memories_file = self.dir / "memories.jsonl"
        self._memories: List[Dict] = self._load()

    def _load(self) -> List[Dict]:
        if self.memories_file.exists():
            with open(self.memories_file, "r", encoding="utf-8") as f:
                return [json.loads(line) for line in f if line.strip()]
        return []

    def _save(self):
        with open(self.memories_file, "w", encoding="utf-8") as f:
            for m in self._memories:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")

    # ===== Add → Learn =====
    def add(self, content: str, metadata: dict = None) -> str:
        """
        Add memory (Mem0-style)
        相当于 Mem0.add(messages, user_id)
        """
        memory = {
            "id": f"{self.agent_name}_{self.user_id}_{int(time.time()*1000)}",
            "content": content,
            "created_at": datetime.now().isoformat(),
            "importance": metadata.get("importance", 1) if metadata else 1,
            "tags": metadata.get("tags", []) if metadata else [],
            "source": metadata.get("source", "conversation") if metadata else "conversation",
            "last_accessed": datetime.now().isoformat(),
            "access_count": 0,
            "agent_name": self.agent_name,
            "user_id": self.user_id,
        }
        self._memories.append(memory)
        self._learn()  # Auto-compress after add
        self._save()
        return memory["id"]

    def _learn(self):
        """
        Learn (Mem0-style) - 自动压缩低重要性记忆
        如果记忆超过100条，压缩最旧的低重要性条目
        """
        if len(self._memories) > 100:
            # 按重要性+时间排序，保留最重要的
            self._memories.sort(key=lambda m: (m["importance"], m["created_at"]), reverse=True)
            self._memories = self._memories[:80]  # 保留80条

    # ===== Retrieve (Search) =====
    def search(self, query: str, limit: int = 5, filters: dict = None) -> List[Dict]:
        """
        Search memories (Mem0-style)
        相当于 Mem0.search(query, filters={"user_id": "xxx"})
        """
        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())

        for mem in self._memories:
            # Filter by user_id / agent_name
            if filters:
                if filters.get("user_id") and mem.get("user_id") != filters["user_id"]:
                    continue
                if filters.get("agent_name") and mem.get("agent_name") != filters["agent_name"]:
                    continue

            # Keyword matching
            content_lower = mem["content"].lower()
            score = 0

            # Exact phrase match
            if query_lower in content_lower:
                score += 10

            # Word overlap
            content_words = set(content_lower.split())
            overlap = len(query_words & content_words)
            score += overlap * 2

            # Tag match
            if any(tag in mem.get("tags", []) for tag in query_words):
                score += 5

            # Time decay (最近的记忆权重更高)
            created = datetime.fromisoformat(mem["created_at"])
            days_old = (datetime.now() - created).days
            time_decay = max(0.1, 1 - days_old * 0.01)  # 每天降1%，最低0.1
            score *= time_decay

            if score > 0:
                mem_copy = dict(mem)
                mem_copy["relevance_score"] = round(score, 2)
                results.append(mem_copy)

        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Update access stats
        for r in results[:limit]:
            for mem in self._memories:
                if mem["id"] == r["id"]:
                    mem["access_count"] = mem.get("access_count", 0) + 1
                    mem["last_accessed"] = datetime.now().isoformat()
                    break

        self._save()
        return results[:limit]

    def get_relevant(self, context: str = None, last_n: int = 5) -> str:
        """获取最相关的记忆摘要（用于填充context window）"""
        if context:
            memories = self.search(context, limit=last_n)
        else:
            memories = sorted(self._memories, key=lambda m: m.get("importance", 0), reverse=True)[:last_n]

        if not memories:
            return ""

        parts = ["[相关记忆]"]
        for mem in memories:
            days_ago = (datetime.now() - datetime.fromisoformat(mem["created_at"])).days
            parts.append(f"- ({days_ago}天前) {mem['content'][:80]}")
        return "\n".join(parts)

    # ===== Memory Stats =====
    def stats(self) -> dict:
        """返回记忆统计"""
        if not self._memories:
            return {"count": 0, "oldest": None, "newest": None, "top_tags": []}
        tags = {}
        for mem in self._memories:
            for tag in mem.get("tags", []):
                tags[tag] = tags.get(tag, 0) + 1
        sorted_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)[:5]
        return {
            "count": len(self._memories),
            "oldest_days": (datetime.now() - datetime.fromisoformat(self._memories[0]["created_at"])).days,
            "newest_days": (datetime.now() - datetime.fromisoformat(self._memories[-1]["created_at"])).days,
            "top_tags": sorted_tags,
        }

    # ===== Delete =====
    def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        for i, mem in enumerate(self._memories):
            if mem["id"] == memory_id:
                self._memories.pop(i)
                self._save()
                return True
        return False

    def clear(self):
        """清空所有记忆"""
        self._memories = []
        self._save()


class MemoryManager:
    """
    多Agent多用户记忆管理器
    对应Mem0的MemoryClient概念
    """

    def __init__(self):
        self._cache: Dict[str, SemanticMemory] = {}

    def get_memory(self, agent_name: str, user_id: str = "default") -> SemanticMemory:
        """获取指定Agent+用户的记忆实例（缓存）"""
        key = f"{agent_name}:{user_id}"
        if key not in self._cache:
            self._cache[key] = SemanticMemory(agent_name, user_id)
        return self._cache[key]

    def add(self, agent_name: str, user_id: str, content: str, metadata: dict = None) -> str:
        """添加记忆"""
        mem = self.get_memory(agent_name, user_id)
        return mem.add(content, metadata)

    def search(self, agent_name: str, query: str, user_id: str = None, limit: int = 5) -> List[Dict]:
        """搜索记忆"""
        filters = {"agent_name": agent_name}
        if user_id:
            filters["user_id"] = user_id
        mem = self.get_memory(agent_name, user_id or "default")
        return mem.search(query, limit=limit, filters=filters)

    def global_search(self, query: str, limit: int = 10) -> List[Dict]:
        """跨所有Agent搜索记忆"""
        all_results = []
        for key in list(self._cache.keys()):
            agent_name, user_id = key.split(":", 1)
            results = self.search(agent_name, query, user_id, limit=3)
            all_results.extend(results)
        all_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return all_results[:limit]

    def stats(self, agent_name: str = None, user_id: str = None) -> dict:
        """统计记忆"""
        if agent_name:
            mem = self.get_memory(agent_name, user_id or "default")
            return mem.stats()
        # 全局统计
        total = sum(len(m._memories) for m in self._cache.values())
        return {"total_memories": total, "agents": len(self._cache)}


# ===== 全局单例 =====
_memory_manager: Optional[MemoryManager] = None

def get_memory_manager() -> MemoryManager:
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


# ===== 对齐Mem0的便捷API =====
def memory_add(agent_name: str, user_id: str, content: str, tags: List[str] = None, importance: int = 1):
    """添加记忆 - 对齐Mem0.add()"""
    mm = get_memory_manager()
    return mm.add(agent_name, user_id, content, {"tags": tags or [], "importance": importance})


def memory_search(agent_name: str, query: str, user_id: str = None, limit: int = 5) -> List[Dict]:
    """搜索记忆 - 对齐Mem0.search()"""
    mm = get_memory_manager()
    return mm.search(agent_name, query, user_id, limit=limit)


def memory_relevant(agent_name: str, context: str = None, user_id: str = None, last_n: int = 5) -> str:
    """获取相关记忆摘要 - 用于填充system prompt"""
    mm = get_memory_manager()
    mem = mm.get_memory(agent_name, user_id or "default")
    return mem.get_relevant(context, last_n)


def memory_stats(agent_name: str = None) -> dict:
    """记忆统计"""
    mm = get_memory_manager()
    return mm.stats(agent_name)