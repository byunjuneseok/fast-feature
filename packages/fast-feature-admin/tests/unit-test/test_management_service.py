from __future__ import annotations

import pytest

from fast_feature.admin import ManagementService
from fast_feature.core import Flag, FlagNotFoundError, FlagState
from fast_feature.storage.inmemory import InMemoryFlagRepository


class TestManagementService:
    @staticmethod
    def _service() -> ManagementService:
        return ManagementService(InMemoryFlagRepository())

    @staticmethod
    def _flag(key: str = "a", *, default: str = "off") -> Flag:
        return Flag(key=key, variants={"on": True, "off": False}, default_variant=default)

    async def test_create_and_get(self) -> None:
        service = self._service()
        await service.create_flag(self._flag("a"))
        loaded = await service.get_flag("a")
        assert loaded is not None
        assert loaded.key == "a"

    async def test_list_flags(self) -> None:
        service = self._service()
        await service.create_flag(self._flag("a"))
        await service.create_flag(self._flag("b"))
        assert [flag.key for flag in await service.list_flags()] == ["a", "b"]

    async def test_update_flag(self) -> None:
        service = self._service()
        await service.create_flag(self._flag("a", default="off"))
        await service.update_flag(self._flag("a", default="on"))
        loaded = await service.get_flag("a")
        assert loaded is not None
        assert loaded.default_variant == "on"

    async def test_toggle(self) -> None:
        service = self._service()
        await service.create_flag(self._flag("a"))
        assert (await service.toggle("a", enabled=False)).state is FlagState.DISABLED
        assert (await service.toggle("a", enabled=True)).state is FlagState.ENABLED

    async def test_toggle_missing_raises(self) -> None:
        with pytest.raises(FlagNotFoundError):
            await self._service().toggle("ghost", enabled=True)

    async def test_delete(self) -> None:
        service = self._service()
        await service.create_flag(self._flag("a"))
        await service.delete_flag("a")
        assert await service.get_flag("a") is None
