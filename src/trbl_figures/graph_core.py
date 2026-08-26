from __future__ import annotations

import os
from collections import Counter
from itertools import pairwise
from pathlib import Path
from typing import Any, cast

import matplotlib as mpl
import numpy as np
import pandas as pd

# Force Matplotlib to use the standard, non-interactive Agg backend
mpl.use("Agg")
import logging

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
from matplotlib import colors
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.ticker import NullFormatter, NullLocator
from matplotlib.transforms import Bbox

from trbl_figures import constants as C
from trbl_figures.composite import output_cmap
from trbl_figures.date_utils import convert_to_datetime

logger = logging.getLogger(__name__)


# TODO 2021 Markham Ravine_Composite has both manual and miniman in the new graph, but the old one just had miniman.

# Figure width and height, values in inches
FIG_W = 6.5
FIG_H = 1
GRAPH_LEFT_PADDING = 0.1

TITLE_FONT_SIZE = 13
AXIS_FONT_SIZE = 8
LEGEND_FONT_SIZE = 8

NO_DATA_COLOR = "lightgray"
HATCH_PATTERN = "////////"
HATCH_BG_COLOR = "mintcream"
HATCH_DARK_COLOR = "silver"
BORDER_WIDTH = 0.25  # for the vertical month dividers and the exterior edges
LABEL_OFFSET = 0.125  # gap between bottom of the graph and the months
EDGE_GRAPH_BORDER_WIDTH = 0.5
EDGE_GRAPH_BORDER_INSET = 0.02

CMAP_NAMES = {
    C.DATA_COL[C.MALE_SONG]: "Male Song",
    C.DATA_COL[C.COURT_SONG]: "Male Chorus",
    C.DATA_COL[C.ALTSONG2]: "Female Chatter",
    C.DATA_COL[C.ALTSONG1]: "Hatchling/Nestling/Fledgling",
}

# TODO what's up with the TBD
TAG_NAME_MAP = {
    "val<Agelaius tricolor/Common Song>": "Male Song",
    "val<Agelaius tricolor/Courtship Song>": "Male Chorus",
    "val<Agelaius tricolor/Alternative Song 2>": "Female Chatter",
    "val<Agelaius tricolor/Alternative Song 1>": "TBD???",
    "sp11/Simple Call": "Hatchling Begging Call",
    "sp22/Simple Call": "Nestling Begging Call",
    "Agelaius tricolor/Simple Call 2": "Fledgling Begging Call",
}


# Helper in case we want to do extra processing here
def plot_title(fig: Figure, title: str, x: float = 0.0, y: float = 1.0):
    fig.suptitle(
        " " + title,
        x=x,
        y=y,
        fontsize=TITLE_FONT_SIZE,
        fontfamily=C.GRAPH_FONT,
        horizontalalignment="left",
        verticalalignment="top",
    )


def overlay_missing_days_hatch(
    axs,
    missing_days: pd.DatetimeIndex,
    start_day,
    last_day,
    *,
    hatch=HATCH_PATTERN,
    color=HATCH_DARK_COLOR,
    facecolor=HATCH_BG_COLOR,
    zorder=10,
):
    if missing_days.empty:
        return

    for ax in axs:
        for missing_day in missing_days:
            if start_day <= missing_day <= last_day:
                i = (missing_day - start_day).days
                ax.axvspan(
                    i,
                    i + 1,
                    ymin=0,
                    ymax=1,
                    facecolor=facecolor,
                    edgecolor=color,
                    hatch=hatch,
                    linewidth=0,
                    zorder=zorder,
                )


def file_missing(site, graph_type, type):
    if graph_type == C.GRAPH_PM:
        site_dir = C.PMJ_DIR / site
        if os.path.isdir(site_dir):
            fname = f"{site} {type}.csv"
            full_file_name = site_dir / fname
            if os.path.isfile(full_file_name):
                return False

    return True


def add_text(ax, x, text, color):
    ax.text(
        x + 0.5,
        0.5,
        text,
        font=C.GRAPH_FONT,
        fontsize=8,
        fontstyle="italic",
        color=color,
        verticalalignment="center",
    )


