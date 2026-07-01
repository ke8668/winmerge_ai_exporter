"""
diff_parser.py — Parse unified diff format into structured format.

MIT License - Original Author: Claude (Anthropic)
Copyright (c) 2024-2025. See LICENSE file for details.

Parses unified diff files (from WinMerge or git) into FileDiff and Hunk objects.
Handles extraction of modified symbols and function-level analysis.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Hunk:
    """One contiguous changed region inside a file diff."""
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[str] = field(default_factory=list)

    @property
    def added(self) -> int:
        return sum(1 for l in self.lines if l.startswith("+") and not l.startswith("+++"))

    @property
    def deleted(self) -> int:
        return sum(1 for l in self.lines if l.startswith("-") and not l.startswith("---"))

    def is_whitespace_only(self) -> bool:
        changed = [l for l in self.lines
                   if (l.startswith("+") and not l.startswith("+++"))
                   or (l.startswith("-") and not l.startswith("---"))]
        if not changed:
            return False
        # Two lines differ only in whitespace if stripping them gives same content
        added   = [l[1:].rstrip() for l in changed if l.startswith("+")]
        removed = [l[1:].rstrip() for l in changed if l.startswith("-")]
        # If every changed token is empty after stripping, it's whitespace-only
        all_empty = all(l.strip() == "" for l in changed)
        # If added and removed content are identical modulo whitespace
        same_tokens = (sorted(a.split() for a in added) ==
                       sorted(r.split() for r in removed))
        return all_empty or same_tokens

    def is_comment_only(self, ext: str) -> bool:
        """Heuristic: changed lines are only comment lines."""
        changed = [l[1:].strip() for l in self.lines
                   if (l.startswith("+") and not l.startswith("+++"))
                   or (l.startswith("-") and not l.startswith("---"))]
        if not changed:
            return False
        comment_patterns = _comment_patterns(ext)
        return all(any(re.match(p, c) for p in comment_patterns) or c == ""
                   for c in changed)


@dataclass
class FileDiff:
    """All hunks for one file."""
    old_path: str
    new_path: str
    hunks: list[Hunk] = field(default_factory=list)
    binary: bool = False

    @property
    def path(self) -> str:
        """Canonical path (prefer new_path)."""
        p = self.new_path if self.new_path != "/dev/null" else self.old_path
        return p.removeprefix("b/").removeprefix("a/")

    @property
    def extension(self) -> str:
        return Path(self.path).suffix.lower().lstrip(".")

    @property
    def total_added(self) -> int:
        return sum(h.added for h in self.hunks)

    @property
    def total_deleted(self) -> int:
        return sum(h.deleted for h in self.hunks)

    def is_identical(self) -> bool:
        return not self.hunks and not self.binary

    def meaningful_hunks(self, skip_whitespace: bool = True, skip_comments: bool = True) -> list[Hunk]:
        result = []
        for h in self.hunks:
            if skip_whitespace and h.is_whitespace_only():
                continue
            if skip_comments and h.is_comment_only(self.extension):
                continue
            result.append(h)
        return result


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

_HUNK_HEADER = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@"
)


def parse_unified_diff(text: str) -> list[FileDiff]:
    """Parse a unified diff string and return a list of FileDiff objects."""
    diffs: list[FileDiff] = []
    current: FileDiff | None = None
    current_hunk: Hunk | None = None

    for raw_line in text.splitlines(keepends=False):
        # --- file header ---
        if raw_line.startswith("--- "):
            if current_hunk and current:
                current.hunks.append(current_hunk)
                current_hunk = None
            old_path = raw_line[4:].split("\t")[0]
            current = FileDiff(old_path=old_path, new_path="")
            diffs.append(current)
            continue

        if raw_line.startswith("+++ ") and current is not None:
            current.new_path = raw_line[4:].split("\t")[0]
            continue

        if raw_line.startswith("Binary files") and current is not None:
            current.binary = True
            continue

        if current is None:
            continue

        # --- hunk header ---
        m = _HUNK_HEADER.match(raw_line)
        if m:
            if current_hunk:
                current.hunks.append(current_hunk)
            os, oc, ns, nc = m.groups()
            current_hunk = Hunk(
                old_start=int(os),
                old_count=int(oc) if oc is not None else 1,
                new_start=int(ns),
                new_count=int(nc) if nc is not None else 1,
            )
            current_hunk.lines.append(raw_line)
            continue

        # --- diff content ---
        if current_hunk is not None:
            current_hunk.lines.append(raw_line)

    # flush last hunk
    if current_hunk and current:
        current.hunks.append(current_hunk)

    return diffs


def parse_diff_file(path: str | Path) -> list[FileDiff]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    return parse_unified_diff(text)


# ---------------------------------------------------------------------------
# Function/class extraction helpers
# ---------------------------------------------------------------------------

# Language → list of (pattern, name_group_index) to detect function/class boundaries
_FUNC_PATTERNS: dict[str, list[re.Pattern]] = {
    "cpp": [
        re.compile(r"^[\w\*&:<>,\s]+\s+(\w+)\s*\([^)]*\)\s*(?:const|override|noexcept|final)?\s*\{?\s*$"),
        re.compile(r"^class\s+(\w+)"),
        re.compile(r"^struct\s+(\w+)"),
        re.compile(r"^namespace\s+(\w+)"),
    ],
    "c": [
        re.compile(r"^[\w\*\s]+\s+(\w+)\s*\([^)]*\)\s*\{?\s*$"),
        re.compile(r"^struct\s+(\w+)"),
    ],
    "cs": [
        re.compile(r"^\s*(?:public|private|protected|internal|static|virtual|override|async)[\w\s<>\[\]]*\s+(\w+)\s*\("),
        re.compile(r"^\s*(?:public|private|internal|sealed|abstract)?\s*class\s+(\w+)"),
        re.compile(r"^\s*interface\s+(\w+)"),
        re.compile(r"^\s*(?:public|private)?\s*(?:static)?\s*(?:readonly)?\s*(?:event)\s+\S+\s+(\w+)"),
    ],
    "py": [
        re.compile(r"^(?:async\s+)?def\s+(\w+)\s*\("),
        re.compile(r"^class\s+(\w+)"),
    ],
    "java": [
        re.compile(r"^\s*(?:public|private|protected|static|final|native|synchronized|abstract|transient)*\s+[\w<>\[\]]+\s+(\w+)\s*\("),
        re.compile(r"^\s*(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)"),
        re.compile(r"^\s*interface\s+(\w+)"),
    ],
    "js": [
        re.compile(r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))"),
        re.compile(r"^\s*class\s+(\w+)"),
        re.compile(r"^\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{"),
    ],
    "ts": [
        re.compile(r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))"),
        re.compile(r"^\s*class\s+(\w+)"),
        re.compile(r"^\s*interface\s+(\w+)"),
        re.compile(r"^\s*(?:export\s+)?(?:async\s+)?(\w+)\s*\([^)]*\)"),
    ],
}

# Aliases
_FUNC_PATTERNS["h"] = _FUNC_PATTERNS["cpp"]
_FUNC_PATTERNS["cxx"] = _FUNC_PATTERNS["cpp"]
_FUNC_PATTERNS["cc"] = _FUNC_PATTERNS["cpp"]
_FUNC_PATTERNS["tsx"] = _FUNC_PATTERNS["ts"]
_FUNC_PATTERNS["jsx"] = _FUNC_PATTERNS["js"]


def _comment_patterns(ext: str) -> list[str]:
    if ext in ("py",):
        return [r"^#", r'^"""', r"^'''"]
    return [r"^//", r"^/\*", r"^\*", r"^<!--"]


def extract_modified_symbols(file_diff: FileDiff, source_text: str | None = None) -> list[str]:
    """
    Attempt to identify which function/class names appear in or near each hunk.
    Returns a deduplicated list of symbol names.
    """
    ext = file_diff.extension
    patterns = _FUNC_PATTERNS.get(ext, [])
    if not patterns:
        return []

    symbols: list[str] = []
    seen: set[str] = set()

    for hunk in file_diff.meaningful_hunks():
        for line in hunk.lines:
            stripped = line.lstrip("+-@ ")
            for pat in patterns:
                m = pat.search(stripped)
                if m:
                    name = next((g for g in m.groups() if g), None)
                    if name and name not in seen:
                        seen.add(name)
                        symbols.append(name)
    return symbols
