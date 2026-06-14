from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fast_feature.engine.coercion import Coercion
from fast_feature.engine.hashing import Hasher
from fast_feature.engine.operator import Operator, SimpleOperator
from fast_feature.engine.semver import SemanticVersion

if TYPE_CHECKING:
    from fast_feature.engine.evaluator import JsonLogicEvaluator


class StartsWithOperator(SimpleOperator):
    def compute(self, *values: Any) -> bool:
        value, prefix = values[0], values[1]
        if not isinstance(value, str) or not isinstance(prefix, str):
            return False
        return value.startswith(prefix)


class EndsWithOperator(SimpleOperator):
    def compute(self, *values: Any) -> bool:
        value, suffix = values[0], values[1]
        if not isinstance(value, str) or not isinstance(suffix, str):
            return False
        return value.endswith(suffix)


class SemVerOperator(SimpleOperator):
    def compute(self, *values: Any) -> bool:
        if len(values) != 3:
            return False
        left = SemanticVersion.parse(values[0])
        right = SemanticVersion.parse(values[2])
        if left is None or right is None:
            return False
        return left.satisfies(values[1], right)


class FractionalOperator(Operator):
    """Deterministic percentage rollout, bucketed by a hash of the bucket key."""

    def __init__(self, hasher: Hasher) -> None:
        self._hasher = hasher

    def apply(self, evaluator: JsonLogicEvaluator, args: list[Any], data: Any) -> Any:
        if not args:
            return None
        first = args[0] if isinstance(args[0], list) else evaluator.apply(args[0], data)
        if isinstance(first, list):
            bucket_key = self._default_bucket_key(data)
            raw_buckets = args
        else:
            bucket_key = Coercion.to_str(first)
            raw_buckets = args[1:]

        names: list[str] = []
        weights: list[float] = []
        for bucket in raw_buckets:
            evaluated = evaluator.apply(bucket, data)
            if isinstance(evaluated, list) and evaluated:
                names.append(Coercion.to_str(evaluated[0]))
                weights.append(float(evaluated[1]) if len(evaluated) > 1 else 1.0)

        total = sum(weights)
        if not names or total <= 0:
            return None

        point = self._hasher.hash(bucket_key) / self._hasher.max_value * 100.0
        cumulative = 0.0
        for name, weight in zip(names, weights, strict=True):
            cumulative += weight * 100.0 / total
            if point < cumulative:
                return name
        return names[-1]

    @staticmethod
    def _default_bucket_key(data: Any) -> str:
        flag_key = ""
        targeting_key = ""
        if isinstance(data, dict):
            meta = data.get("$flag")
            if isinstance(meta, dict):
                flag_key = Coercion.to_str(meta.get("key", ""))
            targeting_key = Coercion.to_str(data.get("targetingKey", ""))
        return f"{flag_key}{targeting_key}"
