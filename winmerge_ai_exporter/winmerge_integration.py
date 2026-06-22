"""
winmerge_integration.py
Bridges WinMerge's output formats to our internal FileDiff model.

WinMerge can export:
  1. Unified diff / patch files  (File → Create Patch)
  2. XML folder compare reports  (Tools → Generate Report)

This module handles both.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from .diff_parser import FileDiff, Hunk, parse_unified_diff


# ---------------------------------------------------------------------------
# 1. Unified diff import (standard path)
# ---------------------------------------------------------------------------

def load_from_patch_file(patch_path: str | Path) -> list[FileDiff]:
    """Parse a .patch/.diff file produced by WinMerge (or git)."""
    text = Path(patch_path).read_text(encoding="utf-8", errors="replace")
    return parse_unified_diff(text)


def load_from_patch_text(text: str) -> list[FileDiff]:
    """Parse unified diff text directly."""
    return parse_unified_diff(text)


# ---------------------------------------------------------------------------
# 2. WinMerge XML folder report
# ---------------------------------------------------------------------------

_XML_STATUS_MAP = {
    "identical": None,        # skip
    "different": "different",
    "leftonly": "left_only",
    "rightonly": "right_only",
    "binarydiffer": "binary_different",
    "error": "error",
}

def load_from_winmerge_xml_report(xml_path: str | Path) -> list[FileDiff]:
    """
    Parse a WinMerge folder compare XML report (Tools → Generate Report).
    Produces FileDiff stubs for each non-identical file.
    Note: XML reports don't contain diff content, so hunks will be empty;
    only metadata is captured.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    diffs: list[FileDiff] = []

    # WinMerge XML structure: <report><paths/><folder><item .../></folder></report>
    for item in root.iter("item"):
        left_file = item.get("leftfile", "")
        right_file = item.get("rightfile", "")
        status = item.get("status", "").lower()

        mapped = _XML_STATUS_MAP.get(status)
        if mapped is None:
            continue  # identical

        fd = FileDiff(
            old_path=left_file,
            new_path=right_file,
            binary=(mapped == "binary_different"),
        )

        # Try to synthesise a minimal hunk with LOC info if available
        left_lines = _try_int(item.get("leftlines", ""))
        right_lines = _try_int(item.get("rightlines", ""))
        if left_lines is not None or right_lines is not None:
            # Create a placeholder hunk so totals show up in summaries
            h = Hunk(
                old_start=1, old_count=left_lines or 0,
                new_start=1, new_count=right_lines or 0,
            )
            # Add synthetic +/- markers for LOC counting
            if right_lines:
                h.lines += [f"+[{right_lines} lines in new file]"]
            if left_lines:
                h.lines += [f"-[{left_lines} lines in old file]"]
            fd.hunks.append(h)

        diffs.append(fd)

    return diffs


def _try_int(s: str) -> int | None:
    try:
        return int(s)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# 3. Generate diff by calling external diff (for folder compare)
# ---------------------------------------------------------------------------

def generate_diff_between_folders(
    left_dir: str | Path,
    right_dir: str | Path,
    exclude_patterns: list[str] | None = None,
) -> list[FileDiff]:
    """
    Use the system `diff` command to compare two folders recursively.
    Falls back gracefully if diff is not available.
    """
    left = Path(left_dir)
    right = Path(right_dir)

    exclude_args = []
    for pat in (exclude_patterns or []):
        exclude_args += ["--exclude", pat]

    cmd = ["diff", "-ruN", "--unified=5"] + exclude_args + [str(left), str(right)]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        # diff returns 0=identical, 1=differences, 2=error
        if result.returncode == 2:
            raise RuntimeError(f"diff error: {result.stderr}")
        return parse_unified_diff(result.stdout)
    except FileNotFoundError:
        raise RuntimeError(
            "System 'diff' command not found. "
            "Install diffutils (MSYS2/Git Bash on Windows) or use WinMerge's patch export."
        )


# ---------------------------------------------------------------------------
# 4. WinMerge plugin script interface
# ---------------------------------------------------------------------------

WINMERGE_PLUGIN_SCRIPT = r"""
; WinMerge Plugin Configuration
; Place this file in WinMerge\Plugins\ directory
; 
; This plugin integrates the AI Review Exporter into WinMerge's Tools menu.
; 
; Usage: After comparing files/folders, use Tools → Export AI Review Package

[PluginInfo]
Name=AI Review Exporter
Description=Export diffs as an AI-ready review package
Version=1.0.0
Author=WinMerge AI Exporter

[Scripts]
ExportPackage=python "%%PLUGIN_DIR%%\ai_exporter\cli.py" export --output "%%TEMP%%\ai_review" --source "%%LEFT%%" --target "%%RIGHT%%"
CopyPrompt=python "%%PLUGIN_DIR%%\ai_exporter\cli.py" copy-prompt --source "%%LEFT%%" --target "%%RIGHT%%"
EstimateTokens=python "%%PLUGIN_DIR%%\ai_exporter\cli.py" estimate --source "%%LEFT%%" --target "%%RIGHT%%"
"""


def generate_winmerge_ini_plugin(output_path: str | Path) -> None:
    """Write a WinMerge plugin .ini stub to disk."""
    Path(output_path).write_text(WINMERGE_PLUGIN_SCRIPT, encoding="utf-8")
