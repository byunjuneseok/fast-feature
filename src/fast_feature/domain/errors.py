from __future__ import annotations


class FastFeatureError(Exception):
    """Base class for all domain-level errors."""


class FlagNotFoundError(FastFeatureError):
    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"Flag {key!r} was not found")


class FlagAlreadyExistsError(FastFeatureError):
    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"Flag {key!r} already exists")


class InvalidFlagError(FastFeatureError):
    """Raised when a flag definition is structurally invalid."""
