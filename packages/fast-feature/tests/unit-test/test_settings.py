from __future__ import annotations

import pytest

from fast_feature.server import Settings

_ENV_VARS = (
    "FAST_FEATURE_BACKEND",
    "FAST_FEATURE_DATABASE_URL",
    "FAST_FEATURE_ADMIN",
    "FAST_FEATURE_ADMIN_PREFIX",
)


class TestSettings:
    def test_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for name in _ENV_VARS:
            monkeypatch.delenv(name, raising=False)
        settings = Settings()
        assert settings.backend == "inmemory"
        assert settings.database_url is None
        assert settings.admin is False
        assert settings.admin_prefix == "/admin"

    def test_reads_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FAST_FEATURE_BACKEND", "postgresql")
        monkeypatch.setenv("FAST_FEATURE_DATABASE_URL", "postgresql://u:p@localhost/db")
        monkeypatch.setenv("FAST_FEATURE_ADMIN", "true")
        settings = Settings()
        assert settings.backend == "postgresql"
        assert settings.database_url == "postgresql://u:p@localhost/db"
        assert settings.admin is True
