from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from trbl_figures import constants as C
from trbl_figures.data_io import load_pm_data

logger = logging.getLogger(__name__)

def normalize_pt(pt: pd.DataFrame, date_range_dict: dict) -> pd.DataFrame:
    date_range = pd.date_range(date_range_dict[C.START], date_range_dict[C.END])
    temp = pt.reindex(date_range)  # .fillna(0)
    temp = temp.transpose()
    temp = temp.astype(float)  # convert all numeric data to floats

    return temp


def filter_df_by_tags(
    df: pd.DataFrame,
    target_tags: list[str],
    filter_str: str = ">0",
    exclude_tags: list[str] | None = None,
) -> pd.DataFrame:
    missing = set(target_tags) - set(df.columns)
    if missing:
        # if the tags aren't there, then just return the whole thing?
        return df
    else:
        exclude_tags = exclude_tags or []

        op_token = filter_str[:2] if filter_str[:2] in C._OPS else filter_str[:1]
        val_token = filter_str[len(op_token) :]
        threshold = float(val_token)
        cmp = C._OPS[op_token]
    
        target_mask = cmp(df[target_tags], threshold).any(axis=1)

        if exclude_tags:
            exclude_mask = cmp(df[exclude_tags], threshold).any(axis=1)
            target_mask &= ~exclude_mask

        return df.loc[target_mask]



def make_pivot_table(
    df, date_range_dict, preserve_edges=False, labels=None, label_dict=None
):
    labels = labels or []
    label_dict = label_dict or {}
    if df.empty:
        return pd.DataFrame()

    if (set(label_dict.keys()) | set(label_dict.values())) - set(df.columns):
        # some columns are missing, so get out
        return pd.DataFrame()

    date_colname = C.DATA_COL[C.DATE_COL]

    if label_dict:
        out = {}
        for tag_col, value_col in label_dict.items():
            # rows where this tag is present
            m = df[tag_col].gt(0)  # same as >0
            if not m.any():
                continue
            # count occurrences where value_col >= 1
            ser = df.loc[m, value_col].ge(1)
            if df.index.name == date_colname:
                s = ser.groupby(level=date_colname).sum()
            else:
                s = ser.groupby(df.loc[m, date_colname]).sum()

            out[tag_col] = s

        aggregate_df = pd.DataFrame(out).fillna(0).astype(int)

    else:
        if not labels:
            return pd.DataFrame()
        date_colname = C.DATA_COL[C.DATE_COL]
        if df.index.name == date_colname:
            aggregate_df = df[labels].ge(1).groupby(level=date_colname).sum()
        else:
            aggregate_df = df[labels].ge(1).groupby(df[date_colname]).sum()

    if preserve_edges:
        aggregate_df = aggregate_df.replace(0, C.PRESERVE_EDGES_FLAG)

    return normalize_pt(aggregate_df, date_range_dict)


def add_core_hour_column(
    df: pd.DataFrame,
    hour_col: str = "hour",
    output_col: str = "core_hour",
) -> pd.DataFrame:
    """
    Add an integer hour column from a string-like hour column.

    Handles common formats:
      - "07:00:00"
      - "7:00:00"
      - "11:20"
      - "11"
      - pandas/Excel-ish datetime strings, if needed

    Returns a copy and leaves the original dataframe unchanged.
    """
    out = df.copy()

    hour_str = out[hour_col].astype(str).str.strip()

    # Preferred: extract a leading 1- or 2-digit hour.
    # Examples:
    # "07:20:00" -> 7
    # "7:20:00"  -> 7
    # "19:00:00" -> 19
    leading_hour = hour_str.str.extract(r"^(\d{1,2})(?::|$)", expand=False)

    out[output_col] = pd.to_numeric(leading_hour, errors="coerce").astype("Int64")

    # Fallback for values that do not start with HH or HH:MM, e.g. full datetime strings.
    missing = out[output_col].isna()
    if missing.any():
        parsed = pd.to_datetime(out.loc[missing, hour_col], errors="coerce")
        out.loc[missing, output_col] = parsed.dt.hour.astype("Int64")

    return out


def get_pmj_detection_hours(df: pd.DataFrame) -> pd.Series:
    df_present_only = df[df["validated"] == "present"]
    df_valid_hours_only = df_present_only[
        (df_present_only["hour"] >= C.CORE_START_HOUR)
        & (df_present_only["hour"] < C.CORE_END_HOUR_EXCLUSIVE)
    ]
    df_detection_hours = df_valid_hours_only.groupby(C.DATE_COL)["hour"].nunique()
    return df_detection_hours



# Take all the PMJ data for a type of call and generate a pivot table that has the count of "detection hours" for each day during
# "core hours" of 7a up to 8p. A detection hour is an hour in which there was a validated recording of the call, and we only
# count one per hour to avoid biasing the data by long recording sessions.
def make_pattern_match_pt(
    df: pd.DataFrame, type_name: str, date_range_dict: dict
) -> pd.DataFrame:

    # Filter it to be just the core hours, and then only 1 recording per hour
    detection_hours = get_pmj_detection_hours(df)
    aggregate = detection_hours.to_frame(name=type_name)

    # If the pivot table is empty, ensure all dates exist with value 0
    if aggregate.empty:
        all_dates = df.index.unique()  # Get all dates from original df
        aggregate = pd.DataFrame(
            np.nan, index=all_dates, columns=[type_name]
        )  # Fill with zeros
        aggregate.index.name = C.DATE_COL  # Set the index name properly

    return normalize_pt(aggregate, date_range_dict)


