from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel

from fast_feature.core import EvaluationOutcome

from .evaluation_failure import EvaluationFailure
from .evaluation_success import EvaluationSuccess


class BulkEvaluationSuccess(BaseModel):
    """The bulk evaluation response: a mix of per-flag successes and failures."""

    flags: list[EvaluationSuccess | EvaluationFailure]
    metadata: dict[str, Any] | None = None

    @classmethod
    def from_outcomes(cls, outcomes: Iterable[EvaluationOutcome]) -> BulkEvaluationSuccess:
        flags: list[EvaluationSuccess | EvaluationFailure] = []
        for outcome in outcomes:
            if outcome.is_error:
                flags.append(EvaluationFailure.from_outcome(outcome))
            else:
                flags.append(EvaluationSuccess.from_outcome(outcome))
        return cls(flags=flags)
