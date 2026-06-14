from __future__ import annotations

from fast_feature.core import FlagRepository
from fast_feature.storage.inmemory import InMemoryFlagRepository

from .settings import Settings


class RepositoryFactory:
    """Builds the configured ``FlagRepository`` for the standalone server."""

    @staticmethod
    def from_settings(settings: Settings) -> FlagRepository:
        if settings.backend == "postgresql":
            if not settings.database_url:
                raise ValueError("FAST_FEATURE_DATABASE_URL is required for the postgresql backend")
            # Imported lazily so the dependency is only needed with the extra.
            from fast_feature.storage.postgresql import PostgresStorage

            return PostgresStorage.from_dsn(settings.database_url).repository
        return InMemoryFlagRepository()
