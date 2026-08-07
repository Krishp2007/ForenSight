"""
Question Router — ForenSight AI (Backward-Compatible Alias)
=============================================================
Delegates to query_router.classify_intent for unified intent routing.
"""

from backend.app.services.copilot.query_router import classify_intent

__all__ = ["classify_intent"]
