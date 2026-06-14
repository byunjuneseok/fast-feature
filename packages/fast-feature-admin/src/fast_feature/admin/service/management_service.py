from __future__ import annotations

from fast_feature.core import Flag, FlagNotFoundError, FlagRepository, FlagState


class ManagementService:
    """Flag administration use cases on top of a ``FlagRepository``."""

    def __init__(self, repository: FlagRepository) -> None:
        self._repository = repository

    async def list_flags(self) -> list[Flag]:
        return await self._repository.list_all()

    async def get_flag(self, key: str) -> Flag | None:
        return await self._repository.get(key)

    async def create_flag(self, flag: Flag) -> Flag:
        return await self._repository.create(flag)

    async def update_flag(self, flag: Flag) -> Flag:
        return await self._repository.update(flag)

    async def delete_flag(self, key: str) -> None:
        await self._repository.delete(key)

    async def toggle(self, key: str, *, enabled: bool) -> Flag:
        flag = await self._repository.get(key)
        if flag is None:
            raise FlagNotFoundError(key)
        flag.state = FlagState.ENABLED if enabled else FlagState.DISABLED
        return await self._repository.update(flag)
