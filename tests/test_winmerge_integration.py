"""Tests for winmerge_integration.py pure-Python diff (no system 'diff' binary)."""

import pytest
from pathlib import Path

from winmerge_ai_exporter.winmerge_integration import (
    generate_diff_between_files,
    generate_diff_between_folders,
)


# ---------------------------------------------------------------------------
# generate_diff_between_files
# ---------------------------------------------------------------------------

class TestGenerateDiffBetweenFiles:
    def test_modified_text_file_produces_diff(self, tmp_path):
        left  = tmp_path / "old.py"
        right = tmp_path / "new.py"
        left.write_text("def foo():\n    return 1\n")
        right.write_text("def foo():\n    return 2\n")

        diffs = generate_diff_between_files(left, right)
        assert len(diffs) == 1
        assert not diffs[0].is_identical()
        assert diffs[0].total_added >= 1
        assert diffs[0].total_deleted >= 1

    def test_identical_files_yield_no_changes(self, tmp_path):
        left  = tmp_path / "a.py"
        right = tmp_path / "b.py"
        content = "x = 1\ny = 2\n"
        left.write_text(content)
        right.write_text(content)

        diffs = generate_diff_between_files(left, right)
        assert diffs[0].is_identical()

    def test_missing_left_file_raises(self, tmp_path):
        right = tmp_path / "exists.py"
        right.write_text("x = 1\n")
        with pytest.raises(RuntimeError, match="does not exist"):
            generate_diff_between_files(tmp_path / "nope.py", right)

    def test_missing_right_file_raises(self, tmp_path):
        left = tmp_path / "exists.py"
        left.write_text("x = 1\n")
        with pytest.raises(RuntimeError, match="does not exist"):
            generate_diff_between_files(left, tmp_path / "nope.py")

    def test_empty_left_path_raises(self, tmp_path):
        right = tmp_path / "exists.py"
        right.write_text("x = 1\n")
        with pytest.raises(RuntimeError, match="empty"):
            generate_diff_between_files("", right)

    def test_empty_right_path_raises(self, tmp_path):
        left = tmp_path / "exists.py"
        left.write_text("x = 1\n")
        with pytest.raises(RuntimeError, match="empty"):
            generate_diff_between_files(left, "")

    def test_folder_passed_instead_of_file_raises(self, tmp_path):
        left_dir = tmp_path / "leftdir"
        left_dir.mkdir()
        right_file = tmp_path / "right.py"
        right_file.write_text("x = 1\n")
        with pytest.raises(RuntimeError, match="must be files"):
            generate_diff_between_files(left_dir, right_file)

    def test_binary_file_flagged(self, tmp_path):
        left  = tmp_path / "img_old.bin"
        right = tmp_path / "img_new.bin"
        left.write_bytes(bytes(range(256)))
        right.write_bytes(bytes(range(255, -1, -1)))

        diffs = generate_diff_between_files(left, right)
        assert diffs[0].binary is True

    def test_no_system_diff_dependency(self, tmp_path, monkeypatch):
        """Simulate environment where system 'diff' is completely unavailable."""
        import subprocess as sp

        def _boom(*args, **kwargs):
            raise FileNotFoundError("diff: command not found")

        monkeypatch.setattr(sp, "run", _boom)

        left  = tmp_path / "old.py"
        right = tmp_path / "new.py"
        left.write_text("a = 1\n")
        right.write_text("a = 2\n")

        # Should succeed purely via difflib, never touching subprocess.run
        diffs = generate_diff_between_files(left, right)
        assert not diffs[0].is_identical()


# ---------------------------------------------------------------------------
# generate_diff_between_folders
# ---------------------------------------------------------------------------

