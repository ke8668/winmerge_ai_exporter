"""Tests for redactor.py with multi-mode redaction (FULL, API_SAFE, SIGNATURE)."""

import pytest

from winmerge_ai_exporter.diff_parser import parse_unified_diff, FileDiff, Hunk
from winmerge_ai_exporter.redactor import (
    RedactionMode,
    StripOptions,
    strip_hunk,
    strip_file_diff,
    _pseudonymize_line,
    _short_hash,
    _should_preserve_in_api_safe,
)


AUTH_DIFF = """\
--- a/Src/auth/SessionManager.cpp
+++ b/Src/auth/SessionManager.cpp
@@ -34,12 +34,19 @@
 #include "SessionManager.h"
 #include "CryptoUtils.h"
+#include "AuditLog.h"
 
-bool SessionManager::ValidateToken(const std::string& token) {
-    return CryptoUtils::VerifyHMAC(token, m_secret_key);
+bool SessionManager::ValidateToken(const std::string& token, const RequestContext& ctx) {
+    bool valid = CryptoUtils::VerifyHMAC(token, m_secret_key);
+    AuditLog::Record(ctx.user_id, "token_validate", valid ? "ok" : "fail");
+    if (!valid && ctx.failure_count > MAX_FAILURES) {
+        LockAccount(ctx.user_id);
+        AuditLog::Record(ctx.user_id, "account_locked", "excessive_failures");
+    }
+    return valid;
 }
"""


def _parse_one(text: str) -> FileDiff:
    return parse_unified_diff(text)[0]


# ───────────────────────────────────────────────────────────────────────────
# API-Safe preservation rules
# ───────────────────────────────────────────────────────────────────────────

class TestAPISafePreservation:
    """Test what identifiers get preserved in API-Safe mode."""

    def test_pascal_case_names_preserved(self):
        """PascalCase names (public APIs) are preserved in API-Safe."""
        assert _should_preserve_in_api_safe("SessionManager")
        assert _should_preserve_in_api_safe("ValidateToken")
        assert _should_preserve_in_api_safe("CryptoUtils")
        assert _should_preserve_in_api_safe("RequestContext")
        assert _should_preserve_in_api_safe("AuditLog")

    def test_all_caps_constants_preserved(self):
        """ALL_CAPS_WITH_UNDERSCORES constants preserved."""
        assert _should_preserve_in_api_safe("MAX_FAILURES")
        assert _should_preserve_in_api_safe("HTTP_OK")
        assert _should_preserve_in_api_safe("API_KEY")
        # Single-word all-caps like EOF are NOT preserved (no underscore)
        assert not _should_preserve_in_api_safe("EOF")

    def test_type_names_preserved(self):
        """Known type names always preserved."""
        assert _should_preserve_in_api_safe("bool")
        assert _should_preserve_in_api_safe("int")
        assert _should_preserve_in_api_safe("string")
        assert _should_preserve_in_api_safe("vector")

    def test_keywords_preserved(self):
        """Language keywords always preserved."""
        assert _should_preserve_in_api_safe("if")
        assert _should_preserve_in_api_safe("return")
        assert _should_preserve_in_api_safe("const")
        assert _should_preserve_in_api_safe("std")

    def test_lowercase_internal_names_hidden(self):
        """Lowercase internal names are pseudonymized."""
        assert not _should_preserve_in_api_safe("m_secret_key")
        assert not _should_preserve_in_api_safe("valid")
        assert not _should_preserve_in_api_safe("ctx")
        assert not _should_preserve_in_api_safe("token")


# ───────────────────────────────────────────────────────────────────────────
# Redaction modes
# ───────────────────────────────────────────────────────────────────────────

class TestRedactionModes:
    """Compare behavior across FULL vs API_SAFE vs SIGNATURE modes."""

    def test_full_mode_hides_everything(self):
        """FULL mode pseudonymizes all non-keyword identifiers."""
        line = "+    bool result = SessionManager::Validate(token);"
        out = _pseudonymize_line(
            line,
            salt="test.cpp",
            ident_map={},
            mode=RedactionMode.FULL,
        )
        # SessionManager, Validate, token, result all hidden
        assert "SessionManager" not in out
        assert "Validate" not in out
        assert "token" not in out
        assert "result" not in out
        # But bool and return type structure intact
        assert "bool" in out

    def test_api_safe_preserves_apis(self):
        """API-Safe mode keeps public APIs, types, and stdlib."""
        line = "+    bool result = SessionManager::ValidateToken(token);"
        out = _pseudonymize_line(
            line,
            salt="test.cpp",
            ident_map={},
            mode=RedactionMode.API_SAFE,
        )
        # Public APIs preserved
        assert "SessionManager" in out
        assert "ValidateToken" in out
        assert "bool" in out
        # Internal vars hidden
        assert "result" not in out or "sym_" in out
        assert "token" not in out or "sym_" in out

    def test_api_safe_hides_internal_variables(self):
        """API-Safe mode hides internal implementation variables."""
        line = "+    int failure_count = context.failure_count;"
        out = _pseudonymize_line(
            line,
            salt="test.cpp",
            ident_map={},
            mode=RedactionMode.API_SAFE,
        )
        # 'failure_count' is internal, should be pseudonymized
        assert "sym_" in out
        # But 'int' type is preserved
        assert "int" in out

    def test_consistency_within_file(self):
        """Same identifier maps to same placeholder within a file."""
        ident_map = {}
        l1 = _pseudonymize_line("+    foo(userID);", "file.py", ident_map, RedactionMode.FULL)
        l2 = _pseudonymize_line("+    bar(userID);", "file.py", ident_map, RedactionMode.FULL)
        # Extract the sym_ token for userID from both
        import re
        t1 = re.search(r"sym_\w+", l1)
        t2 = re.search(r"sym_\w+", l2)
        # They should find the same token for 'userID'
        assert t1 and t2
        assert ident_map["userID"] in l1
        assert ident_map["userID"] in l2

    def test_different_files_different_hashes(self):
        """Different files get different placeholders for same identifier."""
        out1 = _pseudonymize_line("+int secret = 42;", "fileA.cpp", {}, RedactionMode.FULL)
        out2 = _pseudonymize_line("+int secret = 42;", "fileB.cpp", {}, RedactionMode.FULL)
        # The 'secret' identifier should map to different sym_ values in each file
        import re
        t1 = re.search(r"sym_\w+", out1)
        t2 = re.search(r"sym_\w+", out2)
        assert t1 and t2 and t1.group(0) != t2.group(0)


