
from typing import Any

import pandas as pd

from internal import trbl_summarizer as legacy  # noqa: E402


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

