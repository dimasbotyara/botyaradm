"""
menu.py — Интерактивные curses ASCII TUI-экраны PyDM.

Включает:
  - show_menu(...)            — выбор DE/WM с обратным отсчётом
  - show_user_menu(...)       — выбор системного пользователя (если включено)
  - show_password_prompt(...) — запрос и проверка системного пароля
"""

import curses
import locale
import math
import textwrap
import time
from collections.abc import Callable
from datetime import datetime

from config import (
    AUTO_SELECT_TIMEOUT,
    DEFAULT_THEME,
    SHOW_ASCII_LOGO,
    SHOW_SESSION_TYPE,
    SHOW_STATUS_BAR,
    TTY_OPTION_EXEC,
    USERNAME,
    WIZARD_OPTION_EXEC,
)
from detector import get_session_type
from greetings import get_greeting
from themes import init_theme_colors
from tui_utils import (
    ASCII_LOGO,
    decode_escape_sequence,
    safe_addstr,
    truncate,
)


def _shortcut_for_index(idx: int) -> str:
    """Возвращает клавишу быстрого выбора для индекса пункта."""
    if idx < 9:
        return str(idx + 1)
    if idx == 9:
        return "0"
    return " "


def _index_for_key(key: int, total: int) -> int | None:
    """Преобразует нажатую цифру (1-9, 0) в индекс пункта."""
    if ord("1") <= key <= ord("9"):
        idx = key - ord("1")
        return idx if idx < total else None
    if key == ord("0"):
        return 9 if total > 9 else None
    return None


def _find_default_index(
    sessions: list[tuple[str, str]],
    last_used_exec: str | None,
) -> tuple[int, tuple[str, str] | None]:
    """Находит индекс и элемент последней запущенной DE/WM."""
    if last_used_exec is None:
        return 0, None

    for idx, (name, exec_cmd) in enumerate(sessions):
        if exec_cmd == last_used_exec:
            return idx, (name, exec_cmd)

    return 0, None


def _session_badge(exec_cmd: str) -> tuple[str, str]:
    """Возвращает текстовый бейдж типа сессии и ключ стиля."""
    session_type = get_session_type(exec_cmd)
    if session_type == "wayland":
        return "[Wayland]", "tag_wayland"
    if session_type == "tty":
        return "[TTY]", "tag_tty"
    return "[X11]", "tag_x11"


