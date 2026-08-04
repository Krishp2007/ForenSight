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
<<<<<<< HEAD
                "maxOutputTokens": 450,
=======
                "maxOutputTokens": 600,
>>>>>>> 58261d1cef3b9e67659c851a986a40a740be14b7
                "temperature": 0.2,
            }
        }

        # DIRECT FAST-PATH: Send HTTP request to configured model
<<<<<<< HEAD
        models_to_try = [_WORKING_MODEL, "gemini-1.5-flash", "gemini-2.0-flash-exp", "gemini-1.5-pro"]
        seen = set()
        models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

        headers = {"Content-Type": "application/json"}
        is_gcp_token = self._api_key.startswith("AQ.") or self._api_key.startswith("ya29.")
        if is_gcp_token:
            headers["Authorization"] = f"Bearer {self._api_key}"

        async with httpx.AsyncClient(timeout=8.0) as client:
            for m in models_to_try:
                # 1. Standard Generative Language API
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={self._api_key}"
                try:
                    res = await client.post(url, json=payload, headers=headers)
=======
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
>>>>>>> 58261d1cef3b9e67659c851a986a40a740be14b7
                    if res.status_code == 200:
                        data = res.json()
                        text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")
                        if text:
                            _WORKING_MODEL = m
<<<<<<< HEAD
                            return text
                    elif res.status_code == 429:
                        logger.warning(f"Gemini model {m} rate limited (429), trying next model...")
                        await asyncio.sleep(0.3)
                        continue
                except Exception as err:
                    logger.warning(f"Error querying Gemini model {m}: {err}")

                # 2. GCP Vertex AI Publisher Endpoint (for AQ... GCP Tokens)
                if is_gcp_token:
                    v_url = f"https://us-central1-aiplatform.googleapis.com/v1/projects/186503242427/locations/us-central1/publishers/google/models/{m}:generateContent"
                    try:
                        res = await client.post(v_url, json=payload, headers={"Authorization": f"Bearer {self._api_key}"})
                        if res.status_code == 200:
                            data = res.json()
                            candidates = data.get("candidates") or data.get("predictions") or []
                            if candidates:
                                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text")
                                if text:
                                    return text
                    except Exception as err:
                        logger.warning(f"Vertex AI request failed for model {m}: {err}")

        # If all API calls were rate limited or failed, raise ValueError
        raise ValueError("Gemini API models returned rate-limit or authorization error.")
=======
                            _WORKING_VER = "v1beta"
                            return text
                    elif res.status_code == 429:
                        raise ValueError("⏳ Gemini API Rate Limit reached (15 requests/min). Please wait ~30 seconds before sending your next prompt.")
                except Exception:
                    pass

        raise ValueError("Google Gemini API is temporarily unavailable.")
>>>>>>> 58261d1cef3b9e67659c851a986a40a740be14b7
