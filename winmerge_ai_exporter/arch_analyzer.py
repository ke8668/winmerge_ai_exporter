"""
arch_analyzer.py
Infers architecture-level changes from the set of FileDiffs.
Produces structured data for architecture_changes.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .diff_parser import FileDiff


# ---------------------------------------------------------------------------
# Detectors
# ---------------------------------------------------------------------------

_API_SIGNALS = [
    re.compile(r"\bpublic\s+(?:static\s+)?(?:abstract\s+)?[\w<>\[\]]+\s+(\w+)\s*\(", re.M),
    re.compile(r"^\s*def\s+([\w]+)\s*\(self", re.M),
    re.compile(r"^\s*export\s+(?:default\s+)?(?:function|class|const)\s+(\w+)", re.M),
    re.compile(r"^\s*module\.exports", re.M),
    re.compile(r"\[HttpGet\]|\[HttpPost\]|\[HttpPut\]|\[HttpDelete\]|\[Route\(", re.M),
    re.compile(r"@(GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)", re.M),
    re.compile(r"app\.(get|post|put|delete|patch)\s*\(", re.M),
]

_IMPORT_PATTERNS = [
    re.compile(r"^#include\s+[<\"](.+?)[>\"]", re.M),
    re.compile(r"^\s*import\s+(\S+)", re.M),
    re.compile(r"^\s*from\s+(\S+)\s+import", re.M),
    re.compile(r"^\s*using\s+([\w.]+)\s*;", re.M),
    re.compile(r"""require\s*\(\s*['"](.+?)['"]\s*\)""", re.M),
    re.compile(r"""import\s+.*?\s+from\s+['"](.+?)['"]""", re.M),
]

_NEW_CLASS_PATTERNS = [
    re.compile(r"^\+\s*(?:public\s+)?class\s+(\w+)", re.M),
    re.compile(r"^\+\s*(?:export\s+)?class\s+(\w+)", re.M),
    re.compile(r"^\+class\s+(\w+)", re.M),
    re.compile(r"^\+\s*interface\s+(\w+)", re.M),
    re.compile(r"^\+\s*(?:abstract\s+)?class\s+(\w+)", re.M),
    # Also catch when added_text already has the + stripped (added_text pass)
    re.compile(r"^class\s+(\w+)", re.M),
    re.compile(r"^(?:export\s+)?(?:abstract\s+)?class\s+(\w+)", re.M),
    re.compile(r"^interface\s+(\w+)", re.M),
]

_DEL_CLASS_PATTERNS = [
    re.compile(r"^-\s*(?:public\s+)?class\s+(\w+)", re.M),
    re.compile(r"^-\s*(?:export\s+)?class\s+(\w+)", re.M),
    re.compile(r"^-class\s+(\w+)", re.M),
    re.compile(r"^-\s*interface\s+(\w+)", re.M),
]

_CONCURRENCY_PATTERNS = [
    re.compile(r"\bmutex\b|\block\b|\bsemaphore\b|\batomic\b", re.I),
    re.compile(r"\bthread\b|\bworker\b|\basync\b|\bawait\b|\bTask\b|\bFuture\b"),
    re.compile(r"\bstd::thread\b|\bpthread\b|\bQThread\b"),
    re.compile(r"\bCriticalSection\b|\bInterlockedExchange\b"),
]

_MEMORY_PATTERNS = [
    re.compile(r"\bnew\s+\w+\[|\bdelete\s*\[\]"),
    re.compile(r"\bmalloc\b|\bfree\b|\bcalloc\b|\brealloc\b"),
    re.compile(r"\bshared_ptr\b|\bunique_ptr\b|\bweak_ptr\b"),
    re.compile(r"\bmemcpy\b|\bmemmove\b|\bmemset\b"),
]


@dataclass
class ArchAnalysis:
    new_components: list[str] = field(default_factory=list)
    removed_components: list[str] = field(default_factory=list)
    api_changes: list[str] = field(default_factory=list)
    dependency_changes: list[str] = field(default_factory=list)
    affected_subsystems: list[str] = field(default_factory=list)
    potential_side_effects: list[str] = field(default_factory=list)
    concurrency_risks: list[str] = field(default_factory=list)
    memory_risks: list[str] = field(default_factory=list)


