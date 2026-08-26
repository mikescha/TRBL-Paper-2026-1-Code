import csv
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


def validate_manifest_row_width(path: Path) -> None:
    """Raise if any manifest row has too many or too few CSV fields.

    This catches subtle comma errors before pandas can silently shift or drop
    values.
    """
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)

        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError(f"Manifest is empty: {path}") from exc

        expected_width = len(header)

        for line_number, row in enumerate(reader, start=2):
            if not row or all(str(value).strip() == "" for value in row):
                continue

            if len(row) != expected_width:
                raise ValueError(
                    f"Manifest row {line_number} has {len(row)} fields, "
                    f"but the header has {expected_width}. This usually means "
                    f"the row has too many or too few commas. Row: {row}"
                )


def read_manifest(path: Path) -> pd.DataFrame:
    """
    Read and normalize the figure manifest.

    Canonical columns:
        site_id, site_name,
        manual, mini_manual, edge, pattern_matching,
        include_composite, include_key

    Backward-compatible aliases:
        name -> site_name
        composite -> include_composite
    """
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")

    validate_manifest_row_width(path)

    df = pd.read_csv(path, index_col=False)

    # Confirm the columns are what we expect. If not, raise an error with a helpful message.
    required_cols = [
        "site_id",
        "site_name",
        "manual",
        "mini_manual",
        "edge",
        "pattern_matching",
        "include_composite",
        "include_key",
    ]

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Manifest is missing required columns: {missing_cols}")

    df["site_id"] = df["site_id"].astype(str).str.strip()
    df["site_name"] = df["site_name"].astype(str).str.strip()

    blank_site_rows = df[(df["site_id"] == "") | (df["site_name"] == "")]
    if not blank_site_rows.empty:
        raise ValueError(
            "Manifest has blank site_id or site_name values. "
            f"First bad rows:\n{blank_site_rows.head()}"
        )

    bad_site_id_rows = df[~df["site_id"].str.fullmatch(r"\d+")]
    if not bad_site_id_rows.empty:
        raise ValueError(
            "Manifest site_id values must be numeric. "
            "This often means a row has too many commas. "
            f"First bad rows:\n{bad_site_id_rows.head()}"
        )

    df["site_id"] = df["site_id"].astype(str).str.strip()
    df["site_name"] = df["site_name"].astype(str).str.strip()

    # Add missing panel columns as false.
    for col in PANEL_COLUMNS:
        if col not in df.columns:
            df[col] = False

    bool_cols = PANEL_COLUMNS + [
        "include_composite",
        "include_key",
    ]

    for col in bool_cols:
        df[col] = df[col].apply(parse_bool)

    # If the row says "make a composite" but no specific panel columns are true,
    # treat that as "generate all available panels for this site."
    # e.g.
    #
    #   composite=1, manual=0, mini_manual=0, edge=0, pattern_matching=0
    #
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
        if limit < 1:
            raise ValueError(f"--limit must be at least 1, got {limit}.")
        df = df.head(limit)

    df = df.sort_values("site_name").reset_index(drop=True)
    return df
