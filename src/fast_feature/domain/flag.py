from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .errors import InvalidFlagError
from .types import JsonValue

_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


class FlagState(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


@dataclass
class Flag:
    """A feature flag, modelled after the flagd flag definition.

    A flag holds a set of named ``variants`` and resolves to exactly one of
    them. Resolution is governed by an optional ``targeting`` rule (JsonLogic);
    in its absence the ``default_variant`` is used.
    """

    key: str
    variants: dict[str, JsonValue]
    default_variant: str
    state: FlagState = FlagState.ENABLED
    targeting: dict[str, JsonValue] | None = None
    metadata: dict[str, JsonValue] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not _KEY_PATTERN.match(self.key):
            raise InvalidFlagError(
                f"Invalid flag key {self.key!r}: must match {_KEY_PATTERN.pattern}"
            )
        if not self.variants:
            raise InvalidFlagError(f"Flag {self.key!r} must define at least one variant")
        if self.default_variant not in self.variants:
            raise InvalidFlagError(
                f"Flag {self.key!r} default variant {self.default_variant!r} "
                "is not among its variants"
            )

    @property
    def default_value(self) -> JsonValue:
        return self.variants[self.default_variant]

    def value_of(self, variant: str) -> JsonValue:
        return self.variants[variant]

    def has_variant(self, variant: str) -> bool:
        return variant in self.variants
