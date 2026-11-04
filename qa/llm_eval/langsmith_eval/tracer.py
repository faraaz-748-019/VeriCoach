"""LangSmith tracing configuration and helper decorators for VeriCoach."""

from __future__ import annotations

import functools
import os
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def is_langsmith_tracing_enabled() -> bool:
    """Check if LangSmith tracing is enabled via environment variables."""
    return os.getenv("LANGSMITH_TRACING", "").lower() in ("true", "1", "yes")


try:
    from langsmith import traceable as _ls_traceable

    def traceable(*args: Any, **kwargs: Any) -> Callable[[F], F]:
        """Wrap langsmith.traceable with graceful fallback when tracing is disabled."""
        inner_dec = _ls_traceable(*args, **kwargs)

        def decorator(func: F) -> F:
            wrapped = inner_dec(func)

            @functools.wraps(func)
            def wrapper(*a: Any, **kw: Any) -> Any:
                return wrapped(*a, **kw)

            return wrapper  # type: ignore[return-value]

        if args and callable(args[0]):
            fn = args[0]
            return _ls_traceable(fn)  # type: ignore[no-any-return]

        return decorator

except ImportError:

    def traceable(*args: Any, **kwargs: Any) -> Callable[[F], F]:  # type: ignore[misc]
        """No-op fallback decorator if langsmith is not installed."""

        def decorator(func: F) -> F:
            @functools.wraps(func)
            def wrapper(*a: Any, **kw: Any) -> Any:
                return func(*a, **kw)

            return wrapper  # type: ignore[return-value]

        if args and callable(args[0]):
            return args[0]
        return decorator
