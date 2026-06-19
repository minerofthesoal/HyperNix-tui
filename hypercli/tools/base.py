"""Tool base class — callable, schema-described tools the LLM may invoke."""

from __future__ import annotations

import abc
import inspect
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional

from ..providers.base import ToolSpec


@dataclass
class ToolResult:
    ok: bool
    output: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Tool(abc.ABC):
    name: str = "tool"
    description: str = ""

    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def spec(self) -> ToolSpec:
        return ToolSpec(name=self.name, description=self.description,
                        parameters=self.parameters())

    @abc.abstractmethod
    async def run(self, **kwargs: Any) -> ToolResult:
        ...


class FunctionTool(Tool):
    """Wrap a python callable as a Tool."""

    def __init__(self, name: str, description: str,
                 fn: Callable[..., Awaitable[Any]],
                 schema: Optional[Dict[str, Any]] = None) -> None:
        self.name = name
        self.description = description
        self._fn = fn
        self._schema = schema or {
            "type": "object", "properties": {}, "required": []
        }

    def parameters(self) -> Dict[str, Any]:
        return self._schema

    async def run(self, **kwargs: Any) -> ToolResult:
        try:
            if inspect.iscoroutinefunction(self._fn):
                result = await self._fn(**kwargs)
            else:
                result = await _to_awaitable(self._fn, **kwargs)
            if isinstance(result, ToolResult):
                return result
            return ToolResult(ok=True, output=str(result))
        except Exception as e:
            return ToolResult(ok=False, output="", error=str(e))


async def _to_awaitable(fn: Callable, **kw) -> Any:
    return fn(**kw)
