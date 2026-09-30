import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import Tk, LabelFrame, Button, Label, Entry, Scale
import subprocess
import os

class FFmpegGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FFmpeg Toolkit")
        self.root.geometry("600x520")
        
        # Track selected files
        self.selected_files = []
        
        # UI Elements
        self.create_widgets()

    def create_widgets(self):
        # File Selection Frame 
        file_frame = LabelFrame(self.root, text=" 1. Select Video/Audio Files ", padx=10, pady=10)
        file_frame.pack(fill="x", padx=15, pady=10)
        
        self.btn_select = Button(file_frame, text="Browse Files", command=self.browse_files)
        self.btn_select.pack(side="left", padx=5)
        
        self.lbl_files = Label(file_frame, text="No files selected", wraplength=450, justify="left", fg="gray")
        self.lbl_files.pack(side="left", padx=5, fill="x", expand=True)

        # Features Notebook (Tabs)
        tabs = ttk.Notebook(self.root)
        tabs.pack(fill="both", expand=True, padx=15, pady=5)

        # Tab 1: Convert
        self.tab_convert = ttk.Frame(tabs)
        tabs.add(self.tab_convert, text="Convert")
        Label(self.tab_convert, text="Target Format:").grid(row=0, column=0, padx=10, pady=15, sticky="w")
        self.lbl_format = ttk.Combobox(self.tab_convert, values=[".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav"])
        self.lbl_format.set(".mp4")
        self.lbl_format.grid(row=0, column=1, padx=10, pady=15, sticky="w")
        Button(self.tab_convert, text="Run Conversion", bg="#4CAF50", fg="white", command=self.run_convert).grid(row=1, column=0, columnspan=2, pady=10)

        # Tab 2: Merge
        self.tab_merge = ttk.Frame(tabs)
        tabs.add(self.tab_merge, text="Merge")
        Label(self.tab_merge, text="Merge all selected files sequentially into a single video.", wraplength=500).pack(padx=10, pady=15)
        Button(self.tab_merge, text="Run Merge", bg="#4CAF50", fg="white", command=self.run_merge).pack(pady=10)

        # Tab 3: Trim
        self.tab_trim = ttk.Frame(tabs)
        tabs.add(self.tab_trim, text="Trim")
        Label(self.tab_trim, text="Start Time (HH:MM:SS):").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.start_time = Entry(self.tab_trim)
        self.start_time.insert(0, "00:00:00")
        self.start_time.grid(row=0, column=1, padx=10, pady=10)
        
        Label(self.tab_trim, text="Duration / End (HH:MM:SS or seconds):").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.duration = Entry(self.tab_trim)
        self.duration.insert(0, "00:00:10")
        self.duration.grid(row=1, column=1, padx=10, pady=10)
        Button(self.tab_trim, text="Run Trim", bg="#4CAF50", fg="white", command=self.run_trim).grid(row=2, column=0, columnspan=2, pady=10)

        # Tab 4: Compress
        self.tab_compress = ttk.Frame(tabs)
        tabs.add(self.tab_compress, text="Compress")
        Label(self.tab_compress, text="CRF Value (Lower = Higher Quality, 18-28 is normal):").grid(row=0, column=0, padx=10, pady=15, sticky="w")
        self.crf_val = Scale(self.tab_compress, from_=15, to=35, orient="horizontal")
        self.crf_val.set(23)
        self.crf_val.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
        Button(self.tab_compress, text="Run Compression", bg="#4CAF50", fg="white", command=self.run_compress).grid(row=1, column=0, columnspan=2, pady=10)

        # Tab 5: Extract Audio
        self.tab_audio = ttk.Frame(tabs)
        tabs.add(self.tab_audio, text="Extract Audio")
        Label(self.tab_audio, text="Rip the audio track straight out of your selected video file.", wraplength=500).pack(padx=10, pady=15)
        Button(self.tab_audio, text="Extract to MP3", bg="#4CAF50", fg="white", command=self.run_extract_audio).pack(pady=10)

        # Status Output
        self.lbl_status = Label(self.root, text="Status: Ready", bd=1, relief="sunken", anchor="w")
        self.lbl_status.pack(side="bottom", fill="x")

    def browse_files(self):
        files = filedialog.askopenfilenames(title="Select Media Files")
        if files:
            self.selected_files = list(files)
            display_text = "\n".join([os.path.basename(f) for f in self.selected_files])
            self.lbl_files.config(text=display_text, fg="black")
        else:
            self.selected_files = []
            self.lbl_files.config(text="No files selected", fg="gray")

    def check_files_selected(self, min_count=1):
        if len(self.selected_files) < min_count:
            messagebox.showwarning("Warning", f"Please select at least {min_count} file(s) first.")
            return False
        return True

    def execute_ffmpeg(self, cmd):
        self.lbl_status.config(text="Status: Processing... Please wait.")
        self.root.update()
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if result.returncode == 0:
                self.lbl_status.config(text="Status: Task completed successfully!")
                messagebox.showinfo("Success", "FFmpeg process finished successfully!")
            else:
                self.lbl_status.config(text="Status: FFmpeg Error")
                messagebox.showerror("FFmpeg Error", result.stderr)
        except FileNotFoundError:
            self.lbl_status.config(text="Status: FFmpeg not found")
            messagebox.showerror("Error", "FFmpeg is not installed or not added to your system PATH.")

    def run_convert(self):
        if not self.check_files_selected(): return
        for file in self.selected_files:
            output = os.path.splitext(file)[0] + f"_converted{self.lbl_format.get()}"
            cmd = ["ffmpeg", "-y", "-i", file, output]
            self.execute_ffmpeg(cmd)

    def run_merge(self):
        if not self.check_files_selected(min_count=2): return
        txt_path = os.path.join(os.path.dirname(self.selected_files[0]), "temp_merge_list.txt")
        output = os.path.splitext(self.selected_files[0])[0] + "_merged.mp4"
        
        with open(txt_path, "w", encoding="utf-8") as f:
            for file in self.selected_files:
                f.write(f"file '{file}'\n")
        
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", txt_path, "-c", "copy", output]
        self.execute_ffmpeg(cmd)
        if os.path.exists(txt_path):
            os.remove(txt_path)

    def run_trim(self):
        if not self.check_files_selected(): return
        file = self.selected_files[0]
        output = os.path.splitext(file)[0] + "_trimmed" + os.path.splitext(file)[1]
        cmd = ["ffmpeg", "-y", "-ss", self.start_time.get(), "-i", file, "-t", self.duration.get(), "-c", "copy", output]
        self.execute_ffmpeg(cmd)

    def run_compress(self):
        if not self.check_files_selected(): return
        file = self.selected_files[0]
        output = os.path.splitext(file)[0] + "_compressed.mp4"
        cmd = ["ffmpeg", "-y", "-i", file, "-vcodec", "libx264", "-crf", str(self.crf_val.get()), output]
        self.execute_ffmpeg(cmd)

    def run_extract_audio(self):
        if not self.check_files_selected(): return
        file = self.selected_files[0]
        output = os.path.splitext(file)[0] + "_audio.mp3"
        cmd = ["ffmpeg", "-y", "-i", file, "-q:a", "0", "-map", "a", output]
        self.execute_ffmpeg(cmd)

if __name__ == "__main__":
    root = Tk()
    app = FFmpegGUI(root)
    root.mainloop()
