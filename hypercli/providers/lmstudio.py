"""LM Studio provider — exposes an OpenAI-compatible local API."""

from __future__ import annotations

from typing import Any, Optional

from .openai_provider import OpenAIProvider


class LMStudioProvider(OpenAIProvider):
    name = "lmstudio"

    def __init__(self, base_url: str = "http://127.0.0.1:1234/v1",
                 api_key: Optional[str] = "lm-studio", model: Optional[str] = None,
                 **opts: Any) -> None:
        super().__init__(base_url=base_url, api_key=api_key or "lm-studio",
                         model=model or "local-model", **opts)
