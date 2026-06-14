from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine

from .base import Base


class Schema:
    """Creates the database schema.

    Convenient for development and tests; production deployments should manage
    the ``feature_flags`` table with their own migration tooling.
    """

    @staticmethod
    async def create_all(engine: AsyncEngine) -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
