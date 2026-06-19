"""Configuration, API-key storage, model registry."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tomllib import loads as toml_loads  # py311+
except ModuleNotFoundError:  # pragma: no cover
    from tomli import loads as toml_loads  # type: ignore


CONFIG_DIR = Path(os.environ.get("HYPERCLI_HOME", Path.home() / ".hypercli"))
CONFIG_FILE = CONFIG_DIR / "config.json"
SKILLS_DIR = CONFIG_DIR / "skills"
TOOLS_DIR = CONFIG_DIR / "tools"
SESSIONS_DIR = CONFIG_DIR / "sessions"


@dataclass
class ProviderConfig:
    name: str
    base_url: Optional[str] = None
    api_key_env: Optional[str] = None  # env var name to read at runtime
    api_key: Optional[str] = None      # explicit (used by REST/OpenAI/Anthropic)
    default_model: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Config:
    active_provider: str = "hypernix"
    active_model: Optional[str] = None
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)
    history: List[Dict[str, str]] = field(default_factory=list)
    auto_upgrade: bool = True
    skills_enabled: bool = True
    max_tool_iterations: int = 8

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["providers"] = {k: asdict(v) for k, v in self.providers.items()}
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        provs = {}
        for k, v in (data.get("providers") or {}).items():
            provs[k] = ProviderConfig(**v)
        return cls(
            active_provider=data.get("active_provider", "hypernix"),
            active_model=data.get("active_model"),
            providers=provs,
            history=data.get("history", []),
            auto_upgrade=data.get("auto_upgrade", True),
            skills_enabled=data.get("skills_enabled", True),
            max_tool_iterations=data.get("max_tool_iterations", 8),
        )

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        TOOLS_DIR.mkdir(parents=True, exist_ok=True)
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls) -> "Config":
        if CONFIG_FILE.exists():
            try:
                return cls.from_dict(json.loads(CONFIG_FILE.read_text()))
            except Exception:
                pass
        cfg = cls()
        cfg._seed_defaults()
        cfg.save()
        return cfg

    def _seed_defaults(self) -> None:
        self.providers = {
            "hypernix": ProviderConfig(
                name="hypernix",
                default_model="hypernix-1",
                api_key_env="HYPERNIX_API_KEY",
            ),
            "openai": ProviderConfig(
                name="openai",
                base_url="https://api.openai.com/v1",
                default_model="gpt-4o-mini",
                api_key_env="OPENAI_API_KEY",
            ),
            "anthropic": ProviderConfig(
                name="anthropic",
                base_url="https://api.anthropic.com/v1",
                default_model="claude-3-5-sonnet-20241022",
                api_key_env="ANTHROPIC_API_KEY",
            ),
            "ollama": ProviderConfig(
                name="ollama",
                base_url="http://127.0.0.1:11434",
                default_model="llama3.2",
            ),
            "lmstudio": ProviderConfig(
                name="lmstudio",
                base_url="http://127.0.0.1:1234/v1",
                default_model="local-model",
            ),
            "rest": ProviderConfig(
                name="rest",
                base_url=None,
                default_model="custom",
                api_key_env="REST_API_KEY",
            ),
        }

    def resolve_key(self, provider_name: str) -> Optional[str]:
        p = self.providers.get(provider_name)
        if not p:
            return None
        if p.api_key:
            return p.api_key
        if p.api_key_env:
            return os.environ.get(p.api_key_env)
        return None
