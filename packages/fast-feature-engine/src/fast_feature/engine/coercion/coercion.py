from __future__ import annotations

from typing import Any

from fast_feature.engine.errors import JsonLogicError


class Coercion:
    """JavaScript-aligned type coercion shared by the operators."""

    @staticmethod
    def is_truthy(value: Any) -> bool:
        if value is None or value is False:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, int | float):
            return value != 0
        if isinstance(value, str):
            return value != ""
        if isinstance(value, list):
            return len(value) > 0
        if isinstance(value, dict):
            return True
        return bool(value)

    @staticmethod
    def to_str(value: Any) -> str:
        if value is None:
            return ""
        if value is True:
            return "true"
        if value is False:
            return "false"
        return str(value)

    @staticmethod
    def to_number(value: Any) -> float:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int | float):
            return value
        if isinstance(value, str):
            try:
                if any(c in value for c in ".eE"):
                    return float(value)
                return int(value)
            except ValueError as exc:
                raise JsonLogicError(f"cannot convert {value!r} to a number") from exc
        raise JsonLogicError(f"cannot convert {value!r} to a number")

    @classmethod
    def soft_equals(cls, a: Any, b: Any) -> bool:
        if isinstance(a, bool) or isinstance(b, bool):
            return cls.is_truthy(a) is cls.is_truthy(b)
        if isinstance(a, str) or isinstance(b, str):
            return cls.to_str(a) == cls.to_str(b)
        return bool(a == b)

    @staticmethod
    def hard_equals(a: Any, b: Any) -> bool:
        if type(a) is not type(b):
            return False
        return bool(a == b)

    @classmethod
    def less_than(cls, a: Any, b: Any) -> bool:
        if isinstance(a, str) and isinstance(b, str):
            return a < b
        return cls.to_number(a) < cls.to_number(b)

    @classmethod
    def less_than_or_equal(cls, a: Any, b: Any) -> bool:
        if isinstance(a, str) and isinstance(b, str):
            return a <= b
        return cls.to_number(a) <= cls.to_number(b)
