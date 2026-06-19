"""Generic REST provider — POSTs messages JSON to a configured endpoint."""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from .base import Message, Provider, ToolSpec


class RestProvider(Provider):
    name = "rest"

    def __init__(self, base_url: Optional[str] = None,
                 api_key: Optional[str] = None, model: Optional[str] = None,
                 **opts: Any) -> None:
        super().__init__(base_url=base_url, api_key=api_key, model=model, **opts)
        self._client: Optional[httpx.AsyncClient] = None
        if not self.base_url:
            raise ValueError("rest provider requires base_url (REST_API_BASE_URL or config).")

    async def _c(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(base_url=self.base_url,
                                             headers=headers, timeout=120)
        return self._client

    async def chat(self, messages: List[Message], *, model: Optional[str] = None,
                   tools: Optional[List[ToolSpec]] = None, temperature: float = 0.7,
                   max_tokens: Optional[int] = None, **kwargs: Any) -> Dict[str, Any]:
        client = await self._c()
        body = {
            "model": model or self.model or "custom",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        if max_tokens:
            body["max_tokens"] = max_tokens
        r = await client.post("/chat", json=body)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict):
            content = data.get("content") or data.get("message", {}).get("content", "")
            if not content and "choices" in data:
                content = data["choices"][0].get("message", {}).get("content", "")
            return {"content": content, "tool_calls": data.get("tool_calls")}
        return {"content": str(data), "tool_calls": None}

    async def stream(self, messages: List[Message], *, model: Optional[str] = None,
                     temperature: float = 0.7, max_tokens: Optional[int] = None,
                     **kwargs: Any) -> AsyncIterator[str]:
        result = await self.chat(messages, model=model, temperature=temperature,
                                 max_tokens=max_tokens, **kwargs)
        for word in (result.get("content") or "").split():
            yield word + " "
            await asyncio.sleep(0.01)

    async def aclose(self) -> None:
        if self._client:
            await self._client.aclose()
