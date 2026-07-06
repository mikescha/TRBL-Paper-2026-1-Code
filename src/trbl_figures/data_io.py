from __future__ import annotations

import pandas as pd

from internal import trbl_summarizer as legacy


def load_summary_data() -> pd.DataFrame:
    """Load All.csv summary/metadata using the legacy implementation."""
    return legacy.load_summary_data()


def load_site_data(site: str) -> pd.DataFrame:
    """Load source data for one site using the legacy implementation."""
    return legacy.load_data_for_site(site)


def load_pm_data(site: str) -> pd.DataFrame:
    """Load pattern-matching data for one site using the legacy implementation."""
    return legacy.load_pm_data(site)


def empty_pm_data_frame() -> pd.DataFrame:
    """Return an empty PM dataframe with expected legacy columns."""
    return legacy.empty_pm_data_frame()