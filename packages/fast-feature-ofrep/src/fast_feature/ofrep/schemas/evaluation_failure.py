from __future__ import annotations

from pydantic import BaseModel, Field

from fast_feature.core import ErrorCode, EvaluationOutcome


class EvaluationFailure(BaseModel):
    """A failed flag evaluation, per the OFREP contract."""

    key: str
    error_code: str = Field(serialization_alias="errorCode")
    error_details: str | None = Field(default=None, serialization_alias="errorDetails")

    @classmethod
    def from_outcome(cls, outcome: EvaluationOutcome) -> EvaluationFailure:
        code = outcome.error_code or ErrorCode.GENERAL
        return cls(key=outcome.key, error_code=code.value, error_details=outcome.error_details)
