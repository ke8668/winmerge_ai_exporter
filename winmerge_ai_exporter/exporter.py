"""
exporter.py
Generates the full /ai_review/ output package from a list of FileDiff objects.
"""

from __future__ import annotations

import json
import textwrap
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from .arch_analyzer import ArchAnalysis, analyze
from .diff_parser import FileDiff, extract_modified_symbols
from .risk_scorer import RiskResult, score_file
from .token_estimator import TokenEstimate, estimate_for_diffs

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _md_table_row(*cells: str) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def _md_table_header(*headers: str) -> str:
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    return _md_table_row(*headers) + "\n" + sep


# ---------------------------------------------------------------------------
# Per-file diff markdown
# ---------------------------------------------------------------------------

def _render_diff_md(
    fd: FileDiff,
    risk: RiskResult,
    symbols: list[str],
    context_lines: int = 30,
    skip_whitespace: bool = True,
    skip_comments: bool = True,
) -> str:
    hunks = fd.meaningful_hunks(
        skip_whitespace=skip_whitespace,
        skip_comments=skip_comments,
    )

    lines = [
        f"# `{fd.path}`",
        "",
        f"**Risk:** {risk.emoji} {risk.level}  |  "
        f"**+{fd.total_added}** / **-{fd.total_deleted}** LOC  |  "
        f"**Hunks:** {len(hunks)}",
        "",
    ]

    if symbols:
        lines += [
            "**Modified symbols:** " + ", ".join(f"`{s}`" for s in symbols[:20]),
            "",
        ]

    if risk.reasons:
        lines += [
            "**Risk reasons:**",
            *[f"- {r}" for r in risk.reasons],
            "",
        ]

    if not hunks:
        lines += ["*No meaningful changes after filtering.*", ""]
        return "\n".join(lines)

    lines += ["## Diff", ""]

    for hunk in hunks:
        header = hunk.lines[0] if hunk.lines else ""
        lines.append(f"```diff")
        # Truncate context: emit up to context_lines context lines per side
        ctx_budget = context_lines
        for line in hunk.lines:
            if line.startswith(" "):  # context line
                if ctx_budget <= 0:
                    if line == hunk.lines[-1]:
                        pass
                    else:
                        continue
                else:
                    ctx_budget -= 1
            else:
                ctx_budget = context_lines  # reset after a change
            lines.append(line)
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# summary.md
# ---------------------------------------------------------------------------

def _render_summary(
    file_diffs: list[FileDiff],
    risks: dict[str, RiskResult],
    symbols_map: dict[str, list[str]],
    token_est: TokenEstimate | None,
    meta: dict,
) -> str:
    total_added = sum(fd.total_added for fd in file_diffs)
    total_deleted = sum(fd.total_deleted for fd in file_diffs)
    changed = [fd for fd in file_diffs if not fd.is_identical() and not fd.binary]
    binary = [fd for fd in file_diffs if fd.binary]

    risk_counts = {"High": 0, "Med": 0, "Low": 0}
    for r in risks.values():
        risk_counts[r.level] = risk_counts.get(r.level, 0) + 1

    lines = [
        "# AI Review — Summary",
        "",
        f"> Generated: {_now()}",
        f"> Source: {meta.get('source', 'unknown')}",
        "",
        "## Overview",
        "",
        f"| Metric | Value |",
        f"| --- | --- |",
        f"| Changed files | {len(changed)} |",
        f"| Binary files  | {len(binary)} |",
        f"| Lines added   | +{total_added} |",
        f"| Lines deleted | -{total_deleted} |",
        f"| 🔴 High risk  | {risk_counts['High']} |",
        f"| 🟡 Med risk   | {risk_counts['Med']} |",
        f"| 🟢 Low risk   | {risk_counts['Low']} |",
    ]

    if token_est:
        lines += [
            f"| Est. tokens   | {token_est.estimated_tokens:,} |",
            f"| Est. cost     | ${token_est.estimated_cost_usd:.4f} (GPT-4o ref) |",
        ]

    lines += [
        "",
        "## Changed Files",
        "",
        _md_table_header("File", "+LOC", "-LOC", "Hunks", "Symbols", "Risk"),
    ]

    for fd in sorted(changed, key=lambda f: risks[f.path].score, reverse=True):
        r = risks[fd.path]
        syms = symbols_map.get(fd.path, [])
        sym_str = ", ".join(f"`{s}`" for s in syms[:5])
        if len(syms) > 5:
            sym_str += f" +{len(syms)-5} more"
        lines.append(_md_table_row(
            f"`{fd.path}`",
            f"+{fd.total_added}",
            f"-{fd.total_deleted}",
            str(len(fd.hunks)),
            sym_str or "—",
            f"{r.emoji} {r.level}",
        ))

    if binary:
        lines += ["", "### Binary Files", ""]
        for fd in binary:
            lines.append(f"- `{fd.path}`")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# architecture_changes.md
