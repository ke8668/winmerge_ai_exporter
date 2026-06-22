# WinMerge AI Review Exporter — Plugin Installation

## Requirements

- WinMerge 2.16+ (Windows)
- Python 3.10+ on PATH
- Package installed: `pip install winmerge-ai-exporter`

## Installation

### Option A — pip + plugin file (recommended)

1. Install the Python package:
   ```
   pip install winmerge-ai-exporter
   ```

2. Copy `AIReviewExporter.sct` to one of:
   - **User-only:** `%APPDATA%\WinMerge\Plugins\`
   - **System-wide:** `<WinMerge install folder>\Plugins\`

3. Restart WinMerge. The plugin appears under **Plugins** menu.

### Option B — standalone (no pip, portable)

1. Copy the entire `winmerge_ai_exporter/` Python package folder next to
   `AIReviewExporter.sct` in the Plugins folder.
2. Python still needs to be on PATH.

---

## Usage

### Workflow 1 — File Compare

1. Open two files in WinMerge.
2. **File → Create Patch…** → save as `changes.patch`.
3. Open `changes.patch` in WinMerge (or just note its path).
4. **Plugins → AI Review Exporter → Export AI Review Package**
5. Open the generated `ai_review/` folder — paste `prompts/review_prompt.txt`
   into ChatGPT / Claude / Gemini.

### Workflow 2 — Folder Compare

1. Open two folders in WinMerge.
2. **File → Create Patch…** → save as `folder_changes.patch`.
3. Run the plugin on the patch file (same as above).

### Workflow 3 — CLI (no WinMerge GUI needed)

```bat
rem Export
python -m winmerge_ai_exporter export --patch changes.patch --output C:\Reviews

rem Estimate tokens before exporting
python -m winmerge_ai_exporter estimate --patch changes.patch

rem Copy prompt to clipboard
python -m winmerge_ai_exporter copy-prompt --patch changes.patch

rem Compare two folders directly (requires diff on PATH)
python -m winmerge_ai_exporter export --left old\ --right new\ --output C:\Reviews
```

---

## Menu Items

| Menu Item | Action |
|---|---|
| **Export AI Review Package** | Generates full `/ai_review/` folder with all files |
| **Copy AI Review Prompt** | Puts the ready-to-paste LLM prompt on clipboard |
| **Estimate AI Tokens** | Shows token count + cost estimate before exporting |

---

## Troubleshooting

**"Python not found on PATH"**
Add Python to your system PATH, or edit `AIReviewExporter.sct` and hardcode
the path: replace `"python"` with `"C:\\Python312\\python.exe"`.

**Plugin doesn't appear in WinMerge**
Ensure the file is in the correct Plugins directory and WinMerge was restarted.
Check WinMerge → Edit → Options → Plugins → Enable plugins.

**Empty diffs**
Make sure to use **File → Create Patch** with "Unified" format selected.
