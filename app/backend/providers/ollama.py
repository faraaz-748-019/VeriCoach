"""Ollama local LLM provider for VeriCoach backend."""

from __future__ import annotations

import httpx

from backend.providers.base import BaseLLMProvider, LLMResponse


class OllamaLLMProvider(BaseLLMProvider):
    """Calls a locally running Ollama server."""

    def __init__(
        self, base_url: str = "http://localhost:11434", model: str = "llama3"
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    def complete(self, prompt: str, **kwargs: object) -> LLMResponse:
        url = f"{self._base_url}/api/generate"
        payload = {"model": self._model, "prompt": prompt, "stream": False}
        try:
            resp = httpx.post(url, json=payload, timeout=60.0)
            resp.raise_for_status()
            data = resp.json()
            text: str = data.get("response", "")
            pt: int = data.get("prompt_eval_count", 0)
            ct: int = data.get("eval_count", 0)
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
        return LLMResponse(
            text=text,
            provider=self.provider_name,
            model=self._model,
            prompt_tokens=pt,
            completion_tokens=ct,
        )

    def embed(self, text: str) -> list[float]:
        url = f"{self._base_url}/api/embeddings"
        payload = {"model": self._model, "prompt": text}
        try:
            resp = httpx.post(url, json=payload, timeout=30.0)
            resp.raise_for_status()
            return resp.json().get("embedding", [])
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Ollama embeddings failed: {exc}") from exc

    @property
    def provider_name(self) -> str:
        return "ollama"
