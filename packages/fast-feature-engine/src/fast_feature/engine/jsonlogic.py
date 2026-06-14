from __future__ import annotations

from collections.abc import Callable
from typing import Any

SimpleOp = Callable[..., Any]
LazyOp = Callable[["JsonLogic", list[Any], Any], Any]


class JsonLogicError(Exception):
    """Raised when a rule is malformed or cannot be evaluated."""


def is_truthy(value: Any) -> bool:
    """JsonLogic truthiness, aligned with JavaScript.

    ``None``/``False``/``0``/``""``/``[]`` are falsy; a non-empty object is truthy.
    """
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


def to_str(value: Any) -> str:
    if value is None:
        return ""
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


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


def _soft_equals(a: Any, b: Any) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return is_truthy(a) is is_truthy(b)
    if isinstance(a, str) or isinstance(b, str):
        return to_str(a) == to_str(b)
    return bool(a == b)


def _hard_equals(a: Any, b: Any) -> bool:
    if type(a) is not type(b):
        return False
    return bool(a == b)


def _less_than(a: Any, b: Any) -> bool:
    if isinstance(a, str) and isinstance(b, str):
        return a < b
    return to_number(a) < to_number(b)


def _less_than_eq(a: Any, b: Any) -> bool:
    if isinstance(a, str) and isinstance(b, str):
        return a <= b
    return to_number(a) <= to_number(b)


_SENTINEL = object()


def _resolve(data: Any, key: Any) -> Any:
    """Resolve a dotted ``var`` path against ``data``; ``_SENTINEL`` if absent."""
    if key is None or key == "":
        return data
    current = data
    for part in str(key).split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return _SENTINEL
        else:
            return _SENTINEL
    return current


# --- lazy operations (control their own argument evaluation) ------------------


def _op_var(jl: JsonLogic, args: list[Any], data: Any) -> Any:
    key = jl.apply(args[0], data) if args else ""
    default = jl.apply(args[1], data) if len(args) > 1 else None
    resolved = _resolve(data, key)
    return default if resolved is _SENTINEL else resolved


def _op_missing(jl: JsonLogic, args: list[Any], data: Any) -> list[Any]:
    keys = [jl.apply(a, data) for a in args]
    if len(keys) == 1 and isinstance(keys[0], list):
        keys = keys[0]
    return [k for k in keys if _resolve(data, k) in (_SENTINEL, None)]


def _op_missing_some(jl: JsonLogic, args: list[Any], data: Any) -> list[Any]:
    min_required = jl.apply(args[0], data)
    keys = jl.apply(args[1], data)
    if not isinstance(keys, list):
        return []
    present = [k for k in keys if _resolve(data, k) not in (_SENTINEL, None)]
    if len(present) >= int(min_required):
        return []
    return [k for k in keys if _resolve(data, k) in (_SENTINEL, None)]


def _op_if(jl: JsonLogic, args: list[Any], data: Any) -> Any:
    for i in range(0, len(args) - 1, 2):
        if is_truthy(jl.apply(args[i], data)):
            return jl.apply(args[i + 1], data)
    if len(args) % 2:
        return jl.apply(args[-1], data)
    return None


def _op_and(jl: JsonLogic, args: list[Any], data: Any) -> Any:
    result: Any = True
    for arg in args:
        result = jl.apply(arg, data)
        if not is_truthy(result):
            return result
    return result


def _op_or(jl: JsonLogic, args: list[Any], data: Any) -> Any:
    result: Any = False
    for arg in args:
        result = jl.apply(arg, data)
        if is_truthy(result):
            return result
    return result


def _op_map(jl: JsonLogic, args: list[Any], data: Any) -> list[Any]:
    collection = jl.apply(args[0], data)
    if not isinstance(collection, list):
        return []
    return [jl.apply(args[1], item) for item in collection]


def _op_filter(jl: JsonLogic, args: list[Any], data: Any) -> list[Any]:
    collection = jl.apply(args[0], data)
    if not isinstance(collection, list):
        return []
    return [item for item in collection if is_truthy(jl.apply(args[1], item))]


def _op_reduce(jl: JsonLogic, args: list[Any], data: Any) -> Any:
    collection = jl.apply(args[0], data)
    accumulator = jl.apply(args[2], data) if len(args) > 2 else None
    if not isinstance(collection, list):
        return accumulator
    for item in collection:
        accumulator = jl.apply(args[1], {"current": item, "accumulator": accumulator})
    return accumulator


def _op_all(jl: JsonLogic, args: list[Any], data: Any) -> bool:
    collection = jl.apply(args[0], data)
    if not isinstance(collection, list) or not collection:
        return False
    return all(is_truthy(jl.apply(args[1], item)) for item in collection)


