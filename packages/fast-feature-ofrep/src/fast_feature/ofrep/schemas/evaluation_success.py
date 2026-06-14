from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from fast_feature.core import EvaluationOutcome


class EvaluationSuccess(BaseModel):
    """A successful flag evaluation, per the OFREP contract."""

    key: str
    reason: str
    value: Any = None
    variant: str | None = None
    metadata: dict[str, Any] | None = None

    @classmethod
    def from_outcome(cls, outcome: EvaluationOutcome) -> EvaluationSuccess:
        return cls(
            key=outcome.key,
            reason=outcome.reason.value,
            value=outcome.value,
            variant=outcome.variant,
            metadata=outcome.metadata,
        )
