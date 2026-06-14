from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fast_feature.engine.coercion import Coercion
from fast_feature.engine.operator import Operator, SimpleOperator

if TYPE_CHECKING:
    from fast_feature.engine.evaluator import JsonLogicEvaluator


class IfOperator(Operator):
    def apply(self, evaluator: JsonLogicEvaluator, args: list[Any], data: Any) -> Any:
        for index in range(0, len(args) - 1, 2):
            if Coercion.is_truthy(evaluator.apply(args[index], data)):
                return evaluator.apply(args[index + 1], data)
        if len(args) % 2:
            return evaluator.apply(args[-1], data)
        return None


class AndOperator(Operator):
    def apply(self, evaluator: JsonLogicEvaluator, args: list[Any], data: Any) -> Any:
        result: Any = True
        for arg in args:
            result = evaluator.apply(arg, data)
            if not Coercion.is_truthy(result):
                return result
        return result


class OrOperator(Operator):
    def apply(self, evaluator: JsonLogicEvaluator, args: list[Any], data: Any) -> Any:
        result: Any = False
        for arg in args:
            result = evaluator.apply(arg, data)
            if Coercion.is_truthy(result):
                return result
        return result


class NotOperator(SimpleOperator):
    def compute(self, *values: Any) -> bool:
        return not Coercion.is_truthy(values[0])


class ToBoolOperator(SimpleOperator):
    def compute(self, *values: Any) -> bool:
        return Coercion.is_truthy(values[0])
