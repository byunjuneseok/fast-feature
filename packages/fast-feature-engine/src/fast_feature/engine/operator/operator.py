from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fast_feature.engine.evaluator import JsonLogicEvaluator


class Operator(ABC):
    """A JsonLogic operation.

    The operator owns how its arguments are evaluated, so control-flow
    operators (``if``, ``and``, iterators, ...) can evaluate lazily.
    """

    @abstractmethod
    def apply(self, evaluator: JsonLogicEvaluator, args: list[Any], data: Any) -> Any:
        """Evaluate this operation's ``args`` against ``data``."""
