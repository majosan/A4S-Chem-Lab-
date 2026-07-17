"""
analyze.py — Main entry point for tactile glove sensor data analysis.

Usage::

    python analyze.py <data_dir> [--sample <A|B>] [--output <output_dir>]

*data_dir* is a folder containing all exported JSON files from one test session.
The script auto-discovers which test files are present, runs the corresponding
analysis modules, and writes a self-contained HTML report to *output_dir*.

Missing test data causes the relevant module to be skipped (status = N/A)
rather than raising an error.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from report import ReportBuilder, build_report

# ---------------------------------------------------------------------------
# Module imports — each module exposes a single run() function
# ---------------------------------------------------------------------------
import module1_baseline
import module2_response_curve
import module3_repeatability
import module4_cross_point
import module5_grasp
import module6_flex_interference


# ---------------------------------------------------------------------------
# File-discovery helpers
# ---------------------------------------------------------------------------

def find_baseline_files(data_dir: Path, sample_id: str) -> list[Path]:
    """Return baseline JSON files for the given sample in *data_dir*.

    Parameters
    ----------
    data_dir:
        Root data directory.
    sample_id:
        Glove sample identifier (e.g. ``"A"``).

    Returns
    -------
    list[Path]
        Matching files; empty list if none found.
    """
    raise NotImplementedError


def find_singlepoint_files(data_dir: Path, sample_id: str) -> list[Path]:
    """Return single-point response-curve JSON files for *sample_id*.

    Parameters
    ----------
    data_dir:
        Root data directory.
    sample_id:
        Glove sample identifier.

    Returns
    -------
    list[Path]
    """
    raise NotImplementedError


def find_grasp_files(data_dir: Path, sample_id: str) -> dict[str, Path]:
    """Return a mapping of object name → JSON path for grasp tests.

    Parameters
    ----------
    data_dir:
        Root data directory.
    sample_id:
        Glove sample identifier.

    Returns
    -------
    dict[str, Path]
        Keys: ``"bottle"``, ``"beaker"``, ``"tube"`` (present keys only).
    """
    raise NotImplementedError


def find_flex_files(data_dir: Path, sample_id: str) -> list[Path]:
    """Return flex-interference JSON files for *sample_id*.

    Parameters
    ----------
    data_dir:
        Root data directory.
    sample_id:
        Glove sample identifier.

    Returns
    -------
    list[Path]
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_all(data_dir: str | Path,
            sample_id: str = "A",
            output_dir: str | Path = "output") -> None:
    """Discover test files, run all applicable modules, and write the HTML report.

    Parameters
    ----------
    data_dir:
        Directory containing all exported test JSON files.
    sample_id:
        Glove sample identifier (``"A"`` or ``"B"``).
    output_dir:
        Directory for charts and the final report HTML.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tactile glove sensor data analysis — run all modules and "
                    "produce an HTML report.",
    )
    parser.add_argument(
        "data_dir",
        type=Path,
        help="Directory containing exported test JSON files.",
    )
    parser.add_argument(
        "--sample",
        default="A",
        metavar="ID",
        help="Glove sample identifier (default: A).",
    )
    parser.add_argument(
        "--output",
        default="output",
        type=Path,
        metavar="DIR",
        help="Output directory for charts and report (default: output/).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    args = _parse_args(argv)
    run_all(
        data_dir=args.data_dir,
        sample_id=args.sample,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
