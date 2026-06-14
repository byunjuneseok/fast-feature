from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, ClassVar


@dataclass(frozen=True, order=True)
class SemanticVersion:
    """A comparable ``major.minor.patch`` version."""

    major: int
    minor: int
    patch: int

    _PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?")

    @classmethod
    def parse(cls, value: Any) -> SemanticVersion | None:
        if not isinstance(value, str):
            return None
        match = cls._PATTERN.match(value.strip())
        if match is None:
            return None
        return cls(int(match.group(1)), int(match.group(2) or 0), int(match.group(3) or 0))

    def satisfies(self, operator: Any, other: SemanticVersion) -> bool:
        if operator in ("=", "=="):
            return self == other
        if operator == "!=":
            return self != other
        if operator == "<":
            return self < other
        if operator == "<=":
            return self <= other
        if operator == ">":
            return self > other
        if operator == ">=":
            return self >= other
        if operator == "^":
            return self.major == other.major
        if operator == "~":
            return self.major == other.major and self.minor == other.minor
        return False
