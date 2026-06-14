from __future__ import annotations

from typing import Any

from fast_feature.engine import OperatorRegistry, SimpleOperator


class _DoubleOperator(SimpleOperator):
    def compute(self, *values: Any) -> Any:
        return values[0] * 2


class TestOperatorRegistry:
    def test_register_and_resolve(self) -> None:
        registry = OperatorRegistry()
        operator = _DoubleOperator()
        registry.register("double", operator)
        assert registry.resolve("double") is operator

    def test_resolve_unknown_is_none(self) -> None:
        assert OperatorRegistry().resolve("nope") is None

    def test_contains(self) -> None:
        registry = OperatorRegistry({"double": _DoubleOperator()})
        assert "double" in registry
        assert "nope" not in registry

    def test_extended_with_does_not_mutate_the_original(self) -> None:
        base = OperatorRegistry({"a": _DoubleOperator()})
        extended = base.extended_with({"b": _DoubleOperator()})
        assert "b" in extended
        assert "a" in extended
        assert "b" not in base