def _diff_text(file_diff: "FileDiff") -> tuple[str, str]:
    """Return (added_text, removed_text) from all hunks."""
    added, removed = [], []
    for hunk in file_diff.hunks:
        for line in hunk.lines:
            if line.startswith("+") and not line.startswith("+++"):
                added.append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                removed.append(line[1:])
    return "\n".join(added), "\n".join(removed)


def _extract_imports(text: str) -> set[str]:
    results = set()
    for pat in _IMPORT_PATTERNS:
        for m in pat.finditer(text):
            results.add(m.group(1).strip())
    return results


def _subsystem_from_path(path: str) -> str:
    """Map a file path to a subsystem label."""
    parts = path.replace("\\", "/").split("/")
    # Use first meaningful directory
    skip = {"src", "lib", "include", "source", "app", ".", ""}
    for p in parts[:-1]:  # skip filename
        if p.lower() not in skip:
            return p
    return parts[0] if parts else "root"


def analyze(file_diffs: list["FileDiff"]) -> ArchAnalysis:
    result = ArchAnalysis()
    seen_new: set[str] = set()
    seen_del: set[str] = set()
    api_seen: set[str] = set()
    subsystems: set[str] = set()
    old_imports_all: set[str] = set()
    new_imports_all: set[str] = set()

    for fd in file_diffs:
        if fd.is_identical() or fd.binary:
            continue

        added_text, removed_text = _diff_text(fd)
        subsystems.add(_subsystem_from_path(fd.path))

        # --- New / removed classes ---
        hunk_text = "\n".join(
            "\n".join(h.lines) for h in fd.hunks
        )

        for pat in _NEW_CLASS_PATTERNS:
            for search_text in (hunk_text, added_text):
                for m in pat.finditer(search_text):
                    name = m.group(1)
                    if name not in seen_new:
                        seen_new.add(name)
                        result.new_components.append(f"`{name}` in `{fd.path}`")

        for pat in _DEL_CLASS_PATTERNS:
            for m in pat.finditer(hunk_text):
                name = m.group(1)
                if name not in seen_del:
                    seen_del.add(name)
                    result.removed_components.append(f"`{name}` from `{fd.path}`")

        # --- API changes ---
        for pat in _API_SIGNALS:
            for m in pat.finditer(added_text):
                sig = m.group(0).strip()[:80]
                if sig not in api_seen:
                    api_seen.add(sig)
                    result.api_changes.append(f"Added in `{fd.path}`: `{sig}`")
            for m in pat.finditer(removed_text):
                sig = m.group(0).strip()[:80]
                sig_key = "DEL:" + sig
                if sig_key not in api_seen:
                    api_seen.add(sig_key)
                    result.api_changes.append(f"Removed from `{fd.path}`: `{sig}`")

        # --- Imports ---
        old_imports_all |= _extract_imports(removed_text)
        new_imports_all |= _extract_imports(added_text)

        # --- Concurrency ---
        for pat in _CONCURRENCY_PATTERNS:
            if pat.search(added_text):
                result.concurrency_risks.append(
                    f"`{fd.path}` introduces concurrency primitives"
                )
                break

        # --- Memory ---
        for pat in _MEMORY_PATTERNS:
            if pat.search(added_text):
                result.memory_risks.append(
                    f"`{fd.path}` has new direct memory operations"
                )
                break

    # --- Dependency changes ---
    added_deps = new_imports_all - old_imports_all
    removed_deps = old_imports_all - new_imports_all
    for dep in sorted(added_deps)[:20]:
        result.dependency_changes.append(f"New dependency: `{dep}`")
    for dep in sorted(removed_deps)[:20]:
        result.dependency_changes.append(f"Removed dependency: `{dep}`")

    # --- Affected subsystems ---
    result.affected_subsystems = sorted(subsystems)

    # --- Side effects (heuristics) ---
    if result.removed_components:
        result.potential_side_effects.append(
            "Removed components may break existing callers/consumers."
        )
    if result.api_changes:
        result.potential_side_effects.append(
            "Public API surface changed — verify backward compatibility."
        )
    if added_deps:
        result.potential_side_effects.append(
            f"{len(added_deps)} new dependencies introduced — check for conflicts."
        )
    if result.concurrency_risks:
        result.potential_side_effects.append(
            "New concurrency code increases risk of race conditions or deadlocks."
        )
    if result.memory_risks:
        result.potential_side_effects.append(
            "Direct memory management changes may introduce leaks or UB."
        )

    return result
