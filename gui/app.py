import os
import threading
import json
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image, ImageTk
from core.video import create_short, generate_preview, get_source_frame, cancel_render
from core.subtitle import generate_ass, generate_title_ass


class ClipersFfgApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("clipers_ffg")
        self.geometry("1200x650")
        self.input_path = None
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.scale_factor = 3.0
        self.offset_x = 0
        self.offset_y = 0
        self.cam_coords = (1520, 0, 400, 300)
        self.rect_id = None
        self.base_pil_source = None
        self.base_pil_preview = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self.frame_controls = ctk.CTkFrame(self)
        self.frame_controls.grid(row=0, column=0, sticky="nsew", padx=10, pady=20)

        self.frame_source = ctk.CTkFrame(self)
        self.frame_source.grid(row=0, column=1, sticky="nsew", padx=10, pady=20)

        self.frame_preview = ctk.CTkFrame(self)
        self.frame_preview.grid(row=0, column=2, sticky="nsew", padx=10, pady=20)

        self.btn_import = ctk.CTkButton(self.frame_controls, text="Import Video", command=self.import_video)
        self.btn_import.pack(pady=(20, 5), padx=20, fill="x")

        self.lbl_path = ctk.CTkLabel(self.frame_controls, text="No file selected", text_color="gray")
        self.lbl_path.pack(pady=(0, 20), padx=20)

        # ---- Conteneur dédié aux options ----
        self.frame_options = ctk.CTkFrame(self.frame_controls, fg_color="transparent")
        self.frame_options.pack(fill="x")

        self.use_webcam = ctk.BooleanVar(value=True)
        self.chk_webcam = ctk.CTkCheckBox(self.frame_options, text="Enable Webcam", variable=self.use_webcam,
                                          command=self.on_toggle_options)

        self.use_title = ctk.BooleanVar(value=False)
        self.chk_title = ctk.CTkCheckBox(self.frame_options, text="Enable Top Title", variable=self.use_title,
                                         command=self.on_toggle_options)

        self.entry_title = ctk.CTkEntry(self.frame_options, placeholder_text="Enter Top Title...")
        self.entry_title.bind("<Return>", lambda e: self.update_preview())
        self.entry_title.bind("<FocusOut>", lambda e: self.update_preview())

        self.use_subs = ctk.BooleanVar(value=True)
        self.chk_subs = ctk.CTkCheckBox(self.frame_options, text="Enable Subtitles", variable=self.use_subs,
                                        command=self.on_toggle_options)
        self.load_preferences()

        self.btn_export = ctk.CTkButton(self.frame_controls, text="Generate Short", command=self.export)
        self.btn_export.pack(pady=20, padx=20, side="bottom", fill="x")

        ctk.CTkLabel(self.frame_source, text="Zone Selection").pack(pady=(10, 0))

        self.lbl_legend = ctk.CTkLabel(self.frame_source, text="", text_color="red")
        self.lbl_legend.pack(pady=(0, 5))

        self.canvas_src = tk.Canvas(self.frame_source, bg="#2b2b2b", highlightthickness=0)
        self.canvas_src.pack(expand=True, fill="both", padx=10, pady=10)
        self.canvas_src.bind("<Configure>", self.on_resize_source)
        self.canvas_src.bind("<ButtonPress-1>", self.on_draw_start)
        self.canvas_src.bind("<B1-Motion>", self.on_draw_motion)
        self.canvas_src.bind("<ButtonRelease-1>", self.on_draw_release)

        ctk.CTkLabel(self.frame_preview, text="Short Preview").pack(pady=10)

        self.canvas_prev = tk.Canvas(self.frame_preview, bg="#2b2b2b", highlightthickness=0)
        self.canvas_prev.pack(expand=True, fill="both", padx=10, pady=10)
        self.canvas_prev.bind("<Configure>", self.on_resize_preview)

        self.progress = ctk.CTkProgressBar(self.frame_preview)
        self.progress.set(0)
        self.lbl_progress = ctk.CTkLabel(self.frame_preview, text="")

        self.on_toggle_options()

    def on_closing(self):
        cancel_render()
        self.save_preferences()
        self.destroy()

    def load_preferences(self):
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.use_webcam.set(config.get("use_webcam", True))
                self.use_title.set(config.get("use_title", False))
                self.use_subs.set(config.get("use_subs", True))
                # Les tuples JSON deviennent des listes, on retransforme en tuple
                coords = config.get("cam_coords", [1520, 0, 400, 300])
                self.cam_coords = tuple(coords)
            except Exception as e:
                print(f"Error loading config.json: {e}")

    def save_preferences(self):
        config = {
            "use_webcam": self.use_webcam.get(),
            "use_title": self.use_title.get(),
            "use_subs": self.use_subs.get(),
            "cam_coords": self.cam_coords
        }
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config.json: {e}")

    def on_toggle_options(self, *_):
        for widget in [self.chk_webcam, self.chk_title, self.entry_title, self.chk_subs]:
            widget.pack_forget()

        self.chk_webcam.pack(pady=(10, 5), padx=20, anchor="w")

        if not self.use_webcam.get():
            if hasattr(self, "lbl_legend"): self.lbl_legend.configure(text="")
            self.chk_title.pack(pady=(5, 5), padx=20, anchor="w")

            if self.use_title.get():
                self.entry_title.pack(pady=(5, 10), padx=20, fill="x")
        else:
            if hasattr(self, "lbl_legend"): self.lbl_legend.configure(text="■ Webcam Selection")

        self.chk_subs.pack(pady=(10, 20), padx=20, anchor="w")

        if hasattr(self, "canvas_src"):
            self.draw_crop_rect()

        if self.input_path:
            self.update_preview()

    def on_resize_source(self, event=None):
        cw = self.canvas_src.winfo_width()
        ch = self.canvas_src.winfo_height()
        if cw < 10 or ch < 10: return

        iw, ih = cw, int(cw * 9 / 16)
        if ih > ch:
            ih, iw = ch, int(ch * 16 / 9)

        self.scale_factor = 1920 / iw if iw > 0 else 3.0
        self.offset_x = (cw - iw) // 2
        self.offset_y = (ch - ih) // 2

        self.canvas_src.delete("all")
        if self.base_pil_source:
            pil_resized = self.base_pil_source.resize((iw, ih), Image.Resampling.LANCZOS)
            self.tk_source = ImageTk.PhotoImage(pil_resized)
            self.canvas_src.create_image(self.offset_x, self.offset_y, anchor="nw", image=self.tk_source)
            self.draw_crop_rect()
        else:
            self.canvas_src.create_text(cw // 2, ch // 2, text="Upload a video", fill="gray", font=("Arial", 16))

    def on_resize_preview(self, event=None):
        cw = self.canvas_prev.winfo_width()
        ch = self.canvas_prev.winfo_height()
        if cw < 10 or ch < 10: return

        ih, iw = ch, int(ch * 9 / 16)
        if iw > cw:
            iw, ih = cw, int(cw * 16 / 9)

        ox = (cw - iw) // 2
        oy = (ch - ih) // 2

        self.canvas_prev.delete("all")
        if self.base_pil_preview:
            pil_resized = self.base_pil_preview.resize((iw, ih), Image.Resampling.LANCZOS)
            self.tk_preview = ImageTk.PhotoImage(pil_resized)
            self.canvas_prev.create_image(ox, oy, anchor="nw", image=self.tk_preview)
        else:
            self.canvas_prev.create_text(cw // 2, ch // 2, text="Waiting for preview...", fill="gray",
                                         font=("Arial", 16))

    def import_video(self):
        self.input_path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mkv")])
        if self.input_path:
            self.lbl_path.configure(text=self.input_path.split("/")[-1])
            self.base_pil_source = get_source_frame(self.input_path)
            self.on_resize_source()
            self.update_preview()

    def draw_crop_rect(self):
        if self.rect_id:
            self.canvas_src.delete(self.rect_id)
            self.rect_id = None

        if not self.use_webcam.get():
            return

        x, y, w, h = [int(v / self.scale_factor) for v in self.cam_coords]
        self.rect_id = self.canvas_src.create_rectangle(
            x + self.offset_x, y + self.offset_y,
            x + w + self.offset_x, y + h + self.offset_y,
            outline="red", width=3
        )

    def on_draw_start(self, event):
        if not self.base_pil_source or not self.use_webcam.get(): return
        self.start_x, self.start_y = event.x, event.y

    def on_draw_motion(self, event):
        if not self.base_pil_source or not self.use_webcam.get(): return
        if self.rect_id:
            self.canvas_src.delete(self.rect_id)
        self.rect_id = self.canvas_src.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline="red",
                                                        width=3)

    def on_draw_release(self, event):
        if not self.base_pil_source or not self.use_webcam.get(): return

        x1 = max(0, min(event.x, self.start_x) - self.offset_x)
        y1 = max(0, min(event.y, self.start_y) - self.offset_y)
        x2 = max(0, max(event.x, self.start_x) - self.offset_x)
        y2 = max(0, max(event.y, self.start_y) - self.offset_y)

        if x2 - x1 < 10 or y2 - y1 < 10:
            self.draw_crop_rect()
            return

        cx, cy = int(x1 * self.scale_factor), int(y1 * self.scale_factor)
        cw, ch = int((x2 - x1) * self.scale_factor), int((y2 - y1) * self.scale_factor)

        cx, cy = max(0, min(1920, cx)), max(0, min(1080, cy))
        self.cam_coords = (cx, cy, min(1920 - cx, cw), min(1080 - cy, ch))
        self.update_preview()

    def update_preview(self):
        if not self.input_path: return
        self.canvas_prev.delete("all")
        self.canvas_prev.create_text(self.canvas_prev.winfo_width() // 2, self.canvas_prev.winfo_height() // 2,
                                     text="Generating...", fill="gray", font=("Arial", 16))
        self.update_idletasks()

        self.base_pil_preview = generate_preview(
            self.input_path,
            self.cam_coords,
            self.use_webcam.get(),
            self.use_subs.get(),
            self.use_title.get(),
            self.entry_title.get()
        )
        self.on_resize_preview()

    def start_progress_ui(self, text):
        self.btn_export.configure(state="disabled")
        self.progress.pack(pady=(10, 0), padx=20, fill="x", side="bottom")
        self.lbl_progress.pack(pady=(5, 10), side="bottom")
        self.progress.set(0)
        self.lbl_progress.configure(text=text)

    def update_progress_ui(self, value, text):
        self.progress.set(value)
        self.lbl_progress.configure(text=text)

    def stop_progress_ui(self):
        self.btn_export.configure(state="normal")
        self.progress.pack_forget()
        self.lbl_progress.pack_forget()

    def export(self):
        if not self.input_path: return
        threading.Thread(target=self._process, daemon=True).start()

    def _process(self):
        os.makedirs("workspace/temp", exist_ok=True)
        os.makedirs("workspace/output", exist_ok=True)

        ass_path = ""
        if self.use_subs.get():
            ass_path = "workspace/temp/subs.ass"
            self.after(0, self.start_progress_ui, "AI Transcription (1-2 min)...")
            generate_ass(self.input_path, ass_path)
        else:
            self.after(0, self.start_progress_ui, "Initializing Render...")

        title_ass_path = ""
        if not self.use_webcam.get() and self.use_title.get() and self.entry_title.get().strip():
            title_ass_path = "workspace/temp/title.ass"
            generate_title_ass(self.entry_title.get().strip(), title_ass_path)

        def progress_callback(p, text):
            base = 0.2 if self.use_subs.get() else 0.0
            mult = 0.8 if self.use_subs.get() else 1.0
            self.after(0, self.update_progress_ui, base + (p * mult), text)

        create_short(
            self.input_path,
            "workspace/output/final.mp4",
            self.cam_coords,
            ass_path,
            self.use_webcam.get(),
            title_ass_path,
            progress_callback
        )
        self.after(0, self.stop_progress_ui)