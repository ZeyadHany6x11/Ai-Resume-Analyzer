from __future__ import annotations

from collections.abc import Callable
from typing import Protocol


class BackgroundRunner(Protocol):
    def add_task(self, func: Callable, *args, **kwargs) -> None: ...


class InlineBackgroundRunner:
    """Run background work immediately for deterministic tests and local use."""

    def add_task(self, func: Callable, *args, **kwargs) -> None:
        func(*args, **kwargs)
