from __future__ import annotations

from fast_feature.engine.operator import Operator


class OperatorRegistry:
    """A name-to-operator lookup used by the evaluator."""

    def __init__(self, operators: dict[str, Operator] | None = None) -> None:
        self._operators: dict[str, Operator] = dict(operators or {})

    def register(self, name: str, operator: Operator) -> None:
        self._operators[name] = operator

    def resolve(self, name: str) -> Operator | None:
        return self._operators.get(name)

    def extended_with(self, operators: dict[str, Operator]) -> OperatorRegistry:
        """Return a new registry with ``operators`` added on top of this one."""
        merged = dict(self._operators)
        merged.update(operators)
        return OperatorRegistry(merged)

    def __contains__(self, name: object) -> bool:
        return name in self._operators
