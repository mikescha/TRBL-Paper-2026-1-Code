from __future__ import annotations

import pandas as pd
import pytest

from trbl_figures import constants as C
from trbl_figures.metadata import coerce_date_or_none, get_publication_date_range


def test_coerce_date_or_none_handles_blank_values() -> None:
    assert coerce_date_or_none(None) is None
    assert coerce_date_or_none("") is None
    assert coerce_date_or_none("   ") is None
    assert coerce_date_or_none(pd.NA) is None


def test_coerce_date_or_none_normalizes_real_dates() -> None:
    result = coerce_date_or_none("2021-05-17 13:45:00")

    assert result == pd.Timestamp("2021-05-17")


def test_get_publication_date_range_uses_all_csv_dates_by_default() -> None:
    site_summary_dict = {
        C.SUMMARY_FIRST_REC: "2021-03-01",
        C.SUMMARY_LAST_REC: "2021-07-15",
    }

    result = get_publication_date_range(site_summary_dict)

    assert result == {
        "start": pd.Timestamp("2021-03-01").date(),
        "end": pd.Timestamp("2021-07-15").date(),
    }


def test_get_publication_date_range_allows_manifest_overrides() -> None:
    site_summary_dict = {
        C.SUMMARY_FIRST_REC: "2021-03-01",
        C.SUMMARY_LAST_REC: "2021-07-15",
    }

    result = get_publication_date_range(
        site_summary_dict,
        start_date="2021-04-01",
        end_date="2021-06-30",
    )

    assert result == {
        "start": pd.Timestamp("2021-04-01").date(),
        "end": pd.Timestamp("2021-06-30").date(),
    }


def test_get_publication_date_range_rejects_start_after_end() -> None:
    site_summary_dict = {
        C.SUMMARY_FIRST_REC: "2021-03-01",
        C.SUMMARY_LAST_REC: "2021-07-15",
    }

    with pytest.raises(ValueError):
        get_publication_date_range(
            site_summary_dict,
            start_date="2021-08-01",
            end_date="2021-07-01",
        )
