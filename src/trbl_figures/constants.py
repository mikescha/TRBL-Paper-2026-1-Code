from __future__ import annotations

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

# Graph names
GRAPH_PM = legacy.GRAPH_PM
GRAPH_MINIMAN = legacy.GRAPH_MINIMAN
GRAPH_MANUAL = legacy.GRAPH_MANUAL
GRAPH_EDGE = legacy.GRAPH_EDGE

# PM / manual / edge constants
PM_FILE_TYPES = legacy.PM_FILE_TYPES
SONG_COLS = legacy.SONG_COLS
EDGE_COLS = legacy.EDGE_COLS

MALE_SONG = legacy.MALE_SONG
ALTSONG1 = legacy.ALTSONG1
ALTSONG2 = legacy.ALTSONG2
DATA_COL = legacy.data_col
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
