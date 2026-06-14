from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.params import Depends as DependsParam
from httpx import ASGITransport, AsyncClient

from fast_feature.admin import AdminRouter
from fast_feature.core import FlagRepository
from fast_feature.storage.inmemory import InMemoryFlagRepository


class _RejectAll:
    def __call__(self) -> None:
        raise HTTPException(status_code=401, detail="unauthorized")


class TestAdminRouter:
    @staticmethod
    def _client(
        repository: FlagRepository, *, dependencies: Sequence[DependsParam] | None = None
    ) -> AsyncClient:
        app = FastAPI()
        app.include_router(
            AdminRouter.build(repository, dependencies=dependencies), prefix="/admin"
        )
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    @staticmethod
    def _payload(key: str = "banner") -> dict[str, Any]:
        return {"key": key, "variants": {"on": True, "off": False}, "default_variant": "off"}

    # --- JSON API ---

    async def test_create_get_and_list(self) -> None:
        async with self._client(InMemoryFlagRepository()) as client:
            created = await client.post("/admin/api/flags", json=self._payload())
            assert created.status_code == 201
            assert created.json()["key"] == "banner"
            assert (await client.get("/admin/api/flags/banner")).status_code == 200
            assert len((await client.get("/admin/api/flags")).json()) == 1

    async def test_create_duplicate_is_conflict(self) -> None:
        async with self._client(InMemoryFlagRepository()) as client:
            await client.post("/admin/api/flags", json=self._payload())
            assert (await client.post("/admin/api/flags", json=self._payload())).status_code == 409

    async def test_create_invalid_is_unprocessable(self) -> None:
        async with self._client(InMemoryFlagRepository()) as client:
            bad = {"key": "x", "variants": {"on": True}, "default_variant": "missing"}
            assert (await client.post("/admin/api/flags", json=bad)).status_code == 422

    async def test_get_missing_is_404(self) -> None:
        async with self._client(InMemoryFlagRepository()) as client:
            assert (await client.get("/admin/api/flags/ghost")).status_code == 404

    async def test_update_toggle_delete(self) -> None:
        async with self._client(InMemoryFlagRepository()) as client:
            await client.post("/admin/api/flags", json=self._payload())
            updated = await client.put(
                "/admin/api/flags/banner",
                json={"variants": {"on": True, "off": False}, "default_variant": "on"},
            )
            assert updated.status_code == 200
            assert updated.json()["default_variant"] == "on"
            toggled = await client.patch("/admin/api/flags/banner", json={"enabled": False})
            assert toggled.json()["state"] == "DISABLED"
            assert (await client.delete("/admin/api/flags/banner")).status_code == 204
            assert (await client.get("/admin/api/flags/banner")).status_code == 404

    async def test_update_missing_is_404(self) -> None:
        async with self._client(InMemoryFlagRepository()) as client:
            response = await client.put(
                "/admin/api/flags/ghost",
                json={"variants": {"on": True}, "default_variant": "on"},
            )
            assert response.status_code == 404

    async def test_toggle_missing_is_404(self) -> None:
        async with self._client(InMemoryFlagRepository()) as client:
            response = await client.patch("/admin/api/flags/ghost", json={"enabled": True})
            assert response.status_code == 404

    async def test_delete_missing_is_404(self) -> None:
        async with self._client(InMemoryFlagRepository()) as client:
            assert (await client.delete("/admin/api/flags/ghost")).status_code == 404

    # --- web console ---

    async def test_console_list_and_new_pages(self) -> None:
        async with self._client(InMemoryFlagRepository()) as client:
            listing = await client.get("/admin/")
            assert listing.status_code == 200
            assert "fast-feature" in listing.text
            assert (await client.get("/admin/new")).status_code == 200

    async def test_console_full_form_lifecycle(self) -> None:
        async with self._client(InMemoryFlagRepository()) as client:
            created = await client.post(
                "/admin/new",
                data={
                    "key": "banner",
                    "default_variant": "off",
                    "state": "ENABLED",
                    "variants": '{"on": true, "off": false}',
                },
            )
            assert created.status_code == 303
            assert "banner" in (await client.get("/admin/")).text
            assert (await client.get("/admin/banner/edit")).status_code == 200
            assert (
                await client.post("/admin/banner/toggle", data={"enabled": "true"})
            ).status_code == 303
            updated = await client.post(
                "/admin/banner/edit",
                data={
                    "default_variant": "on",
                    "state": "DISABLED",
                    "variants": '{"on": true, "off": false}',
                },
            )
            assert updated.status_code == 303
            assert (await client.post("/admin/banner/delete", data={})).status_code == 303

    async def test_console_create_invalid_rerenders_with_error(self) -> None:
        async with self._client(InMemoryFlagRepository()) as client:
            response = await client.post(
                "/admin/new",
                data={
                    "key": "x",
                    "default_variant": "missing",
                    "state": "ENABLED",
                    "variants": '{"on": true}',
                },
            )
            assert response.status_code == 400
            assert "not among" in response.text

    async def test_console_edit_missing_is_404(self) -> None:
        async with self._client(InMemoryFlagRepository()) as client:
            assert (await client.get("/admin/ghost/edit")).status_code == 404

    # --- auth ---

    async def test_auth_dependency_blocks_every_route(self) -> None:
        guarded = [Depends(_RejectAll())]
        async with self._client(InMemoryFlagRepository(), dependencies=guarded) as client:
            assert (await client.get("/admin/api/flags")).status_code == 401
            assert (await client.get("/admin/")).status_code == 401
