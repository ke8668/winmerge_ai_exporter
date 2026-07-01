"""
risk_scorer.py — Risk assessment for code changes.

MIT License - Original Author: Claude (Anthropic)
Copyright (c) 2024-2025. See LICENSE file for details.

Scores files based on:
- Modification location (auth, security, etc.)
- Dangerous functions (eval, pickle, etc.)
- File type sensitivity (.sql, .sh, etc.)

Risk levels: Low / Med / High
"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .diff_parser import FileDiff


# ---------------------------------------------------------------------------
# Risk signals
# ---------------------------------------------------------------------------

_HIGH_RISK_PATH_PATTERNS = [
    re.compile(r"auth", re.I),
    re.compile(r"security", re.I),
    re.compile(r"crypto", re.I),
    re.compile(r"login", re.I),
    re.compile(r"payment", re.I),
    re.compile(r"database|db_", re.I),
    re.compile(r"migration", re.I),
    re.compile(r"schema", re.I),
    re.compile(r"api[/_]", re.I),
    re.compile(r"core[/_]", re.I),
    re.compile(r"config", re.I),
    re.compile(r"middleware", re.I),
]

_HIGH_RISK_CONTENT_PATTERNS = [
    re.compile(r"\bmemcpy\b|\bmemmove\b|\bstrcpy\b|\bsprintf\b"),  # unsafe C
    re.compile(r"\beval\s*\("),           # eval
    re.compile(r"\bexec\s*\("),           # shell exec
    re.compile(r"\bos\.system\b"),
    re.compile(r"\bsubprocess\b"),
    re.compile(r"\bpickle\.loads?\b"),
    re.compile(r"\bunsafe\b", re.I),
    re.compile(r"TODO.*(security|vuln|hack|fixme)", re.I),
    re.compile(r"\bdelete\s+\[\]|\bfree\s*\("),  # memory management
    re.compile(r"\bnew\s+\w+\s*\["),
    re.compile(r"\bvirtual\b.*\bdestructor\b|\bvirtual\s+~"),
]

_MED_RISK_PATH_PATTERNS = [
    re.compile(r"service", re.I),
    re.compile(r"controller", re.I),
    re.compile(r"handler", re.I),
    re.compile(r"router", re.I),
    re.compile(r"model", re.I),
    re.compile(r"interface", re.I),
    re.compile(r"abstract", re.I),
    re.compile(r"base[/_]", re.I),
    re.compile(r"manager", re.I),
    re.compile(r"factory", re.I),
]

_MED_RISK_CONTENT_PATTERNS = [
    re.compile(r"\bthrow\b|\braise\b"),
    re.compile(r"\basync\b|\bawait\b"),
    re.compile(r"\bthread\b|\bmutex\b|\block\b", re.I),
    re.compile(r"\bpublic\b.*\binterface\b|\bpublic\s+API\b", re.I),
    re.compile(r"\boverride\b|\bvirtual\b"),
    re.compile(r"\bimport\s+\*|\busing\s+namespace\b"),
]


@dataclass
class RiskResult:
    level: str          # "Low" | "Med" | "High"
    score: int
    reasons: list[str]

    @property
    def emoji(self) -> str:
        return {"Low": "🟢", "Med": "🟡", "High": "🔴"}.get(self.level, "⚪")


def score_file(file_diff: "FileDiff") -> RiskResult:
    score = 0
    reasons: list[str] = []

    path = file_diff.path.lower()
    ext = file_diff.extension
    loc_delta = file_diff.total_added + file_diff.total_deleted

    # --- Size signals ---
    if loc_delta > 300:
        score += 3
        reasons.append(f"Large change ({loc_delta} LOC modified)")
    elif loc_delta > 100:
        score += 1
        reasons.append(f"Moderate change ({loc_delta} LOC modified)")

    # --- Many hunks = scattered changes ---
    if len(file_diff.hunks) > 10:
        score += 2
        reasons.append(f"Scattered changes ({len(file_diff.hunks)} hunks)")
    elif len(file_diff.hunks) > 5:
        score += 1

    # --- Path-based signals ---
    for pat in _HIGH_RISK_PATH_PATTERNS:
        if pat.search(path):
            score += 4
            reasons.append(f"High-risk path segment: '{pat.pattern}'")
            break

    for pat in _MED_RISK_PATH_PATTERNS:
        if pat.search(path):
            score += 2
            reasons.append(f"Risk-elevated path: '{pat.pattern}'")
            break

    # --- Content-based signals ---
    changed_lines = []
    for hunk in file_diff.hunks:
        for line in hunk.lines:
            if line.startswith("+") and not line.startswith("+++"):
                changed_lines.append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                changed_lines.append(line[1:])

    combined = "\n".join(changed_lines)

    for pat in _HIGH_RISK_CONTENT_PATTERNS:
        if pat.search(combined):
            score += 3
            reasons.append(f"Dangerous pattern: `{pat.pattern}`")
            break

    for pat in _MED_RISK_CONTENT_PATTERNS:
        if pat.search(combined):
            score += 1

    # --- Binary ---
    if file_diff.binary:
        score += 2
        reasons.append("Binary file changed")

    # --- Extension signals ---
    if ext in ("sql", "sh", "bat", "ps1", "cmd"):
        score += 3
        reasons.append(f"Sensitive file type: .{ext}")

    # --- Classify ---
    if score >= 4:
        level = "High"
    elif score >= 2:
        level = "Med"
    else:
        level = "Low"

    if not reasons:
        reasons.append("No specific risk signals detected")

    return RiskResult(level=level, score=score, reasons=reasons)
