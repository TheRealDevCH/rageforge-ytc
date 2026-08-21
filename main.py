import io
import os
import re
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from urllib.request import urlopen

import customtkinter as ctk
import yt_dlp
from PIL import Image

AUTHOR = "Rageforge"
APP_NAME = "Rageforge YTC"
PRIMARY = "#0891B2"
SECONDARY = "#22D3EE"
CTA = "#22C55E"
BG = "#ECFEFF"
SURFACE = "#FFFFFF"
TEXT = "#164E63"
MUTED = "#0E7490"
BORDER = "#A5F3FC"
DANGER = "#DC2626"

ALLOWED_VIDEO = {"mp4", "webm"}
ALLOWED_AUDIO = {"m4a", "webm", "opus", "mp3"}


def resource_path(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name


def find_ffmpeg() -> str | None:
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe",
        Path(sys.executable).parent / "ffmpeg.exe",
        Path(__file__).resolve().parent / "ffmpeg.exe",
    ]
    for path in candidates:
        if path.is_file():
            return str(path)
    from shutil import which

    found = which("ffmpeg")
    return found


def ytdlp_base_opts() -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "retries": 10,
        "fragment_retries": 10,
        "extractor_args": {"youtube": {"player_client": ["android", "ios", "web"]}},
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
    }
    ffmpeg = find_ffmpeg()
    if ffmpeg:
        opts["ffmpeg_location"] = str(Path(ffmpeg).resolve().parent)
    return opts


def human_size(num: int | float | None) -> str:
    if not num:
        return "?"
    units = ["B", "KB", "MB", "GB"]
    size = float(num)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024
    return "?"


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]+', "_", name).strip().strip(".")
    return cleaned[:120] or "video"


