"""
themes.py — Коллекция цветовых тем оформления для botyaradm (curses TUI).

Поддерживает:
  - 256-цветную палитру (xterm-256color, alacritty, kitty, foot, tmux и др.)
  - Настоящую 16-цветную 24-битную RGB-палитру на Linux TTY (/dev/tty1..63, TERM=linux)
    через ESC ] P с автоматическим восстановлением палитры через ESC ] R
  - Улучшенный fallback на 8 базовых цветов для остальных терминалов
  - Монохромный режим, если терминал не поддерживает цвета
"""

import atexit
import curses
import os
import sys
from dataclasses import dataclass

_KDGETMODE = 0x4B3B
_KD_TEXT_MODES = (0x00, 0x02, 0x03)  # KD_TEXT, KD_TEXT0, KD_TEXT1

_ANSI_16_RGB: tuple[tuple[int, int, int], ...] = (
    (0x00, 0x00, 0x00),
    (0x80, 0x00, 0x00),
    (0x00, 0x80, 0x00),
    (0x80, 0x80, 0x00),
    (0x00, 0x00, 0x80),
    (0x80, 0x00, 0x80),
    (0x00, 0x80, 0x80),
    (0xC0, 0xC0, 0xC0),
    (0x80, 0x80, 0x80),
    (0xFF, 0x00, 0x00),
    (0x00, 0xFF, 0x00),
    (0xFF, 0xFF, 0x00),
    (0x00, 0x00, 0xFF),
    (0xFF, 0x00, 0xFF),
    (0x00, 0xFF, 0xFF),
    (0xFF, 0xFF, 0xFF),
)
_CUBE_LEVELS: tuple[int, ...] = (0x00, 0x5F, 0x87, 0xAF, 0xD7, 0xFF)

_tty_palette_active = False


@dataclass(frozen=True)
class Theme:
    """Описание цветовой темы TUI."""

    id: str
    name: str
    description: str
    # 256-цветные индексы (0..255), -1 означает цвет фона терминала по умолчанию
    palette_256: dict[str, int]
    # 8-цветный fallback (curses.COLOR_*)
    palette_8: dict[str, int]
    # Необязательный цвет фона всего окна в 256-цветном режиме (-1 = прозрачный/дефолтный)
    window_bg_256: int = -1
    # Базовый цвет текста на этом фоне (для светлых тем)
    window_fg_256: int = -1
    # Необязательный цвет фона и текста окна в 8-цветном режиме (для светлых тем)
    window_bg_8: int = -1
    window_fg_8: int = -1


