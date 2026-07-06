
from pathlib import Path
from typing import Any

import pandas as pd

from internal import trbl_summarizer as legacy  # noqa: E402
from trbl_figures.date_ranges import get_publication_date_range
from trbl_figures.manifest import filter_manifest, read_manifest

DEFAULT_INVENTORY_NAME = "figure_inventory.csv"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def configure_legacy_paths(data_dir: Path, output_dir: Path) -> None:
    """Point the legacy module at publication repo paths."""
    data_dir = data_dir.resolve()
    output_dir = output_dir.resolve()

    output_dir.mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "outputs").mkdir(parents=True, exist_ok=True)

    legacy.BEING_DEPLOYED_TO_STREAMLIT = False

    # These names existed in the uploaded version. If your local version renamed one,
    # the first run will tell us exactly where to patch.
    legacy.make_all_graphs = True
    legacy.align_dates = False

    legacy.DATA_DIR = data_dir
    legacy.INPUT_CSV = data_dir / "TRBL Analysis tracking - All.csv"
    legacy.PMJ_DIR = data_dir / "pmj_data"

    legacy.FIGURE_DIR = output_dir
    legacy.ERROR_FILE = PROJECT_ROOT / "outputs" / "grapher_errors.txt"


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


def save_component(site: str, graph_type: str, fig: Any) -> None:
    """Save one graph component using the legacy save function."""
    legacy.save_figure(
        site=site,
        graph_type=graph_type,
        graph=fig,
        make_all_graphs=True,
        do_aligned_dates=False,
    )


def get_site_summary_dict(site: str, summary_df: pd.DataFrame) -> dict:
    """Return the processed All.csv summary dictionary for one site."""
    summary_row = summary_df[summary_df.iloc[:, 1] == site]

    if summary_row.empty:
        raise ValueError(f"Site {site!r} was not found in All.csv.")

    return legacy.process_site_summary_data(summary_row)


def should_build_panel(row: pd.Series, panel_name: str) -> bool:
    """Return whether a panel should be attempted for this manifest row."""
    return bool(row["all_available_panels"] or row[panel_name])


def build_pattern_matching_panel(
    site: str,
    date_range_dict: dict,
    key_dates: dict,
    missing_days: pd.DatetimeIndex,
    rec_norm: pd.Series,
) -> tuple[str, Any | None]:
    """Build and save the pattern-matching panel if data exists."""
    pt_pm, have_pm_data = legacy.do_pattern_matching(
        site=site,
        date_range_dict=date_range_dict
    )

    if not have_pm_data or pt_pm.empty:
        return "no_data", None

    fig = legacy.create_graph(
        site=site,
        df=pt_pm,
        row_names=legacy.PM_FILE_TYPES,
        cmap=legacy.CMAP_PM,
        title=legacy.GRAPH_PM,
        graph_type=legacy.GRAPH_PM,
        key_dates=key_dates,
        missing_days=missing_days,
        denom_by_day=rec_norm,
        do_aligned_dates=False,
    )

    save_component(site, legacy.GRAPH_PM, fig)

    return "generated", pt_pm


def build_mini_manual_panel(
    site: str,
    df_core: pd.DataFrame,
    df_site: pd.DataFrame,
    date_range_dict: dict,
    key_dates: dict,
    missing_days: pd.DatetimeIndex,
) -> tuple[str, Any | None]:
    """Build and save the mini-manual panel if data exists."""
    pt_mini_manual, have_mini_manual_data = legacy.do_mini_manual(
        df_core,
        date_range_dict,
    )

    if not have_mini_manual_data or pt_mini_manual.empty:
        return "no_data", None

    fig = legacy.create_graph(
        site=site,
        df=pt_mini_manual,
        row_names=legacy.SONG_COLS,
        cmap=legacy.CMAP,
        raw_data=df_site,
        draw_vert_rects=True,
        title="Manual Analysis (Periodic)",
        graph_type=legacy.GRAPH_MINIMAN,
        key_dates=key_dates,
        missing_days=missing_days,
    )

    save_component(site, legacy.GRAPH_MINIMAN, fig)

    return "generated", pt_mini_manual


