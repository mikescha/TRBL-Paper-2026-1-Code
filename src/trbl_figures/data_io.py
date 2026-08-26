from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from trbl_figures import constants as C


def empty_pm_data_frame() -> pd.DataFrame:
    """Return the legacy empty PM data shape with a true DatetimeIndex."""
    return pd.DataFrame(
        {
            "type": pd.Series([], dtype="object"),
        },
        index=pd.DatetimeIndex([], name=C.DATE_COL),
    )


# Perform the following operations to clean up the data:
#   - Drop sites that aren't needed, so we're passing around less data
#   - Exclude any data where the year of the data doesn't match the target year
def clean_data(df: pd.DataFrame, site_list: list) -> pd.DataFrame:
    # Drop sites we don't need
    df_clean = pd.DataFrame()
    for site in site_list:
        if C.SITE not in df.columns:
            break

        # Ensure anything outside this year gets dropped
        target_year = site[0:4]
        df_site = df[df[C.SITE] == site]
        df_filtered = df_site.loc[target_year]

        df_filtered = df_filtered.sort_index(ascending=True)
        df_clean = pd.concat([df_clean, df_filtered])

    # We need to preserve the diff between no data and 0 tags. But, we have to also make everything
    # integers for later processing. So, we'll replace the hyphens with a special value and then just
    # realize that we can't do math on this column any more without excluding it. Picked -100 (missing_data_flag) because
    # if we do do math then the answer will be obviously wrong!
    df_clean = df_clean.replace("---", C.MISSING_DATA_FLAG)

    # For each type of song, convert its column to be numeric instead of a string so we can run pivots
    for s in C.ALL_SONGS + C.ALL_TAGS:
        if C.DATA_COL[s] in df_clean.columns:
            df_clean[C.DATA_COL[s]] = pd.to_numeric(df_clean[C.DATA_COL[s]])
    return df_clean


@lru_cache
def load_summary_data(data_dir: Path = C.DATA_DIR) -> pd.DataFrame:
    # Load the summary data and prep it for graphing.
    input_csv = data_dir / C.INPUT_CSV_NAME
    df = pd.read_csv(input_csv, skiprows=C.ALL_SHEET_HEADER_SIZE)

    # Convert numeric columns to integers. As above, you have to force it this way if the types vary.
    # Empty values or strings are converted to NaN
    df[C.SUMMARY_NUMERIC_COLS] = df[C.SUMMARY_NUMERIC_COLS].apply(
        pd.to_numeric, errors="coerce"
    )
    df[C.SUMMARY_NUMERIC_COLS] = df[C.SUMMARY_NUMERIC_COLS].astype(
        pd.Int64Dtype()
    )  # Keeps NaNs

    return df


def get_source_data_columns() -> list[str]:
    """Return the list of columns in the source data files."""
    return [
        C.DATA_COL[C.FILENAME],
        C.DATA_COL[C.SITE],
        C.DATA_COL[C.DATE_COL],
        C.DATA_COL[C.HOUR],
        *[C.DATA_COL[s] for s in C.ALL_SONGS],
        *[C.DATA_COL[t] for t in C.ALL_TAGS],
        C.DATETIME_COL,
    ]


@lru_cache(maxsize=8)
def load_year_data_cached(year: str, data_dir_text: str) -> pd.DataFrame:
    """Load one year of source recording data.

    The cache avoids rereading data YYYY.parquet once for every site.
    """
    data_dir = Path(data_dir_text)
    parquet_path = data_dir / f"data {year}.parquet"

    if not parquet_path.exists():
        raise FileNotFoundError(f"Yearly data file not found: {parquet_path}")

    usecols = get_source_data_columns()
    return pd.read_parquet(parquet_path, columns=usecols)


