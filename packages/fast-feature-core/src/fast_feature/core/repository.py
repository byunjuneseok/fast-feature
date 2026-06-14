from __future__ import annotations

from abc import ABC, abstractmethod

from .flag import Flag


class FlagRepository(ABC):
    """Storage boundary for flags.

    Implementations live behind optional extras (``inmemory``, ``postgresql``,
    ``mysql``). The domain and the evaluation engine depend only on this
    interface, never on a concrete storage technology.
    """

    @abstractmethod
    async def get(self, key: str) -> Flag | None:
        """Return the flag with ``key``, or ``None`` if it does not exist."""

    @abstractmethod
    async def list_all(self) -> list[Flag]:
        """Return every flag, ordered by key."""

    @abstractmethod
    async def create(self, flag: Flag) -> Flag:
        """Persist a new flag.

        Raises:
            FlagAlreadyExistsError: if a flag with the same key exists.
        """

    @abstractmethod
    async def update(self, flag: Flag) -> Flag:
        """Replace an existing flag.

        Raises:
            FlagNotFoundError: if the flag does not exist.
        """

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove a flag.

        Raises:
            FlagNotFoundError: if the flag does not exist.
        """

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None
