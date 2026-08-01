"""
Ollama Provider — ForenSight AI
==================================
Implements LLMProvider using a locally running Ollama instance.
Architecture reference: Section 6 — "LLM (default): Llama 3.1 8B via Ollama"
"""

import logging
import httpx

from backend.app.services.copilot.llm_provider import LLMProvider
from backend.app.config import settings

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """
    Calls the Ollama REST API at /api/generate.
    Default model: llama3.1 (configurable via OLLAMA_MODEL env var).
    """

    def __init__(self, host: str = None, model: str = None):
        self._host = (host or settings.OLLAMA_HOST).rstrip("/")
        self._model = model or settings.OLLAMA_MODEL

    @property
    def name(self) -> str:
        return f"ollama/{self._model}"

    async def generate(self, prompt: str) -> str:
        logger.info(f"Calling Ollama ({self._model}) at {self._host}")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self._host}/api/generate",
                json={"model": self._model, "prompt": prompt, "stream": False},
            )
            if response.status_code == 200:
                text = response.json().get("response", "")
                if not text:
                    raise ValueError("Empty response from Ollama.")
                return text
            raise ValueError(
                f"Ollama returned HTTP {response.status_code}: {response.text[:200]}"
            )
