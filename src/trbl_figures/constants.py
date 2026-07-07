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
TAG_WS = "tag_ws"
TAG_MH = "tag_mh"
TAG_P1N = "tag_p1n"
TAG_P2N = "tag_p2n"
TAG_P3N = "tag_p3n"
TAG_P4N = "tag_p4n"
TAG_YNC_P2 = "tag<YNC-p2>"
TAG_YNC_P3 = "tag<YNC-p3>"
TAG_YNC_P4 = "tag<YNC-p4>"

MALE_SONG = "malesong"
ALTSONG1 = "altsong1"
ALTSONG2 = "altsong2"
COURT_SONG = "courtsong"
SIMPLE_CALL2 = "simplecall2"

DATA_COL = {
    FILENAME: "filename",
    SITE: "site",
    "day": "day",
    "month": "month",
    "year": "year",
    HOUR: "hour",
    DATE_COL: "date",
    TAG_YNC_P2: "tag<YNC-p2>",  # Young nestling call pulse 2
    TAG_YNC_P3: "tag<YNC-p3>",  # Young nestling call pulse 3
    TAG_YNC_P4: "tag<YNC-p4>",  # Young nestling call pulse 4
    "tag_p1a": "tag<p1a>",
    "tag_p1f": "tag<p1f>",
    TAG_P1N: "tag<p1n>",
    "tag_p2f": "tag<p2f>",
    TAG_P2N: "tag<p2n>",
    TAG_P3N: "tag<p3n>",
    TAG_P4N: "tag<p4n>",
    "tag_mhe2": "tag<reviewed-MH-e2>",
    "tag_mhe": "tag<reviewed-MH-e>",
    TAG_MHH: "tag<reviewed-MH-h>",
    TAG_MHM: "tag<reviewed-MH-m>",
    TAG_MH: "tag<reviewed-MH>",
    TAG_WSE: "tag<reviewed-WS-e>",
    TAG_WSM: "tag<reviewed-WS-m>",
    TAG_WS: "tag<reviewed-WS>",
    "tag_": "tag<reviewed>",
    ALTSONG2: "val<Agelaius tricolor/Alternative Song 2>",
    ALTSONG1: "val<Agelaius tricolor/Alternative Song>",
    MALE_SONG: "val<Agelaius tricolor/Common Song>",
    COURT_SONG: "val<Agelaius tricolor/Courtship Song>",
    SIMPLE_CALL2: "val<Agelaius tricolor/Simple Call 2>",
    "val<sp11/Simple Call>": "val<sp11/Simple Call>",
    "val<sp22/Simple Call>": "val<sp22/Simple Call>",
}

START = "start"
END = "end"

# Graph names
GRAPH_MANUAL = "Manual Analysis"
GRAPH_MINIMAN = "MiniMan"
GRAPH_EDGE = "Edge Analysis"
GRAPH_PM = "Pattern Matching Analysis"

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


PHASE_MALE_CHORUS = legacy.PHASE_MALE_CHORUS
PHASE_INC = legacy.PHASE_INC
PHASE_BROOD = legacy.PHASE_BROOD
PHASE_FLDG = legacy.PHASE_FLDG

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

# Columns in all.csv
PULSE_COUNT = "pulse_count"
ABANDONED = "abandon"
PULSES = ["p1", "p2", "p3", "p4"]
SUMMARY_FIRST_REC = "First Recording"
SUMMARY_LAST_REC = "Last Recording"
SUMMARY_EDGE_DATES = [SUMMARY_FIRST_REC, SUMMARY_LAST_REC]
PULSE_MC_START = "mcstart"
PULSE_MC_END = "mcend"
PULSE_INC_START = "incstart"
PULSE_HATCH = "hatch"
PULSE_FIRST_FLDG = "fledgestart"
PULSE_LAST_FLDG = "fledgedisp"
PULSE_DATE_TYPES = [
    PULSE_MC_START,
    PULSE_MC_END,
    PULSE_INC_START,
    PULSE_HATCH,
    PULSE_FIRST_FLDG,
    PULSE_LAST_FLDG,
    ABANDONED,
]
SUMMARY_NUMERIC_COLS = ["Site ID", "Altitude", "Number of Recordings"]

# Potential values in all.csv 
CONTINUOUS = "continuous"
ND_STRING = "ND"
