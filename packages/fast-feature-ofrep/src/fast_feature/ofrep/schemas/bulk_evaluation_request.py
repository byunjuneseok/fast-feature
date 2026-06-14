from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BulkEvaluationRequest(BaseModel):
    """Body of a bulk evaluation request (static context for all flags)."""

    context: dict[str, Any] = Field(default_factory=dict)
