from __future__ import annotations

from fast_feature.core import Flag, FlagAlreadyExistsError, FlagNotFoundError, FlagRepository
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .mapper import FlagMapper
from .model import FeatureFlagRow


class SqlAlchemyFlagRepository(FlagRepository):
    """A ``FlagRepository`` backed by an async SQLAlchemy session factory."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get(self, key: str) -> Flag | None:
        async with self._session_factory() as session:
            row = await session.get(FeatureFlagRow, key)
            return FlagMapper.to_domain(row) if row is not None else None

    async def list_all(self) -> list[Flag]:
        async with self._session_factory() as session:
            result = await session.execute(select(FeatureFlagRow).order_by(FeatureFlagRow.key))
            return [FlagMapper.to_domain(row) for row in result.scalars()]

    async def create(self, flag: Flag) -> Flag:
        async with self._session_factory() as session:
            session.add(FlagMapper.to_row(flag))
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                raise FlagAlreadyExistsError(flag.key) from exc
            return flag

    async def update(self, flag: Flag) -> Flag:
        async with self._session_factory() as session:
            row = await session.get(FeatureFlagRow, flag.key)
            if row is None:
                raise FlagNotFoundError(flag.key)
            FlagMapper.apply(row, flag)
            await session.commit()
            return flag

    async def delete(self, key: str) -> None:
        async with self._session_factory() as session:
            row = await session.get(FeatureFlagRow, key)
            if row is None:
                raise FlagNotFoundError(key)
            await session.delete(row)
            await session.commit()
