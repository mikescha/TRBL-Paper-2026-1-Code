from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from trbl_figures import constants as C
from trbl_figures.date_utils import (
    convert_to_datetime,
    is_valid_date,
    is_valid_date_pair,
    is_valid_date_string,
)

logger = logging.getLogger(__name__)

PULSE_PHASES = {
    C.PHASE_MALE_CHORUS: [C.PULSE_MC_START, C.PULSE_INC_START],  # -1
    C.PHASE_INC: [C.PULSE_INC_START, C.PULSE_HATCH],  # -1
    C.PHASE_BROOD: [C.PULSE_HATCH, C.PULSE_FIRST_FLDG],  # -1
    C.PHASE_FLDG: [C.PULSE_FIRST_FLDG, C.PULSE_LAST_FLDG],
}


def get_val_from_df(df: pd.DataFrame, col) -> str:
    result = df.iloc[0, df.columns.get_loc(col)]
    return str(result)


def count_valid_pulses(pulse_data: dict) -> int:
    # A pulse is considered valid if there is at least one "graphable" date pair
    count = 0
    for p in C.PULSES:
        result = False
        for phase in pulse_data[p]:
            if phase in PULSE_PHASES and is_valid_date_pair(
                pulse_data[p][phase]
            ):  # Need to skip Abandoned, as it doesn't have a pair of dates
                result = True
                break
        count += 1 if result else 0

    return count


# TODO How much of this error checking is still needed?
def process_site_summary_data(summary_row: pd.DataFrame) -> dict:
    first_rec = get_val_from_df(summary_row, C.SUMMARY_FIRST_REC)
    last_rec = get_val_from_df(summary_row, C.SUMMARY_LAST_REC)

    if pd.isna(first_rec):
        raise ValueError("process_site_summary: date of first recording was empty")

    summary_dict = {
        C.SUMMARY_FIRST_REC: convert_to_datetime(first_rec),
        C.SUMMARY_LAST_REC: convert_to_datetime(last_rec),
    }

    VALID_DESCRIPTORS = [
        "inf",
        "before start, hbc present",
        "before start, hbc absent",
        C.CONTINUOUS,
        "missed",
    ]

    for pulse in C.PULSES:
        pulse_result = {}
        error_prefix = f"process_site: {summary_row.iloc[0]['Name']!s} at {pulse}"

        # Make our list of abandoned dates for later graphing purposes
        abandoned_date = convert_to_datetime(
            get_val_from_df(summary_row, f"{pulse}{C.ABANDONED}")
        )
        if is_valid_date(abandoned_date):
            pulse_result[C.ABANDONED] = abandoned_date

        check_for_continuous = False  # flag to track if we see "continuous" in either date for this pulse, so we can check for errors
        for phase, (start, end) in PULSE_PHASES.items():
            target1 = f"{pulse}{start}"
            value1 = get_val_from_df(summary_row, target1)
            result1 = pd.NaT

            target2 = f"{pulse}{end}"
            value2 = get_val_from_df(summary_row, target2)
            result2 = pd.NaT

            if is_valid_date_string(value1):
                # It's a good date, so format it
                result1 = convert_to_datetime(value1)

                if value2.lower() not in [
                    C.ND_STRING.lower(),
                    C.CONTINUOUS,
                ] and not is_valid_date(value2):
                    raise ValueError(
                        f"{error_prefix}: {target1} is a valid date {value1}, but {target2} is {value2} and not ND, Continuous, or a date"
                    )

            elif pd.notna(value1) and value1.startswith(C.ABANDONED):
                if not is_valid_date(abandoned_date):
                    raise ValueError(
                        f"{error_prefix}: Column Abandoned does not have a valid abandoned date"
                    )
                else:
                    result1 = pd.NaT
            # Check: if the phase = brooding and it is one of the strings that indicated the process started before
            # the date of the first recording, then we want to draw a left-pointing arrow on the graph. So, if we find this,
            #  save it with a signal we can pass along to the graph maker (signal=Wendy's bday)
            elif value1.lower() in VALID_DESCRIPTORS:
                if value1.lower() != C.CONTINUOUS:
                    result1 = convert_to_datetime("6/1/1967")
                else:
                    result1 = C.CONTINUOUS
                    if not check_for_continuous:
                        raise ValueError(
                            f"{error_prefix}: Found 'continuous' in {pulse} without it in the prior pulse"
                        )
                        check_for_continuous = False  # reset the flag for the next phase, as continuous should only be valid for one phase per pulse
            elif value1 == C.ND_STRING:
                # this is OK, we aren't going to draw anything in this case
                pass
            else:
                # if not one of the above, then it's an error
                raise ValueError(
                    f"{error_prefix}: Found invalid data in {target1}: {value1}"
                )

            if is_valid_date_string(value2):
                if value1.lower() not in [
                    "inf",
                    C.CONTINUOUS,
                    C.MISSED,
                    C.ND_STRING.lower(),
                ] and not is_valid_date_string(value1):
                    logger.warning(
                        f"{target2} is a valid date, but {target1} is '{value1}' not ND, inf, continuous, or a valid date"
                    )
                # It's a good date, so format it
                if phase == C.PHASE_FLDG:
                    # For fledgling phase, don't subtract one from the end date
                    delta = pd.Timedelta(days=0)
                else:
                    delta = pd.Timedelta(days=1)
                result2 = convert_to_datetime(value2) - delta
            elif pd.notna(value2) and value2.startswith(C.ABANDONED):
                if not is_valid_date(abandoned_date):
                    raise ValueError(
                        f"{error_prefix}: Column Abandoned does not have a valid abandoned date"
                    )
                else:
                    result2 = abandoned_date - pd.Timedelta(days=1)
            elif value2.lower() in VALID_DESCRIPTORS:
                if value2.lower() == C.CONTINUOUS:
                    result2 = C.CONTINUOUS
                    check_for_continuous = True  # set the flag so we can check that the next phase doesn't also have continuous, which would be an error
                elif (
                    value2.lower() == "inf" and value1.lower() not in VALID_DESCRIPTORS
                ):
                    logger.warning(
                        f"{error_prefix}: In {target2} end date is 'inf' but start date is not 'inf'"
                    )
            elif value2 == C.ND_STRING:
                # TODO: This typically isn't an error case, need to figure out if there are any cases where it isn't
                pass
            else:
                raise ValueError(
                    f"{error_prefix}: Found {value2} in {target2}, which is invalid data"
                )

            pulse_result[phase] = {"start": result1, "end": result2}

        # Add the sets of dates to our master dictionary
        summary_dict[pulse] = pulse_result

    # Calculate count of valid pulses. If there were zero, then set the count to 1 else we won't get a graph
    p_count = max(1, count_valid_pulses(summary_dict))
    summary_dict[C.PULSE_COUNT] = p_count

    return summary_dict


