"""Provider registry."""

from __future__ import annotations

import os
from typing import Optional, Type

from ..config import Config, ProviderConfig
from .base import Provider, Message, ToolSpec
from .hypernix import HyperNixProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .ollama import OllamaProvider
from .lmstudio import LMStudioProvider
from .rest import RestProvider

PROVIDERS: dict[str, Type[Provider]] = {
    "hypernix": HyperNixProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
    "lmstudio": LMStudioProvider,
    "rest": RestProvider,
}

__all__ = [
    "PROVIDERS", "Provider", "Message", "ToolSpec",
    "HyperNixProvider", "OpenAIProvider", "AnthropicProvider",
    "OllamaProvider", "LMStudioProvider", "RestProvider",
    "build_provider", "list_providers",
]


def list_providers() -> list[str]:
    return list(PROVIDERS.keys())


def build_provider(cfg: Config, name: Optional[str] = None) -> Provider:
    name = name or cfg.active_provider
    pcfg: ProviderConfig = cfg.providers.get(name) or ProviderConfig(name=name)
    cls = PROVIDERS.get(name)
    if cls is None:
        raise ValueError(f"Unknown provider: {name}. Available: {list(PROVIDERS)}")
    key = cfg.resolve_key(name)
    base_url = pcfg.base_url or os.environ.get(f"{name.upper()}_BASE_URL")
    if name == "rest" and not base_url:
        base_url = os.environ.get("REST_API_BASE_URL")
    return cls(
        base_url=base_url,
        api_key=key,
        model=pcfg.default_model,
        **pcfg.extra,
    )
