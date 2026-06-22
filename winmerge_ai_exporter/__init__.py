"""
winmerge_ai_exporter
====================
Export WinMerge diffs as an AI-ready architecture review package.

Quickstart:
    from winmerge_ai_exporter import export_ai_review_package, load_from_patch_file

    diffs = load_from_patch_file("my_changes.patch")
    out_dir = export_ai_review_package(diffs, output_dir="./review_output")
"""

from .diff_parser import parse_unified_diff, parse_diff_file, FileDiff, Hunk
from .exporter import export_ai_review_package
from .risk_scorer import score_file, RiskResult
from .token_estimator import estimate_for_diffs, TokenEstimate
from .arch_analyzer import analyze, ArchAnalysis
from .winmerge_integration import (
    load_from_patch_file,
    load_from_patch_text,
    load_from_winmerge_xml_report,
    generate_diff_between_folders,
)

__version__ = "1.0.0"
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
    "load_from_patch_file",
    "load_from_patch_text",
    "load_from_winmerge_xml_report",
    "generate_diff_between_folders",
]
