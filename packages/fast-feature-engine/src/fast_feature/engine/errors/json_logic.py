from __future__ import annotations

from .base import EngineError


class JsonLogicError(EngineError):
    """Raised when a rule is malformed or cannot be evaluated."""
