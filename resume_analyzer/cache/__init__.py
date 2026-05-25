"""Cache adapters."""

from resume_analyzer.cache.base import Cache
from resume_analyzer.cache.memory import InMemoryTTLCache

__all__ = ["Cache", "InMemoryTTLCache"]