def get_site_summary_dict(site: str, summary_df: pd.DataFrame) -> dict:
    """Return the processed All.csv summary dictionary for one site."""
    summary_row = summary_df[summary_df.iloc[:, 1] == site]

    if summary_row.empty:
        raise ValueError(f"Site {site!r} was not found in All.csv.")

    return process_site_summary_data(summary_row)


def build_key_dates(site_summary_dict: dict) -> dict:
    """Build the key-date dictionary expected by create_graph."""
    key_dates: dict[str, Any] = {}

    key_dates[C.SUMMARY_FIRST_REC] = site_summary_dict[C.SUMMARY_FIRST_REC]
    key_dates[C.SUMMARY_LAST_REC] = site_summary_dict[C.SUMMARY_LAST_REC]

    for pulse in C.PULSES:
        if pulse not in site_summary_dict:
            continue

        key_dates[pulse] = {}

        mc_date = site_summary_dict[pulse][C.PHASE_MALE_CHORUS]["start"]
        inc_date = site_summary_dict[pulse][C.PHASE_INC]["start"]
        hatch_date = site_summary_dict[pulse][C.PHASE_BROOD]["start"]
        fledge_start_date = site_summary_dict[pulse][C.PHASE_FLDG]["start"]
        dispersal = site_summary_dict[pulse][C.PHASE_FLDG]["end"]

        if "abandon" in site_summary_dict[pulse]:
            key_dates[pulse][C.ABANDONED] = site_summary_dict[pulse]["abandon"]

        if pd.notna(mc_date):
            key_dates[pulse][C.PULSE_MC_START] = mc_date

        if pd.notna(inc_date):
            key_dates[pulse][C.PULSE_INC_START] = inc_date

        if pd.notna(hatch_date):
            key_dates[pulse][C.PULSE_HATCH] = hatch_date

        if pd.notna(fledge_start_date):
            key_dates[pulse][C.PULSE_FIRST_FLDG] = fledge_start_date

        if pd.notna(dispersal):
            key_dates[pulse][C.PULSE_LAST_FLDG] = dispersal

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

    Defaults to All.csv first/last recording dates to avoid
    field-note/manual recordings extending the plotted range.
    """

    all_csv_start = coerce_date_or_none(site_summary_dict[C.SUMMARY_FIRST_REC])
    all_csv_end = coerce_date_or_none(site_summary_dict[C.SUMMARY_LAST_REC])

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
