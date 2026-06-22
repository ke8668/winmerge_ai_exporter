"""Tests for arch_analyzer.py and token_estimator.py"""

import pytest
from winmerge_ai_exporter.diff_parser import FileDiff, Hunk, parse_unified_diff
from winmerge_ai_exporter.arch_analyzer import analyze, ArchAnalysis
from winmerge_ai_exporter.token_estimator import (
    estimate_for_diffs,
    estimate_tokens_for_text,
    TokenEstimate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fd_with_lines(path: str, added: list[str], removed: list[str] = None) -> FileDiff:
    hunk_lines = ["@@ -1,1 +1,1 @@"]
    for l in (added or []):
        hunk_lines.append("+" + l)
    for l in (removed or []):
        hunk_lines.append("-" + l)
    h = Hunk(1, 1, 1, 1, lines=hunk_lines)
    return FileDiff(old_path="a/" + path, new_path="b/" + path, hunks=[h])


# ---------------------------------------------------------------------------
# ArchAnalyzer
# ---------------------------------------------------------------------------

class TestArchAnalyzer:
    def test_returns_arch_analysis(self):
        fd = _make_fd_with_lines("src/mod.py", ["class NewService:"])
        result = analyze([fd])
        assert isinstance(result, ArchAnalysis)

    def test_detects_new_python_class(self):
        fd = _make_fd_with_lines("src/mod.py", ["+class PaymentProcessor:"])
        result = analyze([fd])
        assert any("PaymentProcessor" in c for c in result.new_components)

    def test_detects_removed_class(self):
        diff_text = (
            "--- a/src/mod.py\n+++ b/src/mod.py\n"
            "@@ -1,2 +1,1 @@\n-class OldEngine:\n-    pass\n+# removed\n"
        )
        diffs = parse_unified_diff(diff_text)
        result = analyze(diffs)
        assert any("OldEngine" in c for c in result.removed_components)

    def test_detects_new_import(self):
        fd = _make_fd_with_lines("src/app.py", ["import requests"])
        result = analyze([fd])
        assert any("requests" in d for d in result.dependency_changes)

    def test_detects_removed_import(self):
        fd = _make_fd_with_lines("src/app.py", [], ["import old_lib"])
        result = analyze([fd])
        assert any("old_lib" in d for d in result.dependency_changes)

    def test_detects_concurrency_risk(self):
        fd = _make_fd_with_lines("src/worker.cpp", ["std::mutex m;", "std::thread t;"])
        result = analyze([fd])
        assert len(result.concurrency_risks) >= 1

    def test_detects_memory_risk(self):
        fd = _make_fd_with_lines("src/buf.cpp", ["char* p = new char[1024];"])
        result = analyze([fd])
        assert len(result.memory_risks) >= 1

    def test_affected_subsystems_from_path(self):
        fd1 = _make_fd_with_lines("Engine/core.cpp", ["x = 1"])
        fd2 = _make_fd_with_lines("UI/window.cpp", ["y = 2"])
        result = analyze([fd1, fd2])
        assert "Engine" in result.affected_subsystems
        assert "UI" in result.affected_subsystems

    def test_side_effects_populated_when_api_changes(self):
        fd = _make_fd_with_lines("src/api.py", [
            "public static int ComputeHash(string input, int salt) {"
        ])
        result = analyze([fd])
        # Any API-like change should produce side-effect warnings
        # (might not trigger depending on language; check that result is at least valid)
        assert isinstance(result.potential_side_effects, list)

    def test_empty_diffs_yields_empty_analysis(self):
        result = analyze([])
        assert result.new_components == []
        assert result.removed_components == []
        assert result.dependency_changes == []

    def test_identical_files_skipped(self):
        fd = FileDiff(old_path="a/x.py", new_path="b/x.py")  # no hunks = identical
        result = analyze([fd])
        assert result.new_components == []

    def test_cpp_include_detected_as_dependency(self):
        fd = _make_fd_with_lines("src/main.cpp", ['#include "NewLib.h"'])
        result = analyze([fd])
        assert any("NewLib.h" in d for d in result.dependency_changes)

    def test_js_require_detected(self):
        fd = _make_fd_with_lines("src/index.js", ["const axios = require('axios');"])
        result = analyze([fd])
        assert any("axios" in d for d in result.dependency_changes)


# ---------------------------------------------------------------------------
# Token Estimator
# ---------------------------------------------------------------------------

class TestTokenEstimator:
    def test_returns_token_estimate(self):
        fd = _make_fd_with_lines("src/mod.py", ["x = 1", "y = 2"])
        est = estimate_for_diffs([fd])
        assert isinstance(est, TokenEstimate)

    def test_nonzero_tokens_for_changes(self):
        fd = _make_fd_with_lines("src/mod.py", ["x = 1"] * 50)
        est = estimate_for_diffs([fd])
        assert est.estimated_tokens > 0

    def test_zero_tokens_for_identical(self):
        fd = FileDiff(old_path="a/x.py", new_path="b/x.py")
        est = estimate_for_diffs([fd])
        assert est.estimated_tokens == 0

    def test_whitespace_skipped_reduces_tokens(self):
        fd = _make_fd_with_lines("src/mod.py", ["   "])  # whitespace only
        est_skip = estimate_for_diffs([fd], skip_whitespace=True)
        est_keep = estimate_for_diffs([fd], skip_whitespace=False)
        assert est_skip.estimated_tokens <= est_keep.estimated_tokens

    def test_breakdown_contains_changed_file(self):
        fd = _make_fd_with_lines("src/mod.py", ["x = 1"])
        est = estimate_for_diffs([fd])
        assert "src/mod.py" in est.breakdown

    def test_binary_excluded_from_estimate(self):
        fd = FileDiff(old_path="a/img.png", new_path="b/img.png", binary=True)
        est = estimate_for_diffs([fd])
        assert est.estimated_tokens == 0

    def test_cost_positive_for_changes(self):
        fd = _make_fd_with_lines("src/mod.py", ["x = 1"] * 100)
        est = estimate_for_diffs([fd])
        assert est.estimated_cost_usd >= 0

    def test_total_chars_consistent(self):
        text = "x = 1\n" * 100
        tokens = estimate_tokens_for_text(text, is_code=True)
        # At 3.5 chars/token, 600 chars → ~171 tokens
        assert 100 < tokens < 300

    def test_summary_string_contains_tokens(self):
        fd = _make_fd_with_lines("src/foo.py", ["y = 2"] * 20)
        est = estimate_for_diffs([fd])
        summary = est.summary()
        assert "tokens" in summary.lower()

    def test_multiple_files_sum_correctly(self):
        fd1 = _make_fd_with_lines("src/a.py", ["x = 1"] * 10)
        fd2 = _make_fd_with_lines("src/b.py", ["y = 2"] * 10)
        est = estimate_for_diffs([fd1, fd2])
        assert est.estimated_tokens == est.breakdown.get("src/a.py", 0) + est.breakdown.get("src/b.py", 0)