# ---------------------------------------------------------------------------

def _render_arch(arch: ArchAnalysis, file_diffs: list[FileDiff]) -> str:
    def section(title: str, items: list[str], empty_msg: str = "None detected.") -> list[str]:
        out = [f"## {title}", ""]
        if items:
            out += [f"- {i}" for i in items]
        else:
            out.append(f"*{empty_msg}*")
        out.append("")
        return out

    lines = [
        "# Architecture Changes",
        "",
        f"> Generated: {_now()}",
        "",
        f"**Affected subsystems:** {', '.join(f'`{s}`' for s in arch.affected_subsystems) or 'N/A'}",
        "",
    ]

    lines += section("New Components / Classes", arch.new_components)
    lines += section("Removed Components / Classes", arch.removed_components)
    lines += section("API / Interface Changes", arch.api_changes[:30],
                     "No explicit API changes detected in diff headers.")
    lines += section("Module Dependency Changes", arch.dependency_changes[:30])
    lines += section("Potential Side Effects", arch.potential_side_effects)
    lines += section("Concurrency / Threading Risks", arch.concurrency_risks)
    lines += section("Memory Management Risks", arch.memory_risks)

    lines += [
        "## Notes",
        "",
        "This analysis is heuristic-based. Verify each item manually.",
        "Focus attention on High-risk files listed in `summary.md`.",
        "",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# review_prompt.txt
# ---------------------------------------------------------------------------

_REVIEW_PROMPT_TEMPLATE = """\
You are a senior software architect conducting a thorough code review.
Below are code diffs exported from WinMerge for architecture analysis.

Please analyze these changes and provide:

1. **Executive Summary** — What changed at a high level and what is the overall risk?

2. **Architecture Differences** — How has the system design changed?
   - New components, removed components, restructured modules
   - Interface/API contract changes
   - Dependency changes (new or removed)

3. **Behavioral Changes** — What does the system *do* differently now?
   - Control flow changes
   - State management changes
   - Error handling changes

4. **Regression Risks** — What existing functionality might break?
   - Callers of removed/changed APIs
   - Assumptions that may no longer hold
   - Integration points affected

5. **Hidden Side Effects** — What non-obvious consequences might these changes have?
   - Performance implications
   - Security surface changes
   - Resource usage changes

6. **API Contract Changes** — Are any public contracts violated?
   - Breaking vs. additive changes
   - Versioning considerations

7. **Concurrency & Memory Risks** — Any thread-safety or memory safety concerns?
   - New shared state
   - Locking changes
   - Memory allocation/deallocation patterns

8. **Recommended Test Cases** — What should be tested to validate these changes?
   - Unit tests
   - Integration tests
   - Edge cases

Please be specific and reference file names and function names where relevant.
Flag anything that requires immediate attention before merging.

---

{diff_content}
"""


def _render_prompt(
    file_diffs: list[FileDiff],
    risks: dict[str, RiskResult],
    symbols_map: dict[str, list[str]],
    skip_whitespace: bool = True,
    skip_comments: bool = True,
) -> str:
    parts = []

    # Only include meaningful diffs sorted by risk
    changed = [fd for fd in file_diffs if not fd.is_identical() and not fd.binary]
    changed.sort(key=lambda f: risks[f.path].score, reverse=True)

    for fd in changed:
        hunks = fd.meaningful_hunks(skip_whitespace=skip_whitespace, skip_comments=skip_comments)
        if not hunks:
            continue
        r = risks[fd.path]
        syms = symbols_map.get(fd.path, [])
        header = (
            f"### FILE: {fd.path}\n"
            f"Risk: {r.level} | +{fd.total_added}/-{fd.total_deleted} LOC"
        )
        if syms:
            header += f"\nModified symbols: {', '.join(syms[:10])}"
        hunk_text = "\n".join("\n".join(h.lines) for h in hunks)
        parts.append(f"{header}\n\n```diff\n{hunk_text}\n```")

    diff_content = "\n\n---\n\n".join(parts) if parts else "(No meaningful diffs found)"
    return _REVIEW_PROMPT_TEMPLATE.format(diff_content=diff_content)


# ---------------------------------------------------------------------------
# changed_files.txt
# ---------------------------------------------------------------------------

def _render_changed_files(file_diffs: list[FileDiff], risks: dict[str, RiskResult]) -> str:
    lines = ["# Changed Files", ""]
    for fd in sorted(file_diffs, key=lambda f: f.path):
        if fd.is_identical():
            continue
        r = risks.get(fd.path)
        risk_str = f"[{r.level}]" if r else ""
        status = "BINARY" if fd.binary else f"+{fd.total_added}/-{fd.total_deleted}"
        lines.append(f"{risk_str:<8} {status:<16} {fd.path}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------

def _render_json(
    file_diffs: list[FileDiff],
    risks: dict[str, RiskResult],
    symbols_map: dict[str, list[str]],
    arch: ArchAnalysis,
    token_est: TokenEstimate | None,
) -> str:
    files = []
    for fd in file_diffs:
        if fd.is_identical():
            continue
        r = risks.get(fd.path, RiskResult("Low", 0, []))
        files.append({
            "path": fd.path,
            "added": fd.total_added,
            "deleted": fd.total_deleted,
            "hunks": len(fd.hunks),
            "binary": fd.binary,
            "risk_level": r.level,
            "risk_score": r.score,
            "risk_reasons": r.reasons,
            "modified_symbols": symbols_map.get(fd.path, []),
        })

    data = {
        "generated_at": _now(),
        "files": files,
        "architecture": {
            "new_components": arch.new_components,
            "removed_components": arch.removed_components,
            "api_changes": arch.api_changes[:30],
            "dependency_changes": arch.dependency_changes[:30],
            "affected_subsystems": arch.affected_subsystems,
            "potential_side_effects": arch.potential_side_effects,
            "concurrency_risks": arch.concurrency_risks,
            "memory_risks": arch.memory_risks,
        },
        "token_estimate": {
            "total_tokens": token_est.estimated_tokens if token_est else None,
            "estimated_cost_usd": token_est.estimated_cost_usd if token_est else None,
        },
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main export function
# ---------------------------------------------------------------------------

def export_ai_review_package(
    file_diffs: list[FileDiff],
    output_dir: str | Path,
    source_label: str = "WinMerge comparison",
    context_lines: int = 30,
    skip_whitespace: bool = True,
    skip_comments: bool = True,
    include_json: bool = True,
) -> Path:
    """
    Generate the full /ai_review/ package.
    Returns the output directory path.
    """
    out = Path(output_dir) / "ai_review"
    out.mkdir(parents=True, exist_ok=True)
    (out / "diffs").mkdir(exist_ok=True)
    (out / "prompts").mkdir(exist_ok=True)

    # Filter meaningful diffs
    changed = [fd for fd in file_diffs if not fd.is_identical()]

    # --- Compute per-file metadata ---
    risks: dict[str, RiskResult] = {}
    symbols_map: dict[str, list[str]] = {}
    for fd in changed:
        risks[fd.path] = score_file(fd)
        symbols_map[fd.path] = extract_modified_symbols(fd)

    # --- Architecture analysis ---
    arch = analyze(changed)

    # --- Token estimation ---
    token_est = estimate_for_diffs(
        changed,
        skip_whitespace=skip_whitespace,
        skip_comments=skip_comments,
    )

    meta = {"source": source_label}

    # --- summary.md ---
    (out / "summary.md").write_text(
        _render_summary(changed, risks, symbols_map, token_est, meta),
        encoding="utf-8",
    )

    # --- changed_files.txt ---
    (out / "changed_files.txt").write_text(
        _render_changed_files(changed, risks),
        encoding="utf-8",
    )

    # --- architecture_changes.md ---
    (out / "architecture_changes.md").write_text(
        _render_arch(arch, changed),
        encoding="utf-8",
    )

    # --- prompts/review_prompt.txt ---
    (out / "prompts" / "review_prompt.txt").write_text(
        _render_prompt(changed, risks, symbols_map, skip_whitespace, skip_comments),
        encoding="utf-8",
    )

    # --- diffs/xxx.diff.md ---
    for fd in changed:
        if fd.binary:
            continue
        r = risks[fd.path]
        syms = symbols_map.get(fd.path, [])
        safe_name = fd.path.replace("/", "_").replace("\\", "_").replace(":", "_")
        diff_md = _render_diff_md(
            fd, r, syms,
            context_lines=context_lines,
            skip_whitespace=skip_whitespace,
            skip_comments=skip_comments,
        )
        (out / "diffs" / f"{safe_name}.diff.md").write_text(diff_md, encoding="utf-8")

    # --- JSON export ---
    if include_json:
        (out / "review_data.json").write_text(
            _render_json(changed, risks, symbols_map, arch, token_est),
            encoding="utf-8",
        )

    return out
