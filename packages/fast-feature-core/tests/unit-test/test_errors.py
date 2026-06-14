from __future__ import annotations

from fast_feature.core import (
    CoreError,
    FlagAlreadyExistsError,
    FlagNotFoundError,
    InvalidFlagError,
)


class TestErrors:
    def test_not_found_carries_key(self) -> None:
        error = FlagNotFoundError("missing")
        assert error.key == "missing"
        assert isinstance(error, CoreError)
        assert "missing" in str(error)

    def test_already_exists_carries_key(self) -> None:
        error = FlagAlreadyExistsError("dup")
        assert error.key == "dup"
        assert isinstance(error, CoreError)
        assert "dup" in str(error)

    def test_invalid_flag_is_a_core_error(self) -> None:
        assert issubclass(InvalidFlagError, CoreError)
