from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from fast_feature.core import ErrorCode, FlagRepository
from fast_feature.engine import TargetingEngine

from ..schemas import (
    BulkEvaluationRequest,
    BulkEvaluationSuccess,
    EvaluationFailure,
    EvaluationRequest,
    EvaluationSuccess,
    FlagNotFound,
)
from ..service import EvaluationService


class OfrepRouter:
    """Builds a pluggable ``APIRouter`` exposing the OFREP endpoints.

    Mount it onto any FastAPI app::

        app.include_router(OfrepRouter.build(repository))
    """

    def __init__(
        self, repository: FlagRepository, *, engine: TargetingEngine | None = None
    ) -> None:
        self._service = EvaluationService(repository, engine=engine)
        self._router = APIRouter(prefix="/ofrep/v1", tags=["OFREP"])
        self._register_routes()

    @property
    def router(self) -> APIRouter:
        return self._router

    @classmethod
    def build(
        cls, repository: FlagRepository, *, engine: TargetingEngine | None = None
    ) -> APIRouter:
        return cls(repository, engine=engine).router

    def _register_routes(self) -> None:
        self._router.add_api_route("/evaluate/flags/{key}", self._evaluate_flag, methods=["POST"])
        self._router.add_api_route("/evaluate/flags", self._evaluate_all, methods=["POST"])

    async def _evaluate_flag(self, key: str, request: EvaluationRequest) -> Response:
        outcome = await self._service.evaluate(key, request.context)
        if outcome.error_code is ErrorCode.FLAG_NOT_FOUND:
            return self._json(404, FlagNotFound.from_outcome(outcome))
        if outcome.is_error:
            return self._json(400, EvaluationFailure.from_outcome(outcome))
        return self._json(200, EvaluationSuccess.from_outcome(outcome))

    async def _evaluate_all(
        self, request: BulkEvaluationRequest, http_request: Request
    ) -> Response:
        outcomes = await self._service.evaluate_all(request.context)
        payload = BulkEvaluationSuccess.from_outcomes(outcomes).model_dump(
            by_alias=True, exclude_none=True
        )
        etag = self._etag(payload)
        if http_request.headers.get("if-none-match") == etag:
            return Response(status_code=304, headers={"ETag": etag})
        return JSONResponse(status_code=200, content=payload, headers={"ETag": etag})

    @staticmethod
    def _json(status_code: int, model: BaseModel) -> JSONResponse:
        return JSONResponse(
            status_code=status_code, content=model.model_dump(by_alias=True, exclude_none=True)
        )

    @staticmethod
    def _etag(payload: dict[str, Any]) -> str:
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()
        return f'"{digest[:16]}"'
