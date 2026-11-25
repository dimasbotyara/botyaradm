"""
config.py — Константы, пути, цвета.
Все настройки проекта собраны здесь.
"""

from pathlib import Path

# ─── Пути ──────────────────────────────────────────────
# Корень конфигурации botyaradm
BOTYARADM_DIR = Path.home() / ".config" / "botyaradm"

# Файл истории запусков
HISTORY_FILE = BOTYARADM_DIR / "history.json"

# Файл пользовательских настроек (setup wizard)
SETTINGS_FILE = BOTYARADM_DIR / "settings.json"

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

# ─── Настройки TUI (curses) ───────────────────────────
SHOW_ASCII_LOGO   = True               # Показывать ASCII-логотип в шапке
SHOW_SESSION_TYPE = True               # Показывать теги [X11] / [Wayland] / [TTY]
SHOW_STATUS_BAR   = True               # Показывать строку статуса (время, юзер, сессии)
CLEAR_TERMINAL    = True               # Очищать терминал до и после работы botyaradm
DEFAULT_THEME     = "botyaradm_classic" # Тема по умолчанию до прохождения мастера

# ─── Цвета (имена цветов curses) ──────────────────────
# Доступны: black, red, green, yellow, blue, magenta, cyan, white, default
COLOR_GREETING   = "white"
COLOR_SELECTED   = "blue"
COLOR_UNSELECTED = "cyan"              # голубой
COLOR_COUNTDOWN  = "white"
COLOR_TTY_OPTION = "cyan"
COLOR_ACCENT     = "cyan"

# ─── Названия специальных пунктов / маркеров ───────────
TTY_OPTION_NAME    = "Продолжить в TTY"
TTY_OPTION_EXEC    = "__tty__"         # Маркер выхода в TTY
WIZARD_OPTION_EXEC = "__wizard__"      # Маркер повторного запуска мастера настройки
