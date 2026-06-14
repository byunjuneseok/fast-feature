from __future__ import annotations

import copy
from collections.abc import Iterable

from fast_feature.core import Flag, FlagAlreadyExistsError, FlagNotFoundError, FlagRepository


class InMemoryFlagRepository(FlagRepository):
    """A dict-backed repository. Values are deep-copied so stored flags are
    isolated from later mutation of the caller's objects."""

    def __init__(self, flags: Iterable[Flag] | None = None) -> None:
        self._flags: dict[str, Flag] = {}
        for flag in flags or ():
            self._flags[flag.key] = copy.deepcopy(flag)

    async def get(self, key: str) -> Flag | None:
        flag = self._flags.get(key)
        return copy.deepcopy(flag) if flag is not None else None

    async def list_all(self) -> list[Flag]:
        return [copy.deepcopy(self._flags[key]) for key in sorted(self._flags)]

    async def create(self, flag: Flag) -> Flag:
        if flag.key in self._flags:
            raise FlagAlreadyExistsError(flag.key)
        self._flags[flag.key] = copy.deepcopy(flag)
        return copy.deepcopy(flag)

    async def update(self, flag: Flag) -> Flag:
        if flag.key not in self._flags:
            raise FlagNotFoundError(flag.key)
        self._flags[flag.key] = copy.deepcopy(flag)
        return copy.deepcopy(flag)

    async def delete(self, key: str) -> None:
        if key not in self._flags:
            raise FlagNotFoundError(key)
        del self._flags[key]