def filter_to_core_hours(
    df: pd.DataFrame, hour_col: str = "hour",
    core_start: int = C.CORE_START_HOUR,
    core_end_exclusive: int = C.CORE_END_HOUR_EXCLUSIVE,
) -> pd.DataFrame:
    """
    Only analyze recordings made during core hours: 07:00 <= hour < 20:00.
    """
    out = add_core_hour_column(df, hour_col=hour_col)

    mask = out["core_hour"].between(core_start, core_end_exclusive - 1)

    return out.loc[mask].copy()


def get_missing_days(df_site: pd.DataFrame, date_range_dict: dict) -> pd.DatetimeIndex:
    # returns the set of days between start and end that don't have any recordings, 
    # i.e. are missing from the dataset
    df_temp = df_site.copy()
    df_temp.index = pd.to_datetime(df_temp.index)
    start = date_range_dict[C.START]
    end = date_range_dict[C.END]
    all_days = pd.date_range(start, end, freq="D")
    idx = pd.DatetimeIndex(df_temp.index).normalize().unique()
    missing_days = all_days.difference(idx)
    return missing_days


def do_pattern_matching(site: str, date_range_dict: dict) -> tuple[pd.DataFrame, bool]:
    # Load all the PM files, any errors will return an empty table. For later graphing purposes,
    global align_dates

    df_pattern_match = load_pm_data(site)

    pt_pm = pd.DataFrame()
    pm_date_range_dict = date_range_dict

    if not df_pattern_match.empty:
        if len(df_pattern_match):
            for t in C.PM_FILE_TYPES:
                # For each file type, get the filtered range of just that type
                df_for_file_type = df_pattern_match[df_pattern_match["type"] == t]

                # Build the pivot table for it
                pt_for_file_type = make_pattern_match_pt(
                    df_for_file_type, t, pm_date_range_dict
                )
                # Concat as above
                pt_pm = pd.concat([pt_pm, pt_for_file_type])

    else:
        logger.warning("{site}: All pattern matching data not available")

    return pt_pm, not df_pattern_match.empty


def do_mini_manual(df_site: pd.DataFrame, date_range_dict: dict):
    # 1. Select all rows with one of the following tags:
    #       tag<reviewed-MH-h>, tag<reviewed-MH-m>, tag<reviewed-WS-h>, tag<reviewed-WS-m>
    # 2. Make a pivot table as above
    #
    df_mini_manual = filter_df_by_tags(df_site, C.MINI_MANUAL_COLS)
    pt_mini_manual = make_pivot_table(df_mini_manual, date_range_dict, labels=C.SONG_COLS)
    return pt_mini_manual, not df_mini_manual.empty


def do_manual(df_site: pd.DataFrame, date_range_dict: dict):
    # MANUAL ANALYSIS
    #   1. Select all rows where one of the following tags
    #       tag<reviewed-MH>, tag<reviewed-WS>, tag<reviewed>
    #   2. Make a pivot table with the following columns:
    #       The number of recordings from that set that have Common Song >= 1
    #       The number of recordings from that set that have Courtship Song >= 1
    #       The number of recordings from that set that have AltSong2 >= 1
    #       The number of recordings from that set that have AltSong >= 1
    #
    df_manual = filter_df_by_tags(df_site, C.MANUAL_COLS)
    pt_manual = make_pivot_table(df_manual, date_range_dict, labels=C.SONG_COLS)
    return pt_manual, not df_manual.empty


#TODO fix this so it doesn't modify the original dataframe but returns a new one
def fix_bad_values(df: pd.DataFrame):
    """
    This function finds columns containing "---", prints a warning message,
    and replaces all "---" with 0 in-place within the DataFrame. Note that the way python works,
    I'm actually modifying the original!
    """
    for col in df.columns:
        if col.startswith("tag") and -100 in df[col].values:
            df[col] = df[col].replace(-100, 0)


#TODO is there any error checking we can do on the tags? If so, put it here
def check_edge_cols_for_errors(df: pd.DataFrame, tag_map: dict) -> bool:
    error_found = False
    # Look for -100s
    df_edge_cols = filter_df_by_tags(df, list(tag_map.keys()))
    df_bad_values = df_edge_cols[df_edge_cols.isin([-100]).any(axis=1)]
    if len(df_bad_values) > 0:
        error_found = True
    # Remove any -100 (were "---" in the original file, converted to numbers in the first cleaning pass) and log it, if there are any
    fix_bad_values(df)

    return error_found


def do_edge(df_site: pd.DataFrame, date_range_dict: dict, site: str):
    pt_edge = pd.DataFrame()
    have_edge_data = False

    check_edge_cols_for_errors(df_site, C.TAG_MAP)

    for tag in C.TAG_MAP:
        df_for_tag = filter_df_by_tags(df_site, [tag])
        have_edge_data = have_edge_data or len(df_for_tag) > 0
        pt_for_tag = make_pivot_table(
            df_for_tag,
            date_range_dict,
            preserve_edges=True,
            label_dict={tag: C.TAG_MAP[tag]},
        )
        pt_edge = pd.concat([pt_edge, pt_for_tag])

    return pt_edge, have_edge_data



def get_recs_per_edge_day(df_site: pd.DataFrame, date_range_dict: dict) -> pd.Series:
    # Get the number of recordings per day for the edge data, this is used for normalizing the data by the number of recordings made
    df_edge_recs = filter_df_by_tags(df_site, list(C.TAG_MAP.keys()))
    unique_hours_per_day = df_edge_recs.groupby(level=C.DATE_COL)["core_hour"].nunique()

    start_date = pd.to_datetime(date_range_dict["start"])
    end_date = pd.to_datetime(date_range_dict["end"])
    filtered_to_date_range = unique_hours_per_day[
        (unique_hours_per_day.index >= start_date)
        & (unique_hours_per_day.index <= end_date)
    ]
    return filtered_to_date_range
