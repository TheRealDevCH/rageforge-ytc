import os
import shutil
import sys
import threading
import webbrowser
import winsound
from pathlib import Path

import customtkinter as ctk
import winreg

AUTHOR = "Rageforge"
APP_NAME = "Rageforge YTC"
EXE_NAME = "RageforgeYTC.exe"
UNINSTALL_NAME = "Uninstall Rageforge YTC.exe"
GOODBYE_URL = "https://therealdevch.github.io/rageforge-ytc/wiedersehen/"
PUBLISHER = "Rageforge"
BG = "#F5F5F7"
SURFACE = "#FFFFFF"
TEXT = "#1D1D1F"
MUTED = "#6E6E73"
BLUE = "#0071E3"
BLUE_HOVER = "#0077ED"
LINE = "#D2D2D7"


def resource_path(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name


def install_root() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Rageforge" / "YTC"


def create_shortcut(link_path: Path, target: Path, icon: Path | None = None):
    try:
        import win32com.client

        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(link_path))
        shortcut.Targetpath = str(target)
        shortcut.WorkingDirectory = str(target.parent)
        shortcut.IconLocation = str(icon or target)
        shortcut.save()
        return
    except Exception:
        pass
    ps = (
        f'$ws = New-Object -ComObject WScript.Shell; '
        f'$s = $ws.CreateShortcut(\'{str(link_path)}\'); '
        f'$s.TargetPath = \'{str(target)}\'; '
        f'$s.WorkingDirectory = \'{str(target.parent)}\'; '
        f'$s.IconLocation = \'{str(icon or target)}\'; '
        f'$s.Save()'
    )
    os.system(f'powershell -NoProfile -Command "{ps}"')


