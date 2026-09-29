#!/usr/bin/env python3
"""
QuickBMS Frontend
A single-file Tkinter frontend for QuickBMS.

The program downloads the official Windows QuickBMS ZIP when requested,
extracts it locally, lets you select a BMS script/input/output, builds
QuickBMS command lines, and streams QuickBMS output into the GUI.

Requires: Python 3.9+ (standard library only)
"""

import os
import sys
import re
import shlex
import zipfile
import tempfile
import threading
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_NAME = "QuickBMS Frontend"
GITHUB_URL = "https://github.com/LittleBigBug/QuickBMS"
QUICKBMS_PAGE = "https://aluigi.altervista.org/quickbms.htm"

# Official Windows package commonly distributed by the QuickBMS author.
DOWNLOAD_URL = "https://aluigi.altervista.org/papers/quickbms.zip"

APP_DIR = Path(__file__).resolve().parent
QBMS_DIR = APP_DIR / "QuickBMS"
ZIP_PATH = APP_DIR / "quickbms_download.zip"


def q(value):
    """Quote a command argument safely for Windows subprocess/list display."""
    return str(value)


class QuickBMSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1180x820")
        self.minsize(980, 700)

        self.quickbms_exe = tk.StringVar()
        self.status_var = tk.StringVar(value="QuickBMS is not configured.")
        self.progress_var = tk.DoubleVar(value=0)

        self.script_var = tk.StringVar()
        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()

        self.mode_var = tk.StringVar(value="Extract")
        self.reimport_mode = tk.IntVar(value=1)

        self.filter_var = tk.StringVar()
        self.folder_filter_var = tk.StringVar()

        self.flag_vars = {}
        self.advanced_vars = {}
        self.security_vars = {}

        self.process = None
        self.stop_requested = False

        self._style()
        self._build_ui()
        self._detect_existing()

    def _style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("Big.TButton", font=("Segoe UI", 11, "bold"), padding=10)
        style.configure("Accent.TButton", font=("Segoe UI", 12, "bold"), padding=12)

    def _build_ui(self):
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill="both", expand=True)

        title = ttk.Frame(outer)
        title.pack(fill="x", pady=(0, 10))
        ttk.Label(title, text="QuickBMS Frontend", style="Title.TLabel").pack(side="left")
        ttk.Label(title, text="GUI wrapper • extraction • reimport • advanced options",
                  foreground="#666").pack(side="left", padx=15, pady=(7, 0))

        self.notebook = ttk.Notebook(outer)
        self.notebook.pack(fill="both", expand=True)

        self.setup_tab = ttk.Frame(self.notebook, padding=12)
        self.main_tab = ttk.Frame(self.notebook, padding=12)

        self.notebook.add(self.setup_tab, text="  1 • Setup  ")
        self.notebook.add(self.main_tab, text="  2 • QuickBMS  ")

        self._build_setup()
        self._build_main()

    # ---------------- SETUP TAB ----------------

    def _build_setup(self):
        tab = self.setup_tab

        top = ttk.LabelFrame(tab, text="QuickBMS Installation", padding=14)
        top.pack(fill="x")

        ttk.Label(top, text="Executable:").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.quickbms_exe, width=82).grid(
            row=0, column=1, sticky="ew", padx=8)
        ttk.Button(top, text="Browse...", command=self.browse_exe).grid(row=0, column=2)

        top.columnconfigure(1, weight=1)

        buttons = ttk.Frame(top)
        buttons.grid(row=1, column=0, columnspan=3, sticky="w", pady=(14, 4))

        ttk.Button(buttons, text="Download & Install QuickBMS",
                   style="Accent.TButton",
                   command=self.download_quickbms).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Detect Installation",
                   command=self._detect_existing).pack(side="left", padx=4)
        ttk.Button(buttons, text="Open QuickBMS Folder",
                   command=self.open_qbms_folder).pack(side="left", padx=4)

        status = ttk.LabelFrame(tab, text="Status", padding=14)
        status.pack(fill="x", pady=12)

        ttk.Label(status, textvariable=self.status_var,
                  font=("Segoe UI", 11)).pack(anchor="w")
        self.progress = ttk.Progressbar(status, variable=self.progress_var,
                                        maximum=100)
        self.progress.pack(fill="x", pady=(10, 0))

        info = ttk.LabelFrame(tab, text="What this frontend does", padding=14)
        info.pack(fill="both", expand=True)

        text = (
            "This frontend keeps the original QuickBMS executable intact and "
            "builds command lines for it.\n\n"
            "Setup downloads the Windows QuickBMS package and extracts it into "
            "a QuickBMS folder beside this Python program. Existing installations "
            "can also be selected manually.\n\n"
            "Once configured, switch to the QuickBMS tab. The GUI exposes the "
            "normal extraction workflow, file filters, reimport modes, advanced "
            "debug/experimental switches, security/capability switches, and a "
            "live console.\n\n"
            "Important: QuickBMS scripts can perform powerful operations. "
            "Only enable security/capability options when you understand what "
            "the script requires."
        )
        ttk.Label(info, text=text, justify="left", wraplength=900).pack(
            anchor="nw", fill="x")

        links = ttk.Frame(info)
        links.pack(anchor="w", pady=18)
        ttk.Button(links, text="Open GitHub",
                   command=lambda: self.open_url(GITHUB_URL)).pack(side="left")
        ttk.Button(links, text="Open QuickBMS Website",
                   command=lambda: self.open_url(QUICKBMS_PAGE)).pack(
                       side="left", padx=8)

    def _detect_existing(self):
        candidates = [
            QBMS_DIR / "quickbms.exe",
            APP_DIR / "quickbms.exe",
            Path.home() / "QuickBMS" / "quickbms.exe",
        ]

        current = self.quickbms_exe.get().strip()
        if current and Path(current).is_file():
            self.set_status(f"Ready: {current}")
            return

        for c in candidates:
            if c.is_file():
                self.quickbms_exe.set(str(c))
                self.set_status(f"Ready: {c}")
                return

        self.set_status("QuickBMS is not configured. Download it or browse to quickbms.exe.")

    def browse_exe(self):
        path = filedialog.askopenfilename(
            title="Select quickbms.exe",
            filetypes=[("QuickBMS executable", "quickbms.exe"),
                       ("Executable", "*.exe"),
                       ("All files", "*.*")]
        )
        if path:
            self.quickbms_exe.set(path)
            self.set_status(f"Selected: {path}")

    def download_quickbms(self):
        if self.process:
            messagebox.showwarning(APP_NAME, "QuickBMS is currently running.")
            return

        self.progress_var.set(0)
        self.set_status("Downloading QuickBMS...")
        threading.Thread(target=self._download_worker, daemon=True).start()

    def _download_worker(self):
        try:
            QBMS_DIR.mkdir(parents=True, exist_ok=True)

            def report(block, block_size, total):
                if total > 0:
                    pct = min(100, block * block_size * 100 / total)
                    self.after(0, self.progress_var.set, pct)

            urllib.request.urlretrieve(DOWNLOAD_URL, ZIP_PATH, report)

            self.after(0, self.set_status, "Download complete. Extracting...")
            self.after(0, self.progress_var.set, 100)

            with zipfile.ZipFile(ZIP_PATH, "r") as z:
                # Extract into a temporary directory first, then locate the exe.
                tmp = Path(tempfile.mkdtemp(prefix="quickbms_"))
                z.extractall(tmp)

                exe = None
                for candidate in tmp.rglob("quickbms.exe"):
                    exe = candidate
                    break

                if not exe:
                    raise RuntimeError("Downloaded ZIP did not contain quickbms.exe.")

                # Copy/extract the whole package into our local QuickBMS folder.
                # Python's zip extraction is used rather than requiring 7-Zip.
                for member in z.infolist():
                    target = QBMS_DIR / member.filename
                    target_parent = target.parent
                    target_parent.mkdir(parents=True, exist_ok=True)
                    if member.is_dir():
                        target.mkdir(parents=True, exist_ok=True)
                    else:
                        with z.open(member) as src, open(target, "wb") as dst:
                            dst.write(src.read())

            if not (QBMS_DIR / "quickbms.exe").is_file():
                # Handle packages with a top-level directory.
                found = next(QBMS_DIR.rglob("quickbms.exe"), None)
                if found:
                    self.quickbms_exe.set(str(found))
                else:
                    raise RuntimeError("Extraction completed but quickbms.exe was not found.")
            else:
                self.quickbms_exe.set(str(QBMS_DIR / "quickbms.exe"))

            try:
                ZIP_PATH.unlink()
            except OSError:
                pass

            self.after(0, self.set_status,
                       f"Ready: {self.quickbms_exe.get()}")

            # Put the GUI on the main tab after successful setup.
            self.after(0, lambda: self.notebook.select(self.main_tab))

        except Exception as exc:
            self.after(0, self.set_status, f"Setup failed: {exc}")
            self.after(0, lambda: messagebox.showerror(
                APP_NAME, f"QuickBMS setup failed:\n\n{exc}"))

    def open_qbms_folder(self):
        path = Path(self.quickbms_exe.get()).parent if self.quickbms_exe.get() else QBMS_DIR
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(str(path))

    # ---------------- MAIN TAB ----------------

    def _build_main(self):
        tab = self.main_tab

        # Main operation
        op = ttk.LabelFrame(tab, text="Operation", padding=10)
        op.pack(fill="x")

        ttk.Radiobutton(op, text="Extract / List",
                         variable=self.mode_var, value="Extract",
                         command=self.update_operation_state).pack(side="left")
        ttk.Radiobutton(op, text="Reimport",
                         variable=self.mode_var, value="Reimport",
                         command=self.update_operation_state).pack(side="left", padx=15)

        # Paths
        paths = ttk.LabelFrame(tab, text="QuickBMS Files", padding=10)
        paths.pack(fill="x", pady=8)
        paths.columnconfigure(1, weight=1)

        self._path_row(paths, 0, "BMS Script:", self.script_var,
                       self.browse_script)
        self._path_row(paths, 1, "Input Archive / Folder:", self.input_var,
                       self.browse_input)
        self._path_row(paths, 2, "Output Folder:", self.output_var,
                       self.browse_output)

        # Reimport mode
        self.reimport_frame = ttk.Frame(paths)
        self.reimport_frame.grid(row=3, column=0, columnspan=3, sticky="w", pady=4)
        ttk.Label(self.reimport_frame, text="Reimport mode:").pack(side="left")
        for n, label in [(1, "Reimport"), (2, "Reimport 2"), (3, "Reimport 3")]:
            ttk.Radiobutton(self.reimport_frame, text=label,
                            variable=self.reimport_mode, value=n).pack(
                                side="left", padx=7)

        # Options notebook
        options = ttk.Notebook(tab)
        options.pack(fill="both", expand=True, pady=8)

        self.basic_tab = ttk.Frame(options, padding=10)
        self.filters_tab = ttk.Frame(options, padding=10)
        self.advanced_tab = ttk.Frame(options, padding=10)
        self.security_tab = ttk.Frame(options, padding=10)

        options.add(self.basic_tab, text="Basic Options")
        options.add(self.filters_tab, text="Filters")
        options.add(self.advanced_tab, text="Advanced / Debug")
        options.add(self.security_tab, text="Security / Capabilities")

        self._build_basic_options()
        self._build_filters()
        self._build_advanced()
        self._build_security()

        # Bottom command and actions
        command_box = ttk.LabelFrame(tab, text="Generated Command", padding=8)
        command_box.pack(fill="x")

        self.command_text = tk.Text(command_box, height=3, wrap="word")
        self.command_text.pack(fill="x")

        actions = ttk.Frame(tab)
        actions.pack(fill="x", pady=8)

        ttk.Button(actions, text="Build Command",
                   command=self.refresh_command).pack(side="left")
        ttk.Button(actions, text="Run QuickBMS",
                   style="Accent.TButton",
                   command=self.run_quickbms).pack(side="left", padx=7)
        ttk.Button(actions, text="STOP",
                   command=self.stop_quickbms).pack(side="left")
        ttk.Button(actions, text="Clear Console",
                   command=self.clear_console).pack(side="right")

        console_frame = ttk.LabelFrame(tab, text="QuickBMS Console", padding=6)
        console_frame.pack(fill="both", expand=True)

        self.console = tk.Text(console_frame, height=12, wrap="none",
                               font=("Consolas", 9))
        self.console.pack(side="left", fill="both", expand=True)

        y = ttk.Scrollbar(console_frame, orient="vertical",
                          command=self.console.yview)
        y.pack(side="right", fill="y")
        self.console.configure(yscrollcommand=y.set)

        self.update_operation_state()
        self.refresh_command()

    def _path_row(self, parent, row, label, variable, browse_command):
        ttk.Label(parent, text=label, width=22).grid(
            row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=variable).grid(
            row=row, column=1, sticky="ew", padx=7)
        ttk.Button(parent, text="Browse...", command=browse_command).grid(
            row=row, column=2)

    def _check(self, parent, key, label, row, column=0, target=None):
        if target is None:
            target = parent
        var = tk.BooleanVar(value=False)
        self.flag_vars[key] = var
        ttk.Checkbutton(target, text=label, variable=var,
                        command=self.refresh_command).grid(
                            row=row, column=column, sticky="w", padx=5, pady=2)
        return var

    def _build_basic_options(self):
        tab = self.basic_tab
        ttk.Label(tab, text="Extraction / file handling",
                  style="Header.TLabel").grid(row=0, column=0,
                                              columnspan=2, sticky="w")

        labels = [
            ("list", "List files only (-l)"),
            ("overwrite", "Overwrite existing files (-o)"),
            ("keep", "Keep existing files / skip (-k)"),
            ("rename", "Automatically rename duplicates (-K)"),
            ("continue", "Continue after errors (-.)"),
            ("folder_name", "Create input-named output folder (-d)"),
            ("folder_no_name", "Create folder without filename (-D)"),
            ("yes", "Automatically answer yes (-Y)"),
            ("decimal", "Use decimal names for nameless files (-N)"),
            ("temp", "Keep temporary file (-T)"),
            ("ignore_compression", "Ignore compression errors (-e)"),
            ("no_extract", "Test script without extracting (-0)"),
        ]

        for i, (key, label) in enumerate(labels, start=1):
            self._check(tab, key, label, i // 2, i % 2)

    def _build_filters(self):
        tab = self.filters_tab
        tab.columnconfigure(1, weight=1)

        ttk.Label(tab, text="Archive filters (-f)",
                  style="Header.TLabel").grid(row=0, column=0,
                                              columnspan=2, sticky="w")
        ttk.Label(tab, text="Example: {}.png;{}.dds;!{}.tmp").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(3, 10))

        ttk.Label(tab, text="Filter:").grid(row=2, column=0, sticky="w")
        ttk.Entry(tab, textvariable=self.filter_var).grid(
            row=2, column=1, sticky="ew", padx=8)

        ttk.Label(tab, text="Input-folder filter (-F)").grid(
            row=3, column=0, sticky="w", pady=(15, 0))
        ttk.Entry(tab, textvariable=self.folder_filter_var).grid(
            row=3, column=1, sticky="ew", padx=8, pady=(15, 0))

        ttk.Label(
            tab,
            text="QuickBMS accepts multiple patterns separated by comma/semicolon. "
                 "Use {} instead of * on Windows when wildcard handling causes problems.",
            wraplength=800, justify="left").grid(
                row=4, column=0, columnspan=2, sticky="w", pady=15)

        self.filter_var.trace_add("write", lambda *_: self.refresh_command())
        self.folder_filter_var.trace_add("write", lambda *_: self.refresh_command())

    def _build_advanced(self):
        tab = self.advanced_tab
        tab.columnconfigure(1, weight=1)

        items = [
            ("verbose", "-v  Verbose debug information"),
            ("verbose2", "-V  Alternative verbose debugging"),
            ("quiet", "-q  Quiet"),
            ("veryquiet", "-Q  Very quiet"),
            ("hex", "-x  Hexadecimal notation"),
            ("html_hex", "-H  Experimental HTML hex viewer"),
            ("console_hex", "-X  Experimental console hex viewer"),
            ("debug_alloc", "-9  Disable memory protection"),
            ("case_sensitive", "-I  Variable names case-sensitive"),
            ("debug_dump", "-B  Dump non-parsed file content"),
            ("compare_hash", "-#  Compare archive/imported files in reimport"),
            ("zero_archive", "-Z  Zero archived files in reimport"),
            ("force_utf16", "-j  Force UTF-16 output"),
            ("java_strings", "-J  Treat constant strings as Java/C escaped"),
            ("endian", "-E  Reverse endianess"),
            ("check_update", "-u  Check for QuickBMS update"),
            ("iso", "-i  Generate ISO9660 instead of extracting"),
            ("zip", "-z  Generate ZIP instead of extracting"),
        ]

        for i, (key, label) in enumerate(items):
            self._check(tab, key, label, i // 2, i % 2)

        row = (len(items) + 1) // 2 + 1
        ttk.Separator(tab).grid(row=row, column=0, columnspan=2,
                                sticky="ew", pady=10)
        row += 1

        ttk.Label(tab, text="Options requiring a value",
                  style="Header.TLabel").grid(row=row, column=0,
                                              columnspan=2, sticky="w")
        row += 1

        self.log_file_var = tk.StringVar()
        self.codepage_var = tk.StringVar()
        self.script_arg_var = tk.StringVar()
        self.command_each_var = tk.StringVar()
        self.prefix_script_var = tk.StringVar()
        self.output_file_var = tk.StringVar()
        self.tree_var = tk.StringVar(value="")
        self.web_port_var = tk.StringVar()
        self.debug_output_var = tk.StringVar()
        self.filler_var = tk.StringVar()

        fields = [
            ("Log file (-L):", self.log_file_var),
            ("Codepage (-P):", self.codepage_var),
            ("Script arguments (-a):", self.script_arg_var),
            ("Command per extracted file (-S):", self.command_each_var),
            ("Pre-script / instruction (-s):", self.prefix_script_var),
            ("Concatenated output (-O):", self.output_file_var),
            ("Tree output (-t):", self.tree_var),
            ("Web API port (-W):", self.web_port_var),
            ("Debug output file (-y):", self.debug_output_var),
            ("Reimport filler (-b):", self.filler_var),
        ]

        for label, var in fields:
            ttk.Label(tab, text=label).grid(row=row, column=0,
                                            sticky="w", pady=2)
            ttk.Entry(tab, textvariable=var).grid(row=row, column=1,
                                                  sticky="ew", padx=8, pady=2)
            var.trace_add("write", lambda *_: self.refresh_command())
            row += 1

    def _build_security(self):
        tab = self.security_tab

        ttk.Label(tab, text="Capabilities",
                  style="Header.TLabel").pack(anchor="w")

        text = (
            "These switches explicitly enable capabilities inside QuickBMS. "
            "Leave them disabled unless a script or workflow requires them."
        )
        ttk.Label(tab, text=text, wraplength=850, justify="left").pack(
            anchor="w", pady=(3, 12))

        security = [
            ("write", "-w  Enable write mode"),
            ("calldll", "-C  Allow CallDll without permission prompt"),
            ("network", "-n  Enable network sockets"),
            ("processes", "-p  Enable processes"),
            ("audio", "-A  Enable audio device"),
            ("video", "-g  Enable video/graphics device"),
            ("messages", "-m  Enable Windows messages"),
            ("force_gui", "-G  Force QuickBMS GUI mode"),
        ]

        # _check() uses grid(), so keep its checkboxes inside a grid-managed frame.
        # The surrounding security tab uses pack() for its explanatory labels.
        security_grid = ttk.Frame(tab)
        security_grid.pack(fill="x", anchor="w")

        for i, (key, label) in enumerate(security):
            self._check(security_grid, key, label, i)

        ttk.Label(tab, text="QuickBMS documents these as security activation "
                  "or capability options.", foreground="#666").pack(
                      anchor="w", pady=12)

    # ---------------- FILE BROWSING ----------------

    def browse_script(self):
        path = filedialog.askopenfilename(
            title="Select BMS script",
            filetypes=[("BMS scripts", "*.bms"), ("All files", "*.*")]
        )
        if path:
            self.script_var.set(path)
            self.refresh_command()

    def browse_input(self):
        # First offer a file. A separate folder button is useful for batch work.
        win = tk.Toplevel(self)
        win.title("Choose QuickBMS Input")
        win.transient(self)
        win.grab_set()
        win.resizable(False, False)

        ttk.Label(win, text="Choose what QuickBMS should process:",
                  padding=15).pack()

        def choose_file():
            p = filedialog.askopenfilename(parent=win, title="Select input archive/file")
            if p:
                self.input_var.set(p)
                win.destroy()
                self.refresh_command()

        def choose_folder():
            p = filedialog.askdirectory(parent=win, title="Select input folder")
            if p:
                self.input_var.set(p)
                win.destroy()
                self.refresh_command()

        b = ttk.Frame(win, padding=(15, 0, 15, 15))
        b.pack(fill="x")
        ttk.Button(b, text="Archive / File", command=choose_file).pack(
            side="left", expand=True, fill="x", padx=(0, 5))
        ttk.Button(b, text="Folder", command=choose_folder).pack(
            side="left", expand=True, fill="x", padx=(5, 0))

    def browse_output(self):
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self.output_var.set(path)
            self.refresh_command()

    # ---------------- COMMAND BUILDING ----------------

    def _add_flag(self, args, key, flag):
        if self.flag_vars.get(key, tk.BooleanVar()).get():
            args.append(flag)

    def build_args(self):
        exe = self.quickbms_exe.get().strip()
        script = self.script_var.get().strip()
        inp = self.input_var.get().strip()
        out = self.output_var.get().strip()

        args = [exe] if exe else ["quickbms.exe"]

        # Basic options
        flag_map = [
            ("list", "-l"),
            ("overwrite", "-o"),
            ("keep", "-k"),
            ("rename", "-K"),
            ("continue", "-."),
            ("folder_name", "-d"),
            ("folder_no_name", "-D"),
            ("yes", "-Y"),
            ("decimal", "-N"),
            ("temp", "-T"),
            ("ignore_compression", "-e"),
            ("no_extract", "-0"),
            ("verbose", "-v"),
            ("verbose2", "-V"),
            ("quiet", "-q"),
            ("veryquiet", "-Q"),
            ("hex", "-x"),
            ("html_hex", "-H"),
            ("console_hex", "-X"),
            ("debug_alloc", "-9"),
            ("case_sensitive", "-I"),
            ("debug_dump", "-B"),
            ("compare_hash", "-#"),
            ("zero_archive", "-Z"),
            ("force_utf16", "-j"),
            ("java_strings", "-J"),
            ("endian", "-E"),
            ("check_update", "-u"),
            ("iso", "-i"),
            ("zip", "-z"),
        ]
        for key, flag in flag_map:
            self._add_flag(args, key, flag)

        filt = self.filter_var.get().strip()
        if filt:
            args.extend(["-f", filt])

        folder_filt = self.folder_filter_var.get().strip()
        if folder_filt:
            args.extend(["-F", folder_filt])

        value_map = [
            (self.log_file_var, "-L"),
            (self.codepage_var, "-P"),
            (self.script_arg_var, "-a"),
            (self.command_each_var, "-S"),
            (self.prefix_script_var, "-s"),
            (self.output_file_var, "-O"),
            (self.tree_var, "-t"),
            (self.web_port_var, "-W"),
            (self.debug_output_var, "-y"),
            (self.filler_var, "-b"),
        ]
        for var, flag in value_map:
            value = var.get().strip()
            if value:
                args.extend([flag, value])

        # Security / capability switches
        security_map = [
            ("write", "-w"),
            ("calldll", "-C"),
            ("network", "-n"),
            ("processes", "-p"),
            ("audio", "-A"),
            ("video", "-g"),
            ("messages", "-m"),
            ("force_gui", "-G"),
        ]
        for key, flag in security_map:
            self._add_flag(args, key, flag)

        # Reimport must be expressed as repeated -r switches.
        if self.mode_var.get() == "Reimport":
            # -w is required for physical archive writes.
            if "-w" not in args:
                args.append("-w")
            args.extend(["-r"] * self.reimport_mode.get())

        if script:
            args.append(script)
        else:
            args.append("<script.bms>")

        if inp:
            args.append(inp)
        else:
            args.append("<input archive/folder>")

        if out:
            args.append(out)
        elif self.mode_var.get() != "Extract" or not (
            self.flag_vars.get("iso", tk.BooleanVar()).get()
            or self.flag_vars.get("zip", tk.BooleanVar()).get()
        ):
            args.append("<output folder>")

        return args

    def command_display(self):
        args = self.build_args()
        # Windows-friendly display. shlex.join uses POSIX quoting, so use a
        # simple robust visual representation instead.
        return " ".join(
            '"' + a.replace('"', '\\"') + '"' if (" " in a or "\t" in a)
            else a
            for a in args
        )

    def refresh_command(self):
        if not hasattr(self, "command_text"):
            return
        self.command_text.delete("1.0", "end")
        self.command_text.insert("1.0", self.command_display())

    def update_operation_state(self):
        is_reimport = self.mode_var.get() == "Reimport"
        if is_reimport:
            self.reimport_frame.grid()
        else:
            self.reimport_frame.grid_remove()
        self.refresh_command()

    # ---------------- EXECUTION ----------------

    def validate(self):
        exe = Path(self.quickbms_exe.get().strip())
        if not exe.is_file():
            messagebox.showerror(
                APP_NAME,
                "QuickBMS is not configured.\n\nGo to the Setup tab and "
                "download it or browse to quickbms.exe."
            )
            return False

        if not self.script_var.get().strip():
            messagebox.showerror(APP_NAME, "Select a BMS script.")
            return False

        if not self.input_var.get().strip():
            messagebox.showerror(APP_NAME, "Select an input archive/file/folder.")
            return False

        if self.mode_var.get() == "Reimport" and not self.output_var.get().strip():
            messagebox.showerror(APP_NAME,
                                 "Reimport requires the extracted/modified folder.")
            return False

        return True

    def run_quickbms(self):
        if self.process:
            messagebox.showwarning(APP_NAME, "QuickBMS is already running.")
            return

        if not self.validate():
            return

        args = self.build_args()
        self.clear_console()
        self.append_console("=== QuickBMS Frontend ===\n")
        self.append_console("Command:\n" + self.command_display() + "\n\n")
        self.append_console("Starting QuickBMS...\n\n")

        self.stop_requested = False
        threading.Thread(target=self._run_worker, args=(args,), daemon=True).start()

    def _run_worker(self, args):
        try:
            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NO_WINDOW

            self.process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creationflags,
                cwd=str(Path(args[0]).parent),
            )

            assert self.process.stdout is not None

            for line in self.process.stdout:
                self.after(0, self.append_console, line)
                if self.stop_requested:
                    break

            code = self.process.wait()

            if self.stop_requested:
                self.after(0, self.append_console,
                           "\n=== Process stopped by user ===\n")
            else:
                self.after(0, self.append_console,
                           f"\n=== QuickBMS finished with exit code {code} ===\n")

        except FileNotFoundError:
            self.after(0, self.append_console,
                       "\nERROR: quickbms.exe could not be started.\n")
        except Exception as exc:
            self.after(0, self.append_console,
                       f"\nERROR: {exc}\n")
        finally:
            self.process = None

    def stop_quickbms(self):
        if not self.process:
            return

        self.stop_requested = True
        try:
            self.process.terminate()
        except Exception:
            pass

    def append_console(self, text):
        self.console.insert("end", text)
        self.console.see("end")

    def clear_console(self):
        self.console.delete("1.0", "end")

    def set_status(self, text):
        self.status_var.set(text)

    @staticmethod
    def open_url(url):
        import webbrowser
        webbrowser.open(url)


if __name__ == "__main__":
    app = QuickBMSApp()
    app.mainloop()
