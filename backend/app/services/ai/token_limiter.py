import time
from collections import deque
from typing import Deque, Tuple

class TokenBucket:
    """Simple sliding‑window token bucket.

    - `max_tokens_per_minute` is the quota (e.g. 20 000 tokens).
    - Calls to :meth:`consume` attempt to reserve the requested number of tokens.
    - If enough tokens are available, the method subtracts them and returns ``True``.
    - If the quota would be exceeded, it returns ``False`` (caller should fallback).
    """

    def __init__(self, max_tokens_per_minute: int = 20000):
        self.max_tokens = max_tokens_per_minute
        # Store (timestamp, tokens_used) pairs; timestamps are seconds since epoch.
        self._records: Deque[Tuple[float, int]] = deque()
        self._used = 0

    def _prune(self) -> None:
        """Remove entries older than 60 seconds from the window."""
        cutoff = time.time() - 60
        while self._records and self._records[0][0] < cutoff:
            _, tokens = self._records.popleft()
            self._used -= tokens
        if self._used < 0:
            self._used = 0

    def consume(self, tokens: int) -> bool:
        """Attempt to consume *tokens* from the bucket.

        Returns ``True`` if the reservation succeeded, ``False`` otherwise.
        """
        if tokens <= 0:
            return True
        self._prune()
        if self._used + tokens > self.max_tokens:
            return False
        self._records.append((time.time(), tokens))
        self._used += tokens
        return True