class TestGenerateDiffBetweenFolders:
    def _make_tree(self, base: Path, files: dict[str, str]):
        for rel, content in files.items():
            p = base / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)

    def test_basic_folder_diff(self, tmp_path):
        left  = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(left,  {"src/a.py": "x = 1\n", "src/b.py": "y = 1\n"})
        self._make_tree(right, {"src/a.py": "x = 2\n", "src/b.py": "y = 1\n"})

        diffs = generate_diff_between_folders(left, right)
        changed = [d for d in diffs if not d.is_identical()]
        assert len(changed) == 1
        assert "a.py" in changed[0].path

    def test_identical_folders_no_changes(self, tmp_path):
        left  = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(left,  {"x.py": "same\n"})
        self._make_tree(right, {"x.py": "same\n"})

        diffs = generate_diff_between_folders(left, right)
        assert all(d.is_identical() for d in diffs)

    def test_new_file_detected(self, tmp_path):
        left  = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(left,  {"x.py": "x = 1\n"})
        self._make_tree(right, {"x.py": "x = 1\n", "new_file.py": "z = 1\n"})

        diffs = generate_diff_between_folders(left, right)
        new_files = [d for d in diffs if d.old_path == "/dev/null"]
        assert any("new_file.py" in d.path for d in new_files)

    def test_deleted_file_detected(self, tmp_path):
        left  = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(left,  {"x.py": "x = 1\n", "old_file.py": "z = 1\n"})
        self._make_tree(right, {"x.py": "x = 1\n"})

        diffs = generate_diff_between_folders(left, right)
        deleted = [d for d in diffs if d.new_path == "/dev/null"]
        assert any("old_file.py" in d.path for d in deleted)

    def test_missing_left_folder_raises(self, tmp_path):
        right = tmp_path / "right"
        right.mkdir()
        with pytest.raises(RuntimeError, match="does not exist"):
            generate_diff_between_folders(tmp_path / "nope", right)

    def test_missing_right_folder_raises(self, tmp_path):
        left = tmp_path / "left"
        left.mkdir()
        with pytest.raises(RuntimeError, match="does not exist"):
            generate_diff_between_folders(left, tmp_path / "nope")

    def test_empty_left_path_raises(self, tmp_path):
        right = tmp_path / "right"
        right.mkdir()
        with pytest.raises(RuntimeError, match="empty"):
            generate_diff_between_folders("", right)

    def test_empty_right_path_raises(self, tmp_path):
        left = tmp_path / "left"
        left.mkdir()
        with pytest.raises(RuntimeError, match="empty"):
            generate_diff_between_folders(left, "")

    def test_both_empty_paths_raise(self):
        with pytest.raises(RuntimeError, match="empty"):
            generate_diff_between_folders("", "")

    def test_file_passed_instead_of_folder_raises(self, tmp_path):
        left_file = tmp_path / "left.py"
        left_file.write_text("x = 1\n")
        right_dir = tmp_path / "right"
        right_dir.mkdir()
        with pytest.raises(RuntimeError, match="not a folder"):
            generate_diff_between_folders(left_file, right_dir)

    def test_exclude_pattern_skips_files(self, tmp_path):
        left  = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(left,  {"build/out.txt": "old\n", "src/main.py": "x = 1\n"})
        self._make_tree(right, {"build/out.txt": "new\n", "src/main.py": "x = 2\n"})

        diffs = generate_diff_between_folders(left, right, exclude_patterns=["build/*"])
        changed_paths = [d.path for d in diffs if not d.is_identical()]
        assert not any("build" in p for p in changed_paths)
        assert any("main.py" in p for p in changed_paths)

    def test_nested_directories(self, tmp_path):
        left  = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(left,  {"a/b/c/deep.py": "v = 1\n"})
        self._make_tree(right, {"a/b/c/deep.py": "v = 2\n"})

        diffs = generate_diff_between_folders(left, right)
        changed = [d for d in diffs if not d.is_identical()]
        assert len(changed) == 1
        assert "deep.py" in changed[0].path

    def test_no_system_diff_dependency(self, tmp_path, monkeypatch):
        """Folder compare must work with zero external 'diff' binary calls."""
        import subprocess as sp

        def _boom(*args, **kwargs):
            raise FileNotFoundError("diff: command not found")

        monkeypatch.setattr(sp, "run", _boom)

        left  = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(left,  {"x.py": "a = 1\n"})
        self._make_tree(right, {"x.py": "a = 2\n"})

        diffs = generate_diff_between_folders(left, right)
        changed = [d for d in diffs if not d.is_identical()]
        assert len(changed) == 1
