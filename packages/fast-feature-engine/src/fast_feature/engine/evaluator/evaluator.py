from __future__ import annotations

from typing import Any

from fast_feature.engine.errors import JsonLogicError
from fast_feature.engine.registry import OperatorRegistry


class JsonLogicEvaluator:
    """Evaluates a JsonLogic rule against a data object using a registry."""

    def __init__(self, registry: OperatorRegistry) -> None:
        self._registry = registry

    def apply(self, rule: Any, data: Any = None) -> Any:
        if data is None:
            data = {}
        if isinstance(rule, list):
            return [self.apply(item, data) for item in rule]
        if not self._is_operation(rule):
            return rule
        name, raw = next(iter(rule.items()))
        args = raw if isinstance(raw, list) else [raw]
        operator = self._registry.resolve(name)
        if operator is None:
            raise JsonLogicError(f"Unrecognized operation {name!r}")
        return operator.apply(self, args, data)

    @staticmethod
    def _is_operation(rule: Any) -> bool:
        return isinstance(rule, dict) and len(rule) == 1 and isinstance(next(iter(rule)), str)
