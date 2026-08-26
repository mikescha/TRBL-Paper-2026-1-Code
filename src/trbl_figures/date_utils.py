from __future__ import annotations

import pandas as pd

from trbl_figures import constants as C

DATE_FORMAT = "%m/%d/%Y"


def is_valid_date(timestamp):
    return pd.notna(timestamp)


def is_valid_date_string(date_string):
    potential_date = date_string
    if type(date_string) is str:
        # Strip leading '~' and trailing '*' markers around dates
        # e.g. "~8/24/2024" -> "8/24/2024", "7/14/2024*" -> "7/14/2024"
        potential_date = potential_date.lstrip("~").rstrip("*").strip()

    result = pd.to_datetime(potential_date, format=DATE_FORMAT, errors="coerce")
    return not pd.isna(result)


def is_valid_date_pair(phase_data: dict) -> bool:
    result = False
    start = phase_data[C.START]
    end = phase_data[C.END]
    if is_valid_date(start) and is_valid_date(end):
        result = True
    return result


def convert_to_datetime(date_string):
    potential_date = date_string
    if type(date_string) is str:
        # Strip leading '~' and trailing '*' markers around dates
        # e.g. "~8/24/2024" -> "8/24/2024", "7/14/2024*" -> "7/14/2024"
        potential_date = potential_date.lstrip("~").rstrip("*").strip()

    ts = pd.to_datetime(potential_date, format=DATE_FORMAT, errors="coerce")
    return ts
