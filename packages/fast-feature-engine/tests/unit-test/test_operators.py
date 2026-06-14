from __future__ import annotations

from collections import Counter
from typing import Any

import pytest

from fast_feature.engine.jsonlogic import JsonLogic
from fast_feature.engine.operators import TARGETING_LAZY_OPS, TARGETING_SIMPLE_OPS

jl = JsonLogic(simple_ops=TARGETING_SIMPLE_OPS, lazy_ops=TARGETING_LAZY_OPS)


@pytest.mark.parametrize(
    ("rule", "expected"),
    [
        ({"starts_with": ["admin@corp.com", "admin"]}, True),
        ({"starts_with": ["user@corp.com", "admin"]}, False),
        ({"starts_with": [123, "1"]}, False),
        ({"ends_with": ["user@corp.com", "@corp.com"]}, True),
        ({"ends_with": ["user@other.com", "@corp.com"]}, False),
    ],
)
def test_string_predicates(rule: Any, expected: bool) -> None:
    assert jl.apply(rule, {}) is expected


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
def test_sem_ver(left: str, op: str, right: str, expected: bool) -> None:
    assert jl.apply({"sem_ver": [left, op, right]}, {}) is expected


def _fractional_rule(a: int = 50, b: int = 50) -> dict[str, Any]:
    return {"fractional": [{"var": "targetingKey"}, ["on", a], ["off", b]]}


def test_fractional_is_deterministic() -> None:
    data = {"targetingKey": "user-42"}
    first = jl.apply(_fractional_rule(), data)
    assert first in {"on", "off"}
    assert jl.apply(_fractional_rule(), data) == first


def test_fractional_distribution_tracks_weights() -> None:
    counts: Counter[str] = Counter()
    for i in range(4000):
        counts[jl.apply(_fractional_rule(), {"targetingKey": f"user-{i}"})] += 1
    # 50/50 split — both buckets should land near half, within a loose margin.
    assert abs(counts["on"] - counts["off"]) < 600


def test_fractional_respects_uneven_weights() -> None:
    counts: Counter[str] = Counter()
    for i in range(4000):
        counts[jl.apply(_fractional_rule(80, 20), {"targetingKey": f"u-{i}"})] += 1
    assert counts["on"] > counts["off"] * 2
