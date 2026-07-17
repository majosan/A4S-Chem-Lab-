"""
report.py — HTML report generation module for tactile glove analysis.

Builds a self-contained HTML page that includes:
  1. A summary table of pass/warn/fail judgements for every test module
  2. Per-module sections with embedded charts (base64 PNG) and data tables
  3. An overall verdict: "data usable for VLA training" or not

Usage::

    from report import ReportBuilder
    builder = ReportBuilder(output_dir="analysis/output")
    builder.add_module_result(...)   # repeat for each module
    builder.write("analysis/output/report.html")
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

# Status literals used throughout the reporting pipeline
StatusType = Literal["pass", "warn", "fail", "na"]

# Emoji badges shown in the HTML summary table
STATUS_BADGE: dict[StatusType, str] = {
    "pass": "🟢",
    "warn": "⚠️",
    "fail": "🔴",
    "na": "—",
}


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class ModuleResult:
    """Container for the analysis result of one test module.

    Attributes
    ----------
    module_id:
        Short identifier, e.g. ``"1.1"``, ``"1.2"``, ``"3.5"``.
    module_name:
        Human-readable name, e.g. ``"基线稳定性"``.
    status:
        Overall judgement for this module.
    summary_text:
        One- or two-sentence plain-text summary shown in the report table.
    detail_html:
        Raw HTML fragment for the detailed section (charts, tables, etc.).
        ``None`` if the module was skipped (status == ``"na"``).
    metrics:
        Dict of key metric names → values, shown as a sub-table.
    chart_paths:
        Paths to PNG files that will be embedded in the detail section.
    """
    module_id: str
    module_name: str
    status: StatusType
    summary_text: str = ""
    detail_html: Optional[str] = None
    metrics: dict[str, str | float | int] = field(default_factory=dict)
    chart_paths: list[Path] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------

class ReportBuilder:
    """Incrementally collect module results and render to HTML.

    Parameters
    ----------
    output_dir:
        Directory where charts and the final report are written.
    sample_id:
        Glove sample identifier (e.g. ``"A"`` or ``"B"``).
    test_date:
        ISO date string for the report header.
    """

    def __init__(self,
                 output_dir: str | Path = "analysis/output",
                 sample_id: str = "",
                 test_date: str = "") -> None:
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_module_result(self, result: ModuleResult) -> None:
        """Append a completed module result to the report.

        Parameters
        ----------
        result:
            Populated :class:`ModuleResult` instance.
        """
        raise NotImplementedError

    def set_overall_verdict(self, verdict: StatusType, reason: str) -> None:
        """Set the top-level pass/fail verdict shown at the top of the report.

        Parameters
        ----------
        verdict:
            Overall judgement.
        reason:
            Short explanation displayed prominently in the report header.
        """
        raise NotImplementedError

    def write(self, path: str | Path) -> None:
        """Render all collected results to a self-contained HTML file.

        The file embeds all chart images as base64 data-URIs so it can be
        opened offline without a web server.

        Parameters
        ----------
        path:
            Destination ``.html`` file path.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Internal helpers (private)
    # ------------------------------------------------------------------

    def _render_summary_table(self) -> str:
        """Return HTML for the summary table listing all module statuses.

        Returns
        -------
        str
            ``<table>…</table>`` HTML fragment.
        """
        raise NotImplementedError

    def _render_module_section(self, result: ModuleResult) -> str:
        """Return HTML for one module's detailed section.

        Parameters
        ----------
        result:
            The module whose detail section is rendered.

        Returns
        -------
        str
            HTML fragment.
        """
        raise NotImplementedError

    def _embed_image(self, path: str | Path) -> str:
        """Read a PNG/JPEG and return an ``<img src="data:…">`` tag.

        Parameters
        ----------
        path:
            Path to the image file.

        Returns
        -------
        str
            HTML ``<img>`` element with base64-encoded data URI.
        """
        raise NotImplementedError

    def _compute_overall_verdict(self) -> tuple[StatusType, str]:
        """Derive the overall verdict from individual module results.

        Returns
        -------
        tuple[StatusType, str]
            ``(verdict, reason_text)``
        """
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def build_report(module_results: list[ModuleResult],
                 output_path: str | Path,
                 sample_id: str = "",
                 test_date: str = "") -> None:
    """One-shot function to build and write a complete HTML report.

    Parameters
    ----------
    module_results:
        List of :class:`ModuleResult` objects in display order.
    output_path:
        Destination ``.html`` file.
    sample_id:
        Glove sample identifier for the report header.
    test_date:
        Test date string for the report header.
    """
    raise NotImplementedError
