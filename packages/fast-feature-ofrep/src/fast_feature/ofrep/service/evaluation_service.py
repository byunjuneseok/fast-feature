from __future__ import annotations

from fast_feature.core import (
    CoreError,
    ErrorCode,
    EvaluationContext,
    EvaluationOutcome,
    Flag,
    FlagRepository,
)
from fast_feature.engine import TargetingEngine

from ..errors import OfrepError


class EvaluationService:
    """Orchestrates the repository and the targeting engine for OFREP."""

    def __init__(
        self, repository: FlagRepository, *, engine: TargetingEngine | None = None
    ) -> None:
        self._repository = repository
        self._engine = engine or TargetingEngine()

    async def evaluate(
        self, key: str, context: EvaluationContext | None = None
    ) -> EvaluationOutcome:
        flag = await self._load(key)
        if flag is None:
            return EvaluationOutcome.error(
                key, ErrorCode.FLAG_NOT_FOUND, f"Flag {key!r} was not found"
            )
        return self._engine.evaluate(flag, context)

    async def evaluate_all(
        self, context: EvaluationContext | None = None
    ) -> list[EvaluationOutcome]:
        try:
            flags = await self._repository.list_all()
        except CoreError as exc:
            raise OfrepError("failed to list flags") from exc
        return [self._engine.evaluate(flag, context) for flag in flags]

    async def _load(self, key: str) -> Flag | None:
        try:
            return await self._repository.get(key)
        except CoreError as exc:
            raise OfrepError(f"failed to load flag {key!r}") from exc
