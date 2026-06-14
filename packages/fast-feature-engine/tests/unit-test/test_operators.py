from __future__ import annotations

from collections import Counter
from typing import Any

import pytest

from fast_feature.engine import (
    JsonLogicEvaluator,
    Murmur3Hasher,
    OperatorRegistry,
    StandardOperators,
    TargetingOperators,
)


class TestTargetingOperators:
    evaluator = JsonLogicEvaluator(
        OperatorRegistry(StandardOperators.mapping()).extended_with(
            TargetingOperators.mapping(Murmur3Hasher())
        )
    )

    @staticmethod
    def _fractional_rule(a: int = 50, b: int = 50) -> dict[str, Any]:
        return {"fractional": [{"var": "targetingKey"}, ["on", a], ["off", b]]}

    @pytest.mark.parametrize(
        ("rule", "expected"),
        [
            ({"starts_with": ["admin@corp.com", "admin"]}, True),
            ({"starts_with": ["user@corp.com", "admin"]}, False),
            ({"starts_with": [123, "1"]}, False),
            ({"ends_with": ["user@corp.com", "@corp.com"]}, True),
            ({"ends_with": ["user@other.com", "@corp.com"]}, False),
            ({"ends_with": [123, "3"]}, False),  # non-string operand
        ],
    )
    def test_string_predicates(self, rule: Any, expected: bool) -> None:
        assert self.evaluator.apply(rule, {}) is expected

    def test_sem_ver_wrong_arity_is_false(self) -> None:
        assert self.evaluator.apply({"sem_ver": ["1.0.0", "="]}, {}) is False

    @pytest.mark.parametrize(
        ("left", "op", "right", "expected"),
        [
            ("1.2.3", "=", "1.2.3", True),
            ("1.2.3", "!=", "1.2.4", True),
            ("1.2.3", "<", "1.10.0", True),
            ("2.0.0", ">", "1.9.9", True),
            ("1.2.3", ">=", "1.2.3", True),
            ("1.5.0", "^", "1.2.3", True),
            ("2.0.0", "^", "1.2.3", False),
            ("1.2.9", "~", "1.2.3", True),
            ("1.3.0", "~", "1.2.3", False),
            ("not-a-version", "=", "1.2.3", False),
        ],
    )
    def test_sem_ver(self, left: str, op: str, right: str, expected: bool) -> None:
        assert self.evaluator.apply({"sem_ver": [left, op, right]}, {}) is expected

    def test_fractional_is_deterministic(self) -> None:
        data = {"targetingKey": "user-42"}
        first = self.evaluator.apply(self._fractional_rule(), data)
        assert first in {"on", "off"}
        assert self.evaluator.apply(self._fractional_rule(), data) == first

    def test_fractional_distribution_tracks_weights(self) -> None:
        counts: Counter[str] = Counter()
        for i in range(4000):
            counts[
                self.evaluator.apply(self._fractional_rule(), {"targetingKey": f"user-{i}"})
            ] += 1
        # 50/50 split — both buckets should land near half, within a loose margin.
        assert abs(counts["on"] - counts["off"]) < 600

    def test_fractional_respects_uneven_weights(self) -> None:
        counts: Counter[str] = Counter()
        for i in range(4000):
            counts[
                self.evaluator.apply(self._fractional_rule(80, 20), {"targetingKey": f"u-{i}"})
            ] += 1
        assert counts["on"] > counts["off"] * 2

    def test_fractional_without_args_returns_none(self) -> None:
        assert self.evaluator.apply({"fractional": []}, {}) is None

    def test_fractional_zero_weights_returns_none(self) -> None:
        rule = {"fractional": [{"var": "targetingKey"}, ["on", 0], ["off", 0]]}
        assert self.evaluator.apply(rule, {"targetingKey": "u"}) is None

    def test_fractional_uses_default_bucket_key(self) -> None:
        # No explicit bucketing expression: the first arg is already a bucket,
        # so the key defaults to "$flag.key" + targetingKey.
        rule = {"fractional": [["on", 50], ["off", 50]]}
        data = {"$flag": {"key": "color"}, "targetingKey": "user-1"}
        first = self.evaluator.apply(rule, data)
        assert first in {"on", "off"}
        assert self.evaluator.apply(rule, data) == first
