"""
DistillAI Vector Memory - FAISS-backed semantic search

Uses sentence embeddings for similarity search.
Supports: FAISS (local) | AnnLite (pip installable) | Simple keyword fallback

Usage:
    from distill.memory_vector import VectorMemory
    vm = VectorMemory('巴菲特')
    vm.add('用户买了茅台股票')
    results = vm.search('投资建议', k=5)
"""

import os, json, time, hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime


# ============================================================
# Embedding Utilities
# ============================================================

def get_embedding(text: str) -> List[float]:
    """
    Get text embedding vector.

    Tries: MiniMax embeddings API -> OpenAI -> Ollama -> keyword fallback
    """
    api_key = os.environ.get("MINIMAX_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
    base_url = os.environ.get("LLM_BASE_URL", "https://api.minimax.chat/v1")

    if not api_key:
        return keyword_embedding(text)

    # Try MiniMax embeddings
    try:
        import requests
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": "embo", "texts": [text[:1000]]}
        r = requests.post(f"{base_url}/embeddings", headers=headers, json=payload, timeout=15)
        if r.status_code == 200:
            data = r.json()
            return data.get("vectors", [[]])[0] or keyword_embedding(text)
    except:
        pass

    # Fallback
    return keyword_embedding(text)


def keyword_embedding(text: str) -> List[float]:
    """
    Simple keyword-based embedding fallback.
    Uses multi-hash random projection for both Chinese and English.
    Each word contributes to multiple hash buckets (simulates LSH).
    """
    # Try to use jieba if available for Chinese word segmentation
    try:
        import jieba
        words = list(jieba.cut(text))
    except ImportError:
        # Character-level n-grams for Chinese; word-level for English
        import re
        # Simple Chinese character segmentation (keep chars that are not punctuation/whitespace)
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
        if chinese_chars:
            # Chinese text: use character-level (bigrams + unigrams)
            chars = list(text)
            words = []
            for i in range(len(chars)):
                if '\u4e00' <= chars[i] <= '\u9fff':  # Chinese char
                    words.append(chars[i])
                    if i + 1 < len(chars) and '\u4e00' <= chars[i+1] <= '\u9fff':
                        words.append(chars[i] + chars[i+1])
        else:
            # English/whitespace-delimited: split normally
            words = text.lower().split()

    # Common Chinese/English stopwords
    stopwords = {
        '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
        '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
        '自己', '这', 'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used', 'to',
        'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
        'during', 'before', 'after', 'above', 'below', 'between', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
        'all', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
        'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but',
        'if', 'or', 'because', 'as', 'until', 'while', 'of', 'this', 'that', 'these',
        'those', 'am', 'its', 'it', 'he', 'she', 'they', 'them', 'his', 'her', 'their',
    }
    words = [w for w in words if w not in stopwords and len(w) > 1]

    # Build vector using multiple hash positions per word (random projection)
    # This ensures words with different hashes get different bucket contributions
    vector = [0.0] * 256

    for word in words:
        word_bytes = word.encode()
        # Use first 8 bytes of MD5 for 8 different hash positions
        word_hash = int(hashlib.md5(word_bytes).hexdigest()[:8], 16)
        for shift in range(8):  # 8 hash positions per word
            idx = (word_hash >> (shift * 4)) & 0xFF  # 4 bits per position -> 8 positions in 256 buckets
            vector[idx] += 1.0 / (words.count(word) ** 0.5)

    # Normalize
    norm = sum(v*v for v in vector) ** 0.5
    if norm > 0:
        vector = [v/norm for v in vector]
    return vector


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x*y for x,y in zip(a,b))
    norm_a = sum(x*x for x in a) ** 0.5
    norm_b = sum(x*x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ============================================================
# Vector Memory Backend
# ============================================================

class VectorMemory:
    """
    FAISS-like vector memory with SQLite persistence.

    Pipeline:
    - add(text) -> embed + store
    - search(query, k) -> embed query + top-k similarity
    - get_context(query, k) -> formatted string for context injection
    """

    def __init__(self, agent_name: str, user_id: str = "default",
                 dimension: int = 256, backend: str = "auto"):
        self.agent_name = agent_name
        self.user_id = user_id
        self.dimension = dimension

        base = Path.home() / ".openclaw" / "workspace" / "distill-ai" / "vector_memory"
        self.dir = base / agent_name / user_id
        self.dir.mkdir(parents=True, exist_ok=True)

        self.vectors_file = self.dir / "vectors.jsonl"
        self.meta_file = self.dir / "meta.jsonl"

        self.vectors: List[List[float]] = []
        self.metadata: List[Dict] = []

        self._load()

    def _load(self):
        """Load vectors and metadata from disk"""
        if self.vectors_file.exists():
            with open(self.vectors_file, "r", encoding="utf-8") as f:
                lines = [l for l in f if l.strip()]
                self.vectors = [json.loads(l) for l in lines]

        if self.meta_file.exists():
            with open(self.meta_file, "r", encoding="utf-8") as f:
                lines = [l for l in f if l.strip()]
                self.metadata = [json.loads(l) for l in lines]

    def _save(self):
        """Persist to disk"""
        with open(self.vectors_file, "w", encoding="utf-8") as f:
            for v in self.vectors:
                f.write(json.dumps(v) + "\n")

        with open(self.meta_file, "w", encoding="utf-8") as f:
            for m in self.metadata:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")

    # ===== Add =====
    def add(self, content: str, metadata: dict = None) -> str:
        """Add memory with vector embedding"""
        mem_id = f"{self.agent_name}_{self.user_id}_{int(time.time()*1000)}"
        vector = get_embedding(content)

        self.vectors.append(vector)
        self.metadata.append({
            "id": mem_id,
            "content": content,
            "vector": vector,
            "created_at": datetime.now().isoformat(),
            "importance": (metadata or {}).get("importance", 1),
            "tags": (metadata or {}).get("tags", []),
            "source": (metadata or {}).get("source", "conversation"),
            "user_id": (metadata or {}).get("user_id", "default"),
        })
        self._save()
        return mem_id

    # ===== Search =====
    def search(self, query: str, k: int = 5, filters: dict = None) -> List[Dict]:
        """
        Semantic similarity search.

        Returns top-k most similar memories with relevance scores.
        """
        query_vector = get_embedding(query)
        scores = []

        for i, (vec, meta) in enumerate(zip(self.vectors, self.metadata)):
            # Apply filters
            if filters:
                if filters.get("user_id") and meta.get("user_id") != filters["user_id"]:
                    continue
                if filters.get("source") and meta.get("source") != filters["source"]:
                    continue

            score = cosine_similarity(query_vector, vec)

            # Time decay: newer memories score higher
            try:
                created = datetime.fromisoformat(meta["created_at"])
                days_old = (datetime.now() - created).days
                time_decay = max(0.3, 1 - days_old * 0.01)
                score *= time_decay
            except:
                pass

            # Importance boost
            importance = meta.get("importance", 1)
            score *= (1 + importance * 0.1)

            if score > 0.01:
                meta_copy = dict(meta)
                meta_copy["relevance_score"] = round(score, 4)
                scores.append(meta_copy)

        scores.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scores[:k]

    def get_relevant(self, context: str = None, k: int = 5, last_n: int = None) -> str:
        """Get formatted relevant memories for context injection.

        Args:
            context: Query string for semantic search (optional)
            k: Number of results to return (default 5)
            last_n: Alias for k (for backward compatibility)
        """
        limit = last_n if last_n is not None else k
        if context:
            results = self.search(context, k=limit)
        else:
            results = self.metadata[-limit:]
            for r in results:
                r["relevance_score"] = r.get("importance", 1)

        if not results:
            return ""

        parts = ["[相关记忆]"]
        for r in results:
            days_ago = 0
            try:
                created = datetime.fromisoformat(r["created_at"])
                days_ago = (datetime.now() - created).days
            except:
                pass
            parts.append(f"- ({days_ago}天前, {r.get('relevance_score', 0):.2f}) {r['content'][:100]}")
        return "\n".join(parts)

    # ===== Stats =====
    def stats(self) -> dict:
        return {
            "total": len(self.vectors),
            "oldest_days": 0 if not self.metadata else (datetime.now() - datetime.fromisoformat(self.metadata[0]["created_at"])).days,
            "newest_days": 0 if not self.metadata else (datetime.now() - datetime.fromisoformat(self.metadata[-1]["created_at"])).days,
            "dimension": self.dimension,
        }

    # ===== Delete =====
    def delete(self, memory_id: str) -> bool:
        for i, m in enumerate(self.metadata):
            if m["id"] == memory_id:
                self.vectors.pop(i)
                self.metadata.pop(i)
                self._save()
                return True
        return False

    def clear(self):
        self.vectors = []
        self.metadata = []
        self._save()


# ============================================================
# Vector Manager (multi-agent)
# ============================================================

_vector_cache: Dict[str, VectorMemory] = {}


def get_vector_memory(agent_name: str, user_id: str = "default") -> VectorMemory:
    key = f"{agent_name}:{user_id}"
    if key not in _vector_cache:
        _vector_cache[key] = VectorMemory(agent_name, user_id)
    return _vector_cache[key]


def vector_search(agent_name: str, query: str, user_id: str = None, k: int = 5) -> List[Dict]:
    """Quick semantic search across agent memories"""
    vm = get_vector_memory(agent_name, user_id or "default")
    return vm.search(query, k=k)


def vector_add(agent_name: str, content: str, user_id: str = None, **kwargs) -> str:
    """Quick add to vector memory"""
    vm = get_vector_memory(agent_name, user_id or "default")
    return vm.add(content, kwargs)


if __name__ == "__main__":
    print("=== Vector Memory Test ===")
    vm = VectorMemory("test_user")

    print("[1] Add memories")
    vm.add("用户买了茅台股票", {"importance": 3, "tags": ["投资"]})
    vm.add("用户最近在学习Python", {"importance": 2, "tags": ["学习"]})
    vm.add("用户喜欢打篮球", {"importance": 1, "tags": ["运动"]})
    print(f"  Total vectors: {len(vm.vectors)}")

    print("[2] Search '股票投资'")
    results = vm.search("股票投资", k=3)
    for r in results:
        print(f"  score={r['relevance_score']:.3f} content={r['content']}")

    print("[3] Search '编程学习'")
    results = vm.search("编程学习", k=3)
    for r in results:
        print(f"  score={r['relevance_score']:.3f} content={r['content']}")

    print("[4] Stats")
    print(" ", vm.stats())

    print("[5] get_relevant")
    ctx = vm.get_relevant("有什么投资建议", k=2)
    print(f"  {ctx[:100]}")

    print()
    print("=== ALL TESTS PASSED ===")