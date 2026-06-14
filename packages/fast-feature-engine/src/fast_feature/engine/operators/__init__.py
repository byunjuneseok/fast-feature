from __future__ import annotations

from fast_feature.engine.hashing import Hasher
from fast_feature.engine.operator import Operator

from .arithmetic import (
    AddOperator,
    DivideOperator,
    MaxOperator,
    MinOperator,
    ModuloOperator,
    MultiplyOperator,
    SubtractOperator,
)
from .collection import (
    AllOperator,
    CatOperator,
    FilterOperator,
    InOperator,
    MapOperator,
    MergeOperator,
    NoneMatchOperator,
    ReduceOperator,
    SomeOperator,
    SubstrOperator,
)
from .comparison import (
    EqualsOperator,
    GreaterThanOperator,
    GreaterThanOrEqualOperator,
    LessThanOperator,
    LessThanOrEqualOperator,
    NotEqualsOperator,
    StrictEqualsOperator,
    StrictNotEqualsOperator,
)
from .data import MissingOperator, MissingSomeOperator, VarOperator
from .logic import AndOperator, IfOperator, NotOperator, OrOperator, ToBoolOperator
from .targeting import (
    EndsWithOperator,
    FractionalOperator,
    SemVerOperator,
    StartsWithOperator,
)


class StandardOperators:
    """The JsonLogic operators available in every evaluation."""

    @classmethod
    def mapping(cls) -> dict[str, Operator]:
        return {
            "var": VarOperator(),
            "missing": MissingOperator(),
            "missing_some": MissingSomeOperator(),
            "if": IfOperator(),
            "?:": IfOperator(),
            "and": AndOperator(),
            "or": OrOperator(),
            "!": NotOperator(),
            "!!": ToBoolOperator(),
            "==": EqualsOperator(),
            "!=": NotEqualsOperator(),
            "===": StrictEqualsOperator(),
            "!==": StrictNotEqualsOperator(),
            "<": LessThanOperator(),
            "<=": LessThanOrEqualOperator(),
            ">": GreaterThanOperator(),
            ">=": GreaterThanOrEqualOperator(),
            "+": AddOperator(),
            "-": SubtractOperator(),
            "*": MultiplyOperator(),
            "/": DivideOperator(),
            "%": ModuloOperator(),
            "min": MinOperator(),
            "max": MaxOperator(),
            "in": InOperator(),
            "cat": CatOperator(),
            "substr": SubstrOperator(),
            "merge": MergeOperator(),
            "map": MapOperator(),
            "filter": FilterOperator(),
            "reduce": ReduceOperator(),
            "all": AllOperator(),
            "some": SomeOperator(),
            "none": NoneMatchOperator(),
        }


class TargetingOperators:
    """The extension operators used for flag targeting."""

    @classmethod
    def mapping(cls, hasher: Hasher) -> dict[str, Operator]:
        return {
            "starts_with": StartsWithOperator(),
            "ends_with": EndsWithOperator(),
            "sem_ver": SemVerOperator(),
            "fractional": FractionalOperator(hasher),
        }


__all__ = ["StandardOperators", "TargetingOperators"]