def _draw_logo_or_bar(
    stdscr: "curses.window",
    attrs: dict[str, int],
    y: int,
    left: int,
    box_w: int,
    show_logo: bool,
) -> int:
    """Рисует ASCII-логотип или компактный заголовок. Возвращает новый y."""
    inner_w = box_w - 2
    if show_logo:
        border_top = "+" + "=" * inner_w + "+"
        safe_addstr(stdscr, y, left, border_top, attrs["border"])
        y += 1
        for logo_line in ASCII_LOGO:
            pad_total = max(0, inner_w - len(logo_line))
            pad_left = pad_total // 2
            pad_right = pad_total - pad_left
            row_text = (" " * pad_left) + logo_line + (" " * pad_right)
            safe_addstr(stdscr, y, left, "|", attrs["border"])
            safe_addstr(stdscr, y, left + 1, row_text[:inner_w], attrs["accent"])
            safe_addstr(stdscr, y, left + box_w - 1, "|", attrs["border"])
            y += 1
        safe_addstr(stdscr, y, left, border_top, attrs["border"])
        return y + 1

    title = "[ botyaradm // PyDM ]"
    side = max(1, (box_w - len(title) - 2) // 2)
    compact_bar = (
        ("=" * side)
        + " "
        + title
        + " "
        + ("=" * max(1, box_w - side - len(title) - 2))
    )
    safe_addstr(stdscr, y, left, compact_bar[:box_w], attrs["accent"])
    return y + 1


# ─── 1. Меню выбора пользователя ──────────────────────


def _user_menu_main(
    stdscr: "curses.window",
    users: list[str],
    theme_id: str,
    default_user: str | None,
) -> str | None:
    """Отображает экран выбора системного пользователя."""
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    if hasattr(curses, "set_escdelay"):
        try:
            curses.set_escdelay(25)
        except curses.error:
            pass

    stdscr.keypad(True)
    stdscr.timeout(-1)
    attrs = init_theme_colors(theme_id, stdscr)

    selected_idx = (
        users.index(default_user) if (default_user and default_user in users) else 0
    )
    scroll_offset = 0

    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        if max_y < 10 or max_x < 28:
            safe_addstr(stdscr, 0, 0, "PyDM: terminal too small", attrs["countdown"])
            stdscr.refresh()
            visible_items = 1
        else:
            box_w = min(74, max_x - 2)
            inner_w = box_w - 2
            left = max(1, (max_x - box_w) // 2)

            show_logo = SHOW_ASCII_LOGO and max_y >= 20 and box_w >= 60
            logo_h = (len(ASCII_LOGO) + 2) if show_logo else 1
            fixed_h = logo_h + 7
            visible_items = min(len(users), max(1, max_y - fixed_h))
            max_scroll = max(0, len(users) - visible_items)
            scroll_offset = max(0, min(scroll_offset, max_scroll))

            y = max(0, (max_y - (fixed_h + visible_items)) // 2)
            y = _draw_logo_or_bar(stdscr, attrs, y, left, box_w, show_logo)
            y += 1

            safe_addstr(stdscr, y, left, " > ", attrs["accent"])
            safe_addstr(
                stdscr,
                y,
                left + 3,
                truncate("Выбери пользователя для входа:", box_w - 3),
                attrs["greeting"],
            )
            y += 2

            top_scroll = f" ^ +{scroll_offset} " if scroll_offset > 0 else ""
            hdr = "+-[ Пользователи ]"
            fill_t = max(0, box_w - len(hdr) - len(top_scroll) - 1)
            safe_addstr(
                stdscr,
                y,
                left,
                (hdr + ("-" * fill_t) + top_scroll + "+")[:box_w],
                attrs["border"],
            )
            y += 1

            end_idx = min(len(users), scroll_offset + visible_items)
            for i in range(scroll_offset, end_idx):
                uname = users[i]
                is_sel = i == selected_idx
                shortcut = _shortcut_for_index(i)
                pointer = " >> " if is_sel else "    "
                key_label = f"[{shortcut}] " if shortcut != " " else "    "
                tag = "[USER]"
                left_part = f"{pointer}{key_label}{truncate(uname, inner_w - 18)}"
                gap = max(1, inner_w - len(left_part) - len(tag) - 1)

                safe_addstr(stdscr, y, left, "|", attrs["border"])
                if is_sel:
                    row = (left_part + (" " * gap) + tag + " ")[:inner_w]
                    safe_addstr(stdscr, y, left + 1, row.ljust(inner_w), attrs["selected"])
                else:
                    safe_addstr(stdscr, y, left + 1, left_part, attrs["unselected"])
                    safe_addstr(
                        stdscr,
                        y,
                        left + 1 + len(left_part),
                        " " * gap,
                        attrs["unselected"],
                    )
                    safe_addstr(
                        stdscr,
                        y,
                        left + 1 + len(left_part) + gap,
                        tag,
                        attrs["dim"],
                    )
                    safe_addstr(stdscr, y, left + box_w - 2, " ", attrs["unselected"])
                safe_addstr(stdscr, y, left + box_w - 1, "|", attrs["border"])
                y += 1

            hidden_below = len(users) - end_idx
            bot_scroll = f" v +{hidden_below} " if hidden_below > 0 else ""
            fill_b = max(0, inner_w - len(bot_scroll))
            safe_addstr(
                stdscr,
                y,
                left,
                ("+" + ("-" * fill_b) + bot_scroll + "+")[:box_w],
                attrs["border"],
            )
            y += 2

            if y < max_y - 1:
                safe_addstr(stdscr, y, left, "-" * box_w, attrs["dim"])
                y += 1
            if y < max_y:
                hints = " [Up/Down, j/k] Выбор  [1-9] Быстро  [Enter] Далее  [q/Esc] TTY"
                safe_addstr(stdscr, y, left, truncate(hints, box_w), attrs["dim"])

            stdscr.refresh()

        if selected_idx < scroll_offset:
            scroll_offset = selected_idx
        elif selected_idx >= scroll_offset + visible_items:
            scroll_offset = max(0, selected_idx - visible_items + 1)

        key = stdscr.getch()
        if key == curses.KEY_RESIZE:
            continue
        if key == 27:
            key = decode_escape_sequence(stdscr, -1)
            if key == curses.ERR:
                continue
        if key == 3:
            raise KeyboardInterrupt
        if key in (ord("q"), ord("Q"), 27):
            return None
        if key in (curses.KEY_ENTER, 10, 13):
            return users[selected_idx]
        digit_idx = _index_for_key(key, len(users))
        if digit_idx is not None:
            return users[digit_idx]

        if key in (curses.KEY_UP, ord("k"), ord("K")):
            selected_idx = (selected_idx - 1) % len(users)
        elif key in (curses.KEY_DOWN, ord("j"), ord("J")):
            selected_idx = (selected_idx + 1) % len(users)
        elif key in (curses.KEY_HOME, ord("g")):
            selected_idx = 0
        elif key in (curses.KEY_END, ord("G")):
            selected_idx = len(users) - 1

        if selected_idx < scroll_offset:
            scroll_offset = selected_idx
        elif selected_idx >= scroll_offset + visible_items:
            scroll_offset = max(0, selected_idx - visible_items + 1)


def show_user_menu(
    users: list[str],
    theme_id: str = DEFAULT_THEME,
    default_user: str | None = None,
) -> str | None:
    """Показывает меню выбора пользователя и возвращает выбранное имя или None."""
    if not users:
        return None

    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        pass

    return curses.wrapper(_user_menu_main, users, theme_id, default_user)


# ─── 2. Запрос пароля ─────────────────────────────────


def _password_prompt_main(
    stdscr: "curses.window",
    username: str,
    theme_id: str,
    verify_fn: Callable[[str, str], bool],
) -> bool:
    """Экран ввода системного пароля с маскировкой звёздочками."""
    try:
        curses.curs_set(1)
    except curses.error:
        pass
    if hasattr(curses, "set_escdelay"):
        try:
            curses.set_escdelay(25)
        except curses.error:
            pass

    stdscr.keypad(True)
    stdscr.timeout(-1)
    attrs = init_theme_colors(theme_id, stdscr)

    password = ""
    error_msg = ""
    checking = False

    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()

        if max_y < 9 or max_x < 28:
            safe_addstr(stdscr, 0, 0, "Password:", attrs["greeting"])
            stdscr.refresh()
        else:
            box_w = min(64, max_x - 2)
            inner_w = box_w - 2
            left = max(1, (max_x - box_w) // 2)

            show_logo = SHOW_ASCII_LOGO and max_y >= 20 and box_w >= 60
            logo_h = (len(ASCII_LOGO) + 2) if show_logo else 1
            total_h = logo_h + 9
            y = max(0, (max_y - total_h) // 2)

            y = _draw_logo_or_bar(stdscr, attrs, y, left, box_w, show_logo)
            y += 1

            safe_addstr(stdscr, y, left, " > ", attrs["accent"])
            safe_addstr(
                stdscr,
                y,
                left + 3,
                truncate(f"Авторизация пользователя: {username}", box_w - 3),
                attrs["greeting"],
            )
            y += 2

            hdr = "+-[ Введи пароль ]"
            fill_t = max(0, box_w - len(hdr) - 1)
            safe_addstr(
                stdscr,
                y,
                left,
                (hdr + ("-" * fill_t) + "+")[:box_w],
                attrs["border"],
            )
            y += 1

            prompt_prefix = "  Password: "
            max_stars = max(4, inner_w - len(prompt_prefix) - 2)
            masked = "*" * min(len(password), max_stars)
            if len(password) > max_stars:
                masked = "..." + masked[3:]

            safe_addstr(stdscr, y, left, "|", attrs["border"])
            safe_addstr(stdscr, y, left + 1, prompt_prefix, attrs["accent"])
            safe_addstr(
                stdscr,
                y,
                left + 1 + len(prompt_prefix),
                masked.ljust(inner_w - len(prompt_prefix)),
                attrs["greeting"],
            )
            safe_addstr(stdscr, y, left + box_w - 1, "|", attrs["border"])
            cursor_y = y
            cursor_x = min(left + box_w - 2, left + 1 + len(prompt_prefix) + len(masked))
            y += 1

            safe_addstr(
                stdscr,
                y,
                left,
                "+" + ("-" * inner_w) + "+",
                attrs["border"],
            )
            y += 1

            if checking:
                safe_addstr(
                    stdscr,
                    y,
                    left,
                    truncate(" [*] Проверка пароля...", box_w),
                    attrs["countdown"],
                )
            elif error_msg:
                safe_addstr(
                    stdscr,
                    y,
                    left,
                    truncate(f" [!] {error_msg}", box_w),
                    attrs["error"],
                )
            y += 2

            if y < max_y - 1:
                safe_addstr(stdscr, y, left, "-" * box_w, attrs["dim"])
                y += 1
            if y < max_y:
                safe_addstr(
                    stdscr,
                    y,
                    left,
                    truncate(" [Enter] Войти  [Backspace] Стереть  [Esc] Назад в TTY", box_w),
                    attrs["dim"],
                )

            try:
                stdscr.move(cursor_y, cursor_x)
            except curses.error:
                pass
            stdscr.refresh()

        if checking:
            ok = verify_fn(username, password)
            checking = False
            if ok:
                return True
            password = ""
            error_msg = "Неверный пароль. Попробуй ещё раз."
            continue

        key = stdscr.getch()
        if key == curses.KEY_RESIZE:
            continue
        if key == 27:
            key = decode_escape_sequence(stdscr, -1)
            if key == curses.ERR:
                continue
        if key == 3:
            raise KeyboardInterrupt
        if key == 27:
            return False
        if key in (curses.KEY_ENTER, 10, 13):
            checking = True
            error_msg = ""
            continue
        if key in (curses.KEY_BACKSPACE, 127, 8):
            if password:
                password = password[:-1]
            error_msg = ""
            continue
        # Ctrl+U — очистить поле ввода
        if key == 21:
            password = ""
            error_msg = ""
            continue
        if 32 <= key <= 126 or key >= 160:
            try:
                ch = chr(key)
            except ValueError:
                continue
            password += ch
            error_msg = ""


def show_password_prompt(
    username: str,
    theme_id: str,
    verify_fn: Callable[[str, str], bool],
) -> bool:
    """Показывает окно ввода пароля. Возвращает True при успешной проверке."""
    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        pass

    return curses.wrapper(_password_prompt_main, username, theme_id, verify_fn)


# ─── 3. Главное меню выбора DE/WM ─────────────────────


def _draw_ui(
    stdscr: "curses.window",
    attrs: dict[str, int],
    greeting: str,
    username: str,
    sessions: list[tuple[str, str]],
    selected_idx: int,
    scroll_offset: int,
    last_used_exec: str | None,
    countdown_active: bool,
    remaining_sec: float,
    countdown_cancelled_msg: bool,
) -> int:
    """
    Отрисовывает весь TUI-интерфейс главного меню.
    Возвращает количество видимых строк меню.
    """
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()

    if max_y < 8 or max_x < 24:
        safe_addstr(stdscr, 0, 0, "PyDM: terminal too small", attrs["countdown"])
        stdscr.refresh()
        return 1

    box_w = min(74, max_x - 2)
    inner_w = box_w - 2
    left = max(1, (max_x - box_w) // 2)

    greeting_prefix = "> "
    greeting_lines = textwrap.wrap(
        greeting,
        width=max(16, box_w - len(greeting_prefix) - 2),
    ) or [greeting]
    greeting_lines = greeting_lines[:2]

    show_logo = SHOW_ASCII_LOGO and max_y >= 21 and box_w >= 60
    show_status = SHOW_STATUS_BAR and max_y >= 13

    logo_h = (len(ASCII_LOGO) + 2) if show_logo else 1
    status_h = 1 if show_status else 0
    greeting_h = len(greeting_lines)
    countdown_h = 2 if (countdown_active or countdown_cancelled_msg) else 0
    footer_h = 2 if max_y >= 16 else 1
    menu_borders_h = 2
    spacers_h = 2

    fixed_h = (
        logo_h
        + status_h
        + greeting_h
        + menu_borders_h
        + countdown_h
        + footer_h
        + spacers_h
    )
    avail_for_items = max(1, max_y - fixed_h)
    visible_items = min(len(sessions), avail_for_items)

    max_scroll = max(0, len(sessions) - visible_items)
    scroll_offset = max(0, min(scroll_offset, max_scroll))

    total_h = fixed_h + visible_items
    y = max(0, (max_y - total_h) // 2)

    # ─── 1. Шапка / ASCII-логотип ───────────────────────
    y = _draw_logo_or_bar(stdscr, attrs, y, left, box_w, show_logo)

    # ─── 2. Строка статуса ─────────────────────────────
    if show_status:
        now_str = datetime.now().strftime("%H:%M:%S")
        status_text = (
            f" [*] {now_str}  |  User: {username}"
            f"  |  Sessions: {len(sessions)}"
        )
        safe_addstr(stdscr, y, left, truncate(status_text, box_w), attrs["dim"])
        y += 1

    # ─── 3. Приветствие ────────────────────────────────
    for idx, line in enumerate(greeting_lines):
        prefix = greeting_prefix if idx == 0 else "  "
        safe_addstr(stdscr, y, left, prefix, attrs["accent"])
        safe_addstr(
            stdscr,
            y,
            left + len(prefix),
            truncate(line, box_w - len(prefix)),
            attrs["greeting"],
        )
        y += 1
    y += 1

    # ─── 4. Блок меню выбора DE/WM ─────────────────────
    top_scroll = f" ^ +{scroll_offset} " if scroll_offset > 0 else ""
    menu_title = "+-[ Выбери DE/WM ]"
    fill_top = max(0, box_w - len(menu_title) - len(top_scroll) - 1)
    menu_top = (menu_title + ("-" * fill_top) + top_scroll + "+")[:box_w]
    safe_addstr(stdscr, y, left, menu_top, attrs["border"])
    y += 1

    end_idx = min(len(sessions), scroll_offset + visible_items)
    for i in range(scroll_offset, end_idx):
        name, exec_cmd = sessions[i]
        is_selected = i == selected_idx
        is_last = last_used_exec is not None and exec_cmd == last_used_exec
        is_tty = exec_cmd == TTY_OPTION_EXEC

        shortcut = _shortcut_for_index(i)
        pointer = " >> " if is_selected else "    "
        key_label = f"[{shortcut}] " if shortcut != " " else "    "

        badge_text, badge_style = (
            _session_badge(exec_cmd) if SHOW_SESSION_TYPE else ("", "dim")
        )
        last_marker = " *last" if is_last else ""
        right_meta = f"{badge_text}{last_marker}".strip()

        reserved_right = (len(right_meta) + 2) if right_meta else 1
        name_avail = max(6, inner_w - len(pointer) - len(key_label) - reserved_right)
        display_name = truncate(name, name_avail)

        left_part = f"{pointer}{key_label}{display_name}"
        gap = max(1, inner_w - len(left_part) - len(right_meta) - 1)

        safe_addstr(stdscr, y, left, "|", attrs["border"])

        if is_selected:
            full_row = (left_part + (" " * gap) + right_meta + " ")[:inner_w]
            if len(full_row) < inner_w:
                full_row += " " * (inner_w - len(full_row))
            safe_addstr(stdscr, y, left + 1, full_row, attrs["selected"])
        else:
            row_attr = attrs["tty"] if is_tty else attrs["unselected"]
            safe_addstr(stdscr, y, left + 1, left_part, row_attr)
            safe_addstr(
                stdscr,
                y,
                left + 1 + len(left_part),
                " " * gap,
                attrs["unselected"],
            )
            if badge_text:
                badge_x = left + 1 + len(left_part) + gap
                safe_addstr(stdscr, y, badge_x, badge_text, attrs[badge_style])
                if last_marker:
                    safe_addstr(
                        stdscr,
                        y,
                        badge_x + len(badge_text),
                        last_marker,
                        attrs["last"],
                    )
            elif last_marker:
                safe_addstr(
                    stdscr,
                    y,
                    left + 1 + len(left_part) + gap,
                    last_marker.lstrip(),
                    attrs["last"],
                )
            safe_addstr(stdscr, y, left + box_w - 2, " ", attrs["unselected"])

        safe_addstr(stdscr, y, left + box_w - 1, "|", attrs["border"])
        y += 1

    hidden_below = len(sessions) - end_idx
    bot_scroll = f" v +{hidden_below} " if hidden_below > 0 else ""
    fill_bot = max(0, inner_w - len(bot_scroll))
    menu_bottom = ("+" + ("-" * fill_bot) + bot_scroll + "+")[:box_w]
    safe_addstr(stdscr, y, left, menu_bottom, attrs["border"])
    y += 1

    # ─── 5. Блок автозапуска / статуса таймера ─────────
    if countdown_active:
        secs_left = max(1, math.ceil(remaining_sec))
        total_t = max(1, AUTO_SELECT_TIMEOUT)
        bar_w = 10
        filled = max(0, min(bar_w, round((remaining_sec / total_t) * bar_w)))
        bar = "[" + ("#" * filled) + ("." * (bar_w - filled)) + "]"

        default_name = sessions[selected_idx][0]
        for s_name, s_cmd in sessions:
            if s_cmd == last_used_exec:
                default_name = s_name
                break

        msg = (
            f" [!] Автозапуск \"{truncate(default_name, 26)}\""
            f" через {secs_left} сек... {bar}"
        )
        safe_addstr(stdscr, y, left, truncate(msg, box_w), attrs["countdown"])
        y += 1
        safe_addstr(
            stdscr,
            y,
            left,
            truncate("     Нажми любую клавишу для отмены", box_w),
            attrs["dim"],
        )
        y += 1
    elif countdown_cancelled_msg:
        safe_addstr(
            stdscr,
            y,
            left,
            truncate(" [i] Автозапуск отменён. Выбери сессию вручную.", box_w),
            attrs["dim"],
        )
        y += 2

    y += 1

    # ─── 6. Подвал с подсказками клавиш ────────────────
    if footer_h >= 2 and y < max_y - 1:
        safe_addstr(stdscr, y, left, "-" * box_w, attrs["dim"])
        y += 1
    if y < max_y:
        hints = " [Up/Down, j/k] Выбор  [1-9] Старт  [Enter] OK  [w] Настройки  [q] TTY"
        if box_w < 70:
            hints = " [Up/Down] Выбор  [1-9] Старт  [w] Настройки  [q] TTY"
        safe_addstr(stdscr, y, left, truncate(hints, box_w), attrs["dim"])

    stdscr.refresh()
    return visible_items


def _curses_main(
    stdscr: "curses.window",
    sessions: list[tuple[str, str]],
    last_used_exec: str | None,
    greeting: str,
    username: str,
    theme_id: str,
) -> tuple[str, str] | None:
    """Основной цикл интерактивного curses-меню."""
    try:
        curses.curs_set(0)
    except curses.error:
        pass

    if hasattr(curses, "set_escdelay"):
        try:
            curses.set_escdelay(25)
        except curses.error:
            pass

    stdscr.keypad(True)
    attrs = init_theme_colors(theme_id, stdscr)

    selected_idx, default_result = _find_default_index(sessions, last_used_exec)
    scroll_offset = 0

    countdown_active = default_result is not None and AUTO_SELECT_TIMEOUT > 0
    countdown_cancelled_msg = False
    deadline = time.monotonic() + AUTO_SELECT_TIMEOUT if countdown_active else 0.0

    timeout_ms = 100 if countdown_active else -1
    stdscr.timeout(timeout_ms)

    while True:
        remaining = max(0.0, deadline - time.monotonic()) if countdown_active else 0.0
        if countdown_active and remaining <= 0.0:
            return default_result

        visible_items = _draw_ui(
            stdscr=stdscr,
            attrs=attrs,
            greeting=greeting,
            username=username,
            sessions=sessions,
            selected_idx=selected_idx,
            scroll_offset=scroll_offset,
            last_used_exec=last_used_exec,
            countdown_active=countdown_active,
            remaining_sec=remaining,
            countdown_cancelled_msg=countdown_cancelled_msg,
        )

        if selected_idx < scroll_offset:
            scroll_offset = selected_idx
        elif selected_idx >= scroll_offset + visible_items:
            scroll_offset = max(0, selected_idx - visible_items + 1)

        key = stdscr.getch()

        if key == curses.ERR:
            continue

        if key == curses.KEY_RESIZE:
            continue

        if key == 27:
            key = decode_escape_sequence(stdscr, timeout_ms)
            if key == curses.ERR:
                continue

        # Любая реальная клавиша отменяет таймер автозапуска
        if countdown_active:
            countdown_active = False
            countdown_cancelled_msg = True
            timeout_ms = -1
            stdscr.timeout(timeout_ms)

        if key == 3:
            raise KeyboardInterrupt

        if key in (ord("q"), ord("Q"), 27):
            return None

        if key in (ord("w"), ord("W")):
            return ("Настройки", WIZARD_OPTION_EXEC)

        if key in (curses.KEY_ENTER, 10, 13):
            return sessions[selected_idx]

        digit_idx = _index_for_key(key, len(sessions))
        if digit_idx is not None:
            return sessions[digit_idx]

        if key in (curses.KEY_UP, ord("k"), ord("K")):
            selected_idx = (selected_idx - 1) % len(sessions)
        elif key in (curses.KEY_DOWN, ord("j"), ord("J")):
            selected_idx = (selected_idx + 1) % len(sessions)
        elif key in (curses.KEY_HOME, ord("g")):
            selected_idx = 0
        elif key in (curses.KEY_END, ord("G")):
            selected_idx = len(sessions) - 1
        elif key == curses.KEY_PPAGE:
            selected_idx = max(0, selected_idx - visible_items)
        elif key == curses.KEY_NPAGE:
            selected_idx = min(len(sessions) - 1, selected_idx + visible_items)

        if selected_idx < scroll_offset:
            scroll_offset = selected_idx
        elif selected_idx >= scroll_offset + visible_items:
            scroll_offset = max(0, selected_idx - visible_items + 1)


def show_menu(
    sessions: list[tuple[str, str]],
    last_used_exec: str | None = None,
    username: str | None = None,
    theme_id: str = DEFAULT_THEME,
) -> tuple[str, str] | None:
    """
    Показывает интерактивное curses-меню и возвращает выбор пользователя.
    """
    if not sessions:
        return None

    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        pass

    active_user = username or USERNAME
    greeting = get_greeting(active_user)

    return curses.wrapper(
        _curses_main,
        sessions,
        last_used_exec,
        greeting,
        active_user,
        theme_id,
    )
