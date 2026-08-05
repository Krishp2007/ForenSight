"""
Groq Provider — ForenSight AI Copilot
======================================
Production-grade async Groq LLM client with:
- Streaming SSE support
- Retry logic (3 attempts with exponential backoff)
- Timeout handling (25s connect, 60s read)
- Rate-limit detection (429 → immediate exception)
- Auth failure detection (401/403 → immediate exception)
- Model configurable via GROQ_MODEL env var
- Clean fallback-friendly exception hierarchy
"""

import asyncio
import json
import logging
import os
from typing import AsyncGenerator, Optional

import httpx

from backend.app.config import settings

logger = logging.getLogger(__name__)

GROQ_API_BASE = "https://api.groq.com/openai/v1"
_INSUFFICIENT_PHRASES = [
    "i don't know",
    "i do not know",
    "no relevant information",
    "unable to answer",
    "not enough evidence",
    "insufficient context",
    "i cannot answer",
    "i'm unable",
    "no information found",
    "cannot determine",
]


class GroqError(Exception):
    """Base Groq exception — triggers fallback."""
    pass


class GroqRateLimitError(GroqError):
    """429 Rate Limit — triggers fallback."""
    pass


class GroqAuthError(GroqError):
    """401/403 Auth failure — triggers fallback."""
    pass


class GroqTimeoutError(GroqError):
    """Timeout — triggers fallback."""
    pass


class GroqInsufficientResponseError(GroqError):
    """Groq answered but said it doesn't know — triggers fallback."""
    pass


def _is_insufficient(text: str) -> bool:
    """Detect low-value Groq responses that should trigger fallback."""
    if not text or len(text.strip()) < 50:
        return True
    tl = text.lower().strip()
    return any(phrase in tl for phrase in _INSUFFICIENT_PHRASES)


class GroqProvider:
    """
    Async Groq LLM provider with streaming and fault-tolerant retry logic.
    All public methods raise GroqError subclasses on failure so the caller
    can catch and route to fallback without inspecting HTTP status codes.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key or os.getenv("GROQ_API_KEY", getattr(settings, "GROQ_API_KEY", ""))
        self._model = model or os.getenv("GROQ_MODEL", getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile"))
        self._max_retries = 3
        self._timeout = httpx.Timeout(connect=25.0, read=90.0, write=15.0, pool=10.0)

    @property
    def name(self) -> str:
        return f"groq/{self._model}"

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _build_messages(self, system_prompt: str, user_prompt: str, history: list) -> list:
        """Build OpenAI-compatible messages array for Groq API."""
        messages = [{"role": "system", "content": system_prompt}]

        # Inject last 6 history turns (3 exchanges) for conversation memory
        for turn in (history or [])[-6:]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content[:2000]})  # cap per-turn

        messages.append({"role": "user", "content": user_prompt})
        return messages

    async def generate(self, system_prompt: str, user_prompt: str, history: list = None) -> str:
        """
        Non-streaming generation with retry.
        Returns full text string.
        Raises GroqError subclass on any failure.
        """
        if not self._api_key:
            raise GroqAuthError("GROQ_API_KEY not configured")

        messages = self._build_messages(system_prompt, user_prompt, history or [])
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.15,
            "max_tokens": 2048,
            "stream": False,
        }

        last_err = None
        for attempt in range(1, self._max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    resp = await client.post(
                        f"{GROQ_API_BASE}/chat/completions",
                        headers=self._headers(),
                        json=payload,
                    )

                if resp.status_code == 200:
                    data = resp.json()
                    text = data["choices"][0]["message"]["content"]
                    if _is_insufficient(text):
                        raise GroqInsufficientResponseError(
                            f"Groq response insufficient: {text[:100]}"
                        )
                    logger.info(f"[Groq] Generated successfully on attempt {attempt}")
                    return text

                elif resp.status_code == 429:
                    raise GroqRateLimitError(f"Groq rate limit (429) on attempt {attempt}")

                elif resp.status_code in (401, 403):
                    raise GroqAuthError(f"Groq auth failure ({resp.status_code})")

                elif resp.status_code >= 500:
                    err_msg = resp.json().get("error", {}).get("message", resp.text[:100])
                    last_err = GroqError(f"Groq server error {resp.status_code}: {err_msg}")
                    wait = 2 ** attempt
                    logger.warning(f"[Groq] Server error on attempt {attempt}, retrying in {wait}s...")
                    await asyncio.sleep(wait)

                else:
                    err_msg = resp.text[:200]
                    raise GroqError(f"Groq unexpected status {resp.status_code}: {err_msg}")

            except (GroqRateLimitError, GroqAuthError, GroqInsufficientResponseError):
                raise  # Don't retry auth/rate-limit errors
            except httpx.TimeoutException as e:
                last_err = GroqTimeoutError(f"Groq timeout on attempt {attempt}: {e}")
                logger.warning(f"[Groq] Timeout on attempt {attempt}")
                await asyncio.sleep(2 ** attempt)
            except httpx.ConnectError as e:
                last_err = GroqError(f"Groq connection error on attempt {attempt}: {e}")
                logger.warning(f"[Groq] Connection error on attempt {attempt}")
                await asyncio.sleep(2 ** attempt)

        raise last_err or GroqError("Groq failed after all retries")

    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        history: list = None,
    ) -> AsyncGenerator[str, None]:
        """
        Streaming generation — yields text chunks as they arrive.
        On any failure, raises GroqError so the caller switches to fallback.
        """
        if not self._api_key:
            raise GroqAuthError("GROQ_API_KEY not configured")

        messages = self._build_messages(system_prompt, user_prompt, history or [])
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.15,
            "max_tokens": 2048,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                async with client.stream(
                    "POST",
                    f"{GROQ_API_BASE}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                ) as resp:

                    if resp.status_code == 429:
                        raise GroqRateLimitError("Groq rate limit (429)")
                    if resp.status_code in (401, 403):
                        raise GroqAuthError(f"Groq auth failure ({resp.status_code})")
                    if resp.status_code >= 500:
                        raise GroqError(f"Groq server error {resp.status_code}")
                    if resp.status_code != 200:
                        raise GroqError(f"Groq unexpected status {resp.status_code}")

                    full_text = ""
                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0]["delta"]
                            chunk = delta.get("content", "")
                            if chunk:
                                full_text += chunk
                                yield chunk
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

                    if _is_insufficient(full_text):
                        raise GroqInsufficientResponseError(
                            f"Groq streaming response insufficient"
                        )

        except (GroqRateLimitError, GroqAuthError, GroqInsufficientResponseError, GroqError):
            raise
        except httpx.TimeoutException as e:
            raise GroqTimeoutError(f"Groq stream timeout: {e}")
        except httpx.ConnectError as e:
            raise GroqError(f"Groq stream connection error: {e}")
        except Exception as e:
            raise GroqError(f"Groq stream unexpected error: {e}")
