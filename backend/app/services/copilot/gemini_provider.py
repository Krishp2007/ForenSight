"""
Gemini Provider — ForenSight AI
==================================
Implements LLMProvider using Google Gemini 1.5 Flash.
Architecture reference: Section 6 — "LLM (fallback): Gemini 1.5 Flash via API"
"""

import os
import asyncio
import logging
from typing import Optional
import google.generativeai as genai

from backend.app.services.copilot.llm_provider import LLMProvider
from backend.app.config import settings

logger = logging.getLogger(__name__)


_WORKING_MODEL: str = os.getenv("GEMINI_MODEL", getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash"))
_WORKING_VER: str = "v1beta"


class GeminiProvider(LLMProvider):
    """Google Gemini provider optimized for 1-request per prompt execution."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or settings.GEMINI_API_KEY

    @property
    def name(self) -> str:
        return _WORKING_MODEL

    async def generate(self, prompt: str) -> str:
        global _WORKING_MODEL, _WORKING_VER

        if not self._api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        import httpx
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": 600,
                "temperature": 0.2,
            }
        }

        # DIRECT FAST-PATH: Send HTTP request to configured model
        url = f"https://generativelanguage.googleapis.com/{_WORKING_VER}/models/{_WORKING_MODEL}:generateContent?key={self._api_key}"
        async with httpx.AsyncClient(timeout=25.0) as client:
            try:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    if text:
                        return text
                elif res.status_code == 429:
                    logger.warning("Gemini API 429 Rate Limit hit.")
                    raise ValueError("⏳ Gemini API Rate Limit reached (15 requests/min). Please wait ~30 seconds before sending your next prompt.")
                elif res.status_code == 404:
                    logger.warning(f"Model {_WORKING_MODEL} returned 404, attempting fallback...")
                    _WORKING_MODEL = "gemini-1.5-flash"
                else:
                    msg = res.json().get("error", {}).get("message", res.text[:100])
                    raise ValueError(f"Google Gemini API error ({res.status_code}): {msg}")
            except httpx.HTTPError as err:
                raise ValueError(f"Network error connecting to Gemini API: {err}")

        # FALLBACK PATH (only if main model returned 404)
        fallback_models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
        async with httpx.AsyncClient(timeout=15.0) as client:
            for m in fallback_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={self._api_key}"
                try:
                    res = await client.post(url, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        if text:
                            _WORKING_MODEL = m
                            _WORKING_VER = "v1beta"
                            return text
                    elif res.status_code == 429:
                        raise ValueError("⏳ Gemini API Rate Limit reached (15 requests/min). Please wait ~30 seconds before sending your next prompt.")
                except Exception:
                    pass

        raise ValueError("Google Gemini API is temporarily unavailable.")
