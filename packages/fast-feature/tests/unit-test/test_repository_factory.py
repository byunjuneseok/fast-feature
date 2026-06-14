from __future__ import annotations

import pytest

from fast_feature.server import RepositoryFactory, Settings
from fast_feature.storage.inmemory import InMemoryFlagRepository
from fast_feature.storage.sqlalchemy import SqlAlchemyFlagRepository


class TestRepositoryFactory:
    def test_inmemory_backend(self) -> None:
        repo = RepositoryFactory.from_settings(Settings(backend="inmemory"))
        assert isinstance(repo, InMemoryFlagRepository)

    def test_postgresql_requires_database_url(self) -> None:
        with pytest.raises(ValueError, match="DATABASE_URL"):
            RepositoryFactory.from_settings(Settings(backend="postgresql", database_url=None))

    def test_postgresql_backend(self) -> None:
        repo = RepositoryFactory.from_settings(
            Settings(backend="postgresql", database_url="postgresql://u:p@localhost/db")
        )
        assert isinstance(repo, SqlAlchemyFlagRepository)
