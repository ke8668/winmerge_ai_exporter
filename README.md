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
| **Multiple formats** | Markdown, unified diff, JSON |
| **GUI + CLI** | Tkinter GUI for quick use; full CLI for automation |
| **WinMerge plugin** | `.sct` plugin adds Tools menu items directly in WinMerge |
| **9 languages** | C/C++, C#, Python, Java, JavaScript, TypeScript |

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

# From two folders (requires diff on PATH)
winmerge-ai-exporter export --left old/ --right new/ --output ./review

# Estimate tokens before exporting
winmerge-ai-exporter estimate --patch changes.patch

# Copy prompt to clipboard
winmerge-ai-exporter copy-prompt --patch changes.patch
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
  --patch FILE          Unified diff / patch file
  --xml FILE            WinMerge XML folder compare report
  --left DIR --right DIR   Compare two folders directly

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
│   ├── exporter.py             # Package generator (all output files)
│   └── winmerge_integration.py # WinMerge formats + folder compare
├── gui/
│   ├── launcher.py             # Tkinter GUI
│   ├── __init__.py
│   └── __main__.py
├── winmerge_plugin/
│   ├── AIReviewExporter.sct    # WinMerge JScript plugin
│   └── README.md               # Plugin installation guide
├── tests/
│   ├── conftest.py
│   ├── test_diff_parser.py     # 20 tests
│   ├── test_risk_scorer.py     # 15 tests
│   ├── test_arch_and_tokens.py # 22 tests
│   └── test_integration.py     # 33 tests
├── sample_diffs/
│   └── sample_changes.patch    # Demo patch (WinMerge C++ codebase)
├── launch_gui.bat              # Windows one-click GUI launcher
├── pyproject.toml
└── README.md
```

---

## License

MIT
