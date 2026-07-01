"""
mermaid_panel.py — Mermaid diagram visualization panel for GUI.

MIT License - Original Author: Claude (Anthropic)
Copyright (c) 2024-2025. See LICENSE file for details.

Provides a panel in the GUI to:
- Display Mermaid diagram code
- Show preview (as text or HTML)
- Export diagrams
- Copy code to clipboard
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
from pathlib import Path


class MermaidPanel:
    """GUI panel for displaying and managing Mermaid diagrams."""
    
    def __init__(self, parent, bg="white", fg="black"):
        """
        Initialize Mermaid panel.
        
        Args:
            parent: Parent tkinter widget
            bg: Background color
            fg: Foreground color
        """
        self.parent = parent
        self.bg = bg
        self.fg = fg
        
        # Create main frame
        self.frame = tk.Frame(parent, bg=bg)
        
        # Top toolbar
        self._create_toolbar()
        
        # Diagram type selector
        self._create_type_selector()
        
        # Mermaid code display
        self._create_code_display()
        
        # Status bar
        self._create_status_bar()
        
        self.current_mermaid_code = ""
    
    def _create_toolbar(self):
        """Create toolbar with action buttons."""
        toolbar = tk.Frame(self.frame, bg=self.bg, relief=tk.RAISED, bd=1)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Copy button
        tk.Button(
            toolbar,
            text="📋 Copy Code",
            command=self.copy_to_clipboard,
            bg="#4CAF50",
            fg="white",
            padx=10,
            pady=5
        ).pack(side=tk.LEFT, padx=2)
        
        # Export button
        tk.Button(
            toolbar,
            text="💾 Export SVG",
            command=self.export_svg,
            bg="#2196F3",
            fg="white",
            padx=10,
            pady=5
        ).pack(side=tk.LEFT, padx=2)
        
        # Export PNG button
        tk.Button(
            toolbar,
            text="🖼️ Export PNG",
            command=self.export_png,
            bg="#FF9800",
            fg="white",
            padx=10,
            pady=5
        ).pack(side=tk.LEFT, padx=2)
        
        # Open in editor button
        tk.Button(
            toolbar,
            text="✏️ Edit Online",
            command=self.open_in_editor,
            bg="#9C27B0",
            fg="white",
            padx=10,
            pady=5
        ).pack(side=tk.LEFT, padx=2)
    
    def _create_type_selector(self):
        """Create diagram type selector."""
        type_frame = tk.Frame(self.frame, bg=self.bg)
        type_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(
            type_frame,
            text="Diagram Type:",
            bg=self.bg,
            fg=self.fg
        ).pack(side=tk.LEFT, padx=5)
        
        self.diagram_type = tk.StringVar(value="flowchart")
        
        types = [
            ("📊 Flowchart", "flowchart"),
            ("🔄 Sequence", "sequence"),
            ("🎯 State Machine", "state"),
        ]
        
        for label, value in types:
            tk.Radiobutton(
                type_frame,
                text=label,
                variable=self.diagram_type,
                value=value,
                bg=self.bg,
                fg=self.fg,
                command=self.on_type_changed
            ).pack(side=tk.LEFT, padx=5)
    
    def _create_code_display(self):
        """Create code display area."""
        # Label
        tk.Label(
            self.frame,
            text="Mermaid Code:",
            bg=self.bg,
            fg=self.fg,
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, padx=5, pady=(10, 5))
        
        # Scrolled text widget
        self.code_text = scrolledtext.ScrolledText(
            self.frame,
            height=15,
            width=80,
            bg="#f5f5f5",
            fg="#333333",
            font=("Consolas", 9),
            wrap=tk.WORD
        )
        self.code_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Make read-only
        self.code_text.config(state=tk.DISABLED)
    
    def _create_status_bar(self):
        """Create status bar."""
        self.status_frame = tk.Frame(self.frame, bg="#e0e0e0", relief=tk.SUNKEN, bd=1)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="Ready",
            bg="#e0e0e0",
            fg="#666666",
            font=("Arial", 9),
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, padx=5, pady=2)
    
    def display_code(self, mermaid_code: str):
        """
        Display Mermaid code in the panel.
        
        Args:
            mermaid_code: Mermaid diagram code
        """
        self.current_mermaid_code = mermaid_code
        
        # Update text display
        self.code_text.config(state=tk.NORMAL)
        self.code_text.delete(1.0, tk.END)
        self.code_text.insert(1.0, mermaid_code)
        self.code_text.config(state=tk.DISABLED)
        
        # Update status
        lines = mermaid_code.count('\n') + 1
        self.status_label.config(text=f"✅ Code loaded ({lines} lines)")
    
    def copy_to_clipboard(self):
        """Copy Mermaid code to clipboard."""
        if not self.current_mermaid_code:
            messagebox.showwarning("Empty", "No diagram code to copy")
            return
        
        # Copy to clipboard (platform-specific)
        try:
            # Try xclip (Linux)
            import subprocess
            process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
            process.communicate(self.current_mermaid_code.encode('utf-8'))
            self.status_label.config(text="✅ Code copied to clipboard")
        except:
            try:
                # Try pbcopy (macOS)
                import subprocess
                process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
                process.communicate(self.current_mermaid_code.encode('utf-8'))
                self.status_label.config(text="✅ Code copied to clipboard")
            except:
                # Fallback: use tkinter
                self.parent.clipboard_clear()
                self.parent.clipboard_append(self.current_mermaid_code)
                self.status_label.config(text="✅ Code copied to clipboard")
    
    def export_svg(self):
        """Export diagram as SVG (requires mermaid-cli)."""
        if not self.current_mermaid_code:
            messagebox.showwarning("Empty", "No diagram to export")
            return
        
        try:
            import subprocess
            from pathlib import Path
            import tempfile
            
            # Check if mermaid-cli is installed
            result = subprocess.run(['mmdc', '--version'], capture_output=True)
            if result.returncode != 0:
                messagebox.showwarning(
                    "Not Installed",
                    "mermaid-cli is not installed.\n\n"
                    "Install with: npm install -g @mermaid-js/mermaid-cli\n\n"
                    "Or visit: https://mermaid.live/ for online editor"
                )
                return
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
                f.write(self.current_mermaid_code)
                mmd_file = f.name
            
            svg_file = mmd_file.replace('.mmd', '.svg')
            
            # Convert
            subprocess.run(['mmdc', '-i', mmd_file, '-o', svg_file], check=True)
            
            # Open file
            import webbrowser
            webbrowser.open(f'file://{svg_file}')
            
            self.status_label.config(text=f"✅ SVG exported to {svg_file}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export SVG:\n{str(e)}")
    
    def export_png(self):
        """Export diagram as PNG (requires mermaid-cli)."""
        if not self.current_mermaid_code:
            messagebox.showwarning("Empty", "No diagram to export")
            return
        
        try:
            import subprocess
            from pathlib import Path
            import tempfile
            
            # Check if mermaid-cli is installed
            result = subprocess.run(['mmdc', '--version'], capture_output=True)
            if result.returncode != 0:
                messagebox.showwarning(
                    "Not Installed",
                    "mermaid-cli is not installed.\n\n"
                    "Install with: npm install -g @mermaid-js/mermaid-cli\n\n"
                    "Or visit: https://mermaid.live/ for online editor"
                )
                return
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
                f.write(self.current_mermaid_code)
                mmd_file = f.name
            
            png_file = mmd_file.replace('.mmd', '.png')
            
            # Convert
            subprocess.run(['mmdc', '-i', mmd_file, '-o', png_file, '-e', 'png'], check=True)
            
            # Open file
            import webbrowser
            webbrowser.open(f'file://{png_file}')
            
            self.status_label.config(text=f"✅ PNG exported to {png_file}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PNG:\n{str(e)}")
    
    def open_in_editor(self):
        """Open Mermaid code in online editor (mermaid.live)."""
        if not self.current_mermaid_code:
            messagebox.showwarning("Empty", "No diagram to display")
            return
        
        import webbrowser
        import urllib.parse
        
        # URL encode the mermaid code
        encoded = urllib.parse.quote(self.current_mermaid_code)
        url = f"https://mermaid.live/edit#{encoded}"
        
        # Open in default browser
        webbrowser.open(url)
        self.status_label.config(text="✅ Opened in mermaid.live")
    
    def on_type_changed(self):
        """Called when diagram type changes."""
        # This will be called by parent to regenerate diagram
        pass
    
    def pack(self, **kwargs):
        """Pack the frame."""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the frame."""
        self.frame.grid(**kwargs)
