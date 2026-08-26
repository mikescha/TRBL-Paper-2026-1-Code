from __future__ import annotations

import operator as op
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Paths and related
DATA_DIR = PROJECT_ROOT / "data"
INPUT_CSV_NAME = "TRBL Analysis tracking - All.csv"
INPUT_CSV = DATA_DIR / INPUT_CSV_NAME
PMJ_DIR_NAME = "pmj_data"
PMJ_DIR = DATA_DIR / PMJ_DIR_NAME
FIGURE_DIR = PROJECT_ROOT / "figures"
ERROR_FILE = PROJECT_ROOT / "outputs" / "grapher_errors.txt"
HOURLY_PARQUET_FILES = DATA_DIR / "recordings_per_day_hour.parquet"
SHARING_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "sharing"
# SHARING_OUTPUT_DIR = Path(r"G:\My Drive\TRBL for Wendy GDrive")
ALL_SHEET_HEADER_SIZE = 2  # number of rows to skip over in the All file

# Columns
DATE_COL = "date"
DATETIME_COL = "dt"
SITE = "site"
SITE_COLS = {
    "id": "id",
    "recording": "recording",
    SITE: "site",
    "day": "day",
    "month": "month",
    "year": "year",
    "hour": "hour",
    "minute": "minute",
    "species": "species",
    "songtype": "songtype",
    "x1": "x1",
    "x2": "x2",
    "y1": "y1",
    "y2": "y2",
    "frequency": "frequency",
    "validated": "validated",
    "url": "url",
    "score": "score",
    "site_id": "site_id",
}

TAG_WSE = "tag_edge"
TAG_WSM = "tag_wsm"
TAG_MHE = "tag_mhe"
TAG_MHM = "tag_mhm"
TAG_MHH = "tag_mhh"
TAG_WS = "tag_ws"
TAG_MH = "tag_mh"
TAG_ = "tag_"
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

FILENAME = "filename"
HOUR = "hour"
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
    TAG_: "tag<reviewed>",
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

PM_SONG_TYPES = [
    "Male Song",
    "Male Chorus",
    "Female",
    "Hatchling",
    "Nestling",
    "Fledgling",
]
PM_FILE_TYPES = PM_SONG_TYPES

EDGE_N_TAGS = [
    TAG_P1N,
    TAG_P2N,
    TAG_P3N,
    TAG_P4N,
]  # nestlings, p1 = pulse 1, p2 = pulse 2
EDGE_YNC_TAGS = [TAG_YNC_P2, TAG_YNC_P3, TAG_YNC_P4]
EDGE_TAGS = EDGE_N_TAGS + EDGE_YNC_TAGS
EDGE_COLS = [DATA_COL[t] for t in EDGE_N_TAGS]

MINI_MANUAL_TAGS = [TAG_MHH, TAG_MHM, TAG_WSM]
MINI_MANUAL_COLS = [DATA_COL[t] for t in MINI_MANUAL_TAGS]

MANUAL_TAGS = [TAG_MH, TAG_WS, TAG_]
MANUAL_COLS = [DATA_COL[t] for t in MANUAL_TAGS]

TAG_MAP = {  # map of tag_pXn to ync tag
    DATA_COL[TAG_P1N]: DATA_COL[ALTSONG1],
    DATA_COL[TAG_P2N]: DATA_COL[TAG_YNC_P2],
    DATA_COL[TAG_P3N]: DATA_COL[TAG_YNC_P3],
    DATA_COL[TAG_P4N]: DATA_COL[TAG_YNC_P4],
}
ALL_TAGS = MANUAL_TAGS + MINI_MANUAL_TAGS + EDGE_TAGS

MALE_SONG = "malesong"
ALTSONG1 = "altsong1"
ALTSONG2 = "altsong2"
COURT_SONG = "courtsong"
SIMPLE_CALL2 = "simplecall2"
ALL_SONGS = [MALE_SONG, COURT_SONG, ALTSONG2, ALTSONG1, SIMPLE_CALL2]

SONGS = [MALE_SONG, COURT_SONG, ALTSONG2, ALTSONG1]
SONG_COLS = [DATA_COL[s] for s in SONGS]

PHASE_MALE_CHORUS = "Settlement"
PHASE_INC = "Incubation"
PHASE_BROOD = "Brooding"
PHASE_FLDG = "Fledgling"

ABANDONED = "abandon"
VALIDATED_STR = "validated"

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
MISSED = "missed"

# Color maps
# default color map
CMAP = {
    DATA_COL[MALE_SONG]: "Greens",
    DATA_COL[COURT_SONG]: "Oranges",
    DATA_COL[ALTSONG2]: "Purples",
    DATA_COL[ALTSONG1]: "Blues",
    "Fledgling": "Blues",
}

CMAP_PM = {
    "Male Song": "Greens",
    "Male Chorus": "Oranges",
    "Female": "Purples",
    "Hatchling": "Blues",
    "Nestling": "Blues",
    "Fledgling": "Blues",
}

DPI = 300

GRAPH_FONT = "Franklin Gothic Book"
GRAPH_FONT_TTF = "FRABK.TTF"  # used for output to the file using PIL

ALIGN_DATES = False
