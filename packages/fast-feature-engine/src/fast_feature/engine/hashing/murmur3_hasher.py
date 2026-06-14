from __future__ import annotations

import mmh3


class Murmur3Hasher:
    """MurmurHash3 (x86, 32-bit) hasher backed by the ``mmh3`` library."""

    @property
    def max_value(self) -> int:
        return 0xFFFFFFFF

    def hash(self, key: str) -> int:
        return mmh3.hash(key, signed=False)
