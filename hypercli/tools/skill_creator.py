"""AI self-created tool / skill creator.

The LLM proposes a new tool as Python source + JSON schema; this tool:
  1. validates the source compiles,
  2. writes it to ~/.hypercli/tools/<name>.py,
  3. loads it into the running registry,
  4. confirms back to the model.
"""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path
from typing import Any, Dict

from ..config import TOOLS_DIR
from .base import Tool, ToolResult


class SkillCreatorTool(Tool):
    name = "create_skill"
    description = (
        "Create a new reusable skill (Python tool) that will be available to "
        "you in future turns. Provide a `name` (snake_case), a short `description`, "
        "the JSON `parameters` schema, and the `code` (a python file that defines "
        "either `tools = [<Tool instances>]` or a single `class MyTool(Tool): ...`). "
        "Use only stdlib + already-installed libraries."
    )

    def __init__(self, registry) -> None:
        self._registry = registry

    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "snake_case skill name"},
                "description": {"type": "string"},
                "parameters": {
                    "type": "object",
                    "description": "JSON schema describing the tool's args",
                },
                "code": {"type": "string", "description": "Full python source"},
            },
            "required": ["name", "description", "parameters", "code"],
        }

    async def run(self, name: str, description: str,
                  parameters: Dict[str, Any], code: str, **_) -> ToolResult:
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
        if not safe.endswith(".py"):
            safe += ".py"
        # Basic safety: parse, ban obviously bad builtins usage.
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return ToolResult(ok=False, output="", error=f"SyntaxError: {e}")
        banned = {"eval", "exec", "__import__", "globals", "locals"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                    and node.func.id in banned:
                return ToolResult(ok=False, output="",
                                  error=f"Banned call: {node.func.id}")

        # Wrap user code into a self-contained module exposing `tools = [...]`.
        wrapped = textwrap.dedent(f'''
            """Auto-generated skill: {name}"""
            from hypercli.tools.base import Tool, ToolResult

            class _GeneratedSkill(Tool):
                name = "{name}"
                description = {description!r}
                def parameters(self):
                    return {parameters!r}
                async def run(self, **kw):
                    return await self._impl(**kw)

            _USER_CODE
            {code}

            # If the user defined `tools`, prefer it. Otherwise expose ours.
            tools = list(tools) if 'tools' in dir() else [_GeneratedSkill()]
        ''')

        TOOLS_DIR.mkdir(parents=True, exist_ok=True)
        path = TOOLS_DIR / safe
        path.write_text(wrapped, encoding="utf-8")

        # Try loading immediately.
        try:
            self._registry.load_dynamic(path)
        except Exception as e:
            return ToolResult(ok=False, output="",
                              error=f"Loaded failed: {e}")
        if self._registry.get(name) is None:
            return ToolResult(ok=True,
                              output=f"Skill '{name}' written to {path} but not registered as '{name}'.",
                              metadata={"path": str(path)})
        return ToolResult(
            ok=True,
            output=f"Skill '{name}' created and registered successfully.",
            metadata={"path": str(path), "name": name},
        )
