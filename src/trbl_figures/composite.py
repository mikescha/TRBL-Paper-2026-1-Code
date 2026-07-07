from __future__ import annotations

import os

import matplotlib.pyplot as plt

from trbl_figures import constants as C

LEGEND_NAME = "legend.png"
FIGURE_DIR = C.PROJECT_ROOT / "figures"



def output_cmap():
    # Save the legend if one doesn't exist; if I update the code, need to delete the file to regenerate it
    figure_path = FIGURE_DIR / LEGEND_NAME
    if not os.path.exists(figure_path):
        plt.savefig(figure_path, dpi="figure", bbox_inches="tight", pad_inches=0)

