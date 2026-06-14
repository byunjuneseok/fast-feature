from __future__ import annotations

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from fast_feature.core import Flag, FlagRepository
from fast_feature.ofrep import OfrepRouter


class FakeFlagRepository(FlagRepository):
    def __init__(self, flags: list[Flag] | None = None) -> None:
        self._flags = {flag.key: flag for flag in (flags or [])}

    async def get(self, key: str) -> Flag | None:
        return self._flags.get(key)

    async def list_all(self) -> list[Flag]:
        return list(self._flags.values())

    async def create(self, flag: Flag) -> Flag:
        self._flags[flag.key] = flag
        return flag

    async def update(self, flag: Flag) -> Flag:
        self._flags[flag.key] = flag
        return flag

    async def delete(self, key: str) -> None:
        del self._flags[key]


class TestOfrepRouter:
    @staticmethod
    def _flags() -> list[Flag]:
        return [
            Flag(
                key="banner",
                variants={"on": True, "off": False},
                default_variant="off",
                targeting={"if": [{"==": [{"var": "tier"}, "premium"]}, "on", "off"]},
            ),
            Flag(key="theme", variants={"blue": "blue", "red": "red"}, default_variant="blue"),
        ]

    @staticmethod
    def _client(flags: list[Flag]) -> AsyncClient:
        app = FastAPI()
        app.include_router(OfrepRouter.build(FakeFlagRepository(flags)))
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    async def test_single_targeting_match(self) -> None:
        async with self._client(self._flags()) as client:
            response = await client.post(
                "/ofrep/v1/evaluate/flags/banner", json={"context": {"tier": "premium"}}
            )
        assert response.status_code == 200
        body = response.json()
        assert body["value"] is True
        assert body["reason"] == "TARGETING_MATCH"
        assert body["variant"] == "on"

    async def test_single_static(self) -> None:
        async with self._client(self._flags()) as client:
            response = await client.post("/ofrep/v1/evaluate/flags/theme", json={"context": {}})
        assert response.status_code == 200
        assert response.json()["reason"] == "STATIC"

    async def test_single_not_found(self) -> None:
        async with self._client(self._flags()) as client:
            response = await client.post("/ofrep/v1/evaluate/flags/missing", json={"context": {}})
        assert response.status_code == 404
        body = response.json()
        assert body["errorCode"] == "FLAG_NOT_FOUND"
        assert body["key"] == "missing"

    async def test_single_evaluation_failure(self) -> None:
        flags = [
            Flag(
                key="broken",
                variants={"on": True, "off": False},
                default_variant="off",
                targeting={"bogus_op": [1]},
            )
        ]
        async with self._client(flags) as client:
            response = await client.post("/ofrep/v1/evaluate/flags/broken", json={"context": {}})
        assert response.status_code == 400
        assert response.json()["errorCode"] == "PARSE_ERROR"

    async def test_bulk_and_etag_round_trip(self) -> None:
        async with self._client(self._flags()) as client:
            response = await client.post("/ofrep/v1/evaluate/flags", json={"context": {}})
            assert response.status_code == 200
            etag = response.headers["etag"]
            assert {flag["key"] for flag in response.json()["flags"]} == {"banner", "theme"}

            cached = await client.post(
                "/ofrep/v1/evaluate/flags",
                json={"context": {}},
                headers={"If-None-Match": etag},
            )
        assert cached.status_code == 304

    async def test_bulk_includes_per_flag_failures(self) -> None:
        flags = [
            Flag(key="ok", variants={"on": True}, default_variant="on"),
            Flag(
                key="broken",
                variants={"on": True, "off": False},
                default_variant="off",
                targeting={"bogus_op": [1]},
            ),
        ]
        async with self._client(flags) as client:
            response = await client.post("/ofrep/v1/evaluate/flags", json={"context": {}})
        assert response.status_code == 200
        items = {flag["key"]: flag for flag in response.json()["flags"]}
        assert items["broken"]["errorCode"] == "PARSE_ERROR"
        assert "errorCode" not in items["ok"]
