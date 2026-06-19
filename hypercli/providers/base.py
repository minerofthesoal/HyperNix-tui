"""Abstract LLM provider interface."""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional


@dataclass
class Message:
    role: str  # 'system' | 'user' | 'assistant' | 'tool'
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON-schema-ish


class Provider(abc.ABC):
    name: str = "base"

    def __init__(self, base_url: Optional[str] = None,
                 api_key: Optional[str] = None,
                 model: Optional[str] = None,
                 **opts: Any) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.opts = opts

    @abc.abstractmethod
    async def chat(
        self,
        messages: List[Message],
        *,
        model: Optional[str] = None,
        tools: Optional[List[ToolSpec]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Return {'content': str, 'tool_calls': list[dict] | None}."""

    @abc.abstractmethod
    async def stream(
        self,
        messages: List[Message],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Yield streamed string chunks."""

    async def aclose(self) -> None:
        pass
