from __future__ import annotations

from typing import Any

import pytest

from fast_feature.engine.coercion import Coercion
from fast_feature.engine.errors import JsonLogicError


class TestIsTruthy:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (None, False),
            (False, False),
            (True, True),
            (0, False),
            (1, True),
            (0.0, False),
            (2.5, True),
            ("", False),
            ("x", True),
            ([], False),
            ([1], True),
            ({}, True),
            ({"a": 1}, True),
        ],
    )
    def test_is_truthy(self, value: Any, expected: bool) -> None:
        assert Coercion.is_truthy(value) is expected


class TestToStr:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [(None, ""), (True, "true"), (False, "false"), (1, "1"), ("x", "x")],
    )
    def test_to_str(self, value: Any, expected: str) -> None:
        assert Coercion.to_str(value) == expected


class TestToNumber:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [(True, 1), (False, 0), (3, 3), (2.5, 2.5), ("4", 4), ("2.5", 2.5), ("1e3", 1000.0)],
    )
    def test_converts(self, value: Any, expected: float) -> None:
        assert Coercion.to_number(value) == expected

    @pytest.mark.parametrize("value", ["abc", None, [1]])
    def test_rejects_non_numbers(self, value: Any) -> None:
        with pytest.raises(JsonLogicError):
            Coercion.to_number(value)


class TestEquality:
    def test_soft_equals(self) -> None:
        assert Coercion.soft_equals(1, "1")
        assert Coercion.soft_equals(True, 1) is True
        assert Coercion.soft_equals(1, 2) is False
        assert Coercion.soft_equals("a", "a")

    def test_hard_equals(self) -> None:
        assert Coercion.hard_equals(1, 1)
        assert Coercion.hard_equals(1, "1") is False
        assert Coercion.hard_equals(True, 1) is False


class TestComparison:
    def test_less_than(self) -> None:
        assert Coercion.less_than(1, 2)
        assert Coercion.less_than("a", "b")

    def test_less_than_or_equal(self) -> None:
        assert Coercion.less_than_or_equal(2, 2)
        assert Coercion.less_than_or_equal("a", "a")