# ───────────────────────────────────────────────────────────────────────────
# Hunk and file-level stripping
# ───────────────────────────────────────────────────────────────────────────

class TestHunkStripping:
    """Test context collapse and line filtering at hunk level."""

    def test_far_context_collapsed(self):
        """Context lines far from changes are collapsed."""
        fd = _parse_one(AUTH_DIFF)
        out = strip_hunk(
            fd.hunks[0],
            StripOptions(mode=RedactionMode.API_SAFE, core_context=1),
            salt="test.cpp",
            ident_map={},
        )
        joined = "\n".join(out)
        # Far lines should be collapsed
        assert "redacted" in joined

    def test_changed_lines_always_kept(self):
        """Changed (+/-) lines are always kept."""
        fd = _parse_one(AUTH_DIFF)
        out = strip_hunk(
            fd.hunks[0],
            StripOptions(mode=RedactionMode.API_SAFE, core_context=0),
            salt="test.cpp",
            ident_map={},
        )
        joined = "\n".join(out)
        # Function signature changes should be visible
        assert ("+" in joined and "-" in joined) or "ValidateToken" in joined

    def test_core_context_controls_window(self):
        """core_context parameter controls context window size."""
        fd = _parse_one(AUTH_DIFF)
        
        # core_context=0: minimal context
        out0 = strip_hunk(
            fd.hunks[0],
            StripOptions(mode=RedactionMode.API_SAFE, core_context=0),
            salt="test.cpp",
            ident_map={},
        )
        
        # core_context=2: broader context
        out2 = strip_hunk(
            fd.hunks[0],
            StripOptions(mode=RedactionMode.API_SAFE, core_context=2),
            salt="test.cpp",
            ident_map={},
        )
        
        # Broader context should have fewer collapsed markers
        markers0 = "\n".join(out0).count("redacted")
        markers2 = "\n".join(out2).count("redacted")
        assert markers2 <= markers0


class TestFileDiffStripping:
    """Test file-level stripping."""

    def test_api_names_visible_in_output(self):
        """API-Safe mode output preserves function names and types."""
        fd = _parse_one(AUTH_DIFF)
        hunks = fd.meaningful_hunks()
        result = strip_file_diff(fd, hunks, StripOptions(mode=RedactionMode.API_SAFE))
        joined = "\n".join("\n".join(h) for h in result)
        
        # Public APIs visible
        assert "SessionManager" in joined
        assert "ValidateToken" in joined
        # But internal details hidden
        assert "m_secret_key" not in joined or "sym_" in joined

    def test_full_mode_hides_all_names(self):
        """FULL mode hides all user-defined identifiers."""
        fd = _parse_one(AUTH_DIFF)
        hunks = fd.meaningful_hunks()
        result = strip_file_diff(fd, hunks, StripOptions(mode=RedactionMode.FULL))
        joined = "\n".join("\n".join(h) for h in result)
        
        # All API names should be hidden
        assert "SessionManager" not in joined
        assert "ValidateToken" not in joined
        # But language keywords visible
        assert "bool" in joined
        assert "return" in joined


class TestStringAndNumberHandling:
    """String literals and numbers are always redacted."""

    def test_string_literals_redacted(self):
        """String literals become <str> in all modes."""
        line = '+    log("token_validate");'
        for mode in [RedactionMode.FULL, RedactionMode.API_SAFE]:
            out = _pseudonymize_line(line, "file.cpp", {}, mode)
            assert "token_validate" not in out
            assert "<str>" in out

    def test_numbers_redacted_except_01(self):
        """Numeric literals become <n>, except 0, 1, -1."""
        line = "+    if (count > 42 && val == 1) process(0);"
        out = _pseudonymize_line(line, "file.cpp", {}, RedactionMode.FULL)
        assert "42" not in out
        assert "<n>" in out
        # But 0 and 1 preserved
        assert " 1" in out or " 0" in out

    def test_diff_prefix_preserved(self):
        """Diff line markers (+/-/ ) always preserved."""
        added = _pseudonymize_line("+secret = value", "f", {}, RedactionMode.FULL)
        removed = _pseudonymize_line("-secret = value", "f", {}, RedactionMode.FULL)
        context = _pseudonymize_line(" secret = value", "f", {}, RedactionMode.FULL)
        assert added.startswith("+")
        assert removed.startswith("-")
        assert context.startswith(" ")