class Installer(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        self.title(f"{APP_NAME} Setup · {AUTHOR}")
        self.geometry("560x420")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        icon = resource_path("icon.ico")
        if icon.exists():
            try:
                self.iconbitmap(str(icon))
            except Exception:
                pass

        self.target_dir = install_root()
        self._build()

    def _build(self):
        card = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=24, border_width=1, border_color=LINE)
        card.pack(fill="both", expand=True, padx=28, pady=28)

        ctk.CTkLabel(
            card,
            text=APP_NAME,
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=TEXT,
        ).pack(anchor="w", padx=28, pady=(28, 4))
        ctk.CTkLabel(
            card,
            text="Installationsmanager · installiert nur die EXE",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=MUTED,
        ).pack(anchor="w", padx=28)

        self.path_label = ctk.CTkLabel(
            card,
            text=f"Zielordner\n{self.target_dir}",
            justify="left",
            anchor="w",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=TEXT,
        )
        self.path_label.pack(anchor="w", padx=28, pady=(24, 8))

        self.status = ctk.CTkLabel(card, text="Bereit zur Installation.", text_color=MUTED, anchor="w")
        self.status.pack(anchor="w", padx=28, pady=(8, 8))

        self.progress = ctk.CTkProgressBar(card, height=8, progress_color=BLUE, fg_color=LINE)
        self.progress.pack(fill="x", padx=28, pady=(4, 18))
        self.progress.set(0)

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(fill="x", padx=28, pady=(0, 28))
        self.install_btn = ctk.CTkButton(
            actions,
            text="Installieren",
            height=44,
            fg_color=BLUE,
            hover_color=BLUE_HOVER,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.start_install,
        )
        self.install_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.close_btn = ctk.CTkButton(
            actions,
            text="Schliessen",
            height=44,
            fg_color=SURFACE,
            hover_color=LINE,
            text_color=TEXT,
            border_width=1,
            border_color=LINE,
            command=self.destroy,
        )
        self.close_btn.pack(side="left")

    def start_install(self):
        self.install_btn.configure(state="disabled")
        self.close_btn.configure(state="disabled")
        self.status.configure(text="Installiere…", text_color=MUTED)
        threading.Thread(target=self.install_worker, daemon=True).start()

    def install_worker(self):
        try:
            src = resource_path(EXE_NAME)
            if not src.exists():
                raise FileNotFoundError("RageforgeYTC.exe fehlt im Installer.")
            self.after(0, lambda: self.progress.set(0.2))
            self.target_dir.mkdir(parents=True, exist_ok=True)
            dest = self.target_dir / EXE_NAME
            shutil.copy2(src, dest)
            icon_src = resource_path("icon.ico")
            icon_dest = self.target_dir / "icon.ico"
            if icon_src.exists():
                shutil.copy2(icon_src, icon_dest)
            self.after(0, lambda: self.progress.set(0.45))

            desktop = Path.home() / "Desktop"
            if not desktop.exists():
                desktop = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
            create_shortcut(desktop / f"{APP_NAME}.lnk", dest, icon_dest if icon_dest.exists() else dest)

            start_menu = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Rageforge"
            start_menu.mkdir(parents=True, exist_ok=True)
            create_shortcut(start_menu / f"{APP_NAME}.lnk", dest, icon_dest if icon_dest.exists() else dest)
            self.after(0, lambda: self.progress.set(0.7))

            uninstaller = self.write_uninstaller(dest)
            self.register_uninstall(uninstaller, dest)
            self.after(0, lambda: self.progress.set(1.0))
            self.after(0, self.install_done)
        except Exception as exc:
            message = str(exc) or repr(exc)
            self.after(0, lambda m=message: self.install_failed(m))

    def write_uninstaller(self, app_exe: Path) -> Path:
        script = self.target_dir / "uninstall.ps1"
        content = f"""$ErrorActionPreference = 'SilentlyContinue'
$root = '{self.target_dir}'
$desktop = Join-Path $env:USERPROFILE 'Desktop\\{APP_NAME}.lnk'
$start = Join-Path $env:APPDATA 'Microsoft\\Windows\\Start Menu\\Programs\\Rageforge\\{APP_NAME}.lnk'
Remove-Item -Force $desktop -ErrorAction SilentlyContinue
Remove-Item -Force $start -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force (Join-Path $env:APPDATA 'Microsoft\\Windows\\Start Menu\\Programs\\Rageforge') -ErrorAction SilentlyContinue
$reg = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\RageforgeYTC'
Remove-Item -Recurse -Force $reg -ErrorAction SilentlyContinue
Start-Process '{GOODBYE_URL}'
Start-Sleep -Seconds 1
Remove-Item -Recurse -Force $root -ErrorAction SilentlyContinue
"""
        script.write_text(content, encoding="utf-8")
        launcher = self.target_dir / "Uninstall.cmd"
        launcher.write_text(
            f'@echo off\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "{script}"\r\n',
            encoding="utf-8",
        )
        return launcher

    def register_uninstall(self, uninstaller: Path, app_exe: Path):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\RageforgeYTC"
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(app_exe))
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(self.target_dir))
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, str(uninstaller))
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
            try:
                size_kb = int(app_exe.stat().st_size / 1024)
                winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, size_kb)
            except Exception:
                pass

    def install_done(self):
        self.status.configure(text="Installation fertig. Verknüpfung liegt auf dem Desktop.", text_color=TEXT)
        self.install_btn.configure(text="Starten", state="normal", command=self.launch_app)
        self.close_btn.configure(state="normal")
        try:
            winsound.MessageBeep(winsound.MB_OK)
        except Exception:
            pass

    def launch_app(self):
        app = self.target_dir / EXE_NAME
        if app.exists():
            os.startfile(app)
        self.destroy()

    def install_failed(self, message: str):
        self.status.configure(text=f"Fehler: {message}", text_color="#B91C1C")
        self.install_btn.configure(state="normal")
        self.close_btn.configure(state="normal")


if __name__ == "__main__":
    app = Installer()
    app.mainloop()
