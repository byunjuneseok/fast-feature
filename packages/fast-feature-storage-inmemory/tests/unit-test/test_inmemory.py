from __future__ import annotations

import pytest

from fast_feature.core import FlagRepository
from fast_feature.storage.inmemory import InMemoryFlagRepository
from fast_feature.testing import FlagRepositoryContract


class TestInMemoryFlagRepository(FlagRepositoryContract):
    @pytest.fixture
    def repository(self) -> FlagRepository:
        return InMemoryFlagRepository()