def draw_axis_labels(
    fig,
    month_lengths: dict,
    skip_month_names=False,
    y: float = 0,
    bottom: float = 0,
    top: float = 0,
):

    def approx_text_width_px(text: str, fontsize_pt: float) -> float:
        # Rule-of-thumb: average Latin glyph is ~0.5–0.6 em.
        # 1 pt = 1/72 inch, but we can stay relative because we compare widths in px.
        # In practice: width ≈ fontsize_px * 0.55 * n_chars
        return (
            fontsize_pt * 1.333 * 0.55 * len(text)
        )  # 1.333 ≈ 96/72 (px per pt at 96 dpi)

    def draw_month_label_if_fits(
        ax,
        text: str,
        x_start: float,
        x_end: float,
        y_axes: float,
        *,
        fontsize=AXIS_FONT_SIZE,
        fontfamily=C.GRAPH_FONT,
        pad_px=4,
        **text_kwargs,
    ):
        # available width in display pixels
        x0_disp, _ = ax.transData.transform((x_start, 0))
        x1_disp, _ = ax.transData.transform((x_end, 0))
        available_px = abs(x1_disp - x0_disp)

        text_px = approx_text_width_px(text, fontsize)

        if text_px + pad_px <= available_px:
            ax.text(
                (x_start + x_end) / 2,
                y_axes,
                text,
                ha="center",
                va="bottom",
                transform=ax.get_xaxis_transform(),
                fontsize=fontsize,
                fontfamily=fontfamily,
                **text_kwargs,
            )

    ax = fig.get_axes()[-1]
    x_min, x_max = ax.get_xlim()

    x_fig = 0.0
    x_days = 0.0
    day_width = 1.0 / (x_max - x_min)

    months = list(month_lengths.items())
    total = len(months)

    for i, (month, n_days) in enumerate(months):
        if not skip_month_names:
            draw_month_label_if_fits(
                ax,
                month,
                x_days,
                x_days + n_days,
                y,
            )

        x_days += n_days
        x_fig += n_days * day_width

        # Don't draw the border for the last month
        if i < total - 1:
            line = mlines.Line2D(
                [x_fig, x_fig],
                [bottom + (BORDER_WIDTH / 200), top - (BORDER_WIDTH / 200)],
                transform=fig.transFigure,
                color="black",
                linewidth=BORDER_WIDTH,
                alpha=1,
            )
            fig.add_artist(line)


def calc_x_from_date(df, event_date) -> float:
    loc = df.columns.get_loc(event_date)
    if not isinstance(loc, int):
        raise TypeError(f"Expected unique column for {event_date}, got {type(loc)}")
    x = float(loc)
    return x


def draw_event_date_marker(
    ax, x, add_arrow=False, date_type=C.PULSE_HATCH, graph_width=0
):
    date_markers = {
        C.PULSE_MC_START: "M",
        C.PULSE_INC_START: "I",
        C.PULSE_HATCH: "B",
        C.PULSE_FIRST_FLDG: "F",
        C.PULSE_LAST_FLDG: "D",
    }

    # Draw circular outline marker (no fill)
    if x == 0:
        MARKER_OFFSET_PT = 4
    else:
        MARKER_OFFSET_PT = 3
    TEXT_X_NUDGE_PT = 0
    TEXT_Y_NUDGE_PT = 0
    ARROW_LEN_PT = 11

    # Base transform: anchor at (x, 0.45) in data coords,
    # then shift right by a fixed number of points
    marker_trans = ax.transData + mtransforms.ScaledTranslation(
        MARKER_OFFSET_PT / 72.0, 0, ax.figure.dpi_scale_trans
    )

    # Circle
    ax.scatter(
        [x],
        [0.4],
        s=65,  # tune this
        facecolors="white",
        edgecolors="black",
        linewidths=0.25,
        transform=marker_trans,
        zorder=15,
        clip_on=False,
    )

    # Letter
    text_trans = ax.transData + mtransforms.ScaledTranslation(
        (MARKER_OFFSET_PT + TEXT_X_NUDGE_PT) / 72.0,
        TEXT_Y_NUDGE_PT / 72.0,
        ax.figure.dpi_scale_trans,
    )

    txt = ax.text(
        x,
        0.45,
        date_markers[date_type],
        transform=text_trans,
        ha="center",
        va="center",
        fontsize=8,
        color="black",
        zorder=16,
        clip_on=False,
    )
    txt.set_in_layout(False)

    # arrow
    if add_arrow:
        ax.annotate(
            "",
            xy=(x - 0.1, 0.85),
            xycoords="data",
            xytext=(ARROW_LEN_PT, 0),
            textcoords="offset points",
            arrowprops={
                "arrowstyle": "->",
                "lw": 0.5,
                "color": "black",
                "mutation_scale": 7,
            },
            zorder=18,
            annotation_clip=False,
        )


