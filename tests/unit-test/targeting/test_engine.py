from __future__ import annotations

from typing import Any

from fast_feature.domain.evaluation import ErrorCode, Reason
from fast_feature.domain.flag import Flag, FlagState
from fast_feature.targeting.engine import TargetingEngine

engine = TargetingEngine()


def _flag(**overrides: Any) -> Flag:
    kwargs: dict[str, Any] = {
        "key": "color",
        "variants": {"red": "#f00", "blue": "#00f"},
        "default_variant": "red",
    }
    kwargs.update(overrides)
    return Flag(**kwargs)


def test_disabled_flag_resolves_default_with_disabled_reason() -> None:
    outcome = engine.evaluate(_flag(state=FlagState.DISABLED))
    assert outcome.reason is Reason.DISABLED
    assert outcome.variant == "red"
    assert outcome.value == "#f00"
    assert not outcome.is_error


def test_no_targeting_is_static() -> None:
    outcome = engine.evaluate(_flag())
    assert outcome.reason is Reason.STATIC
    assert outcome.variant == "red"


def test_targeting_match_returns_selected_variant() -> None:
    rule = {"if": [{"==": [{"var": "tier"}, "premium"]}, "blue", "red"]}
    outcome = engine.evaluate(_flag(targeting=rule), {"tier": "premium"})
    assert outcome.reason is Reason.TARGETING_MATCH
    assert outcome.variant == "blue"
    assert outcome.value == "#00f"


def test_targeting_null_falls_back_to_default() -> None:
    # `if` with no else branch yields None when the condition is false.
    rule = {"if": [{"==": [{"var": "tier"}, "premium"]}, "blue"]}
    outcome = engine.evaluate(_flag(targeting=rule), {"tier": "free"})
    assert outcome.reason is Reason.DEFAULT
    assert outcome.variant == "red"


def test_unknown_variant_is_an_error_with_default_value() -> None:
    rule = {"if": [True, "purple"]}
    outcome = engine.evaluate(_flag(targeting=rule), {})
    assert outcome.reason is Reason.ERROR
    assert outcome.error_code is ErrorCode.PARSE_ERROR
    assert outcome.variant == "red"
    assert outcome.value == "#f00"


def test_malformed_rule_is_an_error() -> None:
    outcome = engine.evaluate(_flag(targeting={"bogus_op": [1]}), {})
    assert outcome.reason is Reason.ERROR
    assert outcome.error_code is ErrorCode.PARSE_ERROR


def test_flag_key_is_available_to_targeting() -> None:
    rule = {"if": [{"==": [{"var": "$flag.key"}, "color"]}, "blue", "red"]}
    outcome = engine.evaluate(_flag(targeting=rule), {})
    assert outcome.variant == "blue"


def test_fractional_targeting_is_a_match() -> None:
    rule = {"fractional": [{"var": "targetingKey"}, ["red", 50], ["blue", 50]]}
    outcome = engine.evaluate(_flag(targeting=rule), {"targetingKey": "user-1"})
    assert outcome.reason is Reason.TARGETING_MATCH
    assert outcome.variant in {"red", "blue"}
