from __future__ import annotations

from fast_feature.engine import Murmur3Hasher


class TestMurmur3Hasher:
    hasher = Murmur3Hasher()

    def test_is_deterministic(self) -> None:
        assert self.hasher.hash("targeting-key-123") == self.hasher.hash("targeting-key-123")

    def test_distinct_keys_differ(self) -> None:
        assert self.hasher.hash("user-1") != self.hasher.hash("user-2")

    def test_stays_within_max_value(self) -> None:
        for key in ("", "a", "user-9999", "a much longer targeting key"):
            assert 0 <= self.hasher.hash(key) <= self.hasher.max_value
