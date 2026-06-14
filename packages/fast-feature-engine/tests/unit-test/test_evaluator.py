from __future__ import annotations

from typing import Any

import pytest

from fast_feature.engine import (
    JsonLogicEvaluator,
    OperatorRegistry,
    SimpleOperator,
    StandardOperators,
)
from fast_feature.engine.errors import JsonLogicError

evaluator = JsonLogicEvaluator(OperatorRegistry(StandardOperators.mapping()))


@pytest.mark.parametrize(
    ("rule", "data", "expected"),
    [
        # literals
        (1, {}, 1),
        ("x", {}, "x"),
        ({"a": 1, "b": 2}, {}, {"a": 1, "b": 2}),  # multi-key dict is data, not an op
        # var
        ({"var": "a"}, {"a": 5}, 5),
        ({"var": "a.b"}, {"a": {"b": 7}}, 7),
        ({"var": ["missing", "fallback"]}, {}, "fallback"),
        ({"var": ""}, {"a": 1}, {"a": 1}),
        # missing / missing_some
        ({"missing": ["a", "b"]}, {"a": 1}, ["b"]),
        ({"missing_some": [1, ["a", "b"]]}, {"a": 1}, []),
        ({"missing_some": [2, ["a", "b"]]}, {"a": 1}, ["b"]),
        # logic
        ({"if": [True, "yes", "no"]}, {}, "yes"),
        ({"if": [False, "yes", "no"]}, {}, "no"),
        ({"if": [False, "a", False, "b", "c"]}, {}, "c"),
        ({"and": [True, 3]}, {}, 3),
        ({"and": [False, 3]}, {}, False),
        ({"or": [0, "", "fallback"]}, {}, "fallback"),
        ({"!": [True]}, {}, False),
        ({"!!": [""]}, {}, False),
        # comparison
        ({"==": [1, "1"]}, {}, True),
        ({"===": [1, "1"]}, {}, False),
        ({"!=": [1, 2]}, {}, True),
        ({"<": [1, 2, 3]}, {}, True),
        ({"<": [1, 5, 3]}, {}, False),
        ({">": [3, 2]}, {}, True),
        ({">=": [3, 3]}, {}, True),
        # arithmetic
        ({"+": [1, 2, 3]}, {}, 6),
        ({"-": [5, 2]}, {}, 3),
        ({"-": [5]}, {}, -5),
        ({"*": [2, 3, 4]}, {}, 24),
        ({"/": [10, 4]}, {}, 2.5),
        ({"%": [10, 3]}, {}, 1),
        ({"min": [3, 1, 2]}, {}, 1),
        ({"max": [3, 1, 2]}, {}, 3),
        # strings / arrays
        ({"cat": ["a", "b", 1]}, {}, "ab1"),
        ({"substr": ["jsonlogic", 4]}, {}, "logic"),
        ({"substr": ["jsonlogic", -5, 2]}, {}, "lo"),
        ({"in": ["sub", "a substring"]}, {}, True),
        ({"in": ["x", ["a", "b"]]}, {}, False),
        ({"merge": [[1, 2], 3, [4]]}, {}, [1, 2, 3, 4]),
    ],
)
def test_evaluates_rule(rule: Any, data: Any, expected: Any) -> None:
    assert evaluator.apply(rule, data) == expected


def test_map_filter_reduce() -> None:
    data = {"nums": [1, 2, 3, 4]}
    assert evaluator.apply({"map": [{"var": "nums"}, {"*": [{"var": ""}, 2]}]}, data) == [
        2,
        4,
        6,
        8,
    ]
    assert evaluator.apply({"filter": [{"var": "nums"}, {">": [{"var": ""}, 2]}]}, data) == [3, 4]
    reduce_rule = {
        "reduce": [{"var": "nums"}, {"+": [{"var": "current"}, {"var": "accumulator"}]}, 0]
    }
    assert evaluator.apply(reduce_rule, data) == 10


def test_all_some_none() -> None:
    data = {"nums": [1, 2, 3]}
    assert evaluator.apply({"all": [{"var": "nums"}, {">": [{"var": ""}, 0]}]}, data) is True
    assert evaluator.apply({"some": [{"var": "nums"}, {">": [{"var": ""}, 2]}]}, data) is True
    assert evaluator.apply({"none": [{"var": "nums"}, {">": [{"var": ""}, 5]}]}, data) is True
    assert evaluator.apply({"all": [[], {"var": ""}]}, {}) is False


def test_unknown_operation_raises() -> None:
    with pytest.raises(JsonLogicError):
        evaluator.apply({"nope": [1]}, {})


def test_custom_operator_injection() -> None:
    class DoubleOperator(SimpleOperator):
        def compute(self, *values: Any) -> Any:
            return values[0] * 2

    registry = OperatorRegistry(StandardOperators.mapping()).extended_with(
        {"double": DoubleOperator()}
    )
    assert JsonLogicEvaluator(registry).apply({"double": [21]}, {}) == 42
