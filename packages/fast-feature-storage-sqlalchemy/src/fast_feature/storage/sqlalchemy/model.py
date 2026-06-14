from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FeatureFlagRow(Base):
    __tablename__ = "feature_flags"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    variants: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    default_variant: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    targeting: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # "metadata" is reserved on declarative classes, so the attribute is renamed.
    flag_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
