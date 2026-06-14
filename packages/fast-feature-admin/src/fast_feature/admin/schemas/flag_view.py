from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from fast_feature.core import Flag, FlagState


class FlagView(BaseModel):
    key: str
    variants: dict[str, Any]
    default_variant: str
    state: FlagState
    targeting: dict[str, Any] | None = None
    metadata: dict[str, Any] = {}
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_flag(cls, flag: Flag) -> FlagView:
        return cls(
            key=flag.key,
            variants=flag.variants,
            default_variant=flag.default_variant,
            state=flag.state,
            targeting=flag.targeting,
            metadata=flag.metadata,
            created_at=flag.created_at,
            updated_at=flag.updated_at,
        )
