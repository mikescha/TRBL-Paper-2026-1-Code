from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from trbl_figures import constants as C
from trbl_figures.pivots import clean_data

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_INPUT_CSV = DEFAULT_DATA_DIR / "TRBL Analysis tracking - All.csv"
DEFAULT_PMJ_DIR = DEFAULT_DATA_DIR / "PMJ Data"


def empty_pm_data_frame() -> pd.DataFrame:
    """Return the legacy empty PM data shape with a true DatetimeIndex."""
    return pd.DataFrame(
        {
            "type": pd.Series([], dtype="object"),
        },
        index=pd.DatetimeIndex([], name=C.DATE_COL),
    )


@lru_cache
def load_summary_data() -> pd.DataFrame:
    # Load the summary data and prep it for graphing.
    df = pd.read_csv(C.INPUT_CSV, skiprows=C.ALL_SHEET_HEADER_SIZE)

    # Convert numeric columns to integers. As above, you have to force it this way if the types vary.
    # Empty values or strings are converted to NaN
    df[C.SUMMARY_NUMERIC_COLS] = df[C.SUMMARY_NUMERIC_COLS].apply(pd.to_numeric, errors="coerce")
    df[C.SUMMARY_NUMERIC_COLS] = df[C.SUMMARY_NUMERIC_COLS].astype(pd.Int64Dtype())  # Keeps NaNs

    return df


@lru_cache
def load_site_data(site: str):
    """
    Given a site, retrieve the data set for that

    :param site: Description
    :type site: str
    """
    year = site[0:4]
    pusecols = [C.DATA_COL[C.FILENAME], C.DATA_COL[C.SITE], 
                C.DATA_COL[C.DATE_COL], C.DATA_COL[C.HOUR]]
    for song in C.ALL_SONGS:
        pusecols.append(C.DATA_COL[song])
    for tag in C.ALL_TAGS:
        pusecols.append(C.DATA_COL[tag])

    pfile_name = C.DATA_DIR / f"data {year}.parquet"
    pusecols.append("dt")

    pdf = pd.read_parquet(pfile_name, columns=pusecols)
    pdf = pdf[pdf[C.SITE] == site]
    pdf = pdf.set_index("dt")
    pdf.index = pd.DatetimeIndex(pdf.index).normalize()
    df = clean_data(pdf, [site])
    df = df.rename_axis(C.DATE_COL)

    return df


def load_pmj_subset_from_parquet(
    site: str,
    call_type: str,
    columns: list[str],
) -> pd.DataFrame:
    """Load one site/call-type subset from the partitioned PMJ Parquet dataset."""
    if not C.PMJ_DIR.exists():
        return pd.DataFrame(columns=columns)

    # site and call_type are partition columns. They may be represented as
    # partition metadata rather than physical columns, so do not request them
    # as physical columns from the Parquet files.
    physical_columns = [
        col for col in columns
        if col not in {"site", "call_type"}
    ]

    df = pd.read_parquet(
        C.PMJ_DIR,
        columns=physical_columns,
        filters=[
            ("site", "==", site),
            ("call_type", "==", call_type),
        ],
    )

    if "site" in columns:
        df["site"] = site

    if "call_type" in columns:
        df["call_type"] = call_type

    for col in columns:
        if col not in df.columns:
            df[col] = pd.NA

    return df[columns]


def load_pm_data(site: str) -> pd.DataFrame:
    """Load PMJ detections for one site from the partitioned Parquet dataset.

    The Parquet dataset is partitioned by site and call_type. This replaces the
    legacy CSV layout:

        PMJ Data / <site> / <site> <call_type>.csv

    with exact partition lookups:

        site == <site>
        call_type == <call_type>
    """
    usecols = [
        C.SITE_COLS[C.SITE],
        C.SITE_COLS["year"],
        C.SITE_COLS["month"],
        C.SITE_COLS["day"],
        C.SITE_COLS[C.HOUR],
        C.SITE_COLS[C.VALIDATED_STR],
    ]

    out_cols = [*usecols, C.DATE_COL, "type"]
    frames: list[pd.DataFrame] = []

    for t in C.PM_FILE_TYPES:
        df_single_pmj_type = load_pmj_subset_from_parquet(
            site=site,
            call_type=t,
            columns=usecols,
        )

        if df_single_pmj_type.empty:
            # Preserve the legacy behavior: missing/empty call types simply add
            # no rows, but downstream code still receives a well-shaped frame.
            continue

        missing = set(usecols) - set(df_single_pmj_type.columns)
        if missing:
            raise ValueError(
                f"Missing columns in PMJ Parquet subset for site={site!r}, "
                f"call_type={t!r}: {sorted(missing)}"
            )

        df_single_pmj_type = df_single_pmj_type.copy()

        df_single_pmj_type[C.DATE_COL] = pd.to_datetime(
            df_single_pmj_type[
                [
                    C.SITE_COLS["year"],
                    C.SITE_COLS["month"],
                    C.SITE_COLS["day"],
                ]
            ],
            errors="coerce",
        )

        df_single_pmj_type = df_single_pmj_type[df_single_pmj_type[C.DATE_COL].notna()].copy()

        if df_single_pmj_type.empty:
            continue

        df_single_pmj_type["type"] = t

        # Preserve the old broad dtype behavior to avoid downstream surprises.
        df_single_pmj_type = df_single_pmj_type[out_cols].astype("object")
        frames.append(df_single_pmj_type)

    if not frames:
        return empty_pm_data_frame()

    df = pd.concat(frames, ignore_index=True)

    df[C.DATE_COL] = pd.to_datetime(df[C.DATE_COL], errors="coerce")
    df = df[df[C.DATE_COL].notna()].copy()

    if df.empty:
        return empty_pm_data_frame()

    df.set_index(C.DATE_COL, inplace=True)

    return df
