"""
DistillAI LLM Provider 抽象层
支持: OpenAI / Anthropic / Ollama (本地) / MiniMax / SiliconFlow / 自定义
即插即用，快速切换
"""
import os
import json
from typing import Literal, Optional, Any
from pathlib import Path

# ===== MiniMax (workspace minimax_client.py) =====
class MiniMaxProvider:
    """MiniMax API (via workspace minimax_client.py)"""
    name = "minimax"

    def __init__(self):
        ws = Path.home() / ".openclaw" / "workspace"
        sys_path_add = str(ws)
        import sys
        if sys_path_add not in sys.path:
            sys.path.insert(0, sys_path_add)
        try:
            import minimax_client
            self._fn = minimax_client.chat
            self._ready = True
        except Exception as e:
            self._fn = None
            self._ready = False
            self._err = str(e)

    @property
    def ready(self) -> bool:
        return self._ready

    def chat(self, prompt: str, model: str = "MiniMax-M2", **kwargs) -> str:
        if not self._ready:
            return f"[MiniMax unavailable: {self._err}]"
        return self._fn(prompt, model=model, **kwargs)

    def chat_messages(self, messages: list, model: str = "MiniMax-M2", **kwargs) -> str:
        """messages格式: [{"role":"user","content":"..."}]"""
        if isinstance(messages, list) and len(messages) == 1:
            return self.chat(messages[0]["content"], model=model, **kwargs)
        # 合并为单prompt
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        return self.chat(prompt, model=model, **kwargs)


# ===== OpenAI =====
class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self._client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
                self._ready = True
            except ImportError:
                self._ready = False
                self._err = "openai package not installed"
        else:
            self._ready = False
            self._err = "OPENAI_API_KEY not set"

    @property
    def ready(self) -> bool:
        return self._ready

    def chat(self, prompt: str, model: str = "gpt-4o-mini", **kwargs) -> str:
        if not self._ready:
            return f"[OpenAI unavailable: {self._err}]"
        messages = [{"role": "user", "content": prompt}]
        resp = self._client.chat.completions.create(model=model, messages=messages, **kwargs)
        return resp.choices[0].message.content

    def chat_messages(self, messages: list, model: str = "gpt-4o-mini", **kwargs) -> str:
        if not self._ready:
            return f"[OpenAI unavailable: {self._err}]"
        resp = self._client.chat.completions.create(model=model, messages=messages, **kwargs)
        return resp.choices[0].message.content


# ===== Anthropic Claude =====
class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._client = None
        if self.api_key:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
                self._ready = True
            except ImportError:
                self._ready = False
                self._err = "anthropic package not installed"
        else:
            self._ready = False
            self._err = "ANTHROPIC_API_KEY not set"

    @property
    def ready(self) -> bool:
        return self._ready

    def chat(self, prompt: str, model: str = "claude-sonnet-4-20250514", **kwargs) -> str:
        if not self._ready:
            return f"[Anthropic unavailable: {self._err}]"
        resp = self._client.messages.create(
            model=model,
            max_tokens=kwargs.get("max_tokens", 2000),
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.content[0].text

    def chat_messages(self, messages: list, model: str = "claude-sonnet-4-20250514", **kwargs) -> str:
        if not self._ready:
            return f"[Anthropic unavailable: {self._err}]"
        # Anthropic uses different message format
        claude_msgs = []
        for m in messages:
            if m["role"] == "system":
                continue  # handle separately
            claude_msgs.append({"role": "user" if m["role"] == "user" else "assistant", "content": m["content"]})
        resp = self._client.messages.create(
            model=model,
            max_tokens=kwargs.get("max_tokens", 2000),
            messages=claude_msgs
        )
        return resp.content[0].text


# ===== Ollama (本地大模型) =====
class OllamaProvider:
    name = "ollama"
    default_url = "http://localhost:11434"

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", self.default_url)
        self._ready = None  # lazy check

    @property
    def ready(self) -> bool:
        if self._ready is None:
            self._ready = self._check()
        return self._ready

    def _check(self) -> bool:
        try:
            import urllib.request
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=3) as r:
                return r.status == 200
        except:
            return False

    def list_models(self) -> list:
        try:
            import urllib.request, json
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
                return [m["name"] for m in data.get("models", [])]
        except:
            return []

    def chat(self, prompt: str, model: str = "llama3.2:latest", **kwargs) -> str:
        if not self.ready:
            return f"[Ollama not running at {self.base_url}]"
        try:
            import urllib.request, json
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": kwargs.get("temperature", 0.8)}
            }
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                result = json.loads(r.read())
                return result.get("response", "")
        except Exception as e:
            return f"[Ollama error: {e}]"

    def chat_messages(self, messages: list, model: str = "llama3.2:latest", **kwargs) -> str:
        if not self.ready:
            return f"[Ollama not running at {self.base_url}]"
        try:
            import urllib.request, json
            # Convert messages to Ollama format
            ollama_msgs = [{"role": m["role"], "content": m["content"]} for m in messages]
            payload = {"model": model, "messages": ollama_msgs, "stream": False}
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"{self.base_url}/api/chat",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                result = json.loads(r.read())
                return result.get("message", {}).get("content", "")
        except Exception as e:
            return f"[Ollama chat error: {e}]"


# ===== Provider Manager =====
class LLMProviderManager:
    """
    多模型管理器，自动检测可用provider并按优先级切换
    使用方式: LLM("minimax") / LLM() / LLM("ollama")
    """

    def __init__(self, preferred: str = None):
        self.preferred = preferred
        self._providers = {
            "minimax": MiniMaxProvider(),
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "ollama": OllamaProvider(),
        }
        self._active = self._detect_active()

    def _detect_active(self) -> Optional[Any]:
        """自动检测可用的provider"""
        if self.preferred and self.preferred in self._providers:
            p = self._providers[self.preferred]
            if p.ready:
                return p
        for name, p in self._providers.items():
            if p.ready:
                return p
        return None

    @property
    def active_name(self) -> str:
        return self._active.name if self._active else "none"

    def status(self) -> dict:
        return {name: p.ready for name, p in self._providers.items()}

    def chat(self, prompt: str = None, messages: list = None, model: str = None, **kwargs):
        """统一chat接口"""
        if not self._active:
            return "[Error] No LLM provider available"
        if messages:
            return self._active.chat_messages(messages, model=model, **kwargs)
        elif prompt:
            return self._active.chat(prompt, model=model, **kwargs)
        return "[Error] No prompt or messages provided"

    def __call__(self, prompt: str = None, messages: list = None, model: str = None, **kwargs):
        return self.chat(prompt, messages, model, **kwargs)


# 全局默认实例
_default_provider: Optional[LLMProviderManager] = None

def LLM(provider: str = None) -> LLMProviderManager:
    """获取LLMProvider实例"""
    global _default_provider
    if _default_provider is None:
        _default_provider = LLMProviderManager(preferred=provider)
    return _default_provider