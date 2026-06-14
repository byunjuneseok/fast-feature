from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from fast_feature.storage.sqlalchemy import Schema, SqlAlchemyFlagRepository


class PostgresStorage:
    """Wires a PostgreSQL (asyncpg) engine to the SQLAlchemy repository."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine
        self._session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @classmethod
    def from_dsn(cls, dsn: str, **engine_options: object) -> PostgresStorage:
        return cls(create_async_engine(cls._normalize_dsn(dsn), **engine_options))

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @property
    def repository(self) -> SqlAlchemyFlagRepository:
        return SqlAlchemyFlagRepository(self._session_factory)

    async def create_schema(self) -> None:
        await Schema.create_all(self._engine)

    @staticmethod
    def _normalize_dsn(dsn: str) -> str:
        for prefix in ("postgresql://", "postgres://"):
            if dsn.startswith(prefix):
                return f"postgresql+asyncpg://{dsn[len(prefix) :]}"
        return dsn