def load_site_data(site: str, data_dir: Path) -> pd.DataFrame:
    """
    Given a site, retrieve the data set for that

    :param site: Description
    :type site: str
    """
    year = site[0:4]

    year_df = load_year_data_cached(
        year=year,
        data_dir_text=str(data_dir.resolve()),
    )
    # Important: use a copy so downstream filtering/mutation does not alter
    # the cached year-level dataframe.
    site_df = year_df[year_df[C.SITE] == site].copy()

    if site_df.empty:
        return site_df

    if C.DATETIME_COL not in site_df.columns:
        raise ValueError(
            f"Expected column {C.DATETIME_COL!r} in source data for site {site!r}."
        )

    site_df[C.DATETIME_COL] = pd.to_datetime(site_df[C.DATETIME_COL]).dt.normalize()
    site_df = site_df.set_index(C.DATETIME_COL)
    site_df.index.name = C.DATE_COL

    site_df = clean_data(site_df, [site])

    return site_df.copy()


#
#
# PMJ Data loading functions. The PMJ data is stored in a partitioned Parquet dataset,
# with one partition per site and call type. The following functions provide a convenient
# interface for loading subsets of the PMJ data.
#
#


def get_pmj_columns() -> list[str]:
    """Return the list of columns in the PMJ data files."""
    return [
        C.SITE_COLS[C.SITE],
        C.SITE_COLS["year"],
        C.SITE_COLS["month"],
        C.SITE_COLS["day"],
        C.SITE_COLS[C.HOUR],
        C.SITE_COLS[C.VALIDATED_STR],
    ]


def _load_pm_data_uncached(site: str, data_dir: Path = C.DATA_DIR) -> pd.DataFrame:
    """Load PMJ detections for one site from the partitioned Parquet dataset.

    The Parquet dataset is partitioned by site and call_type. This function reads
    all requested PMJ call types for the site in one Parquet query, then performs
    the same shaping expected by downstream graph code.
    """
    pmj_dir = data_dir / C.PMJ_DIR_NAME

    if not pmj_dir.exists():
        return empty_pm_data_frame()

    usecols = get_pmj_columns()
    out_cols = [*usecols, C.DATE_COL, "type"]

    # "site" is a partition column and is added manually below. "call_type" is
    # needed so we can create the legacy "type" column.
    read_cols = [col for col in usecols if col not in {"site", C.SITE}]
    read_cols.append("call_type")
    read_cols = list(dict.fromkeys(read_cols))

    df = pd.read_parquet(
        pmj_dir,
        columns=read_cols,
        filters=[("site", "==", site)],
    )

    if df.empty:
        return empty_pm_data_frame()

    if "call_type" not in df.columns:
        raise ValueError(
            f"Expected PMJ partition column 'call_type' for site={site!r}."
        )

    df = df[df["call_type"].isin(C.PM_FILE_TYPES)].copy()

    if df.empty:
        return empty_pm_data_frame()

    # Preserve the legacy shape expected by downstream code.
    if "site" in usecols:
        df["site"] = site

    missing = set(usecols) - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing columns in PMJ Parquet subset for site={site!r}: "
            f"{sorted(missing)}"
        )

    df[C.DATE_COL] = pd.to_datetime(
        df[
            [
                C.SITE_COLS["year"],
                C.SITE_COLS["month"],
                C.SITE_COLS["day"],
            ]
        ],
        errors="coerce",
    )

    df = df[df[C.DATE_COL].notna()].copy()

    if df.empty:
        return empty_pm_data_frame()

    df["type"] = df["call_type"]

    # Keep this for now to preserve old downstream behavior. We can test removing
    # it later as a separate optimization.
    df = df[out_cols]

    df[C.DATE_COL] = pd.to_datetime(df[C.DATE_COL], errors="coerce")
    df = df[df[C.DATE_COL].notna()].copy()

    if df.empty:
        return empty_pm_data_frame()

    df.set_index(C.DATE_COL, inplace=True)

    # TODO: This still assumes the PMJ site name matches the summary site name.
    # Merged sites may need explicit alias handling later.
    df = clean_data(df, [site])

    return df


def load_pm_data(site: str, data_dir: Path = C.DATA_DIR) -> pd.DataFrame:
    """Load PMJ detections for one site from the partitioned Parquet dataset."""
    return _load_pm_data_uncached(site=site, data_dir=data_dir)
