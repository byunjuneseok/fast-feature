from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from fast_feature.core import Flag, FlagState


class FlagCreate(BaseModel):
    key: str
    variants: dict[str, Any]
    default_variant: str
    state: FlagState = FlagState.ENABLED
    targeting: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_flag(self) -> Flag:
        return Flag(
            key=self.key,
            variants=self.variants,
            default_variant=self.default_variant,
            state=self.state,
            targeting=self.targeting,
            metadata=self.metadata,
        )
