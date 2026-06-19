"""Local file tools — read, write, list."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from .base import Tool, ToolResult


class ReadFileTool(Tool):
    name = "read_file"
    description = (
        "Read the contents of a local file at `path`. "
        "Use absolute paths or paths relative to the current working directory."
    )

    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Filesystem path to read"},
                "max_bytes": {"type": "integer", "description": "Optional size cap",
                              "default": 200000},
            },
            "required": ["path"],
        }

    async def run(self, path: str, max_bytes: int = 200000, **_) -> ToolResult:
        p = Path(path).expanduser()
        if not p.exists():
            return ToolResult(ok=False, output="", error=f"no such file: {p}")
        if not p.is_file():
            return ToolResult(ok=False, output="", error=f"not a file: {p}")
        try:
            data = p.read_bytes()[:max_bytes]
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                text = f"<binary {len(data)} bytes>"
            return ToolResult(ok=True, output=text,
                              metadata={"path": str(p), "bytes": len(data)})
        except Exception as e:
            return ToolResult(ok=False, output="", error=str(e))


class WriteFileTool(Tool):
    name = "write_file"
    description = (
        "Create or overwrite a local file at `path` with `content`. "
        "Creates parent directories automatically."
    )

    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
                "append": {"type": "boolean", "default": False},
            },
            "required": ["path", "content"],
        }

    async def run(self, path: str, content: str, append: bool = False, **_) -> ToolResult:
        p = Path(path).expanduser()
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if append else "w"
            with open(p, mode, encoding="utf-8") as f:
                f.write(content)
            return ToolResult(
                ok=True,
                output=f"wrote {len(content)} chars to {p}",
                metadata={"path": str(p), "append": append},
            )
        except Exception as e:
            return ToolResult(ok=False, output="", error=str(e))


class ListDirTool(Tool):
    name = "list_dir"
    description = "List the contents of a directory."

    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path",
                         "default": "."},
            },
            "required": ["path"],
        }

    async def run(self, path: str = ".", **_) -> ToolResult:
        p = Path(path).expanduser()
        if not p.exists() or not p.is_dir():
            return ToolResult(ok=False, output="", error=f"not a dir: {p}")
        items: List[str] = []
        for entry in sorted(p.iterdir()):
            tag = "/" if entry.is_dir() else ""
            items.append(f"{entry.name}{tag}")
        return ToolResult(ok=True, output="\n".join(items),
                          metadata={"path": str(p), "count": len(items)})
