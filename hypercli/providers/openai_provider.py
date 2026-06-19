"""OpenAI-compatible REST provider (also works for any OpenAI-style endpoint)."""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from .base import Message, Provider, ToolSpec


class OpenAIProvider(Provider):
    name = "openai"

    def __init__(self, base_url: str = "https://api.openai.com/v1",
                 api_key: Optional[str] = None, model: Optional[str] = None,
                 **opts: Any) -> None:
        super().__init__(base_url=base_url, api_key=api_key, model=model, **opts)
        self._client: Optional[httpx.AsyncClient] = None

    async def _c(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            self._client = httpx.AsyncClient(
                base_url=self.base_url or "https://api.openai.com/v1",
                headers=headers, timeout=120,
            )
        return self._client

    async def chat(self, messages: List[Message], *, model: Optional[str] = None,
                   tools: Optional[List[ToolSpec]] = None, temperature: float = 0.7,
                   max_tokens: Optional[int] = None, **kwargs: Any) -> Dict[str, Any]:
        client = await self._c()
        body: Dict[str, Any] = {
            "model": model or self.model or "gpt-4o-mini",
            "messages": [self._m(m) for m in messages],
            "temperature": temperature,
        }
        if max_tokens:
            body["max_tokens"] = max_tokens
        if tools:
            body["tools"] = [{
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            } for t in tools]
        r = await client.post("/chat/completions", json=body)
        r.raise_for_status()
        data = r.json()
        choice = data["choices"][0]["message"]
        return {
            "content": choice.get("content") or "",
            "tool_calls": choice.get("tool_calls"),
        }

    async def stream(self, messages: List[Message], *, model: Optional[str] = None,
                     temperature: float = 0.7, max_tokens: Optional[int] = None,
                     **kwargs: Any) -> AsyncIterator[str]:
        client = await self._c()
        body = {
            "model": model or self.model or "gpt-4o-mini",
            "messages": [self._m(m) for m in messages],
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            body["max_tokens"] = max_tokens
        async with client.stream("POST", "/chat/completions", json=body) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                payload = line[6:]
                if payload == "[DONE]":
                    break
                try:
                    obj = json.loads(payload)
                    delta = obj["choices"][0]["delta"].get("content")
                    if delta:
                        yield delta
                except Exception:
                    continue

    @staticmethod
    def _m(m: Message) -> Dict[str, Any]:
        d: Dict[str, Any] = {"role": m.role, "content": m.content}
        if m.tool_calls:
            d["tool_calls"] = m.tool_calls
        if m.tool_call_id:
            d["tool_call_id"] = m.tool_call_id
        if m.name:
            d["name"] = m.name
        return d

    async def aclose(self) -> None:
        if self._client:
            await self._client.aclose()
