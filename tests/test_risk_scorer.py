"""Tests for risk_scorer.py"""

import pytest
from winmerge_ai_exporter.diff_parser import FileDiff, Hunk
from winmerge_ai_exporter.risk_scorer import score_file, RiskResult


def _make_fd(path: str, added_lines: list[str], deleted_lines: list[str] = None) -> FileDiff:
    """Helper: build a minimal FileDiff from lists of added/deleted lines."""
    hunk_lines = ["@@ -1,1 +1,1 @@"]
    for l in (added_lines or []):
        hunk_lines.append("+" + l)
    for l in (deleted_lines or []):
        hunk_lines.append("-" + l)
    hunk = Hunk(old_start=1, old_count=1, new_start=1, new_count=1, lines=hunk_lines)
    fd = FileDiff(old_path="a/" + path, new_path="b/" + path, hunks=[hunk])
    return fd


class TestRiskScorer:
    def test_returns_risk_result(self):
        fd = _make_fd("src/utils.py", ["x = 1"])
        r = score_file(fd)
        assert isinstance(r, RiskResult)
        assert r.level in ("Low", "Med", "High")

    def test_low_risk_trivial_change(self):
        fd = _make_fd("src/utils.py", ["x = 1"])
        r = score_file(fd)
        assert r.level == "Low"

    def test_high_risk_auth_path(self):
        fd = _make_fd("src/auth/login.cpp", ["x = 1"])
        r = score_file(fd)
        assert r.level == "High"

    def test_high_risk_crypto_path(self):
        fd = _make_fd("crypto/aes.py", ["pass"])
        r = score_file(fd)
        assert r.level == "High"

    def test_high_risk_security_keyword(self):
        fd = _make_fd("core/security_check.cpp", ["bool ok = true;"])
        r = score_file(fd)
        assert r.level == "High"

    def test_high_risk_unsafe_c_function(self):
        fd = _make_fd("src/parser.c", ["memcpy(dst, src, n);"])
        r = score_file(fd)
        assert r.level in ("Med", "High")

    def test_med_risk_service_path(self):
        fd = _make_fd("src/user_service.py", ["pass"])
        r = score_file(fd)
        assert r.level in ("Med", "High")

    def test_high_risk_large_change(self):
        lines = [f"line_{i} = {i}" for i in range(350)]
        fd = _make_fd("src/module.py", lines)
        r = score_file(fd)
        assert r.level in ("Med", "High")

    def test_binary_file_elevated_risk(self):
        fd = FileDiff(old_path="a/img.bin", new_path="b/img.bin", binary=True)
        r = score_file(fd)
        assert r.score >= 2

    def test_shell_script_elevated_risk(self):
        fd = _make_fd("deploy/setup.sh", ["rm -rf /tmp/old"])
        r = score_file(fd)
        assert r.level in ("Med", "High")

    def test_reasons_not_empty(self):
        fd = _make_fd("src/foo.py", ["x = 1"])
        r = score_file(fd)
        assert len(r.reasons) >= 1

    def test_emoji_mapping(self):
        r = RiskResult(level="High", score=10, reasons=[])
        assert r.emoji == "🔴"
        r2 = RiskResult(level="Med", score=4, reasons=[])
        assert r2.emoji == "🟡"
        r3 = RiskResult(level="Low", score=1, reasons=[])
        assert r3.emoji == "🟢"

    def test_eval_pattern_high_risk(self):
        fd = _make_fd("src/runner.py", ["eval(user_input)"])
        r = score_file(fd)
        assert r.level in ("Med", "High")

    def test_subprocess_pattern(self):
        fd = _make_fd("src/runner.py", ["subprocess.run(cmd, shell=True)"])
        r = score_file(fd)
        assert r.level in ("Med", "High")

    def test_config_path_elevates_risk(self):
        fd = _make_fd("config/settings.py", ["DEBUG = False"])
        r = score_file(fd)
        assert r.level in ("Med", "High")

    def test_many_hunks_elevates_risk(self):
        hunks = []
        for i in range(12):
            h = Hunk(old_start=i*10+1, old_count=1, new_start=i*10+1, new_count=1,
                     lines=[f"+change_{i}"])
            hunks.append(h)
        fd = FileDiff(old_path="a/src/big.py", new_path="b/src/big.py", hunks=hunks)
        r = score_file(fd)
        assert r.score >= 2