def _op_some(jl: JsonLogic, args: list[Any], data: Any) -> bool:
    collection = jl.apply(args[0], data)
    if not isinstance(collection, list):
        return False
    return any(is_truthy(jl.apply(args[1], item)) for item in collection)


def _op_none(jl: JsonLogic, args: list[Any], data: Any) -> bool:
    return not _op_some(jl, args, data)


# --- simple operations (receive already-evaluated arguments) ------------------


def _op_lt(*args: Any) -> bool:
    if len(args) == 3:
        return _less_than(args[0], args[1]) and _less_than(args[1], args[2])
    return _less_than(args[0], args[1])


def _op_lte(*args: Any) -> bool:
    if len(args) == 3:
        return _less_than_eq(args[0], args[1]) and _less_than_eq(args[1], args[2])
    return _less_than_eq(args[0], args[1])


def _op_add(*args: Any) -> float:
    return sum(to_number(a) for a in args)


def _op_mul(*args: Any) -> float:
    product: float = 1
    for a in args:
        product *= to_number(a)
    return product


def _op_sub(*args: Any) -> float:
    if len(args) == 1:
        return -to_number(args[0])
    return to_number(args[0]) - to_number(args[1])


def _op_div(*args: Any) -> float:
    return to_number(args[0]) / to_number(args[1])


def _op_mod(*args: Any) -> float:
    return to_number(args[0]) % to_number(args[1])


def _op_substr(*args: Any) -> str:
    value = to_str(args[0])
    start = int(args[1])
    if len(args) < 3:
        return value[start:]
    length = int(args[2])
    if length < 0:
        return value[start:length]
    return value[start : start + length]


def _op_in(*args: Any) -> bool:
    needle, haystack = args[0], args[1]
    if isinstance(haystack, str):
        return to_str(needle) in haystack
    if isinstance(haystack, list):
        return needle in haystack
    return False


def _op_merge(*args: Any) -> list[Any]:
    merged: list[Any] = []
    for arg in args:
        if isinstance(arg, list):
            merged.extend(arg)
        else:
            merged.append(arg)
    return merged


_LAZY_OPS: dict[str, LazyOp] = {
    "var": _op_var,
    "missing": _op_missing,
    "missing_some": _op_missing_some,
    "if": _op_if,
    "?:": _op_if,
    "and": _op_and,
    "or": _op_or,
    "map": _op_map,
    "filter": _op_filter,
    "reduce": _op_reduce,
    "all": _op_all,
    "some": _op_some,
    "none": _op_none,
}

_SIMPLE_OPS: dict[str, SimpleOp] = {
    "==": lambda a, b: _soft_equals(a, b),
    "!=": lambda a, b: not _soft_equals(a, b),
    "===": lambda a, b: _hard_equals(a, b),
    "!==": lambda a, b: not _hard_equals(a, b),
    "!": lambda a: not is_truthy(a),
    "!!": lambda a: is_truthy(a),
    ">": lambda a, b: _less_than(b, a),
    ">=": lambda a, b: _less_than_eq(b, a),
    "<": _op_lt,
    "<=": _op_lte,
    "+": _op_add,
    "*": _op_mul,
    "-": _op_sub,
    "/": _op_div,
    "%": _op_mod,
    "min": lambda *a: min(to_number(x) for x in a),
    "max": lambda *a: max(to_number(x) for x in a),
    "cat": lambda *a: "".join(to_str(x) for x in a),
    "substr": _op_substr,
    "in": _op_in,
    "merge": _op_merge,
}


class JsonLogic:
    """A JsonLogic evaluator with pluggable operators.

    Extra operators can be supplied to extend the dialect with predicates such
    as ``fractional``/``sem_ver``/``starts_with``/``ends_with``.
    """

    def __init__(
        self,
        *,
        simple_ops: dict[str, SimpleOp] | None = None,
        lazy_ops: dict[str, LazyOp] | None = None,
    ) -> None:
        self._simple: dict[str, SimpleOp] = {**_SIMPLE_OPS, **(simple_ops or {})}
        self._lazy: dict[str, LazyOp] = {**_LAZY_OPS, **(lazy_ops or {})}

    def apply(self, rule: Any, data: Any = None) -> Any:
        if data is None:
            data = {}
        if isinstance(rule, list):
            return [self.apply(item, data) for item in rule]
        if not self._is_operation(rule):
            return rule
        operator, raw = next(iter(rule.items()))
        args = raw if isinstance(raw, list) else [raw]
        if operator in self._lazy:
            return self._lazy[operator](self, args, data)
        if operator in self._simple:
            return self._simple[operator](*[self.apply(a, data) for a in args])
        raise JsonLogicError(f"Unrecognized operation {operator!r}")

    @staticmethod
    def _is_operation(rule: Any) -> bool:
        return isinstance(rule, dict) and len(rule) == 1 and isinstance(next(iter(rule)), str)
