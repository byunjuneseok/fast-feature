from __future__ import annotations

from fast_feature.core import Flag, FlagState

from .model import FeatureFlagRow


class FlagMapper:
    """Translates between the domain ``Flag`` and the ORM row."""

    @staticmethod
    def to_row(flag: Flag) -> FeatureFlagRow:
        return FeatureFlagRow(
            key=flag.key,
            variants=flag.variants,
            default_variant=flag.default_variant,
            state=flag.state.value,
            targeting=flag.targeting,
            flag_metadata=flag.metadata,
            created_at=flag.created_at,
            updated_at=flag.updated_at,
        )

    @staticmethod
    def to_domain(row: FeatureFlagRow) -> Flag:
        return Flag(
            key=row.key,
            variants=row.variants,
            default_variant=row.default_variant,
            state=FlagState(row.state),
            targeting=row.targeting,
            metadata=row.flag_metadata,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def apply(row: FeatureFlagRow, flag: Flag) -> None:
        row.variants = flag.variants
        row.default_variant = flag.default_variant
        row.state = flag.state.value
        row.targeting = flag.targeting
        row.flag_metadata = flag.metadata
        row.created_at = flag.created_at
        row.updated_at = flag.updated_at
