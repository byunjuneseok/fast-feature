from __future__ import annotations

from fast_feature.core import Flag, FlagRepository


class _StubRepository(FlagRepository):
    """Minimal concrete repository used to exercise the base ``exists`` helper."""

    def __init__(self, flags: list[Flag]) -> None:
        self._flags = {flag.key: flag for flag in flags}

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


class TestFlagRepositoryExists:
    async def test_exists_reflects_presence(self) -> None:
        flag = Flag(key="a", variants={"on": True}, default_variant="on")
        repo = _StubRepository([flag])
        assert await repo.exists("a") is True
        assert await repo.exists("missing") is False
