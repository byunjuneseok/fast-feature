from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Hasher(Protocol):
    """A deterministic hash used for ``fractional`` bucketing."""

    @property
    def max_value(self) -> int:
        """The largest value ``hash`` can return (used to normalise to a ratio)."""

    def hash(self, key: str) -> int: ...
