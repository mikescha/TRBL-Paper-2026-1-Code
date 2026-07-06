from __future__ import annotations

from typing import Any

import pandas as pd

from internal import trbl_summarizer as legacy


def get_site_summary_dict(site: str, summary_df: pd.DataFrame) -> dict:
    """Return the processed All.csv summary dictionary for one site."""
    summary_row = summary_df[summary_df.iloc[:, 1] == site]

    if summary_row.empty:
        raise ValueError(f"Site {site!r} was not found in All.csv.")

    return legacy.process_site_summary_data(summary_row)


def build_key_dates(site_summary_dict: dict) -> dict:
    """Build the key-date dictionary expected by legacy.create_graph."""
    key_dates: dict[str, Any] = {}

    key_dates[legacy.SUMMARY_FIRST_REC] = site_summary_dict[legacy.SUMMARY_FIRST_REC]
    key_dates[legacy.SUMMARY_LAST_REC] = site_summary_dict[legacy.SUMMARY_LAST_REC]

    for pulse in legacy.PULSES:
        if pulse not in site_summary_dict:
            continue

        key_dates[pulse] = {}

        mc_date = site_summary_dict[pulse][legacy.PHASE_MALE_CHORUS]["start"]
        inc_date = site_summary_dict[pulse][legacy.PHASE_INC]["start"]
        hatch_date = site_summary_dict[pulse][legacy.PHASE_BROOD]["start"]
        fledge_start_date = site_summary_dict[pulse][legacy.PHASE_FLDG]["start"]
        dispersal = site_summary_dict[pulse][legacy.PHASE_FLDG]["end"]

        if "abandon" in site_summary_dict[pulse]:
            key_dates[pulse][legacy.ABANDONED] = site_summary_dict[pulse]["abandon"]

        if pd.notna(mc_date):
            key_dates[pulse][legacy.PULSE_MC_START] = mc_date

        if pd.notna(inc_date):
            key_dates[pulse][legacy.PULSE_INC_START] = inc_date

        if pd.notna(hatch_date):
            key_dates[pulse][legacy.PULSE_HATCH] = hatch_date

        if pd.notna(fledge_start_date):
            key_dates[pulse][legacy.PULSE_FIRST_FLDG] = fledge_start_date

        if pd.notna(dispersal):
            key_dates[pulse][legacy.PULSE_LAST_FLDG] = dispersal

    return key_dates



def coerce_date_or_none(value: Any) -> pd.Timestamp | None:
    """Convert a date-like value to a normalized Timestamp, or None."""
    if value is None or pd.isna(value) or str(value).strip() == "":
        return None

    return pd.to_datetime(value).normalize()


def get_publication_date_range(
    site_summary_dict: dict,
    *,
    start_date: Any = None,
    end_date: Any = None,
) -> dict:
    """
    Return the publication graph date range.

    Defaults to All.csv first/last recording dates to preserve legacy graphing behavior and avoid
    field-note/manual recordings extending the plotted range.
    """
    all_csv_start = coerce_date_or_none(site_summary_dict[legacy.SUMMARY_FIRST_REC])
    all_csv_end = coerce_date_or_none(site_summary_dict[legacy.SUMMARY_LAST_REC])

    start = coerce_date_or_none(start_date) or all_csv_start
    end = coerce_date_or_none(end_date) or all_csv_end

    if start is None or end is None:
        raise ValueError(
            "Could not determine publication date range from All.csv "
            f"values: start={all_csv_start!r}, end={all_csv_end!r}"
        )

    if start > end:
        raise ValueError(f"Start date {start.date()} is after end date {end.date()}.")

    return {
        "start": start.date(),
        "end": end.date(),
    }

