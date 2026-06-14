from __future__ import annotations

import pytest

from fast_feature.core import (
    Flag,
    FlagAlreadyExistsError,
    FlagNotFoundError,
    FlagRepository,
)


class FlagRepositoryContract:
    """Reusable pytest contract every ``FlagRepository`` must satisfy.

    Subclass it and provide a ``repository`` fixture that returns a fresh,
    empty repository::

        class TestInMemory(FlagRepositoryContract):
            @pytest.fixture
            def repository(self) -> FlagRepository:
                return InMemoryFlagRepository()
    """

    @staticmethod
    def _flag(key: str = "flag", *, default: str = "off") -> Flag:
        return Flag(key=key, variants={"on": True, "off": False}, default_variant=default)

    async def test_create_then_get(self, repository: FlagRepository) -> None:
        await repository.create(self._flag("a"))
        loaded = await repository.get("a")
        assert loaded is not None
        assert loaded.key == "a"
        assert loaded.variants == {"on": True, "off": False}

    async def test_get_missing_returns_none(self, repository: FlagRepository) -> None:
        assert await repository.get("nope") is None

    async def test_create_duplicate_raises(self, repository: FlagRepository) -> None:
        await repository.create(self._flag("a"))
        with pytest.raises(FlagAlreadyExistsError):
            await repository.create(self._flag("a"))

    async def test_update_replaces(self, repository: FlagRepository) -> None:
        await repository.create(self._flag("a", default="off"))
        await repository.update(self._flag("a", default="on"))
        loaded = await repository.get("a")
        assert loaded is not None
        assert loaded.default_variant == "on"

    async def test_update_missing_raises(self, repository: FlagRepository) -> None:
        with pytest.raises(FlagNotFoundError):
            await repository.update(self._flag("ghost"))

    async def test_delete_removes(self, repository: FlagRepository) -> None:
        await repository.create(self._flag("a"))
        await repository.delete("a")
        assert await repository.get("a") is None

    async def test_delete_missing_raises(self, repository: FlagRepository) -> None:
        with pytest.raises(FlagNotFoundError):
            await repository.delete("ghost")

    async def test_list_all_sorted_by_key(self, repository: FlagRepository) -> None:
        for key in ("c", "a", "b"):
            await repository.create(self._flag(key))
        assert [flag.key for flag in await repository.list_all()] == ["a", "b", "c"]

    async def test_exists(self, repository: FlagRepository) -> None:
        await repository.create(self._flag("a"))
        assert await repository.exists("a") is True
        assert await repository.exists("nope") is False

    async def test_stored_flag_is_isolated_from_input(self, repository: FlagRepository) -> None:
        flag = self._flag("a")
        await repository.create(flag)
        flag.variants["on"] = "mutated"
        loaded = await repository.get("a")
        assert loaded is not None
        assert loaded.variants["on"] is True