class FormatChoice:
    def __init__(
        self,
        key: str,
        label: str,
        kind: str,
        format_id: str | None,
        ext: str,
        needs_ffmpeg: bool = False,
    ):
        self.key = key
        self.label = label
        self.kind = kind
        self.format_id = format_id
        self.ext = ext
        self.needs_ffmpeg = needs_ffmpeg
        self.selected = tk.BooleanVar(value=False)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.title(f"{APP_NAME} - {AUTHOR}")
        self.geometry("920x720")
        self.minsize(820, 640)
        self.configure(fg_color=BG)
        icon = resource_path("icon.ico")
        if icon.exists():
            try:
                self.iconbitmap(str(icon))
            except Exception:
                pass

        self.info = None
        self.choices: list[FormatChoice] = []
        self.busy = False
        self.ffmpeg = find_ffmpeg()
        self.out_dir = Path.home() / "Downloads" / "RageforgeYTC"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.thumb_image = None

        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, border_width=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text=APP_NAME,
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=TEXT,
        ).pack(anchor="w", padx=28, pady=(22, 2))
        ctk.CTkLabel(
            header,
            text="YouTube-Link einfügen, Formate wählen, mehrere Versionen laden.",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=MUTED,
        ).pack(anchor="w", padx=28, pady=(0, 18))

        body = ctk.CTkFrame(self, fg_color=BG)
        body.pack(fill="both", expand=True, padx=24, pady=18)

        url_row = ctk.CTkFrame(body, fg_color=SURFACE, corner_radius=14, border_width=1, border_color=BORDER)
        url_row.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(url_row, text="YouTube-URL", text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold")).pack(
            anchor="w", padx=16, pady=(14, 6)
        )
        entry_row = ctk.CTkFrame(url_row, fg_color="transparent")
        entry_row.pack(fill="x", padx=16, pady=(0, 14))
        self.url_entry = ctk.CTkEntry(
            entry_row,
            height=44,
            placeholder_text="https://www.youtube.com/watch?v=...",
            fg_color="#F0FDFA",
            border_color=BORDER,
            text_color=TEXT,
            placeholder_text_color="#67E8F9",
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.analyze_btn = ctk.CTkButton(
            entry_row,
            text="Analysieren",
            width=140,
            height=44,
            fg_color=PRIMARY,
            hover_color=MUTED,
            text_color="#FFFFFF",
            command=self.start_analyze,
        )
        self.analyze_btn.pack(side="left")

        meta = ctk.CTkFrame(body, fg_color=SURFACE, corner_radius=14, border_width=1, border_color=BORDER)
        meta.pack(fill="x", pady=(0, 14))
        meta_inner = ctk.CTkFrame(meta, fg_color="transparent")
        meta_inner.pack(fill="x", padx=16, pady=14)
        self.thumb_label = ctk.CTkLabel(meta_inner, text="", width=160, height=90, fg_color=BORDER, corner_radius=8)
        self.thumb_label.pack(side="left", padx=(0, 16))
        meta_text = ctk.CTkFrame(meta_inner, fg_color="transparent")
        meta_text.pack(side="left", fill="both", expand=True)
        self.title_label = ctk.CTkLabel(
            meta_text,
            text="Noch kein Video geladen",
            anchor="w",
            justify="left",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT,
            wraplength=560,
        )
        self.title_label.pack(anchor="w")
        self.meta_label = ctk.CTkLabel(
            meta_text,
            text="Füge einen Link ein und klicke auf Analysieren.",
            anchor="w",
            justify="left",
            font=ctk.CTkFont(size=13),
            text_color=MUTED,
            wraplength=560,
        )
        self.meta_label.pack(anchor="w", pady=(6, 0))

        tools = ctk.CTkFrame(body, fg_color="transparent")
        tools.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(tools, text="Formate", font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT).pack(
            side="left"
        )
        self.folder_btn = ctk.CTkButton(
            tools,
            text="Ordner wählen",
            width=120,
            height=32,
            fg_color=SECONDARY,
            hover_color=PRIMARY,
            text_color=TEXT,
            command=self.choose_folder,
        )
        self.folder_btn.pack(side="right")
        self.select_all_btn = ctk.CTkButton(
            tools,
            text="Alle",
            width=70,
            height=32,
            fg_color=SURFACE,
            hover_color=BORDER,
            text_color=TEXT,
            border_width=1,
            border_color=BORDER,
            command=lambda: self.set_all(True),
        )
        self.select_all_btn.pack(side="right", padx=(0, 8))
        self.clear_btn = ctk.CTkButton(
            tools,
            text="Keine",
            width=70,
            height=32,
            fg_color=SURFACE,
            hover_color=BORDER,
            text_color=TEXT,
            border_width=1,
            border_color=BORDER,
            command=lambda: self.set_all(False),
        )
        self.clear_btn.pack(side="right", padx=(0, 8))

        self.folder_label = ctk.CTkLabel(
            body,
            text=f"Ziel: {self.out_dir}",
            anchor="w",
            text_color=MUTED,
            font=ctk.CTkFont(size=12),
        )
        self.folder_label.pack(fill="x", pady=(0, 8))

        bottom = ctk.CTkFrame(body, fg_color="transparent")
        bottom.pack(side="bottom", fill="x")
        self.download_btn = ctk.CTkButton(
            bottom,
            text="Auswahl herunterladen",
            height=48,
            fg_color=CTA,
            hover_color="#16A34A",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.start_download,
        )
        self.download_btn.pack(fill="x")
        self.progress = ctk.CTkProgressBar(bottom, height=10, progress_color=PRIMARY, fg_color=BORDER)
        self.progress.pack(fill="x", pady=(12, 6))
        self.progress.set(0)
        self.status = ctk.CTkLabel(bottom, text="Bereit.", anchor="w", text_color=MUTED)
        self.status.pack(fill="x")

        self.list_frame = ctk.CTkScrollableFrame(
            body,
            fg_color=SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
            height=220,
        )
        self.list_frame.pack(fill="both", expand=True, pady=(0, 14))
        self.empty_label = ctk.CTkLabel(
            self.list_frame,
            text="Nach der Analyse erscheinen hier MP4, WEBM, MP3 und M4A.",
            text_color=MUTED,
        )
        self.empty_label.pack(pady=40)

    def set_status(self, text: str, error: bool = False):
        self.status.configure(text=text, text_color=DANGER if error else MUTED)

    def set_busy(self, busy: bool):
        self.busy = busy
        state = "disabled" if busy else "normal"
        self.analyze_btn.configure(state=state)
        self.download_btn.configure(state=state)
        self.folder_btn.configure(state=state)

    def choose_folder(self):
        chosen = filedialog.askdirectory(initialdir=str(self.out_dir))
        if chosen:
            self.out_dir = Path(chosen)
            self.folder_label.configure(text=f"Ziel: {self.out_dir}")

    def set_all(self, value: bool):
        for choice in self.choices:
            choice.selected.set(value)

    def clear_choices(self):
        for child in self.list_frame.winfo_children():
            child.destroy()
        self.choices.clear()

    def start_analyze(self):
        if self.busy:
            return
        url = self.url_entry.get().strip()
        if not url:
            self.set_status("Bitte einen YouTube-Link einfügen.", error=True)
            return
        self.set_busy(True)
        self.set_status("Analysiere Video…")
        self.progress.set(0)
        threading.Thread(target=self.analyze_worker, args=(url,), daemon=True).start()

    def analyze_worker(self, url: str):
        try:
            opts = ytdlp_base_opts()
            opts["skip_download"] = True
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            if info is None:
                raise RuntimeError("Keine Videodaten erhalten.")
            choices = self.build_choices(info)
            thumb = None
            thumb_url = info.get("thumbnail")
            if thumb_url:
                with urlopen(thumb_url, timeout=20) as resp:
                    thumb = Image.open(io.BytesIO(resp.read())).convert("RGBA")
            self.after(0, lambda: self.apply_analyze(info, choices, thumb))
        except Exception as exc:
            message = str(exc) or repr(exc) or type(exc).__name__
            self.after(0, lambda m=message: self.analyze_failed(m))

    def build_choices(self, info: dict) -> list[FormatChoice]:
        formats = info.get("formats") or []
        seen = set()
        choices: list[FormatChoice] = [
            FormatChoice(
                "mp4-best",
                "MP4 · Empfohlen · Beste Qualität (Auto-Merge)",
                "best",
                None,
                "mp4",
                needs_ffmpeg=True,
            ),
            FormatChoice(
                "mp4-1080",
                "MP4 · Empfohlen · bis 1080p (stabil)",
                "preset",
                "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/b",
                "mp4",
                needs_ffmpeg=True,
            ),
            FormatChoice(
                "mp3-best",
                "MP3 · Audio (beste Qualität)",
                "mp3",
                None,
                "mp3",
                needs_ffmpeg=True,
            ),
            FormatChoice("mp3-192", "MP3 · Audio 192kbps", "mp3", None, "mp3", needs_ffmpeg=True),
        ]

        video_rows = []
        for fmt in formats:
            ext = (fmt.get("ext") or "").lower()
            vcodec = fmt.get("vcodec") or "none"
            acodec = fmt.get("acodec") or "none"
            url = fmt.get("url")
            if not url:
                continue
            if ext not in ALLOWED_VIDEO:
                continue
            if vcodec == "none":
                continue
            height = fmt.get("height") or 0
            fps = fmt.get("fps") or 0
            size = fmt.get("filesize") or fmt.get("filesize_approx")
            has_audio = acodec != "none"
            tag = "Video+Audio" if has_audio else "nur Video (+Audio Merge)"
            label = f"MP4 · {height}p" if ext == "mp4" else f"WEBM · {height}p"
            if fps:
                label += f" · {int(fps)}fps"
            label += f" · {tag} · {human_size(size)}"
            key = f"{ext}-{fmt.get('format_id')}"
            if key in seen:
                continue
            seen.add(key)
            video_rows.append(
                (
                    height,
                    1 if has_audio else 0,
                    FormatChoice(
                        key,
                        label,
                        "video",
                        str(fmt.get("format_id")),
                        ext,
                        needs_ffmpeg=not has_audio,
                    ),
                )
            )
        video_rows.sort(key=lambda item: (item[0], item[1]), reverse=True)
        for _, _, choice in video_rows[:16]:
            choices.append(choice)

        audio_rows = []
        for fmt in formats:
            ext = (fmt.get("ext") or "").lower()
            vcodec = fmt.get("vcodec") or "none"
            acodec = fmt.get("acodec") or "none"
            if not fmt.get("url"):
                continue
            if vcodec != "none" or acodec == "none":
                continue
            if ext not in {"m4a", "webm", "opus"}:
                continue
            abr = fmt.get("abr") or fmt.get("tbr") or 0
            size = fmt.get("filesize") or fmt.get("filesize_approx")
            out_ext = "m4a" if ext == "m4a" else "webm"
            label = f"{out_ext.upper()} · Audio · {int(abr)}kbps · {human_size(size)}"
            key = f"audio-{fmt.get('format_id')}"
            if key in seen:
                continue
            seen.add(key)
            audio_rows.append((abr, FormatChoice(key, label, "audio", str(fmt.get("format_id")), out_ext)))
        audio_rows.sort(key=lambda item: item[0], reverse=True)
        for _, choice in audio_rows[:8]:
            choices.append(choice)
        return choices

    def apply_analyze(self, info: dict, choices: list[FormatChoice], thumb: Image.Image | None):
        self.info = info
        self.clear_choices()
        title = info.get("title") or "Unbekanntes Video"
        channel = info.get("uploader") or info.get("channel") or "?"
        duration = info.get("duration") or 0
        mins, secs = divmod(int(duration), 60)
        self.title_label.configure(text=title)
        self.meta_label.configure(text=f"{channel}  ·  {mins}:{secs:02d}  ·  {len(choices)} Formate")
        if thumb is not None:
            preview = thumb.copy()
            preview.thumbnail((160, 90))
            self.thumb_image = ctk.CTkImage(light_image=preview, size=preview.size)
            self.thumb_label.configure(image=self.thumb_image, text="")
        for choice in choices:
            row = ctk.CTkFrame(self.list_frame, fg_color="#F0FDFA", corner_radius=10)
            row.pack(fill="x", padx=8, pady=4)
            box = ctk.CTkCheckBox(
                row,
                text=choice.label,
                variable=choice.selected,
                text_color=TEXT,
                fg_color=PRIMARY,
                hover_color=MUTED,
                border_color=BORDER,
                checkmark_color="#FFFFFF",
            )
            box.pack(anchor="w", padx=12, pady=10)
            self.choices.append(choice)
        self.set_busy(False)
        self.set_status(f"Fertig. {len(choices)} Versionen verfügbar.")
        self.progress.set(0)

    def analyze_failed(self, message: str):
        self.set_busy(False)
        self.set_status(f"Analyse fehlgeschlagen: {message}", error=True)

    def start_download(self):
        if self.busy:
            return
        if not self.info:
            self.set_status("Zuerst ein Video analysieren.", error=True)
            return
        selected = [c for c in self.choices if c.selected.get()]
        if not selected:
            self.set_status("Mindestens ein Format auswählen.", error=True)
            return
        needs_ffmpeg = any(c.needs_ffmpeg for c in selected)
        if needs_ffmpeg and not self.ffmpeg:
            self.set_status("Für MP3/Merge wird ffmpeg benötigt. Bitte ffmpeg installieren.", error=True)
            return
        self.set_busy(True)
        self.progress.set(0)
        self.set_status(f"Lade {len(selected)} Datei(en)…")
        threading.Thread(target=self.download_worker, args=(selected,), daemon=True).start()

    def download_worker(self, selected: list[FormatChoice]):
        total = len(selected)
        title = sanitize_filename(self.info.get("title") or "video")
        url = self.info.get("webpage_url") or self.info.get("original_url") or self.url_entry.get().strip()
        try:
            for index, choice in enumerate(selected, start=1):
                self.after(0, lambda i=index, t=total, c=choice: self.set_status(f"Download {i}/{t}: {c.label}"))

                def hook(d, base=index - 1, count=total, done=index):
                    if d.get("status") == "downloading":
                        total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                        downloaded = d.get("downloaded_bytes") or 0
                        part = (downloaded / total_bytes) if total_bytes else 0
                        value = (base + part) / count
                        self.after(0, lambda v=value: self.progress.set(min(max(v, 0), 1)))
                    elif d.get("status") == "finished":
                        value = done / count
                        self.after(0, lambda v=value: self.progress.set(v))

                opts = ytdlp_base_opts()
                opts["progress_hooks"] = [hook]
                opts["outtmpl"] = str(self.out_dir / f"{title} [%(format_id)s].%(ext)s")

                if choice.kind == "mp3":
                    opts["format"] = "bestaudio/best"
                    opts["outtmpl"] = str(self.out_dir / f"{title}.%(ext)s")
                    quality = "0" if choice.key == "mp3-best" else "192"
                    opts["postprocessors"] = [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": quality,
                        }
                    ]
                elif choice.kind == "best":
                    opts["format"] = (
                        "bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/"
                        "b[ext=mp4]/b"
                    )
                    opts["merge_output_format"] = "mp4"
                    opts["outtmpl"] = str(self.out_dir / f"{title}.%(ext)s")
                elif choice.kind == "preset":
                    opts["format"] = choice.format_id
                    opts["merge_output_format"] = "mp4"
                    opts["outtmpl"] = str(self.out_dir / f"{title}.%(ext)s")
                elif choice.kind == "video":
                    fmt = choice.format_id
                    matched = next(
                        (f for f in (self.info.get("formats") or []) if str(f.get("format_id")) == fmt),
                        None,
                    )
                    acodec = (matched or {}).get("acodec") or "none"
                    height = (matched or {}).get("height") or 0
                    if acodec == "none":
                        if choice.ext == "mp4":
                            opts["format"] = (
                                f"{fmt}+bestaudio[ext=m4a]/{fmt}+bestaudio/"
                                f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
                                f"best[height<={height}]/best"
                            )
                            opts["merge_output_format"] = "mp4"
                        else:
                            opts["format"] = f"{fmt}+bestaudio/best"
                            opts["merge_output_format"] = choice.ext
                    else:
                        opts["format"] = fmt
                else:
                    opts["format"] = choice.format_id

                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
            self.after(0, self.download_done)
        except Exception as exc:
            message = str(exc) or repr(exc) or type(exc).__name__
            if "403" in message:
                message = (
                    "YouTube hat diesen Stream blockiert (403). "
                    "Nutze oben „MP4 · Empfohlen · bis 1080p“ oder „Beste Qualität“."
                )
            self.after(0, lambda m=message: self.download_failed(m))

    def download_done(self):
        self.set_busy(False)
        self.progress.set(1)
        self.set_status(f"Fertig. Gespeichert in: {self.out_dir}")
        try:
            os.startfile(self.out_dir)
        except Exception:
            pass

    def download_failed(self, message: str):
        self.set_busy(False)
        self.set_status(f"Download fehlgeschlagen: {message}", error=True)


if __name__ == "__main__":
    app = App()
    app.mainloop()
