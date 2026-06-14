from __future__ import annotations

from fast_feature.engine import SemanticVersion


class TestParsing:
    def test_parses_full_version(self) -> None:
        assert SemanticVersion.parse("1.2.3") == SemanticVersion(1, 2, 3)

    def test_parses_partial_and_v_prefix(self) -> None:
        assert SemanticVersion.parse("v2") == SemanticVersion(2, 0, 0)
        assert SemanticVersion.parse("1.4") == SemanticVersion(1, 4, 0)

    def test_returns_none_for_garbage(self) -> None:
        assert SemanticVersion.parse("not-a-version") is None
        assert SemanticVersion.parse(123) is None


class TestOrdering:
    def test_orders_by_components(self) -> None:
        assert SemanticVersion(1, 2, 3) < SemanticVersion(1, 10, 0)
        assert SemanticVersion(2, 0, 0) > SemanticVersion(1, 9, 9)


class TestSatisfies:
    def test_caret_matches_major(self) -> None:
        assert SemanticVersion(1, 5, 0).satisfies("^", SemanticVersion(1, 2, 3))
        assert not SemanticVersion(2, 0, 0).satisfies("^", SemanticVersion(1, 2, 3))

    def test_tilde_matches_major_minor(self) -> None:
        assert SemanticVersion(1, 2, 9).satisfies("~", SemanticVersion(1, 2, 0))
        assert not SemanticVersion(1, 3, 0).satisfies("~", SemanticVersion(1, 2, 0))

    def test_unknown_operator_is_false(self) -> None:
        assert not SemanticVersion(1, 0, 0).satisfies("??", SemanticVersion(1, 0, 0))