# ─── Каталог тем (25 тем) ────────────────────────────
_THEMES_LIST: list[Theme] = [
    Theme(
        id="botyaradm_classic",
        name="botyaradm Classic",
        description="Фирменный голубой и глубокий синий",
        palette_256={
            "accent": 51,
            "border": 39,
            "greeting": 255,
            "selected_fg": 255,
            "selected_bg": 27,
            "unselected": 87,
            "tty": 117,
            "dim": 246,
            "countdown": 220,
            "tag_x11": 82,
            "tag_wayland": 177,
            "tag_tty": 245,
            "last": 220,
            "error": 196,
            "success": 82,
        },
        palette_8={
            "accent": curses.COLOR_CYAN,
            "border": curses.COLOR_CYAN,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_WHITE,
            "selected_bg": curses.COLOR_BLUE,
            "unselected": curses.COLOR_CYAN,
            "tty": curses.COLOR_CYAN,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_GREEN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="pacman",
        name="Pacman (Arch Linux)",
        description="Arch Blue (#1793D1) и жёлтый Pacman",
        palette_256={
            "accent": 39,
            "border": 33,
            "greeting": 255,
            "selected_fg": 16,
            "selected_bg": 226,
            "unselected": 75,
            "tty": 117,
            "dim": 245,
            "countdown": 226,
            "tag_x11": 39,
            "tag_wayland": 226,
            "tag_tty": 244,
            "last": 226,
            "error": 196,
            "success": 46,
        },
        palette_8={
            "accent": curses.COLOR_BLUE,
            "border": curses.COLOR_BLUE,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_BLACK,
            "selected_bg": curses.COLOR_YELLOW,
            "unselected": curses.COLOR_BLUE,
            "tty": curses.COLOR_CYAN,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_CYAN,
            "tag_wayland": curses.COLOR_YELLOW,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="ayu_dark",
        name="Ayu Dark",
        description="Золотистый янтарь, бирюза и тёплый кремовый",
        palette_256={
            "accent": 214,
            "border": 172,
            "greeting": 253,
            "selected_fg": 16,
            "selected_bg": 214,
            "unselected": 81,
            "tty": 114,
            "dim": 243,
            "countdown": 221,
            "tag_x11": 114,
            "tag_wayland": 183,
            "tag_tty": 244,
            "last": 214,
            "error": 203,
            "success": 114,
        },
        palette_8={
            "accent": curses.COLOR_YELLOW,
            "border": curses.COLOR_YELLOW,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_BLACK,
            "selected_bg": curses.COLOR_YELLOW,
            "unselected": curses.COLOR_YELLOW,
            "tty": curses.COLOR_GREEN,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_GREEN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="ayu_mirage",
        name="Ayu Mirage",
        description="Мягкий янтарный, мятный и морской синий",
        palette_256={
            "accent": 215,
            "border": 74,
            "greeting": 254,
            "selected_fg": 16,
            "selected_bg": 215,
            "unselected": 117,
            "tty": 150,
            "dim": 245,
            "countdown": 222,
            "tag_x11": 150,
            "tag_wayland": 182,
            "tag_tty": 245,
            "last": 215,
            "error": 203,
            "success": 150,
        },
        palette_8={
            "accent": curses.COLOR_YELLOW,
            "border": curses.COLOR_CYAN,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_BLACK,
            "selected_bg": curses.COLOR_YELLOW,
            "unselected": curses.COLOR_CYAN,
            "tty": curses.COLOR_GREEN,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_GREEN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="ayu_light",
        name="Ayu Light",
        description="Светлая бумага, янтарный акцент и кобальт",
        window_bg_256=255,
        window_fg_256=236,
        window_bg_8=curses.COLOR_WHITE,
        window_fg_8=curses.COLOR_BLACK,
        palette_256={
            "accent": 166,
            "border": 33,
            "greeting": 235,
            "selected_fg": 255,
            "selected_bg": 166,
            "unselected": 25,
            "tty": 28,
            "dim": 244,
            "countdown": 166,
            "tag_x11": 28,
            "tag_wayland": 127,
            "tag_tty": 244,
            "last": 166,
            "error": 160,
            "success": 28,
        },
        palette_8={
            "accent": curses.COLOR_RED,
            "border": curses.COLOR_BLUE,
            "greeting": curses.COLOR_BLACK,
            "selected_fg": curses.COLOR_WHITE,
            "selected_bg": curses.COLOR_RED,
            "unselected": curses.COLOR_BLUE,
            "tty": curses.COLOR_RED,
            "dim": curses.COLOR_BLACK,
            "countdown": curses.COLOR_RED,
            "tag_x11": curses.COLOR_BLUE,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_BLACK,
            "last": curses.COLOR_RED,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_BLUE,
        },
    ),
    Theme(
        id="gruvbox_dark",
        name="Gruvbox Dark",
        description="Тёплый ретро-оранжевый, горчица и аква",
        palette_256={
            "accent": 208,
            "border": 172,
            "greeting": 223,
            "selected_fg": 235,
            "selected_bg": 214,
            "unselected": 108,
            "tty": 142,
            "dim": 244,
            "countdown": 214,
            "tag_x11": 142,
            "tag_wayland": 175,
            "tag_tty": 244,
            "last": 208,
            "error": 167,
            "success": 142,
        },
        palette_8={
            "accent": curses.COLOR_YELLOW,
            "border": curses.COLOR_RED,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_BLACK,
            "selected_bg": curses.COLOR_YELLOW,
            "unselected": curses.COLOR_GREEN,
            "tty": curses.COLOR_YELLOW,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_GREEN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="gruvbox_material",
        name="Gruvbox Material",
        description="Спокойный терракотовый, шалфей и песок",
        palette_256={
            "accent": 209,
            "border": 142,
            "greeting": 223,
            "selected_fg": 235,
            "selected_bg": 142,
            "unselected": 109,
            "tty": 214,
            "dim": 245,
            "countdown": 214,
            "tag_x11": 142,
            "tag_wayland": 175,
            "tag_tty": 245,
            "last": 209,
            "error": 167,
            "success": 142,
        },
        palette_8={
            "accent": curses.COLOR_RED,
            "border": curses.COLOR_GREEN,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_BLACK,
            "selected_bg": curses.COLOR_GREEN,
            "unselected": curses.COLOR_YELLOW,
            "tty": curses.COLOR_GREEN,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_GREEN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="gruvbox_light",
        name="Gruvbox Light",
        description="Светлый пергамент, охра и лесная зелень",
        window_bg_256=230,
        window_fg_256=237,
        window_bg_8=curses.COLOR_WHITE,
        window_fg_8=curses.COLOR_BLACK,
        palette_256={
            "accent": 130,
            "border": 166,
            "greeting": 236,
            "selected_fg": 230,
            "selected_bg": 166,
            "unselected": 24,
            "tty": 64,
            "dim": 243,
            "countdown": 130,
            "tag_x11": 64,
            "tag_wayland": 96,
            "tag_tty": 243,
            "last": 124,
            "error": 124,
            "success": 64,
        },
        palette_8={
            "accent": curses.COLOR_RED,
            "border": curses.COLOR_RED,
            "greeting": curses.COLOR_BLACK,
            "selected_fg": curses.COLOR_WHITE,
            "selected_bg": curses.COLOR_YELLOW,
            "unselected": curses.COLOR_RED,
            "tty": curses.COLOR_BLUE,
            "dim": curses.COLOR_BLACK,
            "countdown": curses.COLOR_RED,
            "tag_x11": curses.COLOR_BLUE,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_BLACK,
            "last": curses.COLOR_RED,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_BLUE,
        },
    ),
    Theme(
        id="catppuccin_mocha",
        name="Catppuccin Mocha",
        description="Пастельный сиреневый, сапфир и персик",
        palette_256={
            "accent": 183,
            "border": 147,
            "greeting": 254,
            "selected_fg": 16,
            "selected_bg": 183,
            "unselected": 111,
            "tty": 150,
            "dim": 246,
            "countdown": 216,
            "tag_x11": 150,
            "tag_wayland": 211,
            "tag_tty": 245,
            "last": 216,
            "error": 210,
            "success": 150,
        },
        palette_8={
            "accent": curses.COLOR_MAGENTA,
            "border": curses.COLOR_MAGENTA,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_BLACK,
            "selected_bg": curses.COLOR_MAGENTA,
            "unselected": curses.COLOR_BLUE,
            "tty": curses.COLOR_GREEN,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_GREEN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="catppuccin_macchiato",
        name="Catppuccin Macchiato",
        description="Мягкий бирюзовый, розовый фламинго и нежный синий",
        palette_256={
            "accent": 116,
            "border": 111,
            "greeting": 254,
            "selected_fg": 16,
            "selected_bg": 111,
            "unselected": 152,
            "tty": 150,
            "dim": 246,
            "countdown": 222,
            "tag_x11": 150,
            "tag_wayland": 211,
            "tag_tty": 245,
            "last": 222,
            "error": 210,
            "success": 150,
        },
        palette_8={
            "accent": curses.COLOR_CYAN,
            "border": curses.COLOR_BLUE,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_BLACK,
            "selected_bg": curses.COLOR_CYAN,
            "unselected": curses.COLOR_BLUE,
            "tty": curses.COLOR_GREEN,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_GREEN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="dracula",
        name="Dracula",
        description="Фиолетовый, неоновый розовый и ледяной голубой",
        palette_256={
            "accent": 141,
            "border": 99,
            "greeting": 255,
            "selected_fg": 16,
            "selected_bg": 141,
            "unselected": 117,
            "tty": 84,
            "dim": 246,
            "countdown": 228,
            "tag_x11": 84,
            "tag_wayland": 212,
            "tag_tty": 245,
            "last": 228,
            "error": 203,
            "success": 84,
        },
        palette_8={
            "accent": curses.COLOR_MAGENTA,
            "border": curses.COLOR_MAGENTA,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_WHITE,
            "selected_bg": curses.COLOR_MAGENTA,
            "unselected": curses.COLOR_MAGENTA,
            "tty": curses.COLOR_GREEN,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_GREEN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="nord",
        name="Nord",
        description="Арктический лёд, северное сияние и скандинавский синий",
        palette_256={
            "accent": 110,
            "border": 74,
            "greeting": 254,
            "selected_fg": 16,
            "selected_bg": 110,
            "unselected": 152,
            "tty": 108,
            "dim": 245,
            "countdown": 222,
            "tag_x11": 108,
            "tag_wayland": 139,
            "tag_tty": 245,
            "last": 222,
            "error": 167,
            "success": 108,
        },
        palette_8={
            "accent": curses.COLOR_CYAN,
            "border": curses.COLOR_BLUE,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_BLACK,
            "selected_bg": curses.COLOR_CYAN,
            "unselected": curses.COLOR_WHITE,
            "tty": curses.COLOR_CYAN,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_GREEN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="tokyo_night",
        name="Tokyo Night",
        description="Ночной Токио: неон-синий, пурпур и бирюза",
        palette_256={
            "accent": 111,
            "border": 68,
            "greeting": 254,
            "selected_fg": 16,
            "selected_bg": 111,
            "unselected": 80,
            "tty": 115,
            "dim": 245,
            "countdown": 215,
            "tag_x11": 115,
            "tag_wayland": 141,
            "tag_tty": 245,
            "last": 215,
            "error": 203,
            "success": 115,
        },
        palette_8={
            "accent": curses.COLOR_BLUE,
            "border": curses.COLOR_MAGENTA,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_WHITE,
            "selected_bg": curses.COLOR_BLUE,
            "unselected": curses.COLOR_MAGENTA,
            "tty": curses.COLOR_CYAN,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_GREEN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="one_dark",
        name="One Dark",
        description="Классика Atom/VSCode: небесный синий, шалфей и коралл",
        palette_256={
            "accent": 75,
            "border": 39,
            "greeting": 253,
            "selected_fg": 16,
            "selected_bg": 75,
            "unselected": 80,
            "tty": 114,
            "dim": 245,
            "countdown": 180,
            "tag_x11": 114,
            "tag_wayland": 176,
            "tag_tty": 245,
            "last": 180,
            "error": 204,
            "success": 114,
        },
        palette_8={
            "accent": curses.COLOR_BLUE,
            "border": curses.COLOR_CYAN,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_BLACK,
            "selected_bg": curses.COLOR_CYAN,
            "unselected": curses.COLOR_GREEN,
            "tty": curses.COLOR_BLUE,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_GREEN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="monokai_pro",
        name="Monokai Pro",
        description="Яркая маджента, лайм и лимонное золото",
        palette_256={
            "accent": 197,
            "border": 148,
            "greeting": 255,
            "selected_fg": 16,
            "selected_bg": 221,
            "unselected": 81,
            "tty": 148,
            "dim": 245,
            "countdown": 221,
            "tag_x11": 148,
            "tag_wayland": 197,
            "tag_tty": 245,
            "last": 221,
            "error": 197,
            "success": 148,
        },
        palette_8={
            "accent": curses.COLOR_MAGENTA,
            "border": curses.COLOR_GREEN,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_BLACK,
            "selected_bg": curses.COLOR_YELLOW,
            "unselected": curses.COLOR_GREEN,
            "tty": curses.COLOR_MAGENTA,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_GREEN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="solarized_dark",
        name="Solarized Dark",
        description="Научно-выверенный Solarized: циан, синий и охра",
        palette_256={
            "accent": 37,
            "border": 33,
            "greeting": 252,
            "selected_fg": 255,
            "selected_bg": 33,
            "unselected": 37,
            "tty": 64,
            "dim": 244,
            "countdown": 136,
            "tag_x11": 64,
            "tag_wayland": 125,
            "tag_tty": 244,
            "last": 136,
            "error": 160,
            "success": 64,
        },
        palette_8={
            "accent": curses.COLOR_CYAN,
            "border": curses.COLOR_BLUE,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_WHITE,
            "selected_bg": curses.COLOR_BLUE,
            "unselected": curses.COLOR_CYAN,
            "tty": curses.COLOR_GREEN,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_GREEN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="everforest",
        name="Everforest",
        description="Уютный хвойный лес, мох и тёплый янтарь",
        palette_256={
            "accent": 107,
            "border": 108,
            "greeting": 223,
            "selected_fg": 235,
            "selected_bg": 107,
            "unselected": 108,
            "tty": 150,
            "dim": 245,
            "countdown": 215,
            "tag_x11": 107,
            "tag_wayland": 175,
            "tag_tty": 245,
            "last": 215,
            "error": 167,
            "success": 107,
        },
        palette_8={
            "accent": curses.COLOR_GREEN,
            "border": curses.COLOR_GREEN,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_BLACK,
            "selected_bg": curses.COLOR_GREEN,
            "unselected": curses.COLOR_GREEN,
            "tty": curses.COLOR_YELLOW,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_GREEN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="kanagawa",
        name="Kanagawa",
        description="Большая волна: глубокий синий, золото и сакура",
        palette_256={
            "accent": 179,
            "border": 68,
            "greeting": 223,
            "selected_fg": 255,
            "selected_bg": 68,
            "unselected": 110,
            "tty": 108,
            "dim": 245,
            "countdown": 179,
            "tag_x11": 108,
            "tag_wayland": 175,
            "tag_tty": 245,
            "last": 179,
            "error": 167,
            "success": 108,
        },
        palette_8={
            "accent": curses.COLOR_YELLOW,
            "border": curses.COLOR_BLUE,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_BLACK,
            "selected_bg": curses.COLOR_YELLOW,
            "unselected": curses.COLOR_BLUE,
            "tty": curses.COLOR_GREEN,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_GREEN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="rose_pine",
        name="Rose Pine",
        description="Нежная роза, ирис, морская пена и золото",
        palette_256={
            "accent": 217,
            "border": 146,
            "greeting": 254,
            "selected_fg": 16,
            "selected_bg": 217,
            "unselected": 116,
            "tty": 146,
            "dim": 246,
            "countdown": 222,
            "tag_x11": 116,
            "tag_wayland": 211,
            "tag_tty": 246,
            "last": 222,
            "error": 211,
            "success": 116,
        },
        palette_8={
            "accent": curses.COLOR_MAGENTA,
            "border": curses.COLOR_RED,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_BLACK,
            "selected_bg": curses.COLOR_MAGENTA,
            "unselected": curses.COLOR_RED,
            "tty": curses.COLOR_MAGENTA,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_CYAN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="synthwave84",
        name="Synthwave '84",
        description="Ретровейв 80-х: горячий розовый, лазерный циан и закат",
        palette_256={
            "accent": 199,
            "border": 135,
            "greeting": 255,
            "selected_fg": 16,
            "selected_bg": 51,
            "unselected": 51,
            "tty": 213,
            "dim": 247,
            "countdown": 227,
            "tag_x11": 51,
            "tag_wayland": 199,
            "tag_tty": 246,
            "last": 227,
            "error": 196,
            "success": 51,
        },
        palette_8={
            "accent": curses.COLOR_MAGENTA,
            "border": curses.COLOR_MAGENTA,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_BLACK,
            "selected_bg": curses.COLOR_CYAN,
            "unselected": curses.COLOR_MAGENTA,
            "tty": curses.COLOR_CYAN,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_CYAN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="cyberpunk",
        name="Cyberpunk 2077",
        description="Найт-Сити: кислотный жёлтый, кибер-циан и неон-розовый",
        palette_256={
            "accent": 226,
            "border": 51,
            "greeting": 255,
            "selected_fg": 16,
            "selected_bg": 226,
            "unselected": 51,
            "tty": 201,
            "dim": 246,
            "countdown": 201,
            "tag_x11": 51,
            "tag_wayland": 201,
            "tag_tty": 245,
            "last": 226,
            "error": 196,
            "success": 51,
        },
        palette_8={
            "accent": curses.COLOR_YELLOW,
            "border": curses.COLOR_CYAN,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_BLACK,
            "selected_bg": curses.COLOR_YELLOW,
            "unselected": curses.COLOR_YELLOW,
            "tty": curses.COLOR_MAGENTA,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_MAGENTA,
            "tag_x11": curses.COLOR_CYAN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_YELLOW,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_CYAN,
        },
    ),
    Theme(
        id="matrix",
        name="Matrix",
        description="Фосфорный зелёный терминал из Матрицы",
        palette_256={
            "accent": 46,
            "border": 34,
            "greeting": 120,
            "selected_fg": 16,
            "selected_bg": 46,
            "unselected": 40,
            "tty": 35,
            "dim": 28,
            "countdown": 82,
            "tag_x11": 46,
            "tag_wayland": 118,
            "tag_tty": 28,
            "last": 154,
            "error": 196,
            "success": 46,
        },
        palette_8={
            "accent": curses.COLOR_GREEN,
            "border": curses.COLOR_GREEN,
            "greeting": curses.COLOR_GREEN,
            "selected_fg": curses.COLOR_BLACK,
            "selected_bg": curses.COLOR_GREEN,
            "unselected": curses.COLOR_GREEN,
            "tty": curses.COLOR_GREEN,
            "dim": curses.COLOR_GREEN,
            "countdown": curses.COLOR_GREEN,
            "tag_x11": curses.COLOR_GREEN,
            "tag_wayland": curses.COLOR_GREEN,
            "tag_tty": curses.COLOR_GREEN,
            "last": curses.COLOR_WHITE,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="oxocarbon",
        name="Oxocarbon",
        description="IBM Carbon: ультра-контрастный циан, кобальт и фуксия",
        palette_256={
            "accent": 81,
            "border": 33,
            "greeting": 255,
            "selected_fg": 255,
            "selected_bg": 205,
            "unselected": 85,
            "tty": 111,
            "dim": 246,
            "countdown": 81,
            "tag_x11": 85,
            "tag_wayland": 205,
            "tag_tty": 245,
            "last": 81,
            "error": 196,
            "success": 85,
        },
        palette_8={
            "accent": curses.COLOR_CYAN,
            "border": curses.COLOR_BLUE,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_WHITE,
            "selected_bg": curses.COLOR_MAGENTA,
            "unselected": curses.COLOR_GREEN,
            "tty": curses.COLOR_CYAN,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_CYAN,
            "tag_x11": curses.COLOR_GREEN,
            "tag_wayland": curses.COLOR_MAGENTA,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_CYAN,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_GREEN,
        },
    ),
    Theme(
        id="amber_crt",
        name="Amber CRT",
        description="Винтажный янтарный ЭЛТ-монитор 80-х",
        palette_256={
            "accent": 214,
            "border": 172,
            "greeting": 222,
            "selected_fg": 16,
            "selected_bg": 214,
            "unselected": 178,
            "tty": 136,
            "dim": 130,
            "countdown": 220,
            "tag_x11": 214,
            "tag_wayland": 220,
            "tag_tty": 130,
            "last": 222,
            "error": 196,
            "success": 214,
        },
        palette_8={
            "accent": curses.COLOR_YELLOW,
            "border": curses.COLOR_YELLOW,
            "greeting": curses.COLOR_YELLOW,
            "selected_fg": curses.COLOR_BLACK,
            "selected_bg": curses.COLOR_YELLOW,
            "unselected": curses.COLOR_YELLOW,
            "tty": curses.COLOR_YELLOW,
            "dim": curses.COLOR_YELLOW,
            "countdown": curses.COLOR_YELLOW,
            "tag_x11": curses.COLOR_YELLOW,
            "tag_wayland": curses.COLOR_WHITE,
            "tag_tty": curses.COLOR_YELLOW,
            "last": curses.COLOR_WHITE,
            "error": curses.COLOR_RED,
            "success": curses.COLOR_YELLOW,
        },
    ),
    Theme(
        id="monochrome",
        name="Monochrome Minimal",
        description="Строгий чёрно-белый минимализм",
        palette_256={
            "accent": 255,
            "border": 248,
            "greeting": 255,
            "selected_fg": 16,
            "selected_bg": 255,
            "unselected": 250,
            "tty": 246,
            "dim": 242,
            "countdown": 255,
            "tag_x11": 252,
            "tag_wayland": 252,
            "tag_tty": 244,
            "last": 255,
            "error": 255,
            "success": 255,
        },
        palette_8={
            "accent": curses.COLOR_WHITE,
            "border": curses.COLOR_WHITE,
            "greeting": curses.COLOR_WHITE,
            "selected_fg": curses.COLOR_BLACK,
            "selected_bg": curses.COLOR_WHITE,
            "unselected": curses.COLOR_WHITE,
            "tty": curses.COLOR_WHITE,
            "dim": curses.COLOR_WHITE,
            "countdown": curses.COLOR_WHITE,
            "tag_x11": curses.COLOR_WHITE,
            "tag_wayland": curses.COLOR_WHITE,
            "tag_tty": curses.COLOR_WHITE,
            "last": curses.COLOR_WHITE,
            "error": curses.COLOR_WHITE,
            "success": curses.COLOR_WHITE,
        },
    ),
]

THEMES: dict[str, Theme] = {theme.id: theme for theme in _THEMES_LIST}
THEME_ORDER: list[str] = [theme.id for theme in _THEMES_LIST]


def _x256_to_rgb(color: int) -> tuple[int, int, int]:
    """Конвертирует индекс 256-цветной палитры xterm (0..255) в (R, G, B)."""
    if color < 0:
        return (0, 0, 0)
    if color < 16:
        return _ANSI_16_RGB[color]
    if color <= 231:
        idx = color - 16
        r = _CUBE_LEVELS[idx // 36]
        g = _CUBE_LEVELS[(idx // 6) % 6]
        b = _CUBE_LEVELS[idx % 6]
        return (r, g, b)
    gray = 8 + (color - 232) * 10
    return (gray, gray, gray)


def _build_linux_vt_palette(theme: Theme) -> list[tuple[int, int, int]]:
    """
    Строит 16-цветную 24-битную RGB-палитру Linux VT (слоты 0..15) для темы.

    Слоты 0..7 доступны как для текста, так и для фона; слоты 8..15 активируются
    в Linux VT флагом A_BOLD на цвете текста 0..7. Это позволяет задать точный
    RGB-цвет для каждого элемента интерфейса (фон окна, выделенная строка,
    невыделенные пункты, описания, рамки, логотип, теги и т.д.).
    """
    p = theme.palette_256
    win_bg = (
        _x256_to_rgb(theme.window_bg_256)
        if theme.window_bg_256 >= 0
        else (0, 0, 0)
    )
    return [
        win_bg,                           # 0: COLOR_BLACK   -> фон окна
        _x256_to_rgb(p["error"]),         # 1: COLOR_RED     -> ошибка
        _x256_to_rgb(p["tag_x11"]),       # 2: COLOR_GREEN   -> [X11]
        _x256_to_rgb(p["tag_tty"]),       # 3: COLOR_YELLOW  -> [TTY]
        _x256_to_rgb(p["selected_bg"]),   # 4: COLOR_BLUE    -> фон выбранной строки
        _x256_to_rgb(p["tag_wayland"]),   # 5: COLOR_MAGENTA -> [Wayland]
        _x256_to_rgb(p["unselected"]),    # 6: COLOR_CYAN    -> невыделенные пункты
        _x256_to_rgb(p["dim"]),           # 7: COLOR_WHITE   -> описания / подсказки
        _x256_to_rgb(p["selected_fg"]),   # 8: BLACK  | BOLD -> текст выбранной строки
        _x256_to_rgb(p["last"]),          # 9: RED    | BOLD -> маркер *last
        _x256_to_rgb(p["tty"]),           # a: GREEN  | BOLD -> пункт TTY
        _x256_to_rgb(p["countdown"]),     # b: YELLOW | BOLD -> таймер автозапуска
        _x256_to_rgb(p["border"]),        # c: BLUE   | BOLD -> рамки
        _x256_to_rgb(p["accent"]),        # d: MAG    | BOLD -> акцент / логотип
        _x256_to_rgb(p["success"]),       # e: CYAN   | BOLD -> успех
        _x256_to_rgb(p["greeting"]),      # f: WHITE  | BOLD -> приветствие / заголовки
    ]


def _is_linux_vt() -> bool:
    """
    Возвращает True, если stdout подключён к настоящей виртуальной консоли
    Linux (/dev/tty1..63, TERM=linux), поддерживающей ESC ] P / ESC ] R.
    """
    term = os.environ.get("TERM", "")
    if not (term == "linux" or term.startswith("linux-")):
        return False

    override = os.environ.get("BOTYARADM_TTY_PALETTE")
    if override is not None:
        return override.strip().lower() in ("1", "true", "yes", "on")

    try:
        fd = sys.stdout.fileno()
        if not os.isatty(fd):
            return False
    except (AttributeError, OSError, ValueError):
        return False

    # Основная проверка: ioctl KDGETMODE работает только на реальном Linux VT
    try:
        import array
        import fcntl

        buf = array.array("i", [0])
        fcntl.ioctl(fd, _KDGETMODE, buf, True)
        if buf[0] in _KD_TEXT_MODES:
            return True
    except (ImportError, OSError, ValueError):
        pass

    # Запасная проверка по имени устройства (/dev/ttyN или /dev/vc/N)
    try:
        tty_name = os.ttyname(fd)
        if tty_name.startswith("/dev/tty") and tty_name[8:].isdigit():
            return True
        if tty_name.startswith("/dev/vc/") and tty_name[8:].isdigit():
            return True
    except OSError:
        pass

    return False


def _write_tty_bytes(data: bytes) -> bool:
    """Надёжно записывает escape-последовательность напрямую в TTY."""
    try:
        fd = sys.stdout.fileno()
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                return False
            view = view[written:]
        return True
    except (AttributeError, OSError, ValueError):
        return False


def _apply_linux_vt_palette(theme: Theme) -> bool:
    """Применяет 16-цветную RGB-палитру темы к текущей виртуальной консоли Linux."""
    global _tty_palette_active
    palette = _build_linux_vt_palette(theme)
    payload = b"".join(
        f"\x1b]P{idx:x}{r:02x}{g:02x}{b:02x}".encode("ascii")
        for idx, (r, g, b) in enumerate(palette)
    )
    if _write_tty_bytes(payload):
        _tty_palette_active = True
        return True
    return False


def reset_tty_palette() -> None:
    """Восстанавливает стандартную палитру Linux TTY (ESC ] R), если она менялась."""
    global _tty_palette_active
    if not _tty_palette_active:
        return
    _tty_palette_active = False
    _write_tty_bytes(b"\x1b]R")


atexit.register(reset_tty_palette)


def get_theme(theme_id: str | None) -> Theme:
    """Возвращает тему по ID или тему по умолчанию."""
    if theme_id and theme_id in THEMES:
        return THEMES[theme_id]
    return THEMES["botyaradm_classic"]


def init_theme_colors(
    theme_id: str | None,
    stdscr: "curses.window | None" = None,
) -> dict[str, int]:
    """
    Инициализирует цветовые пары curses согласно выбранной теме.

    Поддерживает три режима:
      1. 256-цветные терминалы (xterm-256color, alacritty, kitty, foot и др.)
      2. Настоящий Linux TTY (/dev/tty1..63, TERM=linux): точная 16-цветная
         24-битная RGB-палитра через ESC ] P (все элементы, включая селекторы)
      3. Улучшенный 8-цветный fallback для остальных терминалов (плюс монохром)
    """
    attrs = {
        "greeting": curses.A_BOLD,
        "selected": curses.A_REVERSE | curses.A_BOLD,
        "unselected": curses.A_NORMAL,
        "tty": curses.A_NORMAL,
        "accent": curses.A_BOLD,
        "border": curses.A_NORMAL,
        "dim": curses.A_DIM,
        "countdown": curses.A_BOLD,
        "tag_x11": curses.A_BOLD,
        "tag_wayland": curses.A_BOLD,
        "tag_tty": curses.A_DIM,
        "last": curses.A_BOLD,
        "error": curses.A_BOLD | curses.A_REVERSE,
        "success": curses.A_BOLD,
        "bg": curses.A_NORMAL,
    }

    if not curses.has_colors():
        reset_tty_palette()
        if stdscr is not None:
            try:
                stdscr.bkgd(" ", curses.A_NORMAL)
            except curses.error:
                pass
        return attrs

    theme = get_theme(theme_id)

    try:
        curses.start_color()
        use_256 = getattr(curses, "COLORS", 8) >= 256

        # ─── Режим 1: 256-цветный терминал ─────────────────────────
        if use_256:
            reset_tty_palette()
            default_bg = -1
            try:
                curses.use_default_colors()
            except curses.error:
                default_bg = curses.COLOR_BLACK

            pal = theme.palette_256
            bg = theme.window_bg_256 if theme.window_bg_256 >= 0 else default_bg
            base_fg = theme.window_fg_256 if theme.window_fg_256 >= 0 else -1
            if bg != -1 and base_fg == -1:
                base_fg = pal["greeting"]

            curses.init_pair(1, pal["greeting"], bg)
            curses.init_pair(2, pal["selected_fg"], pal["selected_bg"])
            curses.init_pair(3, pal["unselected"], bg)
            curses.init_pair(4, pal["tty"], bg)
            curses.init_pair(5, pal["accent"], bg)
            curses.init_pair(6, pal["border"], bg)
            curses.init_pair(7, pal["dim"], bg)
            curses.init_pair(8, pal["countdown"], bg)
            curses.init_pair(9, pal["tag_x11"], bg)
            curses.init_pair(10, pal["tag_wayland"], bg)
            curses.init_pair(11, pal["tag_tty"], bg)
            curses.init_pair(12, pal["last"], bg)
            curses.init_pair(13, pal["error"], bg)
            curses.init_pair(14, pal["success"], bg)
            curses.init_pair(15, base_fg if bg != -1 else -1, bg)

            attrs["greeting"] = curses.color_pair(1) | curses.A_BOLD
            attrs["selected"] = curses.color_pair(2) | curses.A_BOLD
            attrs["unselected"] = curses.color_pair(3)
            attrs["tty"] = curses.color_pair(4)
            attrs["accent"] = curses.color_pair(5) | curses.A_BOLD
            attrs["border"] = curses.color_pair(6)
            attrs["dim"] = curses.color_pair(7)
            attrs["countdown"] = curses.color_pair(8) | curses.A_BOLD
            attrs["tag_x11"] = curses.color_pair(9)
            attrs["tag_wayland"] = curses.color_pair(10)
            attrs["tag_tty"] = curses.color_pair(11)
            attrs["last"] = curses.color_pair(12) | curses.A_BOLD
            attrs["error"] = curses.color_pair(13) | curses.A_BOLD
            attrs["success"] = curses.color_pair(14) | curses.A_BOLD
            attrs["bg"] = curses.color_pair(15) if bg != -1 else curses.A_NORMAL

            if stdscr is not None:
                try:
                    stdscr.bkgd(" ", attrs["bg"])
                    stdscr.touchwin()
                except curses.error:
                    pass
            return attrs

        # ─── Режим 2: Настоящий Linux TTY (16-цветная RGB-палитра) ─
        if _is_linux_vt():
            bg = curses.COLOR_BLACK
            curses.init_pair(1, curses.COLOR_WHITE, bg)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_BLUE)
            curses.init_pair(3, curses.COLOR_CYAN, bg)
            curses.init_pair(4, curses.COLOR_GREEN, bg)
            curses.init_pair(5, curses.COLOR_MAGENTA, bg)
            curses.init_pair(6, curses.COLOR_BLUE, bg)
            curses.init_pair(7, curses.COLOR_WHITE, bg)
            curses.init_pair(8, curses.COLOR_YELLOW, bg)
            curses.init_pair(9, curses.COLOR_GREEN, bg)
            curses.init_pair(10, curses.COLOR_MAGENTA, bg)
            curses.init_pair(11, curses.COLOR_YELLOW, bg)
            curses.init_pair(12, curses.COLOR_RED, bg)
            curses.init_pair(13, curses.COLOR_RED, bg)
            curses.init_pair(14, curses.COLOR_CYAN, bg)
            curses.init_pair(15, curses.COLOR_WHITE, bg)

            vt_attrs = {
                "greeting": curses.color_pair(1) | curses.A_BOLD,
                "selected": curses.color_pair(2) | curses.A_BOLD,
                "unselected": curses.color_pair(3),
                "tty": curses.color_pair(4) | curses.A_BOLD,
                "accent": curses.color_pair(5) | curses.A_BOLD,
                "border": curses.color_pair(6) | curses.A_BOLD,
                "dim": curses.color_pair(7),
                "countdown": curses.color_pair(8) | curses.A_BOLD,
                "tag_x11": curses.color_pair(9),
                "tag_wayland": curses.color_pair(10),
                "tag_tty": curses.color_pair(11),
                "last": curses.color_pair(12) | curses.A_BOLD,
                "error": curses.color_pair(13),
                "success": curses.color_pair(14) | curses.A_BOLD,
                "bg": curses.color_pair(15),
            }

            if stdscr is not None:
                try:
                    stdscr.bkgd(" ", vt_attrs["bg"])
                except curses.error:
                    pass

            # Сбрасываем буфер ncurses (включая возможный ESC ] R от initscr),
            # чтобы палитра ESC ] P всегда применялась ПОСЛЕ него.
            try:
                curses.doupdate()
            except curses.error:
                pass

            if _apply_linux_vt_palette(theme):
                # На truecolor fbcon изменение палитры требует перерисовки
                # ячеек, чтобы уже нарисованные пиксели обновили свой RGB.
                if stdscr is not None:
                    try:
                        stdscr.clearok(True)
                    except curses.error:
                        pass
                return vt_attrs

        # ─── Режим 3: Улучшенный 8-цветный fallback ────────────────
        reset_tty_palette()
        default_bg = -1
        try:
            curses.use_default_colors()
        except curses.error:
            default_bg = curses.COLOR_BLACK

        pal = theme.palette_8
        bg = theme.window_bg_8 if theme.window_bg_8 >= 0 else default_bg
        is_light_8 = theme.window_bg_8 == curses.COLOR_WHITE
        base_fg = theme.window_fg_8 if theme.window_fg_8 >= 0 else -1
        if bg != -1 and base_fg == -1:
            base_fg = pal["greeting"]

        curses.init_pair(1, pal["greeting"], bg)
        curses.init_pair(2, pal["selected_fg"], pal["selected_bg"])
        curses.init_pair(3, pal["unselected"], bg)
        curses.init_pair(4, pal["tty"], bg)
        curses.init_pair(5, pal["accent"], bg)
        curses.init_pair(6, pal["border"], bg)
        curses.init_pair(7, pal["dim"], bg)
        curses.init_pair(8, pal["countdown"], bg)
        curses.init_pair(9, pal["tag_x11"], bg)
        curses.init_pair(10, pal["tag_wayland"], bg)
        curses.init_pair(11, pal["tag_tty"], bg)
        curses.init_pair(12, pal["last"], bg)
        curses.init_pair(13, pal["error"], bg)
        curses.init_pair(14, pal["success"], bg)
        curses.init_pair(15, base_fg if bg != -1 else -1, bg)

        # В 8-цветном режиме (особенно TERM=linux) A_BOLD на COLOR_BLACK
        # превращает чёрный в серый, поэтому для чёрного текста bold не ставим.
        bold_on_dark = 0 if is_light_8 else curses.A_BOLD
        unsel_bold = (
            curses.A_BOLD
            if (not is_light_8 and pal["unselected"] in (curses.COLOR_BLUE, curses.COLOR_RED))
            else 0
        )
        tty_bold = (
            curses.A_BOLD
            if (not is_light_8 and pal["tty"] in (curses.COLOR_BLUE, curses.COLOR_RED))
            else 0
        )
        sel_bold = (
            curses.A_BOLD if pal["selected_fg"] != curses.COLOR_BLACK else 0
        )
        greet_bold = (
            curses.A_BOLD if pal["greeting"] != curses.COLOR_BLACK else 0
        )

        attrs["greeting"] = curses.color_pair(1) | greet_bold
        attrs["selected"] = curses.color_pair(2) | sel_bold
        attrs["unselected"] = curses.color_pair(3) | unsel_bold
        attrs["tty"] = curses.color_pair(4) | tty_bold
        attrs["accent"] = curses.color_pair(5) | bold_on_dark
        attrs["border"] = curses.color_pair(6)
        attrs["dim"] = curses.color_pair(7)
        attrs["countdown"] = curses.color_pair(8) | bold_on_dark
        attrs["tag_x11"] = curses.color_pair(9)
        attrs["tag_wayland"] = curses.color_pair(10)
        attrs["tag_tty"] = curses.color_pair(11)
        attrs["last"] = curses.color_pair(12) | bold_on_dark
        attrs["error"] = curses.color_pair(13) | bold_on_dark
        attrs["success"] = curses.color_pair(14) | bold_on_dark
        attrs["bg"] = curses.color_pair(15) if bg != -1 else curses.A_NORMAL

        if stdscr is not None:
            try:
                stdscr.bkgd(" ", attrs["bg"])
                stdscr.touchwin()
            except curses.error:
                pass

    except curses.error:
        pass

    return attrs
