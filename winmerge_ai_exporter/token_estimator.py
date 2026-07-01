"""
token_estimator.py — Token count and cost estimation for LLM API calls.

MIT License - Original Author: Claude (Anthropic)
Copyright (c) 2024-2025. See LICENSE file for details.

Estimates token usage and API costs based on:
- Diff content size
- GPT-4o pricing model (roughly 4 chars per token)
- Optional filtering (whitespace, comments)

Uses heuristic: ~3.5 characters per token for code (vs 4 for general text).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .diff_parser import FileDiff

CHARS_PER_TOKEN_CODE = 3.5
CHARS_PER_TOKEN_PROSE = 4.0

# Rough pricing reference (GPT-4o as of 2024, input tokens)
COST_PER_1K_TOKENS_INPUT = 0.005   # USD


@dataclass
class TokenEstimate:
    total_chars: int
    estimated_tokens: int
    breakdown: dict[str, int]  # filename -> token count
    estimated_cost_usd: float

    def summary(self) -> str:
        lines = [
            f"Estimated tokens : {self.estimated_tokens:,}",
            f"Estimated cost   : ${self.estimated_cost_usd:.4f} (GPT-4o input ref)",
            "",
            "Top files by token count:",
        ]
        top = sorted(self.breakdown.items(), key=lambda x: x[1], reverse=True)[:10]
        for path, tok in top:
            lines.append(f"  {tok:>6,}  {path}")
        return "\n".join(lines)


def estimate_tokens_for_text(text: str, is_code: bool = True) -> int:
    chars = len(text)
    divisor = CHARS_PER_TOKEN_CODE if is_code else CHARS_PER_TOKEN_PROSE
    return max(1, int(chars / divisor))


def estimate_for_diffs(
    file_diffs: list["FileDiff"],
    skip_whitespace: bool = True,
    skip_comments: bool = True,
) -> TokenEstimate:
    breakdown: dict[str, int] = {}
    total_chars = 0

    for fd in file_diffs:
        if fd.is_identical() or fd.binary:
            continue
        hunks = fd.meaningful_hunks(
            skip_whitespace=skip_whitespace,
            skip_comments=skip_comments,
        )
        if not hunks:
            continue
        text = "\n".join("\n".join(h.lines) for h in hunks)
        chars = len(text)
        total_chars += chars
        breakdown[fd.path] = estimate_tokens_for_text(text, is_code=True)

    total_tokens = sum(breakdown.values())
    cost = (total_tokens / 1000) * COST_PER_1K_TOKENS_INPUT

    return TokenEstimate(
        total_chars=total_chars,
        estimated_tokens=total_tokens,
        breakdown=breakdown,
        estimated_cost_usd=cost,
    )
