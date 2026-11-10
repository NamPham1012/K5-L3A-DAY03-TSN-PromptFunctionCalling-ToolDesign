from __future__ import annotations

import os

from providers.openai_provider import OpenAIProvider


class GroqProvider(OpenAIProvider):
    """Groq exposes an OpenAI-compatible Chat Completions surface with tool calling."""

    def __init__(self) -> None:
        super().__init__(
            api_key_env="GROQ_API_KEY",
            base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            # Must be a tool-calling capable model. Override with --model if needed.
            default_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        )
