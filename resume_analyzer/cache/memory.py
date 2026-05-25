from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    value: Any
    expires_at: float | None


class InMemoryTTLCache:
    """Small in-process TTL cache for local deployments and tests."""

    def __init__(
        self,
        default_ttl_seconds: int = 3600,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._default_ttl_seconds = default_ttl_seconds
        self._clock = clock
        self._entries: dict[str, CacheEntry] = {}

    def get(self, key: str):
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.expires_at is not None and entry.expires_at <= self._clock():
            self._entries.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value, ttl_seconds: int | None = None) -> None:
        ttl = self._default_ttl_seconds if ttl_seconds is None else ttl_seconds
        expires_at = None if ttl <= 0 else self._clock() + ttl
        self._entries[key] = CacheEntry(value=value, expires_at=expires_at)
