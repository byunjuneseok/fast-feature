from __future__ import annotations

import pytest

from fast_feature.storage.postgresql import PostgresStorage
from fast_feature.storage.sqlalchemy import SqlAlchemyFlagRepository


class TestPostgresStorage:
    @pytest.mark.parametrize(
        "dsn",
        [
            "postgresql://u:p@localhost:5432/db",
            "postgres://u:p@localhost:5432/db",
            "postgresql+asyncpg://u:p@localhost:5432/db",
        ],
    )
    def test_from_dsn_uses_the_asyncpg_driver(self, dsn: str) -> None:
        storage = PostgresStorage.from_dsn(dsn)
        assert storage.engine.url.drivername == "postgresql+asyncpg"

    def test_repository_is_sqlalchemy_backed(self) -> None:
        storage = PostgresStorage.from_dsn("postgresql+asyncpg://u:p@localhost/db")
        assert isinstance(storage.repository, SqlAlchemyFlagRepository)
