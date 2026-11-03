"""Google Gemini LLM provider for VeriCoach backend."""

from __future__ import annotations

import os

from backend.providers.base import BaseLLMProvider, LLMResponse


class GeminiLLMProvider(BaseLLMProvider):
    """
    Wraps google-generativeai for text generation and multilingual embeddings.
    Requires GOOGLE_API_KEY.
    """

    def __init__(
        self,
        model: str = "gemini-1.5-flash",
        embedding_model: str = "text-embedding-004",
        api_key: str | None = None,
    ) -> None:
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise ImportError(
                "Install google-generativeai: pip install google-generativeai"
            ) from exc

        resolved_key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        if not resolved_key:
            raise ValueError(
                "GOOGLE_API_KEY is required for the Gemini provider. "
                "Set LLM_PROVIDER=mock for zero-network testing."
            )

        genai.configure(api_key=resolved_key)
        self._genai = genai
        self._model_name = model
        self._embedding_model = embedding_model
        self._client = genai.GenerativeModel(model_name=model)

    def complete(self, prompt: str, **kwargs: object) -> LLMResponse:
        response = self._client.generate_content(prompt)
        text = response.text or ""
        usage = getattr(response, "usage_metadata", None)
        pt = getattr(usage, "prompt_token_count", 0) or 0
        ct = getattr(usage, "candidates_token_count", 0) or 0
        return LLMResponse(
            text=text,
            provider=self.provider_name,
            model=self._model_name,
            prompt_tokens=pt,
            completion_tokens=ct,
        )

    def embed(self, text: str) -> list[float]:
        result = self._genai.embed_content(
            model=self._embedding_model,
            content=text,
        )
        return result["embedding"]

    @property
    def provider_name(self) -> str:
        return "gemini"