def add_event_date_marker(
    ax, df, date_type, event_date, first_rec_date=None, last_rec_date=None
):
    if event_date == C.CONTINUOUS:
        return

    add_arrow = False
    if event_date == convert_to_datetime("6/1/1967"):
        # This is the new special case of a hatch date prior to graph start
        add_arrow = True
        event_date = first_rec_date

    graph_width = 0 if first_rec_date is None else last_rec_date - first_rec_date
    if event_date >= df.columns[0] and event_date <= df.columns[-1]:
        x = calc_x_from_date(df, event_date)
    else:
        logger.warning(
            f"create_graph: {date_type} {event_date} is outside range of this year, which is {df.columns[0]} through {df.columns[-1]}"
        )
        return
    draw_event_date_marker(
        ax, x, add_arrow=add_arrow, date_type=date_type, graph_width=graph_width
    )


def get_days_per_month(date_list: list) -> dict:
    # Make a list of all the values, but only use the month name. Then, count how many of each
    # month names there are to get the number of days/month
    months = [pd.to_datetime(date).strftime("%B") for date in date_list]
    return Counter(months)


# Set up base theme#
# See here for color options: https://matplotlib.org/3.5.0/tutorials/colors/colormaps.html
def set_global_theme() -> None:
    # https://matplotlib.org/stable/tutorials/introductory/customizing.html#matplotlib-rcparams
    line_color = "black"
    line_width = "1.5"
    custom_params = {
        "figure.dpi": C.DPI,
        "font.family": C.GRAPH_FONT,
        "font.size": AXIS_FONT_SIZE,
        "font.stretch": "normal",
        "xtick.bottom": "False",
        "xtick.labelbottom": "False",
        "ytick.left": "False",
        "ytick.labelleft": "False",
        "figure.frameon": "False",
        "axes.spines.left": "False",
        "axes.spines.right": "False",
        "axes.spines.top": "False",
        "axes.spines.bottom": "False",
        "axes.edgecolor": line_color,
        "axes.xmargin": 0,
        "axes.ymargin": 0,
        "lines.color": line_color,
        "lines.linewidth": line_width,
        "patch.edgecolor": line_color,
        "patch.linewidth": line_width,
        "savefig.facecolor": "white",
    }
    mpl.rcParams.update(cast(Any, custom_params))


