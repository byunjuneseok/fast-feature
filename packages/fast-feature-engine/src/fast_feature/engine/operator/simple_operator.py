from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from .operator import Operator

if TYPE_CHECKING:
    from fast_feature.engine.evaluator import JsonLogicEvaluator


class SimpleOperator(Operator):
    """An operator whose arguments are all eagerly evaluated before computing."""

    def apply(self, evaluator: JsonLogicEvaluator, args: list[Any], data: Any) -> Any:
        return self.compute(*[evaluator.apply(arg, data) for arg in args])

    @abstractmethod
    def compute(self, *values: Any) -> Any:
        """Compute the result from already-evaluated argument ``values``."""
