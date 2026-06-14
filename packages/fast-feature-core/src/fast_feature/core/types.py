from __future__ import annotations

from typing import TypeAlias

JsonValue: TypeAlias = "bool | int | float | str | None | list[JsonValue] | dict[str, JsonValue]"
"""Any value expressible in JSON. Flag variants resolve to one of these."""

EvaluationContext: TypeAlias = "dict[str, JsonValue]"
"""Targeting context supplied by a client at evaluation time.

By OpenFeature convention the optional ``targetingKey`` entry identifies the
subject of the evaluation (a user, account, session, ...).
"""
