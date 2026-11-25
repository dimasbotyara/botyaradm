"""
config.py — Константы, пути, цвета.
Все настройки проекта собраны здесь.
"""

from pathlib import Path

# ─── Пути ──────────────────────────────────────────────
# Корень конфигурации PyDM
PYDM_DIR = Path.home() / ".config" / "pydm"

# Файл истории запусков
HISTORY_FILE = PYDM_DIR / "history.json"

# ─── Пользователь ─────────────────────────────────────
USERNAME = "dimasbotyara"

# ─── Таймаут автозапуска (секунды) ─────────────────────
AUTO_SELECT_TIMEOUT = 5

# ─── Пути к .desktop файлам сессий ─────────────────────
XSESSION_DIRS = [
    Path("/usr/share/xsessions"),
]

WAYLAND_SESSION_DIRS = [
    Path("/usr/share/wayland-sessions"),
]

# ─── Известные DE/WM как fallback (команда → название) ─
# Используется если .desktop файлы не найдены
KNOWN_SESSIONS = {
    "startxfce4":    "XFCE",
    "i3":            "i3wm",
    "sway":          "Sway (Wayland)",
    "openbox-session": "Openbox",
    "bspwm":         "bspwm",
    "dwm":           "dwm",
    "awesome":       "Awesome",
    "herbstluftwm":  "herbstluftwm",
    "qtile start":   "Qtile",
    "hyprland":      "Hyprland (Wayland)",
    "startplasma-x11":   "KDE Plasma (X11)",
    "startplasma-wayland": "KDE Plasma (Wayland)",
    "gnome-session":  "GNOME",
    "cinnamon-session": "Cinnamon",
    "mate-session":   "MATE",
    "budgie-desktop": "Budgie",
    "enlightenment_start": "Enlightenment",
    "startlxqt":     "LXQt",
    "lxsession":     "LXDE",
    "startfluxbox":  "Fluxbox",
    "icewm-session": "IceWM",
    "river":         "River (Wayland)",
    "labwc":         "LabWC (Wayland)",
    "wayfire":       "Wayfire (Wayland)",
    "jwm":           "JWM",
    "fvwm3":         "FVWM3",
    "leftwm":        "LeftWM",
    "spectrwm":      "spectrwm",
    "xmonad":        "XMonad",
    "stumpwm":       "StumpWM",
    "cwm":           "cwm",
    "wmaker":        "Window Maker",
    "2bwm":          "2bwm",
    "berry":         "berry",
    "dk":            "dk",
    "sowm":          "sowm",
    "tinywm":        "TinyWM",
}

# ─── Цвета (Rich markup) ──────────────────────────────
COLOR_GREETING   = "white"
COLOR_SELECTED   = "bold blue"
COLOR_UNSELECTED = "bright_cyan"       # голубой
COLOR_COUNTDOWN  = "dim white"
COLOR_TTY_OPTION = "bright_cyan"

# ─── Название специального пункта ──────────────────────
TTY_OPTION_NAME = "Продолжить в TTY"
TTY_OPTION_EXEC = "__tty__"            # Маркер, не команда
