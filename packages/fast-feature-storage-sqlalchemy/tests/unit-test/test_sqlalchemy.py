from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from fast_feature.core import FlagRepository
from fast_feature.storage.sqlalchemy import Schema, SqlAlchemyFlagRepository
from fast_feature.testing import FlagRepositoryContract


class TestSqlAlchemyFlagRepository(FlagRepositoryContract):
    @pytest.fixture
    async def repository(self) -> AsyncIterator[FlagRepository]:
        engine = create_async_engine(
            "sqlite+aiosqlite://",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
        await Schema.create_all(engine)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            yield SqlAlchemyFlagRepository(session_factory)
        finally:
            await engine.dispose()
