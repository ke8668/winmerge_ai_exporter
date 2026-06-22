"""Integration tests for exporter.py, cli.py, and winmerge_integration.py"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

from winmerge_ai_exporter import (
    load_from_patch_file,
    load_from_patch_text,
    export_ai_review_package,
)
from winmerge_ai_exporter.cli import build_parser, main

# Path to the sample patch that ships with the repo
SAMPLE_PATCH = Path(__file__).parent.parent / "sample_diffs" / "sample_changes.patch"


# ---------------------------------------------------------------------------
# Exporter integration
# ---------------------------------------------------------------------------

class TestExporterIntegration:
    @pytest.fixture(autouse=True)
    def tmp_output(self, tmp_path):
        self.out_base = tmp_path

    def _run_export(self, **kwargs):
        diffs = load_from_patch_file(SAMPLE_PATCH)
        return export_ai_review_package(diffs, output_dir=self.out_base, **kwargs)

    def test_export_creates_ai_review_dir(self):
        out = self._run_export()
        assert out.is_dir()
        assert out.name == "ai_review"

    def test_summary_md_exists(self):
        out = self._run_export()
        assert (out / "summary.md").exists()

    def test_changed_files_txt_exists(self):
        out = self._run_export()
        assert (out / "changed_files.txt").exists()

    def test_architecture_changes_md_exists(self):
        out = self._run_export()
        assert (out / "architecture_changes.md").exists()

    def test_review_prompt_exists(self):
        out = self._run_export()
        assert (out / "prompts" / "review_prompt.txt").exists()

    def test_diffs_dir_populated(self):
        out = self._run_export()
        diff_files = list((out / "diffs").glob("*.diff.md"))
        assert len(diff_files) >= 1

    def test_json_export_exists_by_default(self):
        out = self._run_export()
        assert (out / "review_data.json").exists()

    def test_json_is_valid(self):
        out = self._run_export()
        data = json.loads((out / "review_data.json").read_text())
        assert "files" in data
        assert "architecture" in data
        assert "token_estimate" in data

    def test_json_files_have_required_fields(self):
        out = self._run_export()
        data = json.loads((out / "review_data.json").read_text())
        for f in data["files"]:
            assert "path" in f
            assert "risk_level" in f
            assert f["risk_level"] in ("Low", "Med", "High")

    def test_json_not_created_when_disabled(self):
        out = self._run_export(include_json=False)
        assert not (out / "review_data.json").exists()

    def test_summary_contains_risk_table(self):
        out = self._run_export()
        content = (out / "summary.md").read_text()
        assert "Risk" in content
        assert "LOC" in content or "added" in content.lower()

    def test_prompt_contains_diff_content(self):
        out = self._run_export()
        prompt = (out / "prompts" / "review_prompt.txt").read_text()
        assert "```diff" in prompt or "FILE:" in prompt

    def test_prompt_has_all_review_sections(self):
        out = self._run_export()
        prompt = (out / "prompts" / "review_prompt.txt").read_text()
        assert "Architecture" in prompt
        assert "Regression" in prompt
        assert "Concurrency" in prompt

    def test_arch_md_has_subsystems_section(self):
        out = self._run_export()
        arch = (out / "architecture_changes.md").read_text()
        assert "Affected subsystems" in arch or "subsystem" in arch.lower()

    def test_diff_md_has_risk_level(self):
        out = self._run_export()
        diff_files = list((out / "diffs").glob("*.diff.md"))
        content = diff_files[0].read_text()
        assert any(r in content for r in ("High", "Med", "Low"))

    def test_high_risk_file_identified(self):
        # SessionManager is under auth/ → should be High risk
        out = self._run_export()
        data = json.loads((out / "review_data.json").read_text())
        session_file = next(
            (f for f in data["files"] if "SessionManager" in f["path"]), None
        )
        assert session_file is not None
        assert session_file["risk_level"] == "High"

    def test_context_lines_parameter_accepted(self):
        out = self._run_export(context_lines=5)
        assert (out / "summary.md").exists()

    def test_source_label_in_summary(self):
        out = self._run_export(source_label="test-comparison-v2")
        content = (out / "summary.md").read_text()
        assert "test-comparison-v2" in content

    def test_empty_diffs_handled_gracefully(self):
        out = export_ai_review_package([], output_dir=self.out_base)
        assert (out / "summary.md").exists()


# ---------------------------------------------------------------------------
# load_from_patch_text
# ---------------------------------------------------------------------------

class TestLoadFromPatchText:
    def test_roundtrip(self):
        text = SAMPLE_PATCH.read_text(encoding="utf-8")
        diffs = load_from_patch_text(text)
        assert len(diffs) >= 1

    def test_identical_file_not_changed(self):
        text = "--- a/x.py\n+++ b/x.py\n"
        diffs = load_from_patch_text(text)
        assert diffs[0].is_identical()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class TestCLI:
    def test_export_command_runs(self, tmp_path):
        args = build_parser().parse_args([
            "export",
            "--patch", str(SAMPLE_PATCH),
            "--output", str(tmp_path),
        ])
        args.func(args)
        assert (tmp_path / "ai_review" / "summary.md").exists()

    def test_estimate_command_runs(self, capsys):
        args = build_parser().parse_args([
            "estimate",
            "--patch", str(SAMPLE_PATCH),
        ])
        args.func(args)
        captured = capsys.readouterr()
        assert "token" in captured.out.lower()

    def test_no_json_flag(self, tmp_path):
        args = build_parser().parse_args([
            "export",
            "--patch", str(SAMPLE_PATCH),
            "--output", str(tmp_path),
            "--no-json",
        ])
        args.func(args)
        assert not (tmp_path / "ai_review" / "review_data.json").exists()

    def test_context_flag(self, tmp_path):
        args = build_parser().parse_args([
            "export",
            "--patch", str(SAMPLE_PATCH),
            "--output", str(tmp_path),
            "--context", "10",
        ])
        args.func(args)
        assert (tmp_path / "ai_review" / "summary.md").exists()

    def test_keep_whitespace_flag(self, tmp_path):
        args = build_parser().parse_args([
            "export",
            "--patch", str(SAMPLE_PATCH),
            "--output", str(tmp_path),
            "--keep-whitespace",
        ])
        args.func(args)
        assert (tmp_path / "ai_review" / "summary.md").exists()
