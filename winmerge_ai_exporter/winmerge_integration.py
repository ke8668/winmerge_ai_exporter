"""
winmerge_integration.py — WinMerge integration and folder comparison utilities.

MIT License - Original Author: Claude (Anthropic)
Copyright (c) 2024-2025. See LICENSE file for details.

Provides:
- Patch file loading (unified diff format)
- Folder comparison (pure Python, no external diff)
- XML report parsing from WinMerge
- Multi-language support (C/C++/Python/Java/etc.)

WinMerge can export:
  1. Unified diff / patch files  (File → Create Patch)
  2. XML folder compare reports  (Tools → Generate Report)

This module handles both.
"""

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
# 3. Generate diff using pure Python (no external tools required)
# ---------------------------------------------------------------------------

def generate_diff_between_folders(
    left_dir: str | Path,
    right_dir: str | Path,
    exclude_patterns: list[str] | None = None,
) -> list[FileDiff]:
    """
    Compare two folders recursively using Python's built-in difflib.
    No external 'diff' binary is required — this works on a stock
    Windows Python install with no extra software.
    """
    if not str(left_dir).strip():
        raise RuntimeError("Left folder path is empty. Please select a folder.")
    if not str(right_dir).strip():
        raise RuntimeError("Right folder path is empty. Please select a folder.")

    left = Path(left_dir)
    right = Path(right_dir)

    if not left.exists():
        raise RuntimeError(f"Left folder does not exist:\n{left}")
    if not right.exists():
        raise RuntimeError(f"Right folder does not exist:\n{right}")
    if not left.is_dir():
        raise RuntimeError(f"Left path is not a folder:\n{left}")
    if not right.is_dir():
        raise RuntimeError(f"Right path is not a folder:\n{right}")

    return _python_diff_folders(left, right, exclude_patterns or [])


def generate_diff_between_files(
    left_file: str | Path,
    right_file: str | Path,
) -> list[FileDiff]:
    """
    Compare two individual files using Python's built-in difflib.
    No external 'diff' binary is required.
    """
    if not str(left_file).strip():
        raise RuntimeError("Left file path is empty. Please select a file.")
    if not str(right_file).strip():
        raise RuntimeError("Right file path is empty. Please select a file.")

    left = Path(left_file)
    right = Path(right_file)

    if not left.exists():
        raise RuntimeError(f"Left file does not exist:\n{left}")
    if not right.exists():
        raise RuntimeError(f"Right file does not exist:\n{right}")
    if left.is_dir() or right.is_dir():
        raise RuntimeError(
            "Both paths must be files, not folders. "
            "Use 'Compare Folders' mode for directory comparison."
        )

    return _python_diff_single_pair(left, right, left.name, right.name)


_TEXT_EXTS = {
    "c", "cpp", "cxx", "cc", "h", "hpp", "hxx",
    "cs", "py", "java", "js", "ts", "jsx", "tsx",
    "txt", "md", "json", "xml", "yaml", "yml",
    "cmake", "mk", "makefile", "bat", "sh", "ps1",
    "cfg", "ini", "toml", "gitignore",
}


def _is_text_file(path: Path) -> bool:
    ext = path.suffix.lower().lstrip(".")
    if ext in _TEXT_EXTS:
        return True
    try:
        path.read_bytes()[:512].decode("utf-8")
        return True
    except Exception:
        return False


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    except Exception:
        return []


def _python_diff_single_pair(
    left: Path,
    right: Path,
    display_left: str,
    display_right: str,
) -> list[FileDiff]:
    """Diff exactly one (left, right) file pair using difflib."""
    import difflib

    old_path = f"a/{display_left}"
    new_path = f"b/{display_right}"

    if not _is_text_file(left) or not _is_text_file(right):
        return [FileDiff(old_path=old_path, new_path=new_path, binary=True)]

    l_lines = _read_lines(left)
    r_lines = _read_lines(right)

    if l_lines == r_lines:
        return [FileDiff(old_path=old_path, new_path=new_path)]  # identical

    ud = list(difflib.unified_diff(
        l_lines, r_lines,
        fromfile=old_path, tofile=new_path,
        n=5,
    ))
    if not ud:
        return [FileDiff(old_path=old_path, new_path=new_path)]

    return parse_unified_diff("".join(ud))


def _python_diff_folders(
    left: Path,
    right: Path,
    exclude_patterns: list[str],
) -> list[FileDiff]:
    """Pure-Python recursive folder diff using difflib."""
    import fnmatch

    def _excluded(rel: str) -> bool:
        return any(fnmatch.fnmatch(rel, pat) for pat in exclude_patterns)

    def _collect_files(base: Path) -> dict[str, Path]:
        result = {}
        for p in base.rglob("*"):
            if p.is_file():
                rel = p.relative_to(base).as_posix()
                if not _excluded(rel):
                    result[rel] = p
        return result

    left_files  = _collect_files(left)
    right_files = _collect_files(right)
    all_keys    = sorted(set(left_files) | set(right_files))

    diffs: list[FileDiff] = []

    for rel in all_keys:
        l_path = left_files.get(rel)
        r_path = right_files.get(rel)

        old_path = f"a/{rel}" if l_path else "/dev/null"
        new_path = f"b/{rel}" if r_path else "/dev/null"

        # Binary or missing on one side
        if (l_path and not _is_text_file(l_path)) or (r_path and not _is_text_file(r_path)):
            diffs.append(FileDiff(old_path=old_path, new_path=new_path, binary=True))
            continue

        l_lines = _read_lines(l_path) if l_path else []
        r_lines = _read_lines(r_path) if r_path else []

        if l_lines == r_lines:
            continue  # identical — skip

        import difflib
        ud = list(difflib.unified_diff(
            l_lines, r_lines,
            fromfile=old_path, tofile=new_path,
            n=5,
        ))
        if not ud:
            continue

        diffs.extend(parse_unified_diff("".join(ud)))

    return diffs


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
