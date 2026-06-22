"""
gui/launcher.py
Tkinter-based GUI launcher for WinMerge AI Review Exporter.

Run with:
    python -m winmerge_ai_exporter.gui
    python gui/launcher.py
"""


from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font, messagebox, scrolledtext, ttk



import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure package importable when run directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ---------------------------------------------------------------------------
# Colours / style constants
# ---------------------------------------------------------------------------

BG        = "#1e1e2e"
PANEL     = "#2a2a3e"
ACCENT    = "#7c6af7"
ACCENT2   = "#5eead4"
FG        = "#cdd6f4"
FG_DIM    = "#6c7086"
DANGER    = "#f38ba8"
SUCCESS   = "#a6e3a1"
WARN      = "#fab387"
BTN_FG    = "#ffffff"
ENTRY_BG  = "#313244"
ENTRY_FG  = "#cdd6f4"
MONO_FONT = ("Consolas", "Courier New", "monospace")


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class AIReviewGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WinMerge AI Review Exporter")
        self.resizable(True, True)
        self.minsize(720, 560)
        self.configure(bg=BG)
        self._set_icon()
        self._build_ui()
        self.update_idletasks()
        # Centre on screen
        w, h = 860, 680
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ------------------------------------------------------------------
    def _set_icon(self):
        try:
            # Use a simple emoji-based title icon fallback
            self.iconbitmap(default="")
        except Exception:
            pass

    # ------------------------------------------------------------------
    def _build_ui(self):
        self._build_header()
        self._build_source_panel()
        self._build_options_panel()
        self._build_action_buttons()
        self._build_log_panel()
        self._build_status_bar()

    # ------------------------------------------------------------------
    def _label(self, parent, text, **kw) -> tk.Label:
        kw.setdefault("bg", BG)
        kw.setdefault("fg", FG)
        kw.setdefault("anchor", "w")
        return tk.Label(parent, text=text, **kw)

    def _btn(self, parent, text, command, color=ACCENT, width=22, **kw) -> tk.Button:
        return tk.Button(
            parent, text=text, command=command,
            bg=color, fg=BTN_FG,
            activebackground=color, activeforeground=BTN_FG,
            relief="flat", bd=0, cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=10, pady=6, width=width,
            **kw,
        )

    def _entry(self, parent, textvariable, **kw) -> tk.Entry:
        return tk.Entry(
            parent, textvariable=textvariable,
            bg=ENTRY_BG, fg=ENTRY_FG,
            insertbackground=FG, relief="flat",
            font=("Segoe UI", 10),
            **kw,
        )

    # ------------------------------------------------------------------
    def _build_header(self):
        hdr = tk.Frame(self, bg=PANEL, pady=14)
        hdr.pack(fill="x")
        tk.Label(
            hdr,
            text="🤖  WinMerge AI Review Exporter",
            bg=PANEL, fg=ACCENT,
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left", padx=20)
        tk.Label(
            hdr,
            text="v1.0.0",
            bg=PANEL, fg=FG_DIM,
            font=("Segoe UI", 9),
        ).pack(side="right", padx=20)

    # ------------------------------------------------------------------
    def _build_source_panel(self):
        frm = tk.LabelFrame(
            self, text="  Diff Source  ",
            bg=BG, fg=ACCENT2,
            font=("Segoe UI", 10, "bold"),
            relief="flat", bd=1,
            highlightbackground=PANEL, highlightthickness=1,
        )
        frm.pack(fill="x", padx=16, pady=(12, 4))

        # --- Source mode tabs ---
        self._mode = tk.StringVar(value="patch")
        modes = [("Patch / Diff File", "patch"), ("Compare Folders", "folders")]
        tab_row = tk.Frame(frm, bg=BG)
        tab_row.pack(fill="x", padx=10, pady=(8, 4))
        for label, value in modes:
            tk.Radiobutton(
                tab_row, text=label, variable=self._mode, value=value,
                command=self._on_mode_change,
                bg=BG, fg=FG, selectcolor=PANEL,
                activebackground=BG, activeforeground=ACCENT,
                font=("Segoe UI", 10),
            ).pack(side="left", padx=8)

        # --- Patch row ---
        self._patch_frame = tk.Frame(frm, bg=BG)
        self._patch_frame.pack(fill="x", padx=10, pady=4)
        self._label(self._patch_frame, "Patch file:").pack(anchor="w")
        pr = tk.Frame(self._patch_frame, bg=BG)
        pr.pack(fill="x")
        self._patch_var = tk.StringVar()
        self._entry(pr, self._patch_var).pack(side="left", fill="x", expand=True, ipady=4)
        self._btn(pr, "Browse…", self._browse_patch, width=10).pack(side="right", padx=(6, 0))

        # --- Folder rows ---
        self._folder_frame = tk.Frame(frm, bg=BG)
        for attr, label, browse_fn in [
            ("_left_var",  "Left (old):",  self._browse_left),
            ("_right_var", "Right (new):", self._browse_right),
        ]:
            row_frm = tk.Frame(self._folder_frame, bg=BG)
            row_frm.pack(fill="x", pady=2)
            self._label(row_frm, label).pack(anchor="w")
            r = tk.Frame(row_frm, bg=BG)
            r.pack(fill="x")
            var = tk.StringVar()
            setattr(self, attr, var)
            self._entry(r, var).pack(side="left", fill="x", expand=True, ipady=4)
            self._btn(r, "Browse…", browse_fn, width=10).pack(side="right", padx=(6, 0))

        # --- Output dir ---
        out_frm = tk.Frame(frm, bg=BG)
        out_frm.pack(fill="x", padx=10, pady=(4, 10))
        self._label(out_frm, "Output directory:").pack(anchor="w")
        or_ = tk.Frame(out_frm, bg=BG)
        or_.pack(fill="x")
        self._out_var = tk.StringVar(value=str(Path.home() / "ai_review_output"))
        self._entry(or_, self._out_var).pack(side="left", fill="x", expand=True, ipady=4)
        self._btn(or_, "Browse…", self._browse_output, width=10).pack(side="right", padx=(6, 0))

        self._on_mode_change()

    # ------------------------------------------------------------------
    def _build_options_panel(self):
        frm = tk.LabelFrame(
            self, text="  Options  ",
            bg=BG, fg=ACCENT2,
            font=("Segoe UI", 10, "bold"),
            relief="flat", bd=1,
            highlightbackground=PANEL, highlightthickness=1,
        )
        frm.pack(fill="x", padx=16, pady=4)

        row1 = tk.Frame(frm, bg=BG)
        row1.pack(fill="x", padx=10, pady=6)

        # Context lines
        self._label(row1, "Context lines:").pack(side="left")
        self._ctx_var = tk.IntVar(value=30)
        ctx_spin = tk.Spinbox(
            row1, from_=0, to=200, textvariable=self._ctx_var,
            width=5, bg=ENTRY_BG, fg=ENTRY_FG, relief="flat",
            buttonbackground=PANEL,
        )
        ctx_spin.pack(side="left", padx=(4, 20))

        # Checkboxes
        self._skip_ws = tk.BooleanVar(value=True)
        self._skip_comments = tk.BooleanVar(value=True)
        self._include_json = tk.BooleanVar(value=True)

        for text, var in [
            ("Skip whitespace-only changes", self._skip_ws),
            ("Skip comment-only changes",    self._skip_comments),
            ("Include JSON export",          self._include_json),
        ]:
            tk.Checkbutton(
                row1, text=text, variable=var,
                bg=BG, fg=FG, selectcolor=PANEL,
                activebackground=BG, activeforeground=ACCENT,
                font=("Segoe UI", 10),
            ).pack(side="left", padx=8)

    # ------------------------------------------------------------------
    def _build_action_buttons(self):
        frm = tk.Frame(self, bg=BG)
        frm.pack(fill="x", padx=16, pady=8)

        self._btn(frm, "⚡  Estimate Tokens",  self._run_estimate,  color="#5c5f77", width=20).pack(side="left", padx=(0, 8))
        self._btn(frm, "📋  Copy Prompt",       self._run_copy,      color="#5c5f77", width=16).pack(side="left", padx=(0, 8))
        self._btn(frm, "📦  Export Package",    self._run_export,    color=ACCENT,    width=18).pack(side="left")
        self._btn(frm, "🗂  Open Output",       self._open_output,   color="#3d5a80", width=14).pack(side="right")

    # ------------------------------------------------------------------
    def _build_log_panel(self):
        frm = tk.LabelFrame(
            self, text="  Log  ",
            bg=BG, fg=ACCENT2,
            font=("Segoe UI", 10, "bold"),
            relief="flat", bd=1,
            highlightbackground=PANEL, highlightthickness=1,
        )
        frm.pack(fill="both", expand=True, padx=16, pady=(4, 4))

        self._log = scrolledtext.ScrolledText(
            frm,
            bg="#11111b", fg=FG,
            font=(MONO_FONT[0], 9),
            relief="flat", wrap="word",
            state="disabled",
        )
        self._log.pack(fill="both", expand=True, padx=4, pady=4)
        # Tags for coloured log output
        self._log.tag_config("info",    foreground=FG)
        self._log.tag_config("success", foreground=SUCCESS)
        self._log.tag_config("warn",    foreground=WARN)
        self._log.tag_config("error",   foreground=DANGER)
        self._log.tag_config("header",  foreground=ACCENT2, font=(MONO_FONT[0], 9, "bold"))

    # ------------------------------------------------------------------
    def _build_status_bar(self):
        self._status_var = tk.StringVar(value="Ready")
        self._progress = ttk.Progressbar(self, mode="indeterminate", length=200)
        bar = tk.Frame(self, bg=PANEL, pady=4)
        bar.pack(fill="x", side="bottom")
        tk.Label(bar, textvariable=self._status_var, bg=PANEL, fg=FG_DIM,
                 font=("Segoe UI", 9)).pack(side="left", padx=12)
        self._progress_bar = ttk.Progressbar(bar, mode="indeterminate", length=120)
        self._progress_bar.pack(side="right", padx=12)

    # ------------------------------------------------------------------
    # Mode switching
    # ------------------------------------------------------------------
    def _on_mode_change(self):
        mode = self._mode.get()
        if mode == "patch":
            self._folder_frame.pack_forget()
            self._patch_frame.pack(fill="x", padx=10, pady=4)
        else:
            self._patch_frame.pack_forget()
            self._folder_frame.pack(fill="x", padx=10, pady=4)

    # ------------------------------------------------------------------
    # File / folder browsers
    # ------------------------------------------------------------------
    def _browse_patch(self):
        p = filedialog.askopenfilename(
            title="Select patch / diff file",
            filetypes=[("Patch files", "*.patch *.diff"), ("All files", "*.*")],
        )
        if p:
            self._patch_var.set(p)

    def _browse_left(self):
        d = filedialog.askdirectory(title="Select LEFT (old) folder")
        if d:
            self._left_var.set(d)

    def _browse_right(self):
        d = filedialog.askdirectory(title="Select RIGHT (new) folder")
        if d:
            self._right_var.set(d)

    def _browse_output(self):
        d = filedialog.askdirectory(title="Select output directory")
        if d:
            self._out_var.set(d)

    def _open_output(self):
        out = Path(self._out_var.get()) / "ai_review"
        target = out if out.exists() else Path(self._out_var.get())
        if target.exists():
            os.startfile(str(target))
        else:
            messagebox.showinfo("Not found", f"Output folder not found:\n{target}")

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    def _log_write(self, text: str, tag: str = "info"):
        self._log.configure(state="normal")
        self._log.insert("end", text + "\n", tag)
        self._log.see("end")
        self._log.configure(state="disabled")

    def _log_clear(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    def _set_status(self, text: str):
        self._status_var.set(text)
        self.update_idletasks()

    # ------------------------------------------------------------------
    # Build FileDiff list from current UI state
    # ------------------------------------------------------------------
    def _load_diffs(self):
        from winmerge_ai_exporter import (
            load_from_patch_file,
            load_from_patch_text,
        )
        from winmerge_ai_exporter.winmerge_integration import generate_diff_between_folders

        if self._mode.get() == "patch":
            patch = self._patch_var.get().strip()
            if not patch or not Path(patch).exists():
                raise ValueError(f"Patch file not found: {patch!r}")
            self._log_write(f"Loading patch: {patch}", "info")
            return load_from_patch_file(patch)
        else:
            left  = self._left_var.get().strip()
            right = self._right_var.get().strip()
            if not left or not right:
                raise ValueError("Please specify both Left and Right folders.")
            self._log_write(f"Comparing folders:\n  LEFT : {left}\n  RIGHT: {right}", "info")
            return generate_diff_between_folders(left, right)

    # ------------------------------------------------------------------
    # Actions (run in threads to keep UI responsive)
    # ------------------------------------------------------------------
    def _start_spinner(self):
        self._progress_bar.start(12)

    def _stop_spinner(self):
        self._progress_bar.stop()

    def _run_in_thread(self, fn):
        self._log_clear()
        self._start_spinner()
        threading.Thread(target=self._thread_wrapper, args=(fn,), daemon=True).start()

    def _thread_wrapper(self, fn):
        try:
            fn()
        except Exception as exc:
            self.after(0, self._log_write, f"ERROR: {exc}", "error")
        finally:
            self.after(0, self._stop_spinner)
            self.after(0, self._set_status, "Done")

    # ··· Estimate tokens ···
    def _run_estimate(self):
        self._run_in_thread(self._do_estimate)

    def _do_estimate(self):
        from winmerge_ai_exporter.token_estimator import estimate_for_diffs
        self._set_status("Estimating tokens…")
        diffs = self._load_diffs()
        changed = [d for d in diffs if not d.is_identical()]
        self._log_write(f"Parsed {len(diffs)} files, {len(changed)} with changes.", "info")
        est = estimate_for_diffs(
            changed,
            skip_whitespace=self._skip_ws.get(),
            skip_comments=self._skip_comments.get(),
        )
        self._log_write("\n📊 Token Estimation", "header")
        self._log_write("=" * 48, "header")
        self._log_write(est.summary(), "success")

    # ··· Copy prompt ···
    def _run_copy(self):
        self._run_in_thread(self._do_copy)

    def _do_copy(self):
        from winmerge_ai_exporter.diff_parser import extract_modified_symbols
        from winmerge_ai_exporter.exporter import _render_prompt
        from winmerge_ai_exporter.risk_scorer import score_file
        self._set_status("Generating prompt…")
        diffs = self._load_diffs()
        changed = [d for d in diffs if not d.is_identical()]
        risks = {fd.path: score_file(fd) for fd in changed}
        syms  = {fd.path: extract_modified_symbols(fd) for fd in changed}
        prompt = _render_prompt(
            changed, risks, syms,
            skip_whitespace=self._skip_ws.get(),
            skip_comments=self._skip_comments.get(),
        )
        # Copy to clipboard (main thread required)
        self.after(0, self._copy_to_clipboard, prompt)
        chars = len(prompt)
        tokens = chars // 4
        self._log_write(f"Prompt ready: {chars:,} chars / ~{tokens:,} tokens", "success")
        self._log_write("Copied to clipboard — paste into any LLM!", "success")

    def _copy_to_clipboard(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)

    # ··· Export package ···
    def _run_export(self):
        self._run_in_thread(self._do_export)

    def _do_export(self):
        from winmerge_ai_exporter import export_ai_review_package
        from winmerge_ai_exporter.token_estimator import estimate_for_diffs
        self._set_status("Exporting package…")
        diffs = self._load_diffs()
        changed = [d for d in diffs if not d.is_identical()]
        self._log_write(f"Parsed {len(diffs)} files, {len(changed)} with changes.", "info")

        # Token pre-estimate
        est = estimate_for_diffs(changed,
                                 skip_whitespace=self._skip_ws.get(),
                                 skip_comments=self._skip_comments.get())
        self._log_write(f"Estimated tokens: {est.estimated_tokens:,}  "
                        f"(~${est.estimated_cost_usd:.4f} GPT-4o ref)", "info")

        out_dir = self._out_var.get().strip() or "."
        out = export_ai_review_package(
            diffs,
            output_dir=out_dir,
            context_lines=self._ctx_var.get(),
            skip_whitespace=self._skip_ws.get(),
            skip_comments=self._skip_comments.get(),
            include_json=self._include_json.get(),
        )

        self._log_write(f"\n✅ Package exported to:\n   {out}", "success")
        self._log_write("\nContents:", "header")
        for f in sorted(out.rglob("*")):
            if f.is_file():
                size = f.stat().st_size
                self._log_write(f"  {str(f.relative_to(out)):<50}  {size:>8,} bytes", "info")

        # Risk summary
        import json
        data = json.loads((out / "review_data.json").read_text()) if (out / "review_data.json").exists() else {}
        if data.get("files"):
            highs = [f for f in data["files"] if f["risk_level"] == "High"]
            if highs:
                self._log_write(f"\n🔴 {len(highs)} High-risk file(s):", "warn")
                for hf in highs:
                    self._log_write(f"   {hf['path']}", "warn")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = AIReviewGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
