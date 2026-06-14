"""Canonical real-world targeting configurations, exercised end to end.

These mirror the well-known example flag set used to demonstrate JsonLogic-based
evaluation: a simple equality match, typed (non-boolean) variant payloads, and a
percentage rollout bucketed by a key derived from the flag and the user.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import pytest

from fast_feature.core import Flag, Reason
from fast_feature.engine import TargetingEngine

engine = TargetingEngine()


class TestColorEqualityTargeting:
    """on when the context color is yellow, otherwise off."""

    @staticmethod
    def _flag() -> Flag:
        return Flag(
            key="is-color-yellow",
            variants={"on": True, "off": False},
            default_variant="off",
            targeting={"if": [{"==": [{"var": ["color"]}, "yellow"]}, "on", "off"]},
        )

    @pytest.mark.parametrize(
        ("color", "expected"),
        [("yellow", "on"), ("blue", "off"), (None, "off")],
    )
    def test_color_match(self, color: str | None, expected: str) -> None:
        outcome = engine.evaluate(self._flag(), {"color": color})
        assert outcome.variant == expected
        assert outcome.reason is Reason.TARGETING_MATCH


class TestTypedVariants:
    """Non-boolean variant payloads resolve statically to their default."""

    @pytest.mark.parametrize(
        ("flag", "expected_value"),
        [
            (
                Flag(key="my-int-flag", variants={"one": 1, "two": 2}, default_variant="one"),
                1,
            ),
            (
                Flag(
                    key="my-float-flag",
                    variants={"one": 1.23, "two": 2.34},
                    default_variant="one",
                ),
                1.23,
            ),
            (
                Flag(
                    key="my-object-flag",
                    variants={"object1": {"key": "val"}, "object2": {"key": True}},
                    default_variant="object1",
                ),
                {"key": "val"},
            ),
        ],
    )
    def test_static_default(self, flag: Flag, expected_value: Any) -> None:
        outcome = engine.evaluate(flag)
        assert outcome.value == expected_value
        assert outcome.reason is Reason.STATIC


class TestHeaderColorRollout:
    """Internal users get an even four-way color split, bucketed by flag key plus
    email so each user is sticky; everyone else falls back to the default."""

    @staticmethod
    def _flag() -> Flag:
        return Flag(
            key="header-color",
            variants={
                "red": "#FF0000",
                "blue": "#0000FF",
                "green": "#00FF00",
                "yellow": "#FFFF00",
            },
            default_variant="red",
            targeting={
                "if": [
                    {"in": ["@faas.com", {"var": "email"}]},
                    {
                        "fractional": [
                            {"cat": [{"var": "$flag.key"}, {"var": "email"}]},
                            ["red", 25],
                            ["blue", 25],
                            ["green", 25],
                            ["yellow", 25],
                        ]
                    },
                    None,
                ]
            },
        )

    def test_external_email_falls_to_default(self) -> None:
        outcome = engine.evaluate(self._flag(), {"email": "user@gmail.com"})
        assert outcome.variant == "red"
        assert outcome.reason is Reason.DEFAULT

    def test_internal_email_is_assigned_a_color(self) -> None:
        outcome = engine.evaluate(self._flag(), {"email": "alice@faas.com"})
        assert outcome.variant in {"red", "blue", "green", "yellow"}
        assert outcome.reason is Reason.TARGETING_MATCH

    def test_assignment_is_sticky_per_email(self) -> None:
        flag = self._flag()
        first = engine.evaluate(flag, {"email": "bob@faas.com"}).variant
        assert engine.evaluate(flag, {"email": "bob@faas.com"}).variant == first

    def test_split_is_balanced_across_internal_users(self) -> None:
        counts: Counter[str] = Counter()
        for i in range(4000):
            variant = engine.evaluate(self._flag(), {"email": f"user{i}@faas.com"}).variant
            assert variant is not None
            counts[variant] += 1
        assert set(counts) == {"red", "blue", "green", "yellow"}
        for color in ("red", "blue", "green", "yellow"):
            assert 700 < counts[color] < 1300  # ~1000 each (25% of 4000)
