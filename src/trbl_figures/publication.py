from pathlib import Path
from time import perf_counter
from typing import Any

import pandas as pd

from trbl_figures import composite, data_io, graph_core, metadata, pivots
from trbl_figures import constants as C
from trbl_figures.manifest import filter_manifest, read_manifest

DEFAULT_INVENTORY_NAME = "figure_inventory.csv"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def prepare_output_dirs(output_dir: Path) -> None:
    """Create output directories needed by the publication figure workflow."""
    output_dir = output_dir.resolve()

    output_dir.mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "outputs").mkdir(parents=True, exist_ok=True)


def should_build_panel(row: pd.Series, panel_name: str) -> bool:
    """Return whether a panel should be attempted for this manifest row."""
    return bool(row["all_available_panels"] or row[panel_name])


def build_pattern_matching_panel(
    site: str,
    date_range_dict: dict,
    key_dates: dict,
    missing_days: pd.DatetimeIndex,
    rec_norm: pd.Series,
    data_dir: Path,
    output_dir: Path,
) -> tuple[str, Any | None]:
    """Build and save the pattern-matching panel if data exists."""
    pt_pm, have_pm_data = pivots.do_pattern_matching(
        site=site,
        date_range_dict=date_range_dict,
        data_dir=data_dir,
    )

    if not have_pm_data or pt_pm.empty:
        return "no_data", None

    fig = graph_core.create_graph(
        site=site,
        df=pt_pm,
        row_names=C.PM_FILE_TYPES,
        cmap=C.CMAP_PM,
        title=C.GRAPH_PM,
        graph_type=C.GRAPH_PM,
        key_dates=key_dates,
        missing_days=missing_days,
        denom_by_day=rec_norm,
        do_aligned_dates=False,
    )

    composite.save_figure(site, C.GRAPH_PM, fig, figure_dir=output_dir)

    return "generated", pt_pm


def build_mini_manual_panel(
    site: str,
    df_core: pd.DataFrame,
    date_range_dict: dict,
    key_dates: dict,
    missing_days: pd.DatetimeIndex,
    output_dir: Path,
) -> tuple[str, Any | None]:
    """Build and save the mini-manual panel if data exists."""
    pt_mini_manual, have_mini_manual_data = pivots.do_mini_manual(
        df_core,
        date_range_dict,
    )

    if not have_mini_manual_data or pt_mini_manual.empty:
        return "no_data", None

    fig = graph_core.create_graph(
        site=site,
        df=pt_mini_manual,
        row_names=C.SONG_COLS,
        cmap=C.CMAP,
        title="Manual Analysis (Periodic)",
        graph_type=C.GRAPH_MINIMAN,
        key_dates=key_dates,
        missing_days=missing_days,
        denom_by_day=pd.Series(),
    )

    composite.save_figure(site, C.GRAPH_MINIMAN, fig, figure_dir=output_dir)

    return "generated", pt_mini_manual


def build_manual_panel(
    site: str,
    df_core: pd.DataFrame,
    date_range_dict: dict,
    key_dates: dict,
    missing_days: pd.DatetimeIndex,
    rec_norm: pd.Series,
    output_dir: Path,
) -> tuple[str, Any | None]:
    """Build and save the manual daily-review panel if data exists."""
    pt_manual, have_manual_data = pivots.do_manual(df_core, date_range_dict)

    if not have_manual_data or pt_manual.empty:
        return "no_data", None

    manual_rows = [
        C.DATA_COL[C.MALE_SONG],
        C.DATA_COL[C.ALTSONG2],
        C.DATA_COL[C.ALTSONG1],
    ]

    fig = graph_core.create_graph(
        site=site,
        df=pt_manual,
        row_names=manual_rows,
        cmap=C.CMAP,
        title="Manual Analysis (Daily Review)",
        graph_type=C.GRAPH_MANUAL,
        key_dates=key_dates,
        missing_days=missing_days,
        denom_by_day=rec_norm,
    )

    composite.save_figure(site, C.GRAPH_MANUAL, fig, figure_dir=output_dir)

    return "generated", pt_manual


def build_edge_panel(
    site: str,
    df_core: pd.DataFrame,
    date_range_dict: dict,
    key_dates: dict,
    missing_days: pd.DatetimeIndex,
    output_dir: Path,
) -> tuple[str, Any | None]:
    """Build and save the Edge/hatchling panel if data exists."""
    pt_edge, have_edge_data = pivots.do_edge(df_core, date_range_dict, site)
    edge_recs_per_day = pivots.get_recs_per_edge_day(df_core, date_range_dict)

    if not have_edge_data or pt_edge.empty:
        return "no_data", None

    cmap_edge = {name: "Blues" for name in C.EDGE_COLS}

    fig = graph_core.create_graph(
        site=site,
        df=pt_edge,
        row_names=pt_edge.index.to_list(),
        cmap=cmap_edge,
        draw_horiz_rects=True,
        title="Manual Analysis (Hatchlings Only)",
        graph_type=C.GRAPH_EDGE,
        key_dates=key_dates,
        missing_days=missing_days,
        denom_by_day=edge_recs_per_day,
    )

    composite.save_figure(site, C.GRAPH_EDGE, fig, figure_dir=output_dir)

    return "generated", pt_edge


