"""Ollama local provider (http://127.0.0.1:11434)."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from .base import Message, Provider, ToolSpec


class OllamaProvider(Provider):
    name = "ollama"

    def __init__(self, base_url: str = "http://127.0.0.1:11434",
                 model: Optional[str] = None, **opts: Any) -> None:
        super().__init__(base_url=base_url, model=model, **opts)
        self._client: Optional[httpx.AsyncClient] = None

    async def _c(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url, timeout=300,
            )
        return self._client

    async def list_models(self) -> List[str]:
        client = await self._c()
        try:
            r = await client.get("/api/tags")
            r.raise_for_status()
            return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []

    async def chat(self, messages: List[Message], *, model: Optional[str] = None,
                   tools: Optional[List[ToolSpec]] = None, temperature: float = 0.7,
                   max_tokens: Optional[int] = None, **kwargs: Any) -> Dict[str, Any]:
        client = await self._c()
        body = {
            "model": model or self.model or "llama3.2",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature},
        }
        if max_tokens:
            body["options"]["num_predict"] = max_tokens
        r = await client.post("/api/chat", json=body)
        r.raise_for_status()
        data = r.json()
        return {"content": data.get("message", {}).get("content", ""),
                "tool_calls": None}

    async def stream(self, messages: List[Message], *, model: Optional[str] = None,
                     temperature: float = 0.7, max_tokens: Optional[int] = None,
                     **kwargs: Any) -> AsyncIterator[str]:
        client = await self._c()
        body = {
            "model": model or self.model or "llama3.2",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "options": {"temperature": temperature},
        }
        if max_tokens:
            body["options"]["num_predict"] = max_tokens
        async with client.stream("POST", "/api/chat", json=body) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    chunk = obj.get("message", {}).get("content")
                    if chunk:
                        yield chunk
                    if obj.get("done"):
                        break
                except Exception:
                    continue

    async def aclose(self) -> None:
        if self._client:
            await self._client.aclose()
