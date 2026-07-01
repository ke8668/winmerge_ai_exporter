"""
WinMerge AI Review Exporter

A Python tool for exporting WinMerge diffs as AI-ready architecture review packages.
Supports multi-mode redaction (FULL, API-Safe, API-Safe+Comments, SIGNATURE) for 
selective pseudonymization.

MIT License - Original Author: Claude (Anthropic)
Copyright (c) 2024-2025. See LICENSE file for details.

Features:
  - Export diffs from WinMerge, patch files, or folder comparisons
  - Risk scoring and architecture analysis
  - Token estimation for LLM cost planning
  - Stripped Patch mode: preserve APIs while redacting internals
  - Pure-Python diff generation (zero external dependencies)
  - GUI (Tkinter) and CLI interfaces

Quickstart:
    from winmerge_ai_exporter import export_ai_review_package, load_from_patch_file

    diffs = load_from_patch_file("my_changes.patch")
    out_dir = export_ai_review_package(diffs, output_dir="./review_output")

Example Usage:
    from winmerge_ai_exporter import export_ai_review_package, RedactionMode
    
    export_ai_review_package(
        diffs,
        output_dir="./review",
        strip_patch=True,
        redaction_mode=RedactionMode.API_SAFE
    )
"""

from .diff_parser import parse_unified_diff, parse_diff_file, FileDiff, Hunk
from .exporter import export_ai_review_package
from .risk_scorer import score_file, RiskResult
from .token_estimator import estimate_for_diffs, TokenEstimate
from .arch_analyzer import analyze, ArchAnalysis
from .redactor import StripOptions, strip_file_diff, strip_hunk, RedactionMode
from .winmerge_integration import (
    load_from_patch_file,
    load_from_patch_text,
    load_from_winmerge_xml_report,
    generate_diff_between_folders,
    generate_diff_between_files,
)

__version__ = "1.1.0"
__all__ = [
    "parse_unified_diff",
    "parse_diff_file",
    "FileDiff",
    "Hunk",
    "export_ai_review_package",
    "score_file",
    "RiskResult",
    "estimate_for_diffs",
    "TokenEstimate",
    "analyze",
    "ArchAnalysis",
    "StripOptions",
    "strip_file_diff",
    "strip_hunk",
    "RedactionMode",
    "load_from_patch_file",
    "load_from_patch_text",
    "load_from_winmerge_xml_report",
    "generate_diff_between_folders",
    "generate_diff_between_files",
]
