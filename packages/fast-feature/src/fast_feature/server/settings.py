from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Standalone-server configuration, read from ``FAST_FEATURE_*`` env vars."""

    model_config = SettingsConfigDict(env_prefix="FAST_FEATURE_")

    backend: Literal["inmemory", "postgresql"] = "inmemory"
    database_url: str | None = None
    admin: bool = False
    admin_prefix: str = "/admin"
