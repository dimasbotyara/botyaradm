"""
tui_utils.py — Общие утилиты для TUI и управления терминалом.
"""

import curses
import sys

ASCII_LOGO = [
    r"  ____        _                          ____  __  __ ",
    r" | __ )  ___ | |_ _   _  __ _ _ __ __ _ |  _ \|  \/  |",
    r" |  _ \ / _ \| __| | | |/ _` | '__/ _` || | | | |\/| |",
    r" | |_) | (_) | |_| |_| | (_| | | | (_| || |_| | |  | |",
    r" |____/ \___/ \__|\__, |\__,_|_|  \__,_||____/|_|  |_|",
    r"                  |___/    [ botyaradm // TTY Launcher ]",
]


def clear_terminal() -> None:
    """
    Полностью очищает экран терминала и скроллбэк (где поддерживается).
    Безопасно ничего не делает, если stdout не подключён к TTY.
    """
    try:
        if sys.stdout.isatty():
            sys.stdout.write("\033[H\033[2J\033[3J")
            sys.stdout.flush()
    except OSError:
        pass


def safe_addstr(
    win: "curses.window",
    y: int,
    x: int,
    text: str,
    attr: int = 0,
) -> None:
    """
    Безопасно выводит строку в окно curses, не падая на границах экрана.
    """
    max_y, max_x = win.getmaxyx()
    if y < 0 or y >= max_y or x >= max_x or not text:
        return

    if x < 0:
        text = text[-x:]
        x = 0

    avail = max_x - x
    if y == max_y - 1:
        avail -= 1

    if avail <= 0:
        return

    try:
        win.addstr(y, x, text[:avail], attr)
    except curses.error:
        pass


def truncate(text: str, width: int) -> str:
    """Обрезает строку до width символов с ASCII-многоточием."""
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    return text[: width - 3] + "..."


def decode_escape_sequence(
    stdscr: "curses.window",
    timeout_ms: int,
) -> int:
    """
    Различает реальное нажатие Esc (возвращает 27) и escape-последовательности
    терминала (CSI ^[[A / ^[[B, SS3 ^[OA / ^[OB и др.).
    """
    stdscr.nodelay(True)
    try:
        ch1 = stdscr.getch()
        if ch1 == curses.ERR:
            return 27

        if ch1 in (ord("["), ord("O")):
            ch2 = stdscr.getch()
            if ch2 == ord("A"):
                return curses.KEY_UP
            if ch2 == ord("B"):
                return curses.KEY_DOWN
            if ch2 == ord("H"):
                return curses.KEY_HOME
            if ch2 == ord("F"):
                return curses.KEY_END
            if ch2 in (ord("5"), ord("6")):
                ch3 = stdscr.getch()
                if ch3 == ord("~"):
                    return curses.KEY_PPAGE if ch2 == ord("5") else curses.KEY_NPAGE
            while stdscr.getch() != curses.ERR:
                pass
            return curses.ERR

        while stdscr.getch() != curses.ERR:
            pass
        return curses.ERR
    finally:
        stdscr.nodelay(False)
        stdscr.timeout(timeout_ms)
