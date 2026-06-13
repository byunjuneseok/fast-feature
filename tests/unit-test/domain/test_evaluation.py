from __future__ import annotations

from fast_feature.domain import ErrorCode, EvaluationOutcome, Reason


class TestEvaluationOutcome:
    def test_success_is_not_an_error(self) -> None:
        outcome = EvaluationOutcome(key="k", reason=Reason.STATIC, value=True, variant="on")
        assert not outcome.is_error

    def test_error_factory_marks_the_outcome(self) -> None:
        outcome = EvaluationOutcome.error("k", ErrorCode.FLAG_NOT_FOUND, "nope")
        assert outcome.is_error
        assert outcome.reason is Reason.ERROR
        assert outcome.error_code is ErrorCode.FLAG_NOT_FOUND
        assert outcome.error_details == "nope"
        assert outcome.value is None
