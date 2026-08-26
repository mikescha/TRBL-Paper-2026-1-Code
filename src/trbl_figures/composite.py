from __future__ import annotations

import glob
import os
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
from PIL import Image, ImageDraw, ImageFont

from trbl_figures import constants as C

LEGEND_NAME = "legend.png"
FIGURE_DIR = C.PROJECT_ROOT / "figures"

# Each type of file we're combining
GRAPH_SUMMARY = "Summary"
GRAPH_MANUAL = "Manual Analysis"
GRAPH_MINIMAN = "MiniMan"
GRAPH_EDGE = "Edge Analysis"
GRAPH_PM = "Pattern Matching Analysis"
GRAPH_WEATHER = "Weather"
GRAPH_TYPES = [
    GRAPH_SUMMARY,
    GRAPH_PM,
    GRAPH_MANUAL,
    GRAPH_MINIMAN,
    GRAPH_EDGE,
    GRAPH_WEATHER,
]


def output_cmap(figure_dir: Path = FIGURE_DIR) -> None:
    # Save the legend if one doesn't exist; if I update the code, need to delete the file to regenerate it
    figure_path = figure_dir / LEGEND_NAME
    if not os.path.exists(figure_path):
        plt.savefig(figure_path, dpi="figure", bbox_inches="tight", pad_inches=0)


# Helper to ensure we make the filename consistently because this is done from multiple places
def make_img_filename(site: str, graph_type: str, extra="") -> str:
    filename = f"{site}_{graph_type}_{extra}.png"
    return filename


# Helper for when we need to remove a file
def remove_file(full_path: Path) -> bool:
    result = False
    try:
        os.remove(full_path)
        result = True
    except FileNotFoundError:
        result = True
    except OSError as e:
        print(f"Error {e} trying to remove file {full_path}")
        result = False
    return result


# Save the graphic to a different folder. All file-related options are managed from here.
def save_figure(
    site: str,
    graph_type: str,
    graph: Figure,
    figure_dir: Path,
    delete_only: bool = False,
    do_aligned_dates: bool = False,
):

    aligned_str = "aligned" if do_aligned_dates else ""
    filename = make_img_filename(site, graph_type, extra=aligned_str)
    figure_path = figure_dir / filename
    # We aren't saving the "unclean" one any more, so technically this isn't necessary but doesn't hurt
    remove_file(figure_path)

    extra = aligned_str if do_aligned_dates else "clean"
    cleaned_image_filename = make_img_filename(site, graph_type, extra=extra)
    cleaned_figure_path = figure_dir / cleaned_image_filename
    remove_file(cleaned_figure_path)
    if not delete_only:
        # If we're making the graph where everything is aligned, we don't want the dates
        if do_aligned_dates:
            MONTH_NAMES = {
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            }
            for ax in graph.axes:
                for text in ax.texts[:]:
                    if (
                        text.get_text() in MONTH_NAMES
                        or "data" in text.get_text().lower()
                    ):
                        text.remove()
            bbox_inches = None

        # Now, need to trim off the bottom of the image that we don't need any more
        fig_w, fig_h = graph.get_size_inches()
        fig_w += 1 / C.DPI  # Round up to prevent clipping on the right
        # Crop from the bottom
        if do_aligned_dates:
            trim_amount_in = -(1 / C.DPI)
        else:
            trim_amount_in = 0.1
        bbox_inches = Bbox.from_bounds(
            0,  # x0 (left), -0.25 preserves the margin
            trim_amount_in,  # y0 (bottom trim in inches)
            fig_w,  # width
            fig_h - trim_amount_in,  # height
        )
        plt.savefig(cleaned_figure_path, dpi="figure", bbox_inches=bbox_inches)
        # save_with_reserved_margin(graph, cleaned_figure_path, dpi="figure", bottom_pad_in=trim_amount_in)

    else:
        # TODO If there is no data, what to do? The line below saves an empty image.
        pass

    plt.close()


def concat_images(*images: Image.Image, is_legend: bool = False) -> Image.Image:
    """Generate composite of all supplied images."""
    # Get the widest width. This will be a graph, not the legend
    width = max(image.width for image in images)
    # Add a little padding, so the border has space
    x_padding = 0
    width += x_padding

    # Add up all the heights.
    height = sum(image.height for image in images)

    # put some space between each graph
    y_padding = 25
    height += y_padding * len(images)

    composite = Image.new("RGB", (width, height), color="white")

    # Paste each image below the one before it.
    y = 0 + y_padding

    # Paste each image centered in the graphic
    for image in images:
        x = int((width - image.width) / 2)
        composite.paste(image, (x, y))
        y += image.height + y_padding

    return composite


