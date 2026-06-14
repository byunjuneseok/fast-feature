from __future__ import annotations

from collections import Counter
from typing import Any

import pytest

from fast_feature.core import Flag, Reason
from fast_feature.engine import TargetingEngine

engine = TargetingEngine()


class TestTieredRollout:
    """plan/country/beta tiers, falling through to a fractional rollout."""

    @staticmethod
    def _flag() -> Flag:
        return Flag(
            key="checkout-redesign",
            variants={"on": True, "off": False},
            default_variant="off",
            targeting={
                "if": [
                    {"==": [{"var": "plan"}, "enterprise"]},
                    "on",
                    {
                        "and": [
                            {"==": [{"var": "plan"}, "pro"]},
                            {"in": [{"var": "country"}, ["US", "CA", "KR"]]},
                        ]
                    },
                    "on",
                    {"and": [{"==": [{"var": "plan"}, "free"]}, {"var": "beta"}]},
                    {"fractional": [{"var": "targetingKey"}, ["on", 20], ["off", 80]]},
                    "off",
                ]
            },
        )

    @pytest.mark.parametrize(
        ("context", "expected"),
        [
            ({"plan": "enterprise"}, "on"),
            ({"plan": "enterprise", "country": "ZZ"}, "on"),
            ({"plan": "pro", "country": "US"}, "on"),
            ({"plan": "pro", "country": "KR"}, "on"),
            ({"plan": "pro", "country": "JP"}, "off"),
            ({"plan": "pro"}, "off"),  # country missing -> not in list
            ({"plan": "free", "beta": False}, "off"),
            ({}, "off"),  # nothing matches
        ],
    )
    def test_deterministic_tiers(self, context: dict[str, Any], expected: str) -> None:
        outcome = engine.evaluate(self._flag(), context)
        assert outcome.variant == expected
        assert outcome.reason is Reason.TARGETING_MATCH

    def test_free_beta_users_hit_the_fractional_branch(self) -> None:
        seen = set()
        for i in range(500):
            outcome = engine.evaluate(
                self._flag(), {"plan": "free", "beta": True, "targetingKey": f"u-{i}"}
            )
            seen.add(outcome.variant)
        assert seen == {"on", "off"}  # both buckets are reachable

    def test_fractional_branch_is_deterministic_per_key(self) -> None:
        context: dict[str, Any] = {"plan": "free", "beta": True, "targetingKey": "stable-user"}
        first = engine.evaluate(self._flag(), context).variant
        assert engine.evaluate(self._flag(), context).variant == first


class TestSemVerGating:
    @staticmethod
    def _flag() -> Flag:
        return Flag(
            key="min-app-version",
            variants={"new": "new", "old": "old"},
            default_variant="old",
            targeting={"if": [{"sem_ver": [{"var": "appVersion"}, ">=", "2.4.0"]}, "new", "old"]},
        )

    @pytest.mark.parametrize(
        ("version", "expected"),
        [
            ("2.4.0", "new"),
            ("2.4.1", "new"),
            ("3.0.0", "new"),
            ("2.3.9", "old"),
            ("1.9.9", "old"),
            ("not-a-version", "old"),
        ],
    )
    def test_version_threshold(self, version: str, expected: str) -> None:
        assert engine.evaluate(self._flag(), {"appVersion": version}).variant == expected


class TestEmailDomainTargeting:
    @staticmethod
    def _flag() -> Flag:
        return Flag(
            key="internal-banner",
            variants={"show": True, "hide": False},
            default_variant="hide",
            targeting={
                "if": [
                    {
                        "or": [
                            {"ends_with": [{"var": "email"}, "@corp.com"]},
                            {"starts_with": [{"var": "email"}, "admin+"]},
                        ]
                    },
                    "show",
                    "hide",
                ]
            },
        )

    @pytest.mark.parametrize(
        ("email", "expected"),
        [
            ("jane@corp.com", "show"),
            ("admin+ops@gmail.com", "show"),
            ("user@gmail.com", "hide"),
            ("corp.com@evil.com", "hide"),
        ],
    )
    def test_domain_rules(self, email: str, expected: str) -> None:
        assert engine.evaluate(self._flag(), {"email": email}).variant == expected