def build_one_site(
    site: str,
    manifest_row: pd.Series,
    site_info_df: pd.DataFrame,
    data_dir: Path,
    output_dir: Path,
) -> dict:

    # PERF
    site_start = perf_counter()

    """Generate requested figure panels and composite for one site."""
    status = {
        "site_id": manifest_row.get("site_id", ""),
        "site_name": site,
        "manual": "not_requested",
        "mini_manual": "not_requested",
        "edge": "not_requested",
        "pattern_matching": "not_requested",
        "composite": "not_requested",
        "error": "",
    }

    site_data_df = data_io.load_site_data(site, data_dir=data_dir)

    if site_data_df.empty:
        status["error"] = "No source data found for site"
        return status

    core_hours_only_df = pivots.filter_to_core_hours(site_data_df, hour_col=C.HOUR)

    rec_norm = core_hours_only_df.groupby(level=C.DATE_COL)["core_hour"].nunique()

    site_summary_dict = metadata.process_site_summary_data(site_info_df)

    date_range_dict = metadata.get_publication_date_range(
        site_summary_dict=site_summary_dict,
    )

    missing_days = pivots.get_missing_days(core_hours_only_df, date_range_dict)

    key_dates = metadata.build_key_dates(site_summary_dict)

    month_locs = {}

    if should_build_panel(manifest_row, "pattern_matching"):
        panel_status, pt = build_pattern_matching_panel(
            site=site,
            date_range_dict=date_range_dict,
            key_dates=key_dates,
            missing_days=missing_days,
            rec_norm=rec_norm,
            data_dir=data_dir,
            output_dir=output_dir,
        )
        status["pattern_matching"] = panel_status

        if pt is not None and not month_locs:
            month_locs = graph_core.get_month_locs(pt.columns)

    if should_build_panel(manifest_row, "mini_manual"):
        panel_status, pt = build_mini_manual_panel(
            site=site,
            df_core=core_hours_only_df,
            date_range_dict=date_range_dict,
            key_dates=key_dates,
            missing_days=missing_days,
            output_dir=output_dir,
        )
        status["mini_manual"] = panel_status

        if pt is not None and not month_locs:
            month_locs = graph_core.get_month_locs(pt.columns)

    if should_build_panel(manifest_row, "manual"):
        panel_status, pt = build_manual_panel(
            site=site,
            df_core=core_hours_only_df,
            date_range_dict=date_range_dict,
            key_dates=key_dates,
            missing_days=missing_days,
            rec_norm=rec_norm,
            output_dir=output_dir,
        )
        status["manual"] = panel_status

        if pt is not None and not month_locs:
            month_locs = graph_core.get_month_locs(pt.columns)

    if should_build_panel(manifest_row, "edge"):
        panel_status, pt = build_edge_panel(
            site=site,
            df_core=core_hours_only_df,
            date_range_dict=date_range_dict,
            key_dates=key_dates,
            missing_days=missing_days,
            output_dir=output_dir,
        )
        status["edge"] = panel_status

        if pt is not None and not month_locs:
            month_locs = graph_core.get_month_locs(pt.columns)

    if manifest_row["include_composite"]:
        if month_locs:
            if manifest_row["include_key"]:
                graph_core.draw_legend(
                    C.CMAP,
                    save_files=True,
                    figure_dir=output_dir,
                )

            composite.combine_unaligned_images(
                site=site,
                pretty_name=site_info_df["Pretty Site Name"].item(),
                month_locs=month_locs,
                figure_dir=output_dir,
                align_dates=False,
                include_key=manifest_row["include_key"],
            )

            status["composite"] = "generated"
        else:
            status["composite"] = "no_data"

    # PERF
    elapsed = perf_counter() - site_start
    status["elapsed_seconds"] = round(elapsed, 2)
    print(f"  Finished in {elapsed:.1f}s")

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
    prepare_output_dirs(output_dir=output_dir)
    graph_core.set_global_theme()

    manifest_df = read_manifest(manifest_path)

    # DEBUG
    # TODO Consider removing for publication
    # print(f"Manifest rows before filtering: {len(manifest_df)}")
    # print(f"Manifest columns: {list(manifest_df.columns)}")
    # print(f"only_sites: {only_sites!r}")
    # print(f"limit: {limit!r}")

    # if not manifest_df.empty:
    #     print("First manifest rows:")
    #     print(manifest_df[["site_id", "site_name"]].head().to_string(index=False))

    manifest_df = filter_manifest(
        manifest_df=manifest_df,
        only_sites=only_sites,
        limit=limit,
    )

    # print(f"Manifest rows after filtering: {len(manifest_df)}")

    if manifest_df.empty:
        raise ValueError("No manifest rows remain after applying filters.")

    print(f"Manifest: {manifest_path}")
    print(f"Data dir: {data_dir}")
    print(f"Output dir: {output_dir}")
    print(f"Sites to process: {len(manifest_df)}")

    if dry_run:
        print("\nDry run only. Sites that would be processed:")
        for _, manifest_row in manifest_df.iterrows():
            print(f"  - {manifest_row['site_id']}: {manifest_row['site_name']}")

        return pd.DataFrame()

    summary_df = data_io.load_summary_data(data_dir=data_dir)

    results = []

    for _, manifest_row in manifest_df.iterrows():
        site = str(manifest_row["site_name"])
        print(
            f"\n[{len(results) + 1}/{len(manifest_df)}] Generating figures for {site}..."
        )

        try:
            site_df = metadata.get_site(site, summary_df)
            result = build_one_site(
                site=site,
                manifest_row=manifest_row,
                site_info_df=site_df,
                data_dir=data_dir,
                output_dir=output_dir,
            )

        except Exception as exc:
            if stop_on_error:
                raise

            result = {
                "site_id": manifest_row.get("site_id", ""),
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
