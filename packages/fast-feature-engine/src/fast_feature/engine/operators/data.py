from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fast_feature.engine.operator import Operator

if TYPE_CHECKING:
    from fast_feature.engine.evaluator import JsonLogicEvaluator


class DataPath:
    """Resolves a dotted variable path against an evaluation data object."""

    _MISSING: Any = object()

    def __init__(self, key: Any) -> None:
        self._key = key

    def resolve(self, data: Any, default: Any = None) -> Any:
        found = self._lookup(data)
        return default if found is self._MISSING else found

    def is_present(self, data: Any) -> bool:
        return self._lookup(data) not in (self._MISSING, None)

    def _lookup(self, data: Any) -> Any:
        if self._key is None or self._key == "":
            return data
        current = data
        for part in str(self._key).split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    return self._MISSING
            else:
                return self._MISSING
        return current


class VarOperator(Operator):
    def apply(self, evaluator: JsonLogicEvaluator, args: list[Any], data: Any) -> Any:
        key = evaluator.apply(args[0], data) if args else ""
        default = evaluator.apply(args[1], data) if len(args) > 1 else None
        return DataPath(key).resolve(data, default)


class MissingOperator(Operator):
    def apply(self, evaluator: JsonLogicEvaluator, args: list[Any], data: Any) -> list[Any]:
        keys = [evaluator.apply(arg, data) for arg in args]
        if len(keys) == 1 and isinstance(keys[0], list):
            keys = keys[0]
        return [key for key in keys if not DataPath(key).is_present(data)]


class MissingSomeOperator(Operator):
    def apply(self, evaluator: JsonLogicEvaluator, args: list[Any], data: Any) -> list[Any]:
        minimum = evaluator.apply(args[0], data)
        keys = evaluator.apply(args[1], data)
        if not isinstance(keys, list):
            return []
        present = [key for key in keys if DataPath(key).is_present(data)]
        if len(present) >= int(minimum):
            return []
        return [key for key in keys if not DataPath(key).is_present(data)]
