from __future__ import annotations


class CoreError(Exception):
    """Base class for all fast-feature-core errors.

    Dependents catch this at their boundary and re-raise as their own base
    error (with chaining) rather than coupling to the concrete subclasses.
    """


class FlagNotFoundError(CoreError):
    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"Flag {key!r} was not found")


class FlagAlreadyExistsError(CoreError):
    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"Flag {key!r} already exists")


class InvalidFlagError(CoreError):
    """Raised when a flag definition is structurally invalid."""
