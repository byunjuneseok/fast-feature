from __future__ import annotations

from pydantic import BaseModel, Field

from fast_feature.core import ErrorCode, EvaluationOutcome


class FlagNotFound(BaseModel):
    """The 404 body returned when a flag key does not exist."""

    key: str
    error_code: str = Field(default=ErrorCode.FLAG_NOT_FOUND.value, serialization_alias="errorCode")
    error_details: str | None = Field(default=None, serialization_alias="errorDetails")

    @classmethod
    def from_outcome(cls, outcome: EvaluationOutcome) -> FlagNotFound:
        return cls(key=outcome.key, error_details=outcome.error_details)
