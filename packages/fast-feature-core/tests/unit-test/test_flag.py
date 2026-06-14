from __future__ import annotations

import pytest

from fast_feature.core import Flag, FlagState, InvalidFlagError


def _flag(**overrides: object) -> Flag:
    kwargs: dict[str, object] = {
        "key": "discount-banner",
        "variants": {"on": True, "off": False},
        "default_variant": "off",
    }
    kwargs.update(overrides)
    return Flag(**kwargs)  # type: ignore[arg-type]


class TestFlagValidation:
    def test_accepts_a_well_formed_flag(self) -> None:
        flag = _flag()
        assert flag.state is FlagState.ENABLED
        assert flag.metadata == {}

    @pytest.mark.parametrize("key", ["has space", "slash/key", "한글", ""])
    def test_rejects_invalid_keys(self, key: str) -> None:
        with pytest.raises(InvalidFlagError):
            _flag(key=key)

    def test_rejects_empty_variants(self) -> None:
        with pytest.raises(InvalidFlagError):
            Flag(key="x", variants={}, default_variant="on")

    def test_rejects_default_variant_outside_variants(self) -> None:
        with pytest.raises(InvalidFlagError):
            Flag(key="x", variants={"on": True}, default_variant="off")


class TestFlagAccessors:
    def test_default_value_follows_default_variant(self) -> None:
        assert _flag(default_variant="on").default_value is True
        assert _flag(default_variant="off").default_value is False

    def test_value_of_returns_the_named_variant(self) -> None:
        flag = _flag()
        assert flag.value_of("on") is True

    def test_has_variant(self) -> None:
        flag = _flag()
        assert flag.has_variant("on")
        assert not flag.has_variant("missing")
