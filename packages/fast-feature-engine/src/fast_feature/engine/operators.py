from __future__ import annotations

import re
from typing import Any

import mmh3

from .jsonlogic import JsonLogic, LazyOp, SimpleOp, to_str

# --- string predicates --------------------------------------------------------


def _op_starts_with(*args: Any) -> bool:
    value, prefix = args[0], args[1]
    if not isinstance(value, str) or not isinstance(prefix, str):
        return False
    return value.startswith(prefix)


def _op_ends_with(*args: Any) -> bool:
    value, suffix = args[0], args[1]
    if not isinstance(value, str) or not isinstance(suffix, str):
        return False
    return value.endswith(suffix)


# --- semantic versioning ------------------------------------------------------

_SEMVER = re.compile(r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?")
SemVer = tuple[int, int, int]


def _parse_semver(value: Any) -> SemVer | None:
    if not isinstance(value, str):
        return None
    match = _SEMVER.match(value.strip())
    if match is None:
        return None
    return (int(match.group(1)), int(match.group(2) or 0), int(match.group(3) or 0))


def _op_sem_ver(*args: Any) -> bool:
    if len(args) != 3:
        return False
    left, operator, right = _parse_semver(args[0]), args[1], _parse_semver(args[2])
    if left is None or right is None:
        return False
    if operator in ("=", "=="):
        return left == right
    if operator == "!=":
        return left != right
    if operator == "<":
        return left < right
    if operator == "<=":
        return left <= right
    if operator == ">":
        return left > right
    if operator == ">=":
        return left >= right
    if operator == "^":
        return left[0] == right[0]
    if operator == "~":
        return left[0] == right[0] and left[1] == right[1]
    return False


# --- fractional rollout -------------------------------------------------------


def _default_bucket_key(data: Any) -> str:
    flag_key = ""
    targeting_key = ""
    if isinstance(data, dict):
        meta = data.get("$flag")
        if isinstance(meta, dict):
            flag_key = to_str(meta.get("key", ""))
        targeting_key = to_str(data.get("targetingKey", ""))
    return f"{flag_key}{targeting_key}"


def _op_fractional(jl: JsonLogic, args: list[Any], data: Any) -> Any:
    if not args:
        return None

    first = args[0] if isinstance(args[0], list) else jl.apply(args[0], data)
    if isinstance(first, list):
        bucket_key = _default_bucket_key(data)
        raw_buckets = args
    else:
        bucket_key = to_str(first)
        raw_buckets = args[1:]

    names: list[str] = []
    weights: list[float] = []
    for bucket in raw_buckets:
        evaluated = jl.apply(bucket, data)
        if isinstance(evaluated, list) and evaluated:
            names.append(to_str(evaluated[0]))
            weights.append(float(evaluated[1]) if len(evaluated) > 1 else 1.0)

    total = sum(weights)
    if not names or total <= 0:
        return None

    ratio = mmh3.hash(bucket_key, signed=False) / 0xFFFFFFFF
    bucket_point = ratio * 100.0
    cumulative = 0.0
    for name, weight in zip(names, weights, strict=True):
        cumulative += weight * 100.0 / total
        if bucket_point < cumulative:
            return name
    return names[-1]


TARGETING_SIMPLE_OPS: dict[str, SimpleOp] = {
    "starts_with": _op_starts_with,
    "ends_with": _op_ends_with,
    "sem_ver": _op_sem_ver,
}

TARGETING_LAZY_OPS: dict[str, LazyOp] = {
    "fractional": _op_fractional,
}
