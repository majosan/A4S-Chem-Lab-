"""
load_data.py — Data loading module for tactile glove sensor data.

Supports two JSON formats:
  Format A (single frame): {"points": {"P1": 0, ...}, "timestamp": <ms>}
  Format B (multi-frame):  {"frames": [{"timestamp": ..., "points": {...}}, ...]}

Auto-detects format on load and normalises to a common DataFrame structure.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
FormatType = Literal["single_frame", "multi_frame"]
"""String literal identifying which JSON layout was detected."""


# ---------------------------------------------------------------------------
# Low-level parsers
# ---------------------------------------------------------------------------

def detect_format(data: dict) -> FormatType:
    """Detect whether *data* is Format A (single frame) or Format B (multi-frame).

    Parameters
    ----------
    data:
        Parsed JSON dict straight from ``json.load``.

    Returns
    -------
    FormatType
        ``"single_frame"`` if *data* has a top-level ``"points"`` key,
        ``"multi_frame"`` if it has a top-level ``"frames"`` key.

    Raises
    ------
    ValueError
        If neither key is present.
    """
    raise NotImplementedError


def parse_single_frame(data: dict) -> pd.DataFrame:
    """Parse a Format-A single-frame dict into a one-row DataFrame.

    Columns are point names (``P1`` … ``P124``), index is the timestamp.

    Parameters
    ----------
    data:
        Dict with ``"points"`` and optional ``"timestamp"`` keys.

    Returns
    -------
    pd.DataFrame
        Shape ``(1, n_points)``.  Index is the timestamp in ms (or 0 if absent).
    """
    raise NotImplementedError


def parse_multi_frame(data: dict) -> pd.DataFrame:
    """Parse a Format-B multi-frame dict into a time-indexed DataFrame.

    Parameters
    ----------
    data:
        Dict with ``"frames"`` key; each frame has ``"timestamp"`` and ``"points"``.

    Returns
    -------
    pd.DataFrame
        Shape ``(n_frames, n_points)``.  Index is timestamps in ms.
        Columns are point names sorted naturally (``P1``, ``P2``, …).
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def load_json(path: str | Path) -> tuple[pd.DataFrame, FormatType]:
    """Load a single glove-sensor JSON file, auto-detecting its format.

    Parameters
    ----------
    path:
        Filesystem path to the ``.json`` file.

    Returns
    -------
    df : pd.DataFrame
        Normalised sensor readings.  Each row is one time-frame; each column
        is one sensor point (``P1`` … ``P124``).
    fmt : FormatType
        Which format was detected (``"single_frame"`` or ``"multi_frame"``).

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    ValueError
        If the file cannot be parsed as either known format.
    """
    raise NotImplementedError


def load_directory(directory: str | Path,
                   pattern: str = "*.json") -> dict[str, tuple[pd.DataFrame, FormatType]]:
    """Load all JSON files in *directory* matching *pattern*.

    Parameters
    ----------
    directory:
        Folder to scan.
    pattern:
        Glob pattern (default ``"*.json"``).

    Returns
    -------
    dict[str, tuple[pd.DataFrame, FormatType]]
        Mapping from filename stem to ``(df, fmt)`` pairs.
        Files that fail to parse are skipped with a warning.
    """
    raise NotImplementedError


def get_point_names(df: pd.DataFrame) -> list[str]:
    """Return sorted point-name columns from *df*, excluding metadata columns.

    Parameters
    ----------
    df:
        DataFrame returned by :func:`load_json`.

    Returns
    -------
    list[str]
        Sorted list such as ``["P1", "P2", …, "P124"]``.
    """
    raise NotImplementedError


def apply_threshold(df: pd.DataFrame, threshold: float = 7.0) -> pd.DataFrame:
    """Zero-out sensor readings below *threshold* (treat as no-pressure).

    Parameters
    ----------
    df:
        Raw sensor DataFrame.
    threshold:
        Readings strictly below this value are set to ``0``.  Default ``7.0``
        per project spec.

    Returns
    -------
    pd.DataFrame
        Copy of *df* with sub-threshold values replaced by ``0``.
    """
    raise NotImplementedError


def get_timestamps_seconds(df: pd.DataFrame) -> np.ndarray:
    """Return the DataFrame's millisecond index converted to seconds from t=0.

    Parameters
    ----------
    df:
        DataFrame whose index holds timestamps in milliseconds.

    Returns
    -------
    np.ndarray
        Float array of elapsed seconds, shape ``(n_frames,)``.
    """
    raise NotImplementedError
