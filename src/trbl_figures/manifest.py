from pathlib import Path
from typing import Any

import pandas as pd

PANEL_COLUMNS = ["manual", "mini_manual", "edge", "pattern_matching"]


def parse_bool(value: Any) -> bool:
    """Parse common CSV boolean-ish values."""
    if pd.isna(value):
        return False

    if isinstance(value, bool):
        return value

    if isinstance(value, int | float):
        return value != 0

    text = str(value).strip().lower()

    if text in {"1", "true", "t", "yes", "y"}:
        return True

    if text in {"0", "false", "f", "no", "n", ""}:
        return False

    raise ValueError(f"Cannot parse boolean value: {value!r}")


def read_manifest(path: Path) -> pd.DataFrame:
    """
    Read and normalize the figure manifest.

    Canonical columns:
        site_id, site_name,
        manual, mini_manual, edge, pattern_matching,
        include_components, include_composite, include_key

    Backward-compatible aliases:
        name -> site_name
        composite -> include_composite
    """
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")

    df = pd.read_csv(path)

    if "site_name" not in df.columns and "name" in df.columns:
        df = df.rename(columns={"name": "site_name"})

    if "include_composite" not in df.columns and "composite" in df.columns:
        df = df.rename(columns={"composite": "include_composite"})

    required = {"site_id", "site_name"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Manifest is missing required columns: {sorted(missing)}")

    # Add missing panel columns as false.
    for col in PANEL_COLUMNS:
        if col not in df.columns:
            df[col] = False

    # Sensible defaults.
    if "include_components" not in df.columns:
        df["include_components"] = True

    if "include_composite" not in df.columns:
        df["include_composite"] = True

    if "include_key" not in df.columns:
        df["include_key"] = True

    bool_cols = PANEL_COLUMNS + [
        "include_components",
        "include_composite",
        "include_key",
    ]

    for col in bool_cols:
        df[col] = df[col].apply(parse_bool)

    # If the row says "make a composite" but no specific panel columns are true,
    # treat that as "generate all available panels for this site."
    #
    # This preserves your original idea:
    #   composite=1, manual=0, mini_manual=0, edge=0, pattern_matching=0
    # means "make the composite from whatever graph types exist."
    df["all_available_panels"] = False
    no_panels_selected = ~df[PANEL_COLUMNS].any(axis=1)
    df.loc[df["include_composite"] & no_panels_selected, "all_available_panels"] = True

    return df


def filter_manifest(
    manifest_df: pd.DataFrame,
    only_sites: list[str] | None,
    limit: int | None,
) -> pd.DataFrame:
    """Apply command-line filters to the manifest."""
    df = manifest_df.copy()

    if only_sites:
        site_set = set(only_sites)

        # Match either site_id or site_name because both are handy during debugging.
        df = df[
            df["site_id"].astype(str).isin(site_set)
            | df["site_name"].astype(str).isin(site_set)
        ]

    if limit is not None:
        df = df.head(limit)

    return df

