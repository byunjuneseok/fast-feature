from __future__ import annotations

from typing import Any

from fast_feature.engine.coercion import Coercion
from fast_feature.engine.errors import JsonLogicError
from fast_feature.engine.operator import SimpleOperator


class AddOperator(SimpleOperator):
    def compute(self, *values: Any) -> float:
        return sum(Coercion.to_number(value) for value in values)


class SubtractOperator(SimpleOperator):
    def compute(self, *values: Any) -> float:
        if len(values) == 1:
            return -Coercion.to_number(values[0])
        return Coercion.to_number(values[0]) - Coercion.to_number(values[1])


class MultiplyOperator(SimpleOperator):
    def compute(self, *values: Any) -> float:
        product: float = 1
        for value in values:
            product *= Coercion.to_number(value)
        return product


class DivideOperator(SimpleOperator):
    def compute(self, *values: Any) -> float:
        try:
            return Coercion.to_number(values[0]) / Coercion.to_number(values[1])
        except ZeroDivisionError as exc:
            raise JsonLogicError("division by zero") from exc


class ModuloOperator(SimpleOperator):
    def compute(self, *values: Any) -> float:
        try:
            return Coercion.to_number(values[0]) % Coercion.to_number(values[1])
        except ZeroDivisionError as exc:
            raise JsonLogicError("modulo by zero") from exc


class MinOperator(SimpleOperator):
    def compute(self, *values: Any) -> float:
        return min(Coercion.to_number(value) for value in values)


class MaxOperator(SimpleOperator):
    def compute(self, *values: Any) -> float:
        return max(Coercion.to_number(value) for value in values)