class TestArrayMembership:
    @staticmethod
    def _flag() -> Flag:
        return Flag(
            key="premium-features",
            variants={"full": "full", "limited": "limited"},
            default_variant="limited",
            targeting={
                "if": [
                    {"some": [{"var": "roles"}, {"==": [{"var": ""}, "admin"]}]},
                    "full",
                    "limited",
                ]
            },
        )

    @pytest.mark.parametrize(
        ("roles", "expected"),
        [
            (["admin"], "full"),
            (["viewer", "admin"], "full"),
            (["viewer"], "limited"),
            ([], "limited"),
        ],
    )
    def test_role_membership(self, roles: list[Any], expected: str) -> None:
        context: dict[str, Any] = {"roles": roles}
        assert engine.evaluate(self._flag(), context).variant == expected


class TestNumericBands:
    @staticmethod
    def _flag() -> Flag:
        return Flag(
            key="ltv-band",
            variants={"vip": "vip", "mid": "mid", "low": "low"},
            default_variant="low",
            targeting={
                "if": [
                    {">=": [{"var": "ltv"}, 1000]},
                    "vip",
                    {"<": [{"var": "ltv"}, 100]},
                    "low",
                    "mid",
                ]
            },
        )

    @pytest.mark.parametrize(
        ("ltv", "expected"),
        [(5000, "vip"), (1000, "vip"), (500, "mid"), (100, "mid"), (99, "low"), (0, "low")],
    )
    def test_bands(self, ltv: int, expected: str) -> None:
        assert engine.evaluate(self._flag(), {"ltv": ltv}).variant == expected


class TestMultiVariantFractional:
    @staticmethod
    def _flag() -> Flag:
        return Flag(
            key="theme-experiment",
            variants={"a": "a", "b": "b", "c": "c"},
            default_variant="a",
            targeting={"fractional": [{"var": "targetingKey"}, ["a", 34], ["b", 33], ["c", 33]]},
        )

    def test_three_way_split_is_balanced_and_deterministic(self) -> None:
        counts: Counter[str] = Counter()
        for i in range(6000):
            key = f"user-{i}"
            variant = engine.evaluate(self._flag(), {"targetingKey": key}).variant
            assert variant is not None
            counts[variant] += 1
            assert engine.evaluate(self._flag(), {"targetingKey": key}).variant == variant
        assert set(counts) == {"a", "b", "c"}
        # each bucket is within a loose band around its ~1/3 weight
        for variant in ("a", "b", "c"):
            assert 1500 < counts[variant] < 2500


class TestDeeplyNestedBooleans:
    @staticmethod
    def _flag() -> Flag:
        # enable for premium, OR (free AND beta AND NOT blocked AND region in EU)
        return Flag(
            key="gdpr-export",
            variants={"on": True, "off": False},
            default_variant="off",
            targeting={
                "if": [
                    {
                        "or": [
                            {"==": [{"var": "plan"}, "premium"]},
                            {
                                "and": [
                                    {"==": [{"var": "plan"}, "free"]},
                                    {"var": "beta"},
                                    {"!": [{"var": "blocked"}]},
                                    {"in": [{"var": "region"}, ["EU", "EEA"]]},
                                ]
                            },
                        ]
                    },
                    "on",
                    "off",
                ]
            },
        )

    @pytest.mark.parametrize(
        ("context", "expected"),
        [
            ({"plan": "premium"}, "on"),
            ({"plan": "free", "beta": True, "blocked": False, "region": "EU"}, "on"),
            ({"plan": "free", "beta": True, "blocked": True, "region": "EU"}, "off"),
            ({"plan": "free", "beta": True, "blocked": False, "region": "US"}, "off"),
            ({"plan": "free", "beta": False, "blocked": False, "region": "EU"}, "off"),
            ({"plan": "free"}, "off"),
        ],
    )
    def test_nested_logic(self, context: dict[str, Any], expected: str) -> None:
        assert engine.evaluate(self._flag(), context).variant == expected
