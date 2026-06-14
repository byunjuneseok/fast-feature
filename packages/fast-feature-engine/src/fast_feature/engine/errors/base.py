from __future__ import annotations


class EngineError(Exception):
    """Base class for all targeting-engine errors.

    Dependents catch this at their boundary and re-raise as their own base
    error (with chaining) rather than coupling to the concrete subclasses.
    """
