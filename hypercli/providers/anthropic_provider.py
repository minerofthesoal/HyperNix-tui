"""Anthropic Messages API provider."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from .base import Message, Provider, ToolSpec


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, base_url: str = "https://api.anthropic.com/v1",
                 api_key: Optional[str] = None, model: Optional[str] = None,
                 **opts: Any) -> None:
        super().__init__(base_url=base_url, api_key=api_key, model=model, **opts)
        self._client: Optional[httpx.AsyncClient] = None

    async def _c(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url or "https://api.anthropic.com/v1",
                headers={
                    "x-api-key": self.api_key or "",
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                timeout=120,
            )
        return self._client

    @staticmethod
    def _split(messages: List[Message]):
        sys_msg = ""
        conv = []
        for m in messages:
            if m.role == "system":
                sys_msg += (m.content + "\n")
            else:
                conv.append({"role": m.role, "content": m.content})
        return sys_msg.strip(), conv

    async def chat(self, messages: List[Message], *, model: Optional[str] = None,
                   tools: Optional[List[ToolSpec]] = None, temperature: float = 0.7,
                   max_tokens: Optional[int] = None, **kwargs: Any) -> Dict[str, Any]:
        client = await self._c()
        sys_msg, conv = self._split(messages)
        body: Dict[str, Any] = {
            "model": model or self.model or "claude-3-5-sonnet-20241022",
            "messages": conv,
            "temperature": temperature,
            "max_tokens": max_tokens or 2048,
        }
        if sys_msg:
            body["system"] = sys_msg
        if tools:
            body["tools"] = [{
                "name": t.name, "description": t.description,
                "input_schema": t.parameters,
            } for t in tools]
        r = await client.post("/messages", json=body)
        r.raise_for_status()
        data = r.json()
        content = ""
        tool_calls = []
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append({
                    "id": block.get("id"),
                    "type": "function",
                    "function": {
                        "name": block.get("name"),
                        "arguments": json.dumps(block.get("input", {})),
                    },
                })
        return {"content": content, "tool_calls": tool_calls or None}

    async def stream(self, messages: List[Message], *, model: Optional[str] = None,
                     temperature: float = 0.7, max_tokens: Optional[int] = None,
                     **kwargs: Any) -> AsyncIterator[str]:
        client = await self._c()
        sys_msg, conv = self._split(messages)
        body = {
            "model": model or self.model or "claude-3-5-sonnet-20241022",
            "messages": conv, "temperature": temperature,
            "max_tokens": max_tokens or 2048, "stream": True,
        }
        if sys_msg:
            body["system"] = sys_msg
        async with client.stream("POST", "/messages", json=body) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                try:
                    obj = json.loads(line[6:])
                    if obj.get("type") == "content_block_delta":
                        d = obj.get("delta", {})
                        if d.get("type") == "text_delta":
                            yield d.get("text", "")
                except Exception:
                    continue

    async def aclose(self) -> None:
        if self._client:
            await self._client.aclose()
