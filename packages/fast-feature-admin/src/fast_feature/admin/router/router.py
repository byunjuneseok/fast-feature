from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.params import Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from starlette.datastructures import FormData

from fast_feature.core import (
    FlagAlreadyExistsError,
    FlagNotFoundError,
    FlagRepository,
    InvalidFlagError,
)

from ..schemas import FlagCreate, FlagToggle, FlagUpdate, FlagView
from ..service import ManagementService

_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


class AdminRouter:
    """Builds a pluggable admin ``APIRouter``: JSON CRUD under ``/api/flags``
    plus an optional server-rendered console under ``/``.

        app.include_router(AdminRouter.build(repository), prefix="/admin")

    Pass ``dependencies`` (e.g. an auth guard) to protect every route.
    """

    def __init__(
        self,
        repository: FlagRepository,
        *,
        dependencies: Sequence[Depends] | None = None,
        ui: bool = True,
    ) -> None:
        self._service = ManagementService(repository)
        self._router = APIRouter(dependencies=list(dependencies or []))
        self._templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))
        self._register_json_routes()
        if ui:
            self._register_ui_routes()

    @property
    def router(self) -> APIRouter:
        return self._router

    @classmethod
    def build(
        cls,
        repository: FlagRepository,
        *,
        dependencies: Sequence[Depends] | None = None,
        ui: bool = True,
    ) -> APIRouter:
        return cls(repository, dependencies=dependencies, ui=ui).router

    # --- JSON API ------------------------------------------------------------

    def _register_json_routes(self) -> None:
        router = self._router
        router.add_api_route(
            "/api/flags", self._list, methods=["GET"], response_model=list[FlagView]
        )
        router.add_api_route(
            "/api/flags", self._create, methods=["POST"], response_model=FlagView, status_code=201
        )
        router.add_api_route(
            "/api/flags/{key}", self._get, methods=["GET"], response_model=FlagView
        )
        router.add_api_route(
            "/api/flags/{key}", self._update, methods=["PUT"], response_model=FlagView
        )
        router.add_api_route(
            "/api/flags/{key}", self._toggle, methods=["PATCH"], response_model=FlagView
        )
        router.add_api_route("/api/flags/{key}", self._delete, methods=["DELETE"], status_code=204)

    async def _list(self) -> list[FlagView]:
        return [FlagView.from_flag(flag) for flag in await self._service.list_flags()]

    async def _create(self, body: FlagCreate) -> FlagView:
        try:
            flag = body.to_flag()
        except InvalidFlagError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        try:
            created = await self._service.create_flag(flag)
        except FlagAlreadyExistsError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return FlagView.from_flag(created)

    async def _get(self, key: str) -> FlagView:
        flag = await self._service.get_flag(key)
        if flag is None:
            raise HTTPException(status_code=404, detail=f"Flag {key!r} was not found")
        return FlagView.from_flag(flag)

    async def _update(self, key: str, body: FlagUpdate) -> FlagView:
        try:
            flag = body.to_flag(key)
        except InvalidFlagError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        try:
            updated = await self._service.update_flag(flag)
        except FlagNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return FlagView.from_flag(updated)

    async def _toggle(self, key: str, body: FlagToggle) -> FlagView:
        try:
            flag = await self._service.toggle(key, enabled=body.enabled)
        except FlagNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return FlagView.from_flag(flag)

    async def _delete(self, key: str) -> Response:
        try:
            await self._service.delete_flag(key)
        except FlagNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return Response(status_code=204)

    # --- web console ---------------------------------------------------------

    def _register_ui_routes(self) -> None:
        router = self._router
        router.add_api_route(
            "/", self._ui_list, methods=["GET"], response_class=HTMLResponse, name="admin:list"
        )
        router.add_api_route(
            "/new", self._ui_new, methods=["GET"], response_class=HTMLResponse, name="admin:new"
        )
        router.add_api_route("/new", self._ui_create, methods=["POST"], name="admin:create")
        router.add_api_route(
            "/{key}/edit",
            self._ui_edit,
            methods=["GET"],
            response_class=HTMLResponse,
            name="admin:edit",
        )
        router.add_api_route("/{key}/edit", self._ui_update, methods=["POST"], name="admin:update")
        router.add_api_route(
            "/{key}/toggle", self._ui_toggle, methods=["POST"], name="admin:toggle"
        )
        router.add_api_route(
            "/{key}/delete", self._ui_delete, methods=["POST"], name="admin:delete"
        )

    async def _ui_list(self, request: Request) -> Response:
        flags = await self._service.list_flags()
        return self._templates.TemplateResponse(request, "list.html", {"flags": flags})

    async def _ui_new(self, request: Request) -> Response:
        return self._render_form(request, flag=None, error=None)

    async def _ui_create(self, request: Request) -> Response:
        form = await request.form()
        try:
            flag = FlagCreate(**self._parse_form(form, with_key=True)).to_flag()
            await self._service.create_flag(flag)
        except (InvalidFlagError, FlagAlreadyExistsError, ValidationError, ValueError) as exc:
            return self._render_form(request, flag=None, error=str(exc), status_code=400)
        return RedirectResponse(str(request.url_for("admin:list")), status_code=303)

    async def _ui_edit(self, request: Request, key: str) -> Response:
        flag = await self._service.get_flag(key)
        if flag is None:
            raise HTTPException(status_code=404, detail=f"Flag {key!r} was not found")
        return self._render_form(request, flag=flag, error=None)

    async def _ui_update(self, request: Request, key: str) -> Response:
        form = await request.form()
        try:
            flag = FlagUpdate(**self._parse_form(form, with_key=False)).to_flag(key)
            await self._service.update_flag(flag)
        except (InvalidFlagError, FlagNotFoundError, ValidationError, ValueError) as exc:
            existing = await self._service.get_flag(key)
            return self._render_form(request, flag=existing, error=str(exc), status_code=400)
        return RedirectResponse(str(request.url_for("admin:list")), status_code=303)

    async def _ui_toggle(self, request: Request, key: str) -> Response:
        form = await request.form()
        enabled = self._text(form, "enabled").lower() in ("1", "true", "on", "yes")
        try:
            await self._service.toggle(key, enabled=enabled)
        except FlagNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return RedirectResponse(str(request.url_for("admin:list")), status_code=303)

    async def _ui_delete(self, request: Request, key: str) -> Response:
        try:
            await self._service.delete_flag(key)
        except FlagNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return RedirectResponse(str(request.url_for("admin:list")), status_code=303)

    # --- helpers -------------------------------------------------------------

    def _render_form(
        self, request: Request, *, flag: Any, error: str | None, status_code: int = 200
    ) -> Response:
        context = {
            "flag": flag,
            "error": error,
            "variants_json": json.dumps(flag.variants, indent=2) if flag else "",
            "targeting_json": json.dumps(flag.targeting, indent=2)
            if flag and flag.targeting
            else "",
            "metadata_json": json.dumps(flag.metadata, indent=2) if flag and flag.metadata else "",
        }
        return self._templates.TemplateResponse(
            request, "form.html", context, status_code=status_code
        )

    @classmethod
    def _parse_form(cls, form: FormData, *, with_key: bool) -> dict[str, Any]:
        data: dict[str, Any] = {
            "variants": json.loads(cls._text(form, "variants") or "{}"),
            "default_variant": cls._text(form, "default_variant").strip(),
            "state": cls._text(form, "state") or "ENABLED",
        }
        if with_key:
            data["key"] = cls._text(form, "key").strip()
        targeting = cls._text(form, "targeting").strip()
        data["targeting"] = json.loads(targeting) if targeting else None
        metadata = cls._text(form, "metadata").strip()
        data["metadata"] = json.loads(metadata) if metadata else {}
        return data

    @staticmethod
    def _text(form: FormData, name: str) -> str:
        value = form.get(name)
        return value if isinstance(value, str) else ""
