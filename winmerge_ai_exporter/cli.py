"""
cli.py
Command-line interface for the WinMerge AI Review Exporter.

Usage examples:
    # Export from a patch file
    python -m winmerge_ai_exporter export --patch changes.patch --output ./out

    # Export by comparing two folders (requires system diff)
    python -m winmerge_ai_exporter export --left ./old --right ./new --output ./out

    # Just estimate tokens
    python -m winmerge_ai_exporter estimate --patch changes.patch

    # Copy prompt to clipboard
    python -m winmerge_ai_exporter copy-prompt --patch changes.patch
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _load_diffs(args):
    """Load FileDiff list from CLI arguments."""
    from .winmerge_integration import (
        load_from_patch_file,
        load_from_winmerge_xml_report,
        generate_diff_between_folders,
    )

    if getattr(args, "patch", None):
        print(f"[*] Loading patch file: {args.patch}")
        return load_from_patch_file(args.patch)

    elif getattr(args, "xml", None):
        print(f"[*] Loading WinMerge XML report: {args.xml}")
        return load_from_winmerge_xml_report(args.xml)

    elif getattr(args, "left", None) and getattr(args, "right", None):
        print(f"[*] Comparing folders:\n    LEFT : {args.left}\n    RIGHT: {args.right}")
        exclude = getattr(args, "exclude", None) or []
        return generate_diff_between_folders(args.left, args.right, exclude)

    else:
        print("ERROR: Provide --patch, --xml, or both --left and --right.", file=sys.stderr)
        sys.exit(1)


def cmd_export(args) -> None:
    from .exporter import export_ai_review_package

    diffs = _load_diffs(args)
    if not diffs:
        print("No diffs found.")
        return

    changed = [d for d in diffs if not d.is_identical()]
    print(f"[*] Found {len(diffs)} file entries, {len(changed)} with changes.")

    source_label = getattr(args, "source_label", None) or str(
        getattr(args, "patch", None) or getattr(args, "left", "comparison")
    )

    out = export_ai_review_package(
        file_diffs=diffs,
        output_dir=args.output,
        source_label=source_label,
        context_lines=getattr(args, "context", 30),
        skip_whitespace=not getattr(args, "keep_whitespace", False),
        skip_comments=not getattr(args, "keep_comments", False),
        include_json=getattr(args, "json", True),
    )

    print(f"\n✅ AI Review Package exported to:\n   {out}\n")
    print("Package contents:")
    for f in sorted(out.rglob("*")):
        if f.is_file():
            size = f.stat().st_size
            print(f"   {f.relative_to(out)}  ({size:,} bytes)")


def cmd_estimate(args) -> None:
    from .token_estimator import estimate_for_diffs

    diffs = _load_diffs(args)
    changed = [d for d in diffs if not d.is_identical()]
    est = estimate_for_diffs(
        changed,
        skip_whitespace=not getattr(args, "keep_whitespace", False),
        skip_comments=not getattr(args, "keep_comments", False),
    )
    print("\n📊 Token Estimation")
    print("=" * 50)
    print(est.summary())


def cmd_copy_prompt(args) -> None:
    from .diff_parser import extract_modified_symbols
    from .exporter import _render_prompt
    from .risk_scorer import score_file

    diffs = _load_diffs(args)
    changed = [d for d in diffs if not d.is_identical()]

    risks = {fd.path: score_file(fd) for fd in changed}
    symbols_map = {fd.path: extract_modified_symbols(fd) for fd in changed}

    prompt = _render_prompt(
        changed, risks, symbols_map,
        skip_whitespace=not getattr(args, "keep_whitespace", False),
        skip_comments=not getattr(args, "keep_comments", False),
    )

    # Try clipboard
    try:
        import subprocess
        proc = subprocess.run(
            ["clip"] if sys.platform == "win32" else ["pbcopy"],
            input=prompt.encode("utf-8"),
            check=True,
        )
        print("✅ Review prompt copied to clipboard!")
    except Exception:
        # Fall back: write to file
        out_file = Path(getattr(args, "output", ".")) / "review_prompt.txt"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(prompt, encoding="utf-8")
        print(f"Clipboard unavailable. Prompt written to: {out_file}")

    lines = prompt.splitlines()
    print(f"\nPrompt size: {len(prompt):,} chars / ~{len(prompt)//4:,} tokens")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="winmerge-ai-exporter",
        description="Export WinMerge diffs as an AI-ready code review package.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Shared diff source arguments ---
    def add_source_args(p):
        group = p.add_mutually_exclusive_group()
        group.add_argument("--patch", "-p", help="Unified diff / patch file")
        group.add_argument("--xml", help="WinMerge XML folder compare report")
        p.add_argument("--left", "-l", help="Left folder (with --right)")
        p.add_argument("--right", "-r", help="Right folder (with --left)")
        p.add_argument("--exclude", nargs="*", metavar="PAT",
                       help="Glob patterns to exclude (folder compare only)")

    def add_filter_args(p):
        p.add_argument("--keep-whitespace", action="store_true",
                       help="Include whitespace-only changes")
        p.add_argument("--keep-comments", action="store_true",
                       help="Include comment-only changes")

    # --- export ---
    exp = subparsers.add_parser("export", help="Generate full AI review package")
    add_source_args(exp)
    add_filter_args(exp)
    exp.add_argument("--output", "-o", default=".", help="Output directory (default: .)")
    exp.add_argument("--context", type=int, default=30, metavar="N",
                     help="Context lines around each change (default: 30)")
    exp.add_argument("--no-json", dest="json", action="store_false",
                     help="Skip JSON export")
    exp.add_argument("--source-label", help="Label for the comparison source")
    exp.set_defaults(func=cmd_export, json=True)

    # --- estimate ---
    est = subparsers.add_parser("estimate", help="Estimate token count before export")
    add_source_args(est)
    add_filter_args(est)
    est.set_defaults(func=cmd_estimate)

    # --- copy-prompt ---
    cp = subparsers.add_parser("copy-prompt", help="Copy AI review prompt to clipboard")
    add_source_args(cp)
    add_filter_args(cp)
    cp.add_argument("--output", "-o", default=".", help="Fallback output dir for prompt file")
    cp.set_defaults(func=cmd_copy_prompt)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
