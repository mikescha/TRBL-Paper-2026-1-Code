from __future__ import annotations

import operator as op
from pathlib import Path

from internal import trbl_summarizer as legacy

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Paths
DATA_DIR = PROJECT_ROOT / "data"
INPUT_CSV = legacy.INPUT_CSV
PMJ_DIR = legacy.PMJ_DIR
ALL_SHEET_HEADER_SIZE = legacy.ALL_SHEET_HEADER_SIZE
FILENAME = legacy.FILENAME

# Columns
DATE_COL = legacy.DATE_COL
HOUR = legacy.HOUR
SITE = legacy.SITE
SITE_COLS = legacy.site_columns
TAG_WSE = "tag_edge"
TAG_WSM = "tag_wsm"
TAG_MHE = "tag_mhe"
TAG_MHM = "tag_mhm"
TAG_MHH = "tag_mhh"
TAG_MHE2 = "tag_mhe2"
TAG_WS = "tag_ws"
TAG_MH = "tag_mh"
TAG_P1N = "tag_p1n"
TAG_P2N = "tag_p2n"
TAG_P3N = "tag_p3n"
TAG_P4N = "tag_p4n"
ALTSONG1 = "altsong1"
TAG_YNC_P2 = "tag<YNC-p2>"
TAG_YNC_P3 = "tag<YNC-p3>"
TAG_YNC_P4 = "tag<YNC-p4>"

START = "start"
END = "end"

# Graph names
GRAPH_PM = legacy.GRAPH_PM
GRAPH_MINIMAN = legacy.GRAPH_MINIMAN
GRAPH_MANUAL = legacy.GRAPH_MANUAL
GRAPH_EDGE = legacy.GRAPH_EDGE

# PM / manual / edge constants
DATA_COL = legacy.data_col
PM_FILE_TYPES = legacy.PM_FILE_TYPES
SONG_COLS = legacy.SONG_COLS
EDGE_COLS = legacy.EDGE_COLS

MINI_MANUAL_TAGS = [TAG_MHH, TAG_MHM, TAG_WSM]
MANUAL_TAGS = [TAG_MH, TAG_WS, TAG_WSE]

MINI_MANUAL_COLS = [DATA_COL[t] for t in MINI_MANUAL_TAGS]
MANUAL_COLS = [DATA_COL[t] for t in MANUAL_TAGS]

TAG_MAP = {  # map of tag_pXn to ync tag
    DATA_COL[TAG_P1N]: DATA_COL[ALTSONG1],
    DATA_COL[TAG_P2N]: DATA_COL[TAG_YNC_P2],
    DATA_COL[TAG_P3N]: DATA_COL[TAG_YNC_P3],
    DATA_COL[TAG_P4N]: DATA_COL[TAG_YNC_P4],
}

MALE_SONG = legacy.MALE_SONG
ALTSONG1 = legacy.ALTSONG1
ALTSONG2 = legacy.ALTSONG2
ALL_SONGS = legacy.ALL_SONGS
ALL_TAGS = legacy.ALL_TAGS

# Color maps
CMAP = legacy.CMAP
CMAP_PM = legacy.CMAP_PM

# Summary / phase constants
SUMMARY_FIRST_REC = legacy.SUMMARY_FIRST_REC
SUMMARY_LAST_REC = legacy.SUMMARY_LAST_REC
SUMMARY_NUMERIC_COLS = legacy.SUMMARY_NUMERIC_COLS

PULSES = legacy.PULSES

PHASE_MALE_CHORUS = legacy.PHASE_MALE_CHORUS
PHASE_INC = legacy.PHASE_INC
PHASE_BROOD = legacy.PHASE_BROOD
PHASE_FLDG = legacy.PHASE_FLDG

PULSE_MC_START = legacy.PULSE_MC_START
PULSE_INC_START = legacy.PULSE_INC_START
PULSE_HATCH = legacy.PULSE_HATCH
PULSE_FIRST_FLDG = legacy.PULSE_FIRST_FLDG
PULSE_LAST_FLDG = legacy.PULSE_LAST_FLDG

ABANDONED = legacy.ABANDONED

VALIDATED_STR = legacy.VALIDATED_STR
MISSING_DATA_FLAG = legacy.MISSING_DATA_FLAG

MISSING_DATA_FLAG = -100
PRESERVE_EDGES_FLAG = -99

_OPS = {
    ">": op.gt,
    ">=": op.ge,
    "<": op.lt,
    "<=": op.le,
    "==": op.eq,
    "!=": op.ne,
}

# Core hours, these are the only ones we check for presences
CORE_START_HOUR = 7
CORE_END_HOUR_EXCLUSIVE = 20  # includes 7 through 19, excludes 20
MIN_CORE_HOURS_FOR_MEANINGFUL_ABSENCE = 4  # Fewer than this and we can't say much about an absence, so we won't count it as an absence in the effort-aware logic
MAX_CONSECUTIVE_BRIDGE_DAYS = 2
EFFORT_THRESHOLD_RATIOS = {
    "male_chorus": (3, 13),
    "female_chatter": (2, 13),
    "hbc": (1, 2),
    "nbc": (3, 13),
    "fbc": (3, 13),
}
