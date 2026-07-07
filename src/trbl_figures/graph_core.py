from __future__ import annotations

from typing import Any

from internal import trbl_summarizer as legacy


def set_global_theme() -> None:
    legacy.set_global_theme()


def create_graph(*args: Any, **kwargs: Any):
    return legacy.create_graph(*args, **kwargs)


def get_month_locs(columns) -> dict:
    return legacy.get_month_locs(columns)


def draw_legend(*args: Any, **kwargs: Any) -> None:
    legacy.draw_legend(*args, **kwargs)