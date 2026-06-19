"""Runtime tool registry."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from ..config import TOOLS_DIR
from .base import FunctionTool, Tool, ToolResult
from .file_ops import ReadFileTool, WriteFileTool, ListDirTool
from .web_search import WebSearchTool
from .skill_creator import SkillCreatorTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def names(self) -> List[str]:
        return sorted(self._tools.keys())

    def all(self) -> List[Tool]:
        return list(self._tools.values())

    def specs(self) -> List[dict]:
        from ..providers.base import ToolSpec
        return [t.spec() if not isinstance(t.spec(), dict) else t.spec()
                for t in self._tools.values()]

    async def call(self, name: str, args: dict) -> ToolResult:
        t = self.get(name)
        if not t:
            return ToolResult(ok=False, output="", error=f"Unknown tool: {name}")
        try:
            return await t.run(**args)
        except TypeError as e:
            return ToolResult(ok=False, output="", error=f"Bad args: {e}")

    def load_dynamic(self, path: Path) -> None:
        """Load a python file defining Tool subclasses or `tools=[...]`."""
        if not path.exists():
            return
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if not spec or not spec.loader:
            return
        mod = importlib.util.module_from_spec(spec)
        sys.modules[path.stem] = mod
        spec.loader.exec_module(mod)
        if hasattr(mod, "tools"):
            for t in mod.tools:
                self.register(t)


def default_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(ReadFileTool())
    reg.register(WriteFileTool())
    reg.register(ListDirTool())
    reg.register(WebSearchTool())
    reg.register(SkillCreatorTool(reg))
    # Load user-defined tools
    if TOOLS_DIR.exists():
        for f in TOOLS_DIR.glob("*.py"):
            if f.name.startswith("_"):
                continue
            try:
                reg.load_dynamic(f)
            except Exception as e:
                print(f"[hypercli] failed to load tool {f.name}: {e}", file=sys.stderr)
    return reg