def build_manual_panel(
    site: str,
    df_core: pd.DataFrame,
    date_range_dict: dict,
    key_dates: dict,
    missing_days: pd.DatetimeIndex,
    rec_norm: pd.Series,
) -> tuple[str, Any | None]:
    """Build and save the manual daily-review panel if data exists."""
    pt_manual, have_manual_data = legacy.do_manual(df_core, date_range_dict)

    if not have_manual_data or pt_manual.empty:
        return "no_data", None

    manual_rows = [
        legacy.data_col[legacy.MALE_SONG],
        legacy.data_col[legacy.ALTSONG2],
        legacy.data_col[legacy.ALTSONG1],
    ]

    fig = legacy.create_graph(
        site=site,
        df=pt_manual,
        row_names=manual_rows,
        cmap=legacy.CMAP,
        title="Manual Analysis (Daily Review)",
        graph_type=legacy.GRAPH_MANUAL,
        key_dates=key_dates,
        missing_days=missing_days,
        denom_by_day=rec_norm,
    )

    save_component(site, legacy.GRAPH_MANUAL, fig)

    return "generated", pt_manual


def build_edge_panel(
    site: str,
    df_core: pd.DataFrame,
    df_site: pd.DataFrame,
    date_range_dict: dict,
    key_dates: dict,
    missing_days: pd.DatetimeIndex,
) -> tuple[str, Any | None]:
    """Build and save the Edge/hatchling panel if data exists."""
    pt_edge, have_edge_data = legacy.do_edge(df_core, date_range_dict, site)
    edge_recs_per_day = legacy.get_recs_per_edge_day(df_core, date_range_dict)

    if not have_edge_data or pt_edge.empty:
        return "no_data", None

    cmap_edge = {name: "Blues" for name in legacy.EDGE_COLS}

    fig = legacy.create_graph(
        site=site,
        df=pt_edge,
        row_names=pt_edge.index.to_list(),
        cmap=cmap_edge,
        raw_data=df_site,
        draw_horiz_rects=True,
        title="Manual Analysis (Hatchlings Only)",
        graph_type=legacy.GRAPH_EDGE,
        key_dates=key_dates,
        missing_days=missing_days,
        denom_by_day=edge_recs_per_day,
    )

    save_component(site, legacy.GRAPH_EDGE, fig)

    return "generated", pt_edge


