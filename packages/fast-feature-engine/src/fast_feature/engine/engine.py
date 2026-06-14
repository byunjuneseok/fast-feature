from __future__ import annotations

from fast_feature.core.evaluation import ErrorCode, EvaluationOutcome, Reason
from fast_feature.core.flag import Flag, FlagState
from fast_feature.core.types import EvaluationContext, JsonValue

from .jsonlogic import JsonLogic, JsonLogicError
from .operators import TARGETING_LAZY_OPS, TARGETING_SIMPLE_OPS


class TargetingEngine:
    """Resolves a flag against a context using the following evaluation semantics.

    - ``DISABLED`` flag                  → reason ``DISABLED``
    - no targeting rule                  → reason ``STATIC``
    - targeting returns a known variant  → reason ``TARGETING_MATCH``
    - targeting returns ``null``         → reason ``DEFAULT``
    - targeting errors / unknown variant → reason ``ERROR`` (``PARSE_ERROR``)

    In every non-match case the flag's default variant value is returned, so a
    caller always receives a usable value.
    """

    def __init__(self) -> None:
        self._jsonlogic = JsonLogic(simple_ops=TARGETING_SIMPLE_OPS, lazy_ops=TARGETING_LAZY_OPS)

    def evaluate(self, flag: Flag, context: EvaluationContext | None = None) -> EvaluationOutcome:
        if flag.state is FlagState.DISABLED:
            return self._resolved(flag, flag.default_variant, Reason.DISABLED)

        if not flag.targeting:
            return self._resolved(flag, flag.default_variant, Reason.STATIC)

        try:
            result = self._jsonlogic.apply(flag.targeting, self._build_data(flag, context))
        except JsonLogicError as exc:
            return self._errored(flag, str(exc))

        if result is None:
            return self._resolved(flag, flag.default_variant, Reason.DEFAULT)
        if not isinstance(result, str) or not flag.has_variant(result):
            return self._errored(
                flag, f"targeting resolved to {result!r}, which is not a defined variant"
            )
        return self._resolved(flag, result, Reason.TARGETING_MATCH)

    @staticmethod
    def _build_data(flag: Flag, context: EvaluationContext | None) -> dict[str, JsonValue]:
        data: dict[str, JsonValue] = dict(context or {})
        data["$flag"] = {"key": flag.key}
        return data

    @staticmethod
    def _resolved(flag: Flag, variant: str, reason: Reason) -> EvaluationOutcome:
        return EvaluationOutcome(
            key=flag.key,
            reason=reason,
            value=flag.value_of(variant),
            variant=variant,
            metadata=flag.metadata or None,
        )

    @staticmethod
    def _errored(flag: Flag, details: str) -> EvaluationOutcome:
        return EvaluationOutcome(
            key=flag.key,
            reason=Reason.ERROR,
            value=flag.default_value,
            variant=flag.default_variant,
            metadata=flag.metadata or None,
            error_code=ErrorCode.PARSE_ERROR,
            error_details=details,
        )
