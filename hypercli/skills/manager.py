"""Skill manager — high-level orchestration of dynamic skills."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from ..config import SKILLS_DIR
from ..tools import ToolRegistry, default_registry


class SkillManager:
    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self.registry = registry or default_registry()

    def list_skills(self) -> List[str]:
        if not SKILLS_DIR.exists():
            return []
        return sorted(p.stem for p in SKILLS_DIR.glob("*.json"))

    def installed_tools(self) -> List[str]:
        return self.registry.names()

    def describe(self, name: str) -> str:
        t = self.registry.get(name)
        if not t:
            return f"(no tool named {name})"
        return f"{t.name}: {t.description}\nparams: {t.parameters()}"
