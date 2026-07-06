from __future__ import annotations

import pandas as pd

from internal import trbl_summarizer as legacy
from trbl_figures import constants as C


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


def filter_to_core_hours(df: pd.DataFrame, hour_col: str) -> pd.DataFrame:
    return legacy.filter_to_core_hours(df, hour_col=hour_col)


def get_missing_days(df: pd.DataFrame, date_range_dict: dict) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(legacy.get_missing_days(df, date_range_dict))


def do_pattern_matching(site: str, date_range_dict: dict) -> tuple[pd.DataFrame, bool]:
    return legacy.do_pattern_matching(site, date_range_dict)


def do_mini_manual(df_core: pd.DataFrame, date_range_dict: dict):
    return legacy.do_mini_manual(df_core, date_range_dict)


def do_manual(df_core: pd.DataFrame, date_range_dict: dict):
    return legacy.do_manual(df_core, date_range_dict)


def do_edge(df_core: pd.DataFrame, date_range_dict: dict, site: str):
    return legacy.do_edge(df_core, date_range_dict, site)


def get_recs_per_edge_day(df_core: pd.DataFrame, date_range_dict: dict) -> pd.Series:
    return legacy.get_recs_per_edge_day(df_core, date_range_dict)