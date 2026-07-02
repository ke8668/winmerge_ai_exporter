# WinMerge AI Review Exporter

> **One-click export of WinMerge diffs into an AI-ready architecture review package.**
> Paste the output directly into ChatGPT, Claude, Gemini, or any LLM for instant architecture analysis.

---

## Features

| Feature | Detail |
|---|---|
| **One-click export** | All changed files exported, identical files skipped |
| **Function-level diff** | Extracts modified functions/classes, collapses unchanged regions |
| **AI Review Package** | Structured `/ai_review/` folder ready to feed an LLM |
| **Risk scoring** | Each file rated Low / Med / High based on path, content, and size |
| **Architecture analysis** | Detects new/removed components, API changes, new dependencies |
| **Token optimization** | Skip whitespace/comment-only changes; token count + cost estimate |
| **Stripped Patch** | 🔒 Redacts surrounding context with 4 redaction modes: |
| | • **Full**: Hide all except keywords (maximum secrecy) |
| | • **API-Safe** ⭐: Keep public APIs, types, stdlib (recommended) |
| | • **API-Safe+Comments**: Same as API-Safe, but preserve all comments (// /* */ ''' """) |
| | • **Signature**: Show only function signatures & control flow |
| **Drag-and-drop** | 📂 Drag files/folders directly into GUI (visual feedback, keyboard paste support) |
| **Multiple formats** | Markdown, unified diff, JSON |
| **GUI + CLI** | Tkinter GUI for quick use; full CLI for automation |
| **WinMerge plugin** | `.sct` plugin adds Tools menu items directly in WinMerge |
| **9 languages** | C/C++, C#, Python, Java, JavaScript, TypeScript |

---

## Prerequisites

Before using this tool, make sure the following are installed on your machine.

| Dependency | Minimum Version | Where to get it | Why required |
|---|---|---|---|
| **Python** | 3.10 | [python.org](https://www.python.org/downloads/) | Runtime — the tool is written in Python |
| **WinMerge** | 2.16.x | [winmerge.org](https://winmerge.org/downloads/) | Generates the `.patch` / diff files this tool reads |
| **Git** | 2.x | [git-scm.com](https://git-scm.com/) | Required only for `deploy-local.bat` (versioning + tagging) |
| **PyInstaller** | 6.x | `pip install pyinstaller` | Required only to build `.exe` releases (`build-release.bat`) |
| **Node.js + mermaid-cli** | Node 18+ | [nodejs.org](https://nodejs.org/) then `npm install -g @mermaid-js/mermaid-cli` | Optional — only needed to export Visualize Flow diagrams locally |

> **Restricted account note:** The core export and analysis features require **zero** third-party Python packages — everything runs on the Python standard library. You can use the tool on a corporate machine with no internet access.

---

## Quick Start

### Install

```bash
pip install winmerge-ai-exporter
```

### Use (CLI)

```bash
# From a WinMerge patch file
winmerge-ai-exporter export --patch changes.patch --output ./review

# From two folders (pure Python — no external 'diff' tool needed)
winmerge-ai-exporter export --left old/ --right new/ --output ./review

# From two individual files (pure Python — no external 'diff' tool needed)
winmerge-ai-exporter export --left-file old.cpp --right-file new.cpp --output ./review

# Estimate tokens before exporting
winmerge-ai-exporter estimate --patch changes.patch

# Copy prompt to clipboard
winmerge-ai-exporter copy-prompt --patch changes.patch

# Stripped Patch with different redaction modes:
winmerge-ai-exporter export --patch changes.patch --output ./review \
  --strip-patch --redaction-mode api-safe

# Keep all comments in output (best for old code with helpful comments)
winmerge-ai-exporter export --patch changes.patch --output ./review \
  --strip-patch --redaction-mode api-safe-comments

# Maximum security (hide all identifiers)
winmerge-ai-exporter export --patch changes.patch --output ./review \
  --strip-patch --redaction-mode full

# Adjust context window (default 1 line)
winmerge-ai-exporter export --patch changes.patch --output ./review \
  --strip-patch --strip-context 2
```

### Use (GUI)

```bash
# Launch the Tkinter GUI
python gui/launcher.py

# Or on Windows, double-click:
launch_gui.bat
```

### Use (Python API)

```python
from winmerge_ai_exporter import load_from_patch_file, export_ai_review_package

diffs = load_from_patch_file("changes.patch")
out   = export_ai_review_package(diffs, output_dir="./review")
print(f"Package at: {out}")
```

---

## Output Structure

```
ai_review/
├── summary.md               # Per-file table: LOC, symbols, risk level
├── changed_files.txt        # Quick list of all changed paths + risk
├── architecture_changes.md  # New/removed components, API changes, risks
├── review_data.json         # Machine-readable JSON (for automation)
├── prompts/
│   └── review_prompt.txt    # ← PASTE THIS INTO YOUR LLM
└── diffs/
    ├── Src_DiffEngine.cpp.diff.md
    ├── Src_auth_SessionManager.cpp.diff.md
    └── ...
```

### summary.md

For each changed file:
- File path
- Lines added / deleted
- Modified functions/classes (detected via AST-lite pattern matching)
- Risk level: 🟢 Low / 🟡 Med / 🔴 High

### architecture_changes.md

Inferred from diffs:
- New / removed classes and interfaces
- API / public method signature changes
- Added / removed imports and dependencies
- Concurrency and memory management risks
- Potential side effects

### review_prompt.txt

A structured prompt with all diffs embedded, ready to paste into any LLM:
```
Analyze these code changes. Focus on:
- architecture differences
- behavioral changes
- regression risks
- hidden side effects
- API contract changes
- concurrency/memory risks
- recommended test cases
```

---

## WinMerge Plugin Installation

1. Install the package: `pip install winmerge-ai-exporter`
2. Copy `winmerge_plugin/AIReviewExporter.sct` to:
   - `%APPDATA%\WinMerge\Plugins\`  (user)
   - `<WinMerge install>\Plugins\`  (system-wide)
3. Restart WinMerge
4. Use **File → Create Patch** to create a `.patch` file, then run the plugin on it

See [`winmerge_plugin/README.md`](winmerge_plugin/README.md) for full details.

---

## CLI Reference

```
winmerge-ai-exporter export   [options]    # Generate full package
winmerge-ai-exporter estimate [options]    # Token count only
winmerge-ai-exporter copy-prompt [options] # Copy LLM prompt to clipboard

Source (pick one):
  --patch FILE              Unified diff / patch file
  --xml FILE                WinMerge XML folder compare report
  --left-file F --right-file F   Compare two individual files
  --left DIR --right DIR    Compare two folders directly (recursive, pure Python)

Filters:
  --keep-whitespace     Include whitespace-only changes (default: skip)
  --keep-comments       Include comment-only changes (default: skip)

Export options:
  --output DIR          Output directory (default: .)
  --context N           Context lines around each change (default: 30)
  --no-json             Skip JSON export
  --source-label TEXT   Label for the comparison
```

---

## Stripped Patch (Sensitive Code Redaction)

For proprietary or security-sensitive codebases, enable **🔒 Stripped Patch**
(checkbox in the GUI, `--strip-patch` on the CLI) before sending diffs to an
external LLM. This mode:

- Keeps only the core changed (`+`/`-`) lines plus a small symmetric window
  of context (default ±1 line, configurable)
- Collapses everything else into a `··· [N line(s) redacted] ···` marker
- Pseudonymizes identifiers, string literals, and most numeric constants
  into generic placeholders (`sym_a1b2c3`, `<str>`, `<n>`) — the same name
  always maps to the same placeholder *within a file*, so an LLM can still
  follow repeated references, but the real names never leave your machine
- Preserves language structure (keywords, control flow, braces, common
  stdlib calls) so the LLM can still reason about *what changed logically*

```bash
# Default: ±1 line of context, full pseudonymization
winmerge-ai-exporter export --patch changes.patch --output ./review --strip-patch

# More context, still pseudonymized
winmerge-ai-exporter export --patch changes.patch --output ./review --strip-patch --strip-context 3

# Redact context only, keep real names (lighter redaction)
winmerge-ai-exporter export --patch changes.patch --output ./review --strip-patch --no-pseudonymize
```

Example output (`auth/SessionManager.cpp`):

```diff
@@ -34,12 +34,19 @@
··· [1 line(s) redacted] ···
 #include "<str>"
+#include "<str>"

-bool sym_4f987b::sym_d8bce1(const std::string& sym_490e3e) {
-    return sym_e89641::sym_74de42(sym_490e3e, sym_ccf604);
+bool sym_4f987b::sym_d8bce1(const std::string& sym_490e3e, const sym_d8b85c& sym_020b23) {
+    bool sym_72bcd6 = sym_e89641::sym_74de42(sym_490e3e, sym_ccf604);
+    if (!sym_72bcd6 && sym_020b23.sym_02c6f0 > sym_ac2604) {
+        sym_b780d0(sym_020b23.sym_8eba69);
+    }
+    return sym_72bcd6;
 }
```

This works in both the **Export Package** and **Copy Prompt** actions —
the LLM receives a disclaimer noting the patch is redacted and is asked to
reason about structure/shape rather than literal names.

---

## Risk Scoring

| Signal | Weight |
|---|---|
| Path contains `auth`, `crypto`, `security`, `payment`, `config`, `database` … | +4 |
| Path contains `service`, `controller`, `handler`, `model`, `factory` … | +2 |
| Dangerous code: `memcpy`, `eval()`, `subprocess`, `pickle.loads`, `new[]` … | +3 |
| Concurrency code: `mutex`, `thread`, `async`, `lock` … | +1 |
| Sensitive extension: `.sh`, `.sql`, `.bat`, `.ps1` | +3 |
| Large change (>300 LOC) | +3 |
| Many hunks (>10) | +2 |
| Binary file | +2 |

- **High** (score ≥ 4): Review carefully before merging
- **Med** (score 2–3): Review recommended
- **Low** (score 0–1): Routine change

---

## Supported Languages

| Language | Symbol detection | Import tracking |
|---|---|---|
| C / C++ | ✅ functions, classes, structs | ✅ `#include` |
| C# | ✅ methods, classes, interfaces | ✅ `using` |
| Python | ✅ `def`, `class` | ✅ `import`, `from … import` |
| Java | ✅ methods, classes, interfaces | ✅ `import` |
| JavaScript | ✅ functions, classes | ✅ `require()`, `import … from` |
| TypeScript | ✅ functions, classes, interfaces | ✅ `import … from` |

---

## Development

```bash
git clone <repo>
cd winmerge_ai_exporter
pip install -e ".[dev]"
pytest                        # 90 tests
pytest --cov=winmerge_ai_exporter --cov-report=term-missing
```

---

## Project Structure

```
winmerge_ai_exporter/
├── winmerge_ai_exporter/
│   ├── __init__.py             # Public API
│   ├── __main__.py             # python -m winmerge_ai_exporter
│   ├── cli.py                  # CLI (export / estimate / copy-prompt)
│   ├── diff_parser.py          # Unified diff parser + symbol extractor
│   ├── risk_scorer.py          # Heuristic risk classification
│   ├── arch_analyzer.py        # Architecture change inference
│   ├── token_estimator.py      # Token count + cost estimation
│   ├── redactor.py             # Stripped Patch: context redaction + pseudonymization
│   ├── exporter.py             # Package generator (all output files)
│   └── winmerge_integration.py # WinMerge formats + pure-Python file/folder compare
├── gui/
│   ├── launcher.py             # Tkinter GUI
│   ├── __init__.py
│   └── __main__.py
├── winmerge_plugin/
│   ├── AIReviewExporter.sct    # WinMerge JScript plugin
│   └── README.md               # Plugin installation guide
├── tests/
│   ├── conftest.py
│   ├── test_diff_parser.py            # 25 tests
│   ├── test_risk_scorer.py            # 16 tests
│   ├── test_arch_and_tokens.py        # 23 tests
│   ├── test_integration.py            # 26 tests
│   ├── test_winmerge_integration.py   # 22 tests
│   └── test_redactor.py               # 26 tests
├── sample_diffs/
│   └── sample_changes.patch    # Demo patch (WinMerge C++ codebase)
├── launch_gui.bat              # Windows one-click GUI launcher
├── pyproject.toml
└── README.md
```

**138 tests total, all passing.**

---

## License

MIT
