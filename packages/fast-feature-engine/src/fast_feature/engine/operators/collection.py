from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fast_feature.engine.coercion import Coercion
from fast_feature.engine.operator import Operator, SimpleOperator

if TYPE_CHECKING:
    from fast_feature.engine.evaluator import JsonLogicEvaluator


class InOperator(SimpleOperator):
    def compute(self, *values: Any) -> bool:
        needle, haystack = values[0], values[1]
        if isinstance(haystack, str):
            return Coercion.to_str(needle) in haystack
        if isinstance(haystack, list):
            return needle in haystack
        return False


class CatOperator(SimpleOperator):
    def compute(self, *values: Any) -> str:
        return "".join(Coercion.to_str(value) for value in values)


class SubstrOperator(SimpleOperator):
    def compute(self, *values: Any) -> str:
        text = Coercion.to_str(values[0])
        start = int(values[1])
        if len(values) < 3:
            return text[start:]
        length = int(values[2])
        if length < 0:
            return text[start:length]
        return text[start : start + length]


class MergeOperator(SimpleOperator):
    def compute(self, *values: Any) -> list[Any]:
        merged: list[Any] = []
        for value in values:
            if isinstance(value, list):
                merged.extend(value)
            else:
                merged.append(value)
        return merged


class MapOperator(Operator):
    def apply(self, evaluator: JsonLogicEvaluator, args: list[Any], data: Any) -> list[Any]:
        collection = evaluator.apply(args[0], data)
        if not isinstance(collection, list):
            return []
        return [evaluator.apply(args[1], item) for item in collection]


class FilterOperator(Operator):
    def apply(self, evaluator: JsonLogicEvaluator, args: list[Any], data: Any) -> list[Any]:
        collection = evaluator.apply(args[0], data)
        if not isinstance(collection, list):
            return []
        return [item for item in collection if Coercion.is_truthy(evaluator.apply(args[1], item))]


class ReduceOperator(Operator):
    def apply(self, evaluator: JsonLogicEvaluator, args: list[Any], data: Any) -> Any:
        collection = evaluator.apply(args[0], data)
        accumulator = evaluator.apply(args[2], data) if len(args) > 2 else None
        if not isinstance(collection, list):
            return accumulator
        for item in collection:
            accumulator = evaluator.apply(args[1], {"current": item, "accumulator": accumulator})
        return accumulator


class AllOperator(Operator):
    def apply(self, evaluator: JsonLogicEvaluator, args: list[Any], data: Any) -> bool:
        collection = evaluator.apply(args[0], data)
        if not isinstance(collection, list) or not collection:
            return False
        return all(Coercion.is_truthy(evaluator.apply(args[1], item)) for item in collection)


class SomeOperator(Operator):
    def apply(self, evaluator: JsonLogicEvaluator, args: list[Any], data: Any) -> bool:
        collection = evaluator.apply(args[0], data)
        if not isinstance(collection, list):
            return False
        return any(Coercion.is_truthy(evaluator.apply(args[1], item)) for item in collection)


class NoneMatchOperator(Operator):
    def __init__(self) -> None:
        self._some = SomeOperator()

    def apply(self, evaluator: JsonLogicEvaluator, args: list[Any], data: Any) -> bool:
        return not self._some.apply(evaluator, args, data)
