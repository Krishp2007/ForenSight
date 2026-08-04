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


_WORKING_MODEL: Optional[str] = None
_WORKING_VER: Optional[str] = None


class GeminiProvider(LLMProvider):
    """Google Gemini provider with memory caching & fast-path REST execution (<1s latency)."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or settings.GEMINI_API_KEY

    @property
    def name(self) -> str:
        return _WORKING_MODEL or "gemini-1.5-flash"

    async def generate(self, prompt: str) -> str:
        global _WORKING_MODEL, _WORKING_VER

        if not self._api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        import httpx
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        # FAST-PATH: Use previously verified working model & version immediately
        if _WORKING_MODEL and _WORKING_VER:
            url = f"https://generativelanguage.googleapis.com/{_WORKING_VER}/models/{_WORKING_MODEL}:generateContent?key={self._api_key}"
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    res = await client.post(url, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        if text:
                            return text
            except Exception as e:
                logger.warning(f"Fast-path model {_WORKING_MODEL} failed ({e}), clearing cache...")
                _WORKING_MODEL = None
                _WORKING_VER = None

        # DISCOVERY & RECOVERY PATH (runs once or on cache miss)
        models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro", "gemini-2.0-flash-exp"]
        errors = []
        is_rate_limited = False

        async with httpx.AsyncClient(timeout=12.0) as client:
            for ver in ["v1beta", "v1"]:
                for m in models_to_try:
                    url = f"https://generativelanguage.googleapis.com/{ver}/models/{m}:generateContent?key={self._api_key}"
                    try:
                        res = await client.post(url, json=payload)
                        if res.status_code == 200:
                            data = res.json()
                            text = data["candidates"][0]["content"]["parts"][0]["text"]
                            if text:
                                _WORKING_MODEL = m
                                _WORKING_VER = ver
                                logger.info(f"Successfully cached working model: {ver}/{m}")
                                return text
                        elif res.status_code == 429:
                            is_rate_limited = True
                            msg = res.json().get("error", {}).get("message", "Quota / Rate Limit Exceeded")
                            errors.append(f"Rate Limit (429): {msg}")
                        else:
                            msg = res.json().get("error", {}).get("message", res.text[:80])
                            errors.append(f"{ver}/{m}: {res.status_code} ({msg})")
                    except Exception as err:
                        errors.append(f"{ver}/{m}: {err}")

        if is_rate_limited:
            raise ValueError("⏳ Gemini Free Tier Rate Limit reached (15 requests/min). Please wait ~45 seconds before asking your next question.")

        raise ValueError(f"Google Gemini API error: {'; '.join(errors[:2])}")
