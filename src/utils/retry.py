"""Simple retry decorator helpers."""

from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


def retry(
    *,
    max_attempts: int = 3,
    initial_delay: float = 0.1,
    backoff_factor: float = 2.0,
    max_delay: float = 5.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    sleep_func: Callable[[float], None] = time.sleep,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Retry decorated function with bounded exponential backoff."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            delay = max(0.0, initial_delay)
            attempts = 0

            while True:
                attempts += 1
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempts >= max_attempts:
                        raise
                    sleep_func(delay)
                    delay = min(max_delay, delay * backoff_factor if delay > 0 else initial_delay)

        return wrapped

    return decorator