def apply_decorations_to_composite(
    pretty_name: str, composite: Image.Image, month_locs: dict
) -> Image.Image:
    scale = C.DPI / 300

    # Make a new image that's a little bigger so we can add the site name at the top
    width, height = composite.size
    title_height = 100 * scale
    month_row_height = 0
    border_width = 0
    border_height = border_width * 2 * scale
    margin_bottom = 20 * scale
    margin_left = 0 + 0 * scale
    margin_right = width - 0 * scale

    months_at_top = False
    if months_at_top:
        month_row_height = 80 * scale

    new_height = int(
        height + title_height + month_row_height + border_height + margin_bottom
    )

    title_font_size = 72 * scale
    month_font_size = 36 * scale
    fudge = 10 * scale  # for descenders

    final = Image.new(composite.mode, (width, new_height), color="white")

    # Get the font path
    font_path = os.path.join(os.environ["WINDIR"], "Fonts", C.GRAPH_FONT_TTF)

    # Add the title
    draw = ImageDraw.Draw(final)
    font = ImageFont.truetype(font_path, size=title_font_size)
    draw.text(
        (width / 2, title_height - fudge),
        pretty_name,
        fill="black",
        anchor="ms",
        font=font,
    )

    # Add the months
    if months_at_top:
        font = ImageFont.truetype(font_path, size=month_font_size)
        v_pos = title_height + month_row_height - fudge
        month_row_width = margin_right - margin_left

        total_days = sum(end - start + 1 for start, end in month_locs.values())
        day_width = month_row_width / total_days
        h_pos = margin_left
        for month in month_locs:
            days_in_month = month_locs[month][1] - month_locs[month][0] + 1
            m_center = days_in_month / 2
            text_pos = h_pos + (m_center * day_width)
            draw.text((text_pos, v_pos), month, fill="black", font=font, anchor="ms")
            h_pos += days_in_month * day_width

    # Paste in the composite
    max_height = int(title_height + month_row_height + border_width)
    final.paste(composite, box=(0, max_height))

    # Add the border
    border_top = title_height + month_row_height
    border_left = 0
    border_right = margin_right - border_width * 2
    draw.rectangle(
        [(border_left, border_top), (border_right, new_height - margin_bottom)],
        outline="black",
        width=int(border_width),
    )

    return final


# Code from ChatGPT to draw the labels without clipping
def wrap_text(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int
) -> list[str]:
    """
    Word-wrap `text` into lines that fit within `max_width` pixels.
    Preserves existing newlines as paragraph breaks.
    """
    lines: list[str] = []
    for para in text.splitlines() or [""]:
        words = para.split()
        if not words:
            lines.append("")  # blank line
            continue

        cur = words[0]
        for w in words[1:]:
            trial = f"{cur} {w}"
            if draw.textlength(trial, font=font) <= max_width:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


# Load all the images that match the site name, combine them into a single composite,
# and then save that out
def combine_unaligned_images(
    site: str,
    pretty_name: str,
    month_locs: dict,
    figure_dir: Path,
    align_dates: bool = False,
    include_key: bool = False,
):
    # if there are no months, then we didn't have any data to graph so don't make a composite
    if len(month_locs) == 0:
        return

    if align_dates:
        composite_filename = make_img_filename(site, "Aligned_Composite")
    else:
        composite_filename = make_img_filename(site, "Composite")

    composite_path = figure_dir / composite_filename
    remove_file(composite_path)

    # Get all the files that match
    pattern = f"{site}_*clean.png"
    matching_files = glob.glob(str(figure_dir / pattern))

    if align_dates:
        matching_files = [f for f in matching_files if "aligned" in f]
    else:
        matching_files = [f for f in matching_files if "aligned" not in f]

    site_fig_dict = {}
    for graph_type in GRAPH_TYPES:
        result = [f for f in matching_files if graph_type in f]
        assert len(result) <= 1
        if result:
            site_fig_dict[graph_type] = result[0]
    legend = figure_dir / LEGEND_NAME

    if len(site_fig_dict):
        image_list = []
        for graph_type, filename in site_fig_dict.items():
            with Image.open(filename) as im:
                image_list.append(im.copy())

        # add the legend if needed
        if include_key and os.path.exists(legend):
            with Image.open(legend) as im:
                image_list.append(im.copy())

        composite = concat_images(*image_list)

        final = apply_decorations_to_composite(pretty_name, composite, month_locs)
        final.save(composite_path)
    return