# Create a graph, given a dataframe, list of row names, color map, and friendly names for the rows
def create_graph(
    site: str,
    df: pd.DataFrame,
    row_names: list,
    cmap: dict,
    key_dates: dict,
    missing_days: pd.DatetimeIndex,
    denom_by_day: pd.Series,
    draw_horiz_rects: bool = False,
    title="",
    graph_type="",
) -> Figure:
    plt.close()  # close any prior graph that was open

    # data cleanup -- for scenarios where the incubation date was calculated, we could have an actual number
    # although the number is earlier than the date of the first recording. To ensure this gets graphed correctly,
    # we need to update the date
    if (
        key_dates != None
        and "p1" in key_dates
        and C.PULSE_INC_START in key_dates["p1"]
        and key_dates["p1"][C.PULSE_INC_START] < key_dates[C.SUMMARY_FIRST_REC]
    ):
        key_dates["p1"][C.PULSE_INC_START] = convert_to_datetime("6/1/1967")

    if len(df) == 0:
        # return an empty plot if nothing to graph
        fig, axs = plt.subplots(nrows=1, ncols=1)
        return fig

    if graph_type == C.GRAPH_EDGE:
        row_count = 1  # All data should be drawn on the same axis for edge
    else:
        row_count = len(row_names)
    graph_drawn = []

    # --- inches-based spec ---
    top_pad_in = 0.0  # Whitespace at the top
    title_band_in = 0.2  # Gap for the label
    top_band_in = top_pad_in + title_band_in

    # Height in inches of the actual graph, allot 0.2" per row
    row_height = 0.2

    label_height_in = 0.25  # Axis labels
    legend_height_in = 0.0
    bottom_pad_in = 0.0  # Whitespace at the bottom
    bottom_band_in = label_height_in + legend_height_in + bottom_pad_in
    fig_w = FIG_W  # keep your width in inches

    plot_in = row_count * row_height
    fig_h = top_band_in + plot_in + bottom_band_in

    fig, axs = plt.subplots(
        nrows=row_count,
        ncols=1,
        sharex=True,
        figsize=(fig_w, fig_h),
        gridspec_kw={
            "height_ratios": np.ones(row_count),
            "hspace": 0.0,
        },
        squeeze=False,  # forces axs to be 2D array even if 1 row
    )
    axs = axs.flatten()  # normalize axs to 1D

    def disable_ticks(ax):
        ax.set_xticks([])
        ax.set_yticks([])

        for axis in (ax.xaxis, ax.yaxis):
            axis.set_major_locator(NullLocator())
            axis.set_minor_locator(NullLocator())
            axis.set_major_formatter(NullFormatter())
            axis.set_minor_formatter(NullFormatter())

    for ax in axs:
        disable_ticks(ax)

    # This is the left gutter to allow the decorations to hang out
    fig_width_in = fig.get_size_inches()[0]
    left_margin = GRAPH_LEFT_PADDING / fig_width_in
    fig.subplots_adjust(left=left_margin)

    # Convert inches -> figure fractions for subplot rectangle
    bottom = bottom_band_in / fig_h
    top = 1.0 - (top_band_in / fig_h)
    fig.subplots_adjust(left=0, right=1, bottom=bottom, top=top)

    # If we have one, add the title for the graph and set appropriate formatting
    if len(title):
        title_y = 1.0 - (top_pad_in / fig_h)
        plot_title(fig, title, y=title_y)

    # Ensure that we have a row for each index. If a row is missing, add it with NaN values
    for row in row_names:
        if row not in df.index:
            df.loc[row] = pd.Series(data=np.nan, index=df.columns)

    df_clean = df.copy()

    i = 0
    for row in row_names:
        # plotting the heatmap
        # pull out the one row we want and transpose it to be wide
        if graph_type == C.GRAPH_EDGE:
            df_sel = df.loc[row_names].replace(
                -100, np.nan
            )  # keep all rows in df, select subset here
            df_to_graph = df_sel.bfill(axis=0).iloc[[0]]  # 1-row DataFrame
        else:
            df_to_graph = df_clean.loc[[row]].copy()

        # Get the colormap names
        cmap_name = cmap[row] if len(cmap) > 1 else cmap[0]

        # Grab the map from Matplotlib and create a safe copy of it
        cmap_final = plt.colormaps.get_cmap(cmap_name).copy()

        cmap_final.set_under("white")
        no_data_color = "white" if graph_type == C.GRAPH_PM else NO_DATA_COLOR
        cmap_final.set_bad(
            no_data_color
        )  # representing the days where analysis was not done

        # Normalize all the data by the number of recordings that were used per day
        if graph_type == C.GRAPH_MINIMAN:
            df_norm = df_to_graph / 3  # 3 recordings per day
        else:
            # Align denom to the same columns (dates)
            denom = denom_by_day.reindex(df_to_graph.columns)
            df_norm = df_to_graph.div(
                denom, axis="columns"
            )  # normalize by count of recordings per day

        # Adjust colors so that lighter values are more visible
        # gamma < 1 brightens lows, closer to 0 is more extreme
        gamma = 0.85
        vmin = 0.001  # slightly above 0 so that 0 values get the 'under' color
        vmax = 1  # as we're normalizing the data, the ranges will all be 0-1
        norm = colors.PowerNorm(gamma=gamma, vmin=vmin, vmax=vmax)

        arr = np.ma.masked_invalid(df_norm.to_numpy(dtype=float))
        _, n_cols = arr.shape

        ax = axs[i]
        ax.imshow(
            arr,
            cmap=cmap_final,
            norm=norm,
            aspect="auto",
            interpolation="nearest",
            origin="upper",
            extent=(
                0,
                n_cols,
                1,
                0,
            ),  # forces the axis settings to be like the old seaborn one
            zorder=1,
        )

        # If we drew an empty graph, write text on top to indicate that it is supposed to be empty
        # and not that it's just hard to read!
        if df_clean.loc[row].sum() == 0:
            # The conundrum: at least for edge, it's possible that a row we drew is blank, but the actual
            # row is going to get some boxes and lines. In this case, there will be -100s in the data,
            # and if we find those, we should NOT draw the text that says there is no data
            if graph_type == C.GRAPH_EDGE and df.loc[row].lt(0).any():
                pass
            else:
                if file_missing(site, graph_type, row):
                    label = row
                    display_label = TAG_NAME_MAP.get(label, label)

                    x = (key_dates[C.SUMMARY_FIRST_REC] - df.columns[0]).days
                    add_text(axs[i], x, f"No data for {display_label}", "gray")
        elif graph_type == C.GRAPH_EDGE:
            pass

        # Track which graphs we drew, so we can put the proper ticks on later
        graph_drawn.append(i)
        if graph_type == C.GRAPH_PM:
            # Add the event markers if available
            for pulse, pulse_dates in key_dates.items():
                if pulse in C.PULSES:  # Do this to skip the start/end recording dates
                    for date_type, event_date in pulse_dates.items():
                        if (
                            row == "Male Chorus"
                            and date_type == C.PULSE_MC_START
                            or row == "Female"
                            and date_type == C.PULSE_INC_START
                            or row == "Hatchling"
                            and date_type == C.PULSE_HATCH
                            or row == "Fledgling"
                            and (
                                date_type == C.PULSE_FIRST_FLDG
                                or date_type == C.PULSE_LAST_FLDG
                            )
                        ):
                            add_event_date_marker(
                                ax,
                                df,
                                date_type,
                                event_date,
                                first_rec_date=key_dates[C.SUMMARY_FIRST_REC],
                                last_rec_date=key_dates[C.SUMMARY_LAST_REC],
                            )

        # For edge: Add a rectangle around the regions of consective tags, and a line between
        # non-consectutive if it's a N tag.
        if draw_horiz_rects and row in df_clean.index:
            df_col_nonzero = df.loc[
                [row]
            ].T  # pull out the row we want, it turns into a column as above
            df_col_nonzero = (
                df_col_nonzero.reset_index()
            )  # index by ints for easy graphing
            df_col_nonzero = df_col_nonzero[df_col_nonzero[row] != 0]

            if len(df_col_nonzero):
                # Scale the color maps so we get the same color but a little lighter
                c = mpl.colormaps[(cmap[row] if len(cmap) > 1 else cmap[0])](0.5)
                # n tags get boxes around each consecutive block
                idx = df_col_nonzero[row].dropna().index.to_numpy()
                if len(idx) == 0:
                    borders: list[tuple[int, int]] = []
                elif len(idx) == 1:
                    start_and_end = int(idx[0])
                    borders = [(start_and_end, start_and_end)]
                else:
                    # Find boundaries where contiguity breaks
                    breaks = np.where(np.diff(idx) > 1)[0]

                    starts = np.r_[idx[0], idx[breaks + 1]]
                    ends = np.r_[idx[breaks], idx[-1]]
                    borders = [(int(a), int(b)) for a, b in zip(starts, ends)]
                # We now have a list of pairs of coordinates where we need a rect. For each pair, draw one.
                for start, end in borders:
                    left = start
                    width = (end - start) + 1
                    ax.add_patch(
                        Rectangle(
                            (left, EDGE_GRAPH_BORDER_INSET),
                            width,
                            1 - 2 * EDGE_GRAPH_BORDER_INSET,
                            ec=c,
                            fc=c,
                            lw=EDGE_GRAPH_BORDER_WIDTH,
                            alpha=1,
                            fill=False,
                        )
                    )
                # For each pair of rects, draw a line between them.
                gaps = [
                    (end1 + 1, start2 - 1)
                    for (_, end1), (start2, _) in pairwise(borders)
                ]
                for start_gap, end_gap in gaps:
                    left = start_gap
                    right = end_gap + 1
                    line_distance = right - left
                    line_height = EDGE_GRAPH_BORDER_WIDTH / 10
                    y_start_pos = 0.5
                    ax.add_patch(
                        Rectangle(
                            (left, y_start_pos),
                            line_distance,
                            line_height,
                            ec=c,
                            fc=c,
                            lw=0,
                            alpha=1,
                            fill=True,
                        )
                    )

        # For edge, all data is drawn on the same axis so don't increment the counter here and just get out of the loop
        if graph_type == C.GRAPH_EDGE:
            break
        else:
            i += 1

    # Draw shading over every missing date
    start_day = pd.Timestamp(df.columns.min()).normalize()
    last_day = pd.Timestamp(df.columns.max()).normalize()
    overlay_missing_days_hatch(
        axs,
        missing_days,
        start_day=start_day,
        last_day=last_day,
    )

    # Add the vertical lines and month names
    text_offset_in = LABEL_OFFSET
    text_y = bottom - (text_offset_in / fig_h)
    text_y = -0.65
    draw_axis_labels(
        fig,
        get_days_per_month(df.columns.tolist()),
        y=text_y,
        bottom=bottom,
        top=top,
    )

    # Draw a bounding rectangle around everything except the caption
    b = Bbox.union([ax.get_position() for ax in fig.axes])

    border = Rectangle(
        (b.x0, b.y0),  # (x0, y0) in figure coords
        b.width,  # width (full figure width)
        b.height,  # height = plot area only
        transform=fig.transFigure,
        linewidth=BORDER_WIDTH,
        edgecolor="black",
        fill=False,
        zorder=8,
    )
    fig.add_artist(border)

    # return the final plotted heatmap
    return fig


