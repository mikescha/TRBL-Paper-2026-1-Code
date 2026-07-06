from __future__ import annotations

import argparse
import sys
from pathlib import Path

from trbl_figures.publication import build_figures

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

# Make imports work whether the script is run from VS Code, PowerShell,
# or later from a thin wrapper.
for path in [PROJECT_ROOT, SRC_DIR]:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_MANIFEST = PROJECT_ROOT / "config" / "supplemental_figures.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "figures" / "supplemental"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate TRBL paper/supplemental figures from a figure manifest."
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help=f"Path to figure manifest CSV. Default: {DEFAULT_MANIFEST}",
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Path to data directory. Default: {DEFAULT_DATA_DIR}",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for generated figures. Default: {DEFAULT_OUTPUT_DIR}",
    )

    parser.add_argument(
        "--site",
        action="append",
        default=None,
        help=(
            "Limit run to a site_id or exact site_name. "
            "Can be supplied multiple times."
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit run to the first N manifest rows after filtering.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print selected sites without generating figures.",
    )

    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop immediately on first error instead of writing an error row to the inventory.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    build_figures(
        manifest_path=args.manifest,
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        only_sites=args.site,
        limit=args.limit,
        dry_run=args.dry_run,
        stop_on_error=args.stop_on_error,
    )


if __name__ == "__main__":
    main()