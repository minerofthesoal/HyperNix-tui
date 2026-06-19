"""hyperNix provider — uses the installed hyperNix package (v0.70.3)."""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional

from .base import Message, Provider, ToolSpec


class HyperNixProvider(Provider):
    name = "hypernix"

    def __init__(self, **opts: Any) -> None:
        super().__init__(**opts)
        try:
            import hyperNix  # type: ignore  # noqa: F401
            self._hn = hyperNix
        except ImportError as e:
            raise RuntimeError(
                "hyperNix>=0.70.3 not installed. `pip install hyperNix==0.70.3`."
            ) from e

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
        msgs = [{"role": m.role, "content": m.content} for m in messages]

        def _call() -> Dict[str, Any]:
            # hyperNix 0.70.x exposes a high-level `chat` helper.
            fn = getattr(self._hn, "chat", None) or getattr(self._hn, "complete", None)
            if fn is None:
                raise RuntimeError("hyperNix package missing chat/complete API.")
            try:
                resp = fn(
                    msgs,
                    model=model or self.model or "hypernix-1",
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=[t.__dict__ if hasattr(t, "__dict__") else t for t in (tools or [])],
                    **kwargs,
                )
            except TypeError:
                # Older signature: no tools kwarg.
                resp = fn(
                    msgs,
                    model=model or self.model or "hypernix-1",
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            return resp if isinstance(resp, dict) else {"content": str(resp)}

        return await asyncio.to_thread(_call)

    async def stream(
        self,
        messages: List[Message],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        result = await self.chat(
            messages, model=model, temperature=temperature,
            max_tokens=max_tokens, **kwargs,
        )
        # Fallback "streaming": emit content word-by-word.
        content = result.get("content", "")
        for word in content.split():
            yield word + " "
            await asyncio.sleep(0.01)
