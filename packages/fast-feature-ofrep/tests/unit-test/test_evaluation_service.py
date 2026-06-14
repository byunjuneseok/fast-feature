from __future__ import annotations

import pytest

from fast_feature.core import CoreError, ErrorCode, Flag, FlagRepository, Reason
from fast_feature.ofrep import EvaluationService, OfrepError


class FakeFlagRepository(FlagRepository):
    def __init__(self, flags: list[Flag] | None = None, *, failing: bool = False) -> None:
        self._flags = {flag.key: flag for flag in (flags or [])}
        self._failing = failing

    async def get(self, key: str) -> Flag | None:
        if self._failing:
            raise CoreError("storage unavailable")
        return self._flags.get(key)

    async def list_all(self) -> list[Flag]:
        if self._failing:
            raise CoreError("storage unavailable")
        return list(self._flags.values())

    async def create(self, flag: Flag) -> Flag:
        self._flags[flag.key] = flag
        return flag

    async def update(self, flag: Flag) -> Flag:
        self._flags[flag.key] = flag
        return flag

    async def delete(self, key: str) -> None:
        del self._flags[key]


class TestEvaluationService:
    @staticmethod
    def _flag(key: str = "f") -> Flag:
        return Flag(key=key, variants={"on": True, "off": False}, default_variant="on")

    async def test_evaluate_returns_outcome(self) -> None:
        service = EvaluationService(FakeFlagRepository([self._flag("f")]))
        outcome = await service.evaluate("f", {})
        assert outcome.reason is Reason.STATIC
        assert outcome.value is True

    async def test_evaluate_missing_flag_is_not_found(self) -> None:
        service = EvaluationService(FakeFlagRepository())
        outcome = await service.evaluate("nope")
        assert outcome.is_error
        assert outcome.error_code is ErrorCode.FLAG_NOT_FOUND

    async def test_evaluate_all_covers_every_flag(self) -> None:
        service = EvaluationService(FakeFlagRepository([self._flag("a"), self._flag("b")]))
        outcomes = await service.evaluate_all({})
        assert {outcome.key for outcome in outcomes} == {"a", "b"}

    async def test_load_failure_translates_to_ofrep_error(self) -> None:
        service = EvaluationService(FakeFlagRepository(failing=True))
        with pytest.raises(OfrepError):
            await service.evaluate("f")

    async def test_list_failure_translates_to_ofrep_error(self) -> None:
        service = EvaluationService(FakeFlagRepository(failing=True))
        with pytest.raises(OfrepError):
            await service.evaluate_all()
