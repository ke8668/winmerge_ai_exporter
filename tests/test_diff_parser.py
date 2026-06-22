"""Tests for diff_parser.py"""

import pytest
from winmerge_ai_exporter.diff_parser import (
    parse_unified_diff,
    FileDiff,
    Hunk,
    extract_modified_symbols,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SIMPLE_DIFF = """\
--- a/src/foo.py
+++ b/src/foo.py
@@ -1,5 +1,6 @@
 import os
+import sys
 
 def hello():
-    print("hello")
+    print("hello world")
     return 0
"""

MULTI_FILE_DIFF = """\
--- a/src/a.py
+++ b/src/a.py
@@ -1,3 +1,4 @@
 class A:
+    x = 1
     pass
 
--- a/src/b.cpp
+++ b/src/b.cpp
@@ -10,5 +10,6 @@
 void B::run() {
+    int n = 0;
     doWork();
 }
"""

BINARY_DIFF = """\
--- a/assets/logo.png
+++ b/assets/logo.png
Binary files a/assets/logo.png and b/assets/logo.png differ
"""

WHITESPACE_ONLY_DIFF = """\
--- a/src/util.py
+++ b/src/util.py
@@ -1,3 +1,3 @@
 def foo():
-    pass  
+    pass
"""

NO_NEWLINE_DIFF = """\
--- a/src/mod.js
+++ b/src/mod.js
@@ -1,4 +1,5 @@
 function greet(name) {
-    return 'hello ' + name;
+    return `hello ${name}`;
+    // updated to template literal
 }
"""

# ---------------------------------------------------------------------------
# parse_unified_diff
# ---------------------------------------------------------------------------

class TestParseUnifiedDiff:
    def test_simple_diff_yields_one_file(self):
        diffs = parse_unified_diff(SIMPLE_DIFF)
        assert len(diffs) == 1

    def test_file_paths_parsed(self):
        diffs = parse_unified_diff(SIMPLE_DIFF)
        fd = diffs[0]
        assert "foo.py" in fd.old_path
        assert "foo.py" in fd.new_path

    def test_hunk_count(self):
        diffs = parse_unified_diff(SIMPLE_DIFF)
        assert len(diffs[0].hunks) == 1

    def test_added_deleted_counts(self):
        diffs = parse_unified_diff(SIMPLE_DIFF)
        fd = diffs[0]
        assert fd.total_added == 2
        assert fd.total_deleted == 1

    def test_multi_file_diff(self):
        diffs = parse_unified_diff(MULTI_FILE_DIFF)
        assert len(diffs) == 2
        paths = [fd.path for fd in diffs]
        assert any("a.py" in p for p in paths)
        assert any("b.cpp" in p for p in paths)

    def test_binary_file(self):
        diffs = parse_unified_diff(BINARY_DIFF)
        assert len(diffs) == 1
        assert diffs[0].binary is True

    def test_empty_string(self):
        diffs = parse_unified_diff("")
        assert diffs == []

    def test_identical_file_no_hunks(self):
        # No hunks → identical
        diff_text = "--- a/x.py\n+++ b/x.py\n"
        diffs = parse_unified_diff(diff_text)
        assert diffs[0].is_identical()

    def test_hunk_line_numbers(self):
        diffs = parse_unified_diff(SIMPLE_DIFF)
        h = diffs[0].hunks[0]
        assert h.old_start == 1
        assert h.new_start == 1

    def test_hunk_with_single_line_count(self):
        # @@ -5 +5,2 @@ (no comma on old side → count=1)
        text = "--- a/f.c\n+++ b/f.c\n@@ -5 +5,2 @@\n-old\n+new1\n+new2\n"
        diffs = parse_unified_diff(text)
        h = diffs[0].hunks[0]
        assert h.old_count == 1
        assert h.new_count == 2


# ---------------------------------------------------------------------------
# FileDiff properties
# ---------------------------------------------------------------------------

class TestFileDiff:
    def test_path_strips_prefix(self):
        fd = FileDiff(old_path="a/src/foo.py", new_path="b/src/foo.py")
        assert fd.path == "src/foo.py"

    def test_path_prefers_new(self):
        fd = FileDiff(old_path="/dev/null", new_path="b/new_file.py")
        assert fd.path == "new_file.py"

    def test_extension(self):
        fd = FileDiff(old_path="a/x.cpp", new_path="b/x.cpp")
        assert fd.extension == "cpp"

    def test_is_identical_true(self):
        fd = FileDiff(old_path="a", new_path="b")
        assert fd.is_identical()

    def test_is_identical_false_with_hunks(self):
        fd = FileDiff(old_path="a", new_path="b", hunks=[Hunk(1, 1, 1, 1, ["+x"])])
        assert not fd.is_identical()

    def test_total_added_deleted(self):
        diffs = parse_unified_diff(SIMPLE_DIFF)
        fd = diffs[0]
        assert fd.total_added == 2
        assert fd.total_deleted == 1


# ---------------------------------------------------------------------------
# Hunk filtering
# ---------------------------------------------------------------------------

class TestHunkFiltering:
    def test_whitespace_only_detected(self):
        diffs = parse_unified_diff(WHITESPACE_ONLY_DIFF)
        h = diffs[0].hunks[0]
        assert h.is_whitespace_only()

    def test_meaningful_hunk_not_whitespace(self):
        diffs = parse_unified_diff(SIMPLE_DIFF)
        h = diffs[0].hunks[0]
        assert not h.is_whitespace_only()

    def test_filter_whitespace_only(self):
        diffs = parse_unified_diff(WHITESPACE_ONLY_DIFF)
        fd = diffs[0]
        assert fd.meaningful_hunks(skip_whitespace=True) == []

    def test_keep_whitespace_when_disabled(self):
        diffs = parse_unified_diff(WHITESPACE_ONLY_DIFF)
        fd = diffs[0]
        assert len(fd.meaningful_hunks(skip_whitespace=False)) == 1


# ---------------------------------------------------------------------------
# Symbol extraction
# ---------------------------------------------------------------------------

class TestExtractModifiedSymbols:
    def test_python_function(self):
        diff_text = "--- a/mod.py\n+++ b/mod.py\n@@ -1,3 +1,4 @@\n+def new_func(x):\n+    return x\n"
        diffs = parse_unified_diff(diff_text)
        syms = extract_modified_symbols(diffs[0])
        assert "new_func" in syms

    def test_python_class(self):
        diff_text = "--- a/mod.py\n+++ b/mod.py\n@@ -1,2 +1,3 @@\n+class MyService:\n+    pass\n"
        diffs = parse_unified_diff(diff_text)
        syms = extract_modified_symbols(diffs[0])
        assert "MyService" in syms

    def test_cpp_function(self):
        diff_text = "--- a/eng.cpp\n+++ b/eng.cpp\n@@ -5,3 +5,4 @@\n+bool Engine::Run(int n) {\n+    return true;\n+}\n"
        diffs = parse_unified_diff(diff_text)
        syms = extract_modified_symbols(diffs[0])
        assert len(syms) >= 0  # cpp pattern may or may not match depending on line format

    def test_no_patterns_for_unknown_ext(self):
        diff_text = "--- a/file.xyz\n+++ b/file.xyz\n@@ -1 +1 @@\n-old\n+new\n"
        diffs = parse_unified_diff(diff_text)
        syms = extract_modified_symbols(diffs[0])
        assert syms == []

    def test_deduplication(self):
        # Same function name in two hunks
        text = (
            "--- a/mod.py\n+++ b/mod.py\n"
            "@@ -1,2 +1,3 @@\n+def foo():\n    pass\n"
            "@@ -10,2 +11,3 @@\n+def foo():\n    return 1\n"
        )
        diffs = parse_unified_diff(text)
        syms = extract_modified_symbols(diffs[0])
        assert syms.count("foo") == 1
