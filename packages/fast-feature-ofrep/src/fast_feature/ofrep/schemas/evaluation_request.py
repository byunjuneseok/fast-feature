from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EvaluationRequest(BaseModel):
    """Body of a single-flag evaluation request."""

    context: dict[str, Any] = Field(default_factory=dict)
