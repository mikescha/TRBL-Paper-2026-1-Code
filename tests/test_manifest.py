from __future__ import annotations

from pathlib import Path

import pytest

from trbl_figures.manifest import filter_manifest, read_manifest


def write_manifest(tmp_path: Path, text: str) -> Path:
    """Write a temporary manifest CSV and return its path."""
    manifest_path = tmp_path / "manifest.csv"
    manifest_path.write_text(text, encoding="utf-8")
    return manifest_path


def test_read_manifest_preserves_site_id_and_site_name(tmp_path: Path) -> None:
    manifest_path = write_manifest(
        tmp_path,
        "\n".join(
            [
                "site_id,site_name,manual,mini_manual,edge,pattern_matching,include_composite,include_key",
                "2059,2017 Rush Ranch,,,,,1,1",
                "3150,2018 Iron Point,,,,,1,1",
            ]
        ),
    )

    df = read_manifest(manifest_path)

    assert list(df["site_id"]) == ["2059", "3150"]
    assert list(df["site_name"]) == ["2017 Rush Ranch", "2018 Iron Point"]


def test_read_manifest_rejects_extra_commas_that_shift_columns(tmp_path: Path) -> None:
    manifest_path = write_manifest(
        tmp_path,
        "\n".join(
            [
                "site_id,site_name,manual,mini_manual,edge,pattern_matching,include_composite,include_key",
                # This row has one too many empty fields between site_name and include_composite.
                # It caused pandas to shift site_name into site_id during refactoring.
                "2059,2017 Rush Ranch,,,,,,,1,1",
            ]
        ),
    )

    with pytest.raises(ValueError):
        read_manifest(manifest_path)


def test_filter_manifest_matches_site_id(tmp_path: Path) -> None:
    manifest_path = write_manifest(
        tmp_path,
        "\n".join(
            [
                "site_id,site_name,manual,mini_manual,edge,pattern_matching,include_composite,include_key",
                "2059,2017 Rush Ranch,,,,,1,1",
                "3150,2018 Iron Point,,,,,1,1",
            ]
        ),
    )

    df = read_manifest(manifest_path)
    filtered = filter_manifest(df, only_sites=["2059"], limit=None)

    assert len(filtered) == 1
    assert filtered.iloc[0]["site_id"] == "2059"
    assert filtered.iloc[0]["site_name"] == "2017 Rush Ranch"


def test_filter_manifest_matches_site_name(tmp_path: Path) -> None:
    manifest_path = write_manifest(
        tmp_path,
        "\n".join(
            [
                "site_id,site_name,manual,mini_manual,edge,pattern_matching,include_composite,include_key",
                "2059,2017 Rush Ranch,,,,,1,1",
                "3150,2018 Iron Point,,,,,1,1",
            ]
        ),
    )

    df = read_manifest(manifest_path)
    filtered = filter_manifest(df, only_sites=["2018 Iron Point"], limit=None)

    assert len(filtered) == 1
    assert filtered.iloc[0]["site_id"] == "3150"
    assert filtered.iloc[0]["site_name"] == "2018 Iron Point"


def test_filter_manifest_limit_must_be_positive(tmp_path: Path) -> None:
    manifest_path = write_manifest(
        tmp_path,
        "\n".join(
            [
                "site_id,site_name,manual,mini_manual,edge,pattern_matching,include_composite,include_key",
                "2059,2017 Rush Ranch,,,,,1,1",
            ]
        ),
    )

    df = read_manifest(manifest_path)

    with pytest.raises(ValueError):
        filter_manifest(df, only_sites=None, limit=0)


def test_filter_manifest_applies_limit(tmp_path: Path) -> None:
    manifest_path = write_manifest(
        tmp_path,
        "\n".join(
            [
                "site_id,site_name,manual,mini_manual,edge,pattern_matching,include_composite,include_key",
                "2059,2017 Rush Ranch,,,,,1,1",
                "3150,2018 Iron Point,,,,,1,1",
                "3348,2018 Markham Ravine Main,,,,,1,1",
            ]
        ),
    )

    df = read_manifest(manifest_path)
    filtered = filter_manifest(df, only_sites=None, limit=2)

    assert len(filtered) == 2
    assert list(filtered["site_id"]) == ["2059", "3150"]
