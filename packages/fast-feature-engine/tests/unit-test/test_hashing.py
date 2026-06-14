from __future__ import annotations

from fast_feature.engine import Murmur3Hasher

hasher = Murmur3Hasher()


def test_is_deterministic() -> None:
    assert hasher.hash("targeting-key-123") == hasher.hash("targeting-key-123")


def test_distinct_keys_differ() -> None:
    assert hasher.hash("user-1") != hasher.hash("user-2")


def test_stays_within_max_value() -> None:
    for key in ("", "a", "user-9999", "a much longer targeting key"):
        assert 0 <= hasher.hash(key) <= hasher.max_value
