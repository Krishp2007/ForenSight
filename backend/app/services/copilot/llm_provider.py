"""
LLM Provider Base — ForenSight AI
====================================
Abstract base class that every LLM provider implements.
Swapping Gemini → Ollama → local requires zero changes outside this module.
"""

from abc import ABC, abstractmethod
from typing import Optional


class LLMProvider(ABC):
    """Abstract interface for all language model providers."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """
        Send a prompt and return the model's text response.
        Must raise an exception on failure so the router can fallback.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name for logging."""
