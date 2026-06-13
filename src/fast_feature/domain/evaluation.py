from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .types import JsonValue


class Reason(str, Enum):
    """OpenFeature resolution reasons.

    OFREP's core enum is a subset of these; the wider set is kept because the
    OpenFeature specification treats ``reason`` as an open string.
    """

    STATIC = "STATIC"
    DEFAULT = "DEFAULT"
    TARGETING_MATCH = "TARGETING_MATCH"
    SPLIT = "SPLIT"
    DISABLED = "DISABLED"
    CACHED = "CACHED"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"


class ErrorCode(str, Enum):
    """OpenFeature error codes used when an evaluation fails."""

    FLAG_NOT_FOUND = "FLAG_NOT_FOUND"
    PARSE_ERROR = "PARSE_ERROR"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    INVALID_CONTEXT = "INVALID_CONTEXT"
    TARGETING_KEY_MISSING = "TARGETING_KEY_MISSING"
    PROVIDER_NOT_READY = "PROVIDER_NOT_READY"
    GENERAL = "GENERAL"


@dataclass
class EvaluationOutcome:
    """The result of evaluating a single flag against a context."""

    key: str
    reason: Reason
    value: JsonValue = None
    variant: str | None = None
    metadata: dict[str, JsonValue] | None = None
    error_code: ErrorCode | None = None
    error_details: str | None = None

    @property
    def is_error(self) -> bool:
        return self.error_code is not None

    @classmethod
    def error(
        cls,
        key: str,
        error_code: ErrorCode,
        details: str | None = None,
    ) -> EvaluationOutcome:
        return cls(
            key=key,
            reason=Reason.ERROR,
            error_code=error_code,
            error_details=details,
        )
