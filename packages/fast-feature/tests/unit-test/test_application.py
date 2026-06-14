from __future__ import annotations

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from fast_feature.server import Application, Settings


class TestApplication:
    @staticmethod
    def _client(app: FastAPI) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    async def test_ofrep_is_mounted(self) -> None:
        app = Application.create(Settings(backend="inmemory", admin=False))
        async with self._client(app) as client:
            response = await client.post("/ofrep/v1/evaluate/flags", json={"context": {}})
        assert response.status_code == 200
        assert response.json()["flags"] == []

    async def test_admin_is_absent_by_default(self) -> None:
        app = Application.create(Settings(admin=False))
        async with self._client(app) as client:
            assert (await client.get("/admin/")).status_code == 404

    async def test_admin_is_mounted_when_enabled(self) -> None:
        app = Application.create(Settings(admin=True))
        async with self._client(app) as client:
            assert (await client.get("/admin/")).status_code == 200
