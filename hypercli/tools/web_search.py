"""Web search tool (DuckDuckGo)."""

from __future__ import annotations

from typing import Any, Dict

from .base import Tool, ToolResult


class WebSearchTool(Tool):
    name = "web_search"
    description = (
        "Search the web for `query` and return the top results "
        "(title, URL, snippet). Use this for up-to-date information."
    )

    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        }

    async def run(self, query: str, max_results: int = 5, **_) -> ToolResult:
        try:
            from duckduckgo_search import DDGS  # type: ignore
        except ImportError:
            return ToolResult(ok=False, output="",
                              error="duckduckgo-search not installed")
        try:
            import asyncio
            def _do():
                with DDGS() as ddgs:
                    out = []
                    for r in ddgs.text(query, max_results=max_results):
                        out.append(
                            f"- {r.get('title','')}\n  {r.get('href','')}\n  {r.get('body','')}"
                        )
                    return out
            results = await asyncio.to_thread(_do)
            if not results:
                return ToolResult(ok=True, output="(no results)",
                                  metadata={"query": query})
            return ToolResult(ok=True, output="\n\n".join(results),
                              metadata={"query": query, "count": len(results)})
        except Exception as e:
            return ToolResult(ok=False, output="", error=str(e))
