"""
Gemini Provider — ForenSight AI
==================================
Implements LLMProvider using Google Gemini 1.5 Flash.
Architecture reference: Section 6 — "LLM (fallback): Gemini 1.5 Flash via API"
"""

import asyncio
import logging
from typing import Optional
import google.generativeai as genai

from backend.app.services.copilot.llm_provider import LLMProvider
from backend.app.config import settings

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini 1.5 Flash provider via the google-generativeai SDK."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or settings.GEMINI_API_KEY

    @property
    def name(self) -> str:
        return "gemini-1.5-flash"

    async def generate(self, prompt: str) -> str:
        if not self._api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, lambda: model.generate_content(prompt)
        )

        if response and response.text:
            logger.info("Gemini returned a valid response.")
            return response.text

        raise ValueError("Empty response from Google Gemini.")
