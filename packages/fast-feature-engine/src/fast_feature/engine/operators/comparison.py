from __future__ import annotations

from typing import Any

from fast_feature.engine.coercion import Coercion
from fast_feature.engine.operator import SimpleOperator


class EqualsOperator(SimpleOperator):
    def compute(self, *values: Any) -> bool:
        return Coercion.soft_equals(values[0], values[1])


class NotEqualsOperator(SimpleOperator):
    def compute(self, *values: Any) -> bool:
        return not Coercion.soft_equals(values[0], values[1])


class StrictEqualsOperator(SimpleOperator):
    def compute(self, *values: Any) -> bool:
        return Coercion.hard_equals(values[0], values[1])


class StrictNotEqualsOperator(SimpleOperator):
    def compute(self, *values: Any) -> bool:
        return not Coercion.hard_equals(values[0], values[1])


class LessThanOperator(SimpleOperator):
    def compute(self, *values: Any) -> bool:
        if len(values) == 3:
            return Coercion.less_than(values[0], values[1]) and Coercion.less_than(
                values[1], values[2]
            )
        return Coercion.less_than(values[0], values[1])


class LessThanOrEqualOperator(SimpleOperator):
    def compute(self, *values: Any) -> bool:
        if len(values) == 3:
            return Coercion.less_than_or_equal(
                values[0], values[1]
            ) and Coercion.less_than_or_equal(values[1], values[2])
        return Coercion.less_than_or_equal(values[0], values[1])


class GreaterThanOperator(SimpleOperator):
    def compute(self, *values: Any) -> bool:
        return Coercion.less_than(values[1], values[0])


class GreaterThanOrEqualOperator(SimpleOperator):
    def compute(self, *values: Any) -> bool:
        return Coercion.less_than_or_equal(values[1], values[0])