def get_month_locs(cols: pd.Index) -> dict[str, list[int]]:
    def get_visible_month_day_ranges(
        start: pd.Timestamp, end: pd.Timestamp
    ) -> dict[str, list[int]]:
        result: dict[str, list[int]] = {}

        # Snap start to the first day of its month
        first_month_start = start.replace(day=1)

        # Generate all months intersecting the interval
        month_starts = pd.date_range(
            start=first_month_start,
            end=end,
            freq="MS",
        )

        for ms in month_starts:
            me = ms + pd.offsets.MonthEnd(0)

            # Clip to visible interval
            visible_start = max(ms, start)
            visible_end = min(me, end)

            month_name = ms.strftime("%B")  # "April"
            result[month_name] = [visible_start.day, visible_end.day]

        return result

    if not isinstance(cols, pd.DatetimeIndex):
        raise TypeError("get_month_locs requires a DatetimeIndex")
    start = cols.min().normalize()
    end = cols.max().normalize()
    month_locs = get_visible_month_day_ranges(start, end)
    return month_locs


def draw_legend(cmap: dict, save_files: bool, figure_dir: Path = C.FIGURE_DIR) -> None:
    # --- Geometry (all in ax.transAxes units) ---
    BAR_X = 0.00
    BAR_Y = 0.10
    BAR_W = 0.4
    BAR_H = 0.80

    LABEL_PAD = 0.05
    LABEL_X = BAR_X + BAR_W + LABEL_PAD
    LABEL_Y = 0.50

    # For swatch-only items (no gradient bar)
    SW_W = 0.18
    SW_H = 0.70
    SW_X = 0.00
    SW_Y = 0.50 - SW_H / 2.0

    # Gradient image used for all gradient legend items
    gradient = np.linspace(0, 1, 32)
    gradient = np.vstack((gradient, gradient))

    def imshow_rect(ax, img, *, x: float, y: float, w: float, h: float, **kwargs):
        ax.imshow(
            img,
            extent=(x, x + w, y, y + h),
            transform=ax.transAxes,
            **kwargs,
        )

    def draw_gradient_item(ax, cmap_name: str, label: str, scale=1.0):
        if label.startswith("Hatchling"):
            bar_w = BAR_W * scale
        else:
            bar_w = BAR_W

        imshow_rect(
            ax,
            gradient,
            x=BAR_X,
            y=BAR_Y,
            w=bar_w,
            h=BAR_H,
            aspect="auto",
            cmap=mpl.colormaps[cmap_name],
        )
        label_x = LABEL_X - (BAR_W - bar_w)
        ax.text(
            label_x,
            LABEL_Y,
            label,
            transform=ax.transAxes,
            va="center",
            ha="left",
            fontfamily=C.GRAPH_FONT,
            fontsize=LEGEND_FONT_SIZE,
        )
        ax.set_axis_off()

    def draw_swatch_item(
        ax,
        label: str,
        *,
        facecolor: str,
        hatch: str | None = None,
        hatch_edge_color: str | None = None,
    ):
        ax.add_patch(
            Rectangle(
                (SW_X, SW_Y),
                SW_W,
                SW_H,
                transform=ax.transAxes,
                facecolor=facecolor,
                edgecolor="black" if hatch_edge_color is None else hatch_edge_color,
                linewidth=0.2,
                hatch=hatch,
            )
        )
        ax.text(
            SW_X + SW_W + LABEL_PAD,
            LABEL_Y,
            label,
            transform=ax.transAxes,
            va="center",
            ha="left",
            fontfamily=C.GRAPH_FONT,
            fontsize=LEGEND_FONT_SIZE,
        )
        ax.set_axis_off()

    # --- Build 6 legend items in one row ---
    # First 4 = your gradient items (order from CMAP_NAMES)
    legend_items = []
    for key, label in CMAP_NAMES.items():
        label_text = label.replace(" ", "\n")
        label_text = label_text.replace("/", "\n")
        legend_items.append(("gradient", key, label_text))

    # Add the 2 new items at the end (or move them earlier if you prefer)
    legend_items.append(("swatch", "No analysis\ndone", None))
    legend_items.append(("hatch", "Missing\nrecordings", None))

    # Relative column widths (tweakable)
    width_ratios = [
        1.0,  # Male Song
        1.0,  # Male Chorus
        1.0,  # Female Chatter
        1.2,  # Hatchling / Nestling / Fledgling (wider)
        0.9,  # No data (narrow)
        0.9,  # Missing days
    ]

    ncols = len(legend_items)
    _, axs = plt.subplots(
        nrows=1,
        ncols=ncols,
        figsize=(FIG_W * 0.8, FIG_H * 0.15),
        gridspec_kw={"width_ratios": width_ratios},
        squeeze=False,
    )
    axs = axs.flatten()

    for i, (ax, item) in enumerate(zip(axs, legend_items)):
        kind = item[0]
        ratio = 1 / width_ratios[i]

        if kind == "gradient":
            _, key, label = item
            cmap_name = cmap[key] if isinstance(cmap, dict) else cmap
            draw_gradient_item(ax, cmap_name, label, scale=ratio)
        elif kind == "swatch":
            _, label, _ = item
            draw_swatch_item(ax, label, facecolor=NO_DATA_COLOR, hatch=None)

        elif kind == "hatch":
            _, label, _ = item
            # White face so hatch reads clearly; NaN / missing gets the hatch signal
            draw_swatch_item(
                ax,
                label,
                facecolor=HATCH_BG_COLOR,
                hatch=HATCH_PATTERN,
                hatch_edge_color=HATCH_DARK_COLOR,
            )

        else:
            ax.set_axis_off()

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)

    if save_files:
        output_cmap(figure_dir=figure_dir)