def build_one_site(site: str, row: pd.Series, summary_df: pd.DataFrame) -> dict:
    """Generate requested figure panels and composite for one site."""
    status = {
        "site_id": row.get("site_id", ""),
        "site_name": site,
        "manual": "not_requested",
        "mini_manual": "not_requested",
        "edge": "not_requested",
        "pattern_matching": "not_requested",
        "composite": "not_requested",
        "error": "",
    }

    df_site = legacy.load_data_for_site(site)

    if df_site.empty:
        status["error"] = "No source data found for site"
        return status

    df_core = legacy.filter_to_core_hours(df_site, hour_col=legacy.HOUR)

    rec_norm = df_core.groupby(level=legacy.DATE_COL)["core_hour"].nunique()

    site_summary_dict = get_site_summary_dict(site, summary_df)

    date_range_dict = get_publication_date_range(
        site_summary_dict=site_summary_dict,
    )

    missing_days: pd.DatetimeIndex = pd.DatetimeIndex(
        legacy.get_missing_days(df_core, date_range_dict)
    )

    key_dates = build_key_dates(site_summary_dict)

    month_locs = {}

    if should_build_panel(row, "pattern_matching"):
        panel_status, pt = build_pattern_matching_panel(
            site=site,
            date_range_dict=date_range_dict,
            key_dates=key_dates,
            missing_days=missing_days,
            rec_norm=rec_norm,
        )
        status["pattern_matching"] = panel_status

        if pt is not None and not month_locs:
            month_locs = legacy.get_month_locs(pt.columns)

    if should_build_panel(row, "mini_manual"):
        panel_status, pt = build_mini_manual_panel(
            site=site,
            df_core=df_core,
            df_site=df_site,
            date_range_dict=date_range_dict,
            key_dates=key_dates,
            missing_days=missing_days,
        )
        status["mini_manual"] = panel_status

        if pt is not None and not month_locs:
            month_locs = legacy.get_month_locs(pt.columns)

    if should_build_panel(row, "manual"):
        panel_status, pt = build_manual_panel(
            site=site,
            df_core=df_core,
            date_range_dict=date_range_dict,
            key_dates=key_dates,
            missing_days=missing_days,
            rec_norm=rec_norm,
        )
        status["manual"] = panel_status

        if pt is not None and not month_locs:
            month_locs = legacy.get_month_locs(pt.columns)

    if should_build_panel(row, "edge"):
        panel_status, pt = build_edge_panel(
            site=site,
            df_core=df_core,
            df_site=df_site,
            date_range_dict=date_range_dict,
            key_dates=key_dates,
            missing_days=missing_days,
        )
        status["edge"] = panel_status

        if pt is not None and not month_locs:
            month_locs = legacy.get_month_locs(pt.columns)

    if row["include_composite"]:
        if month_locs:
            if row["include_key"]:
                legacy.draw_legend(
                    legacy.CMAP,
                    make_all_graphs=True,
                    save_files=True,
                )

            legacy.combine_unaligned_images(
                site=site,
                month_locs=month_locs,
                include_weather=False,
                align_dates=False,
            )

            status["composite"] = "generated"
        else:
            status["composite"] = "no_data"

    return status


def build_figures(
    manifest_path: Path,
    data_dir: Path,
    output_dir: Path,
    only_sites: list[str] | None = None,
    limit: int | None = None,
    dry_run: bool = False,
    stop_on_error: bool = False,
) -> pd.DataFrame:
    """Main workflow used by the command-line runner."""
    configure_legacy_paths(data_dir=data_dir, output_dir=output_dir)
    legacy.set_global_theme()

    manifest_df = read_manifest(manifest_path)
    manifest_df = filter_manifest(
        manifest_df=manifest_df,
        only_sites=only_sites,
        limit=limit,
    )

    if manifest_df.empty:
        raise ValueError("No manifest rows remain after applying filters.")

    print(f"Manifest: {manifest_path}")
    print(f"Data dir: {data_dir}")
    print(f"Output dir: {output_dir}")
    print(f"Sites to process: {len(manifest_df)}")

    if dry_run:
        print("\nDry run only. Sites that would be processed:")
        for _, row in manifest_df.iterrows():
            print(f"  - {row['site_id']}: {row['site_name']}")

        return pd.DataFrame()

    summary_df = legacy.load_summary_data()

    results = []

    for index, row in manifest_df.iterrows():
        site = str(row["site_name"])
        print(f"\n[{len(results) + 1}/{len(manifest_df)}] Generating figures for {site}...")

        try:
            result = build_one_site(site=site, row=row, summary_df=summary_df)

        except Exception as exc:
            if stop_on_error:
                raise

            result = {
                "site_id": row.get("site_id", ""),
                "site_name": site,
                "manual": "error",
                "mini_manual": "error",
                "edge": "error",
                "pattern_matching": "error",
                "composite": "error",
                "error": repr(exc),
            }

            print(f"  ERROR: {exc!r}")

        results.append(result)

    inventory_df = pd.DataFrame(results)

    output_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = output_dir / DEFAULT_INVENTORY_NAME
    inventory_df.to_csv(inventory_path, index=False)

    print(f"\nWrote inventory: {inventory_path}")

    return inventory_df

