"""
setup_wizard.py — Интерактивный мастер первоначальной настройки botyaradm на curses.

Шаги:
  1. (Если > 1 пользователя) Всегда ли спрашивать пользователя при запуске
     (и выбор пользователя по умолчанию, если «Нет»; при 1 пользователе — автовыбор)
  2. Запрашивать ли системный пароль при входе
  3. Выбор цветовой темы оформления (25 тем с мгновенным живым предпросмотром)
"""

import curses
import locale
from typing import Any

from settings import default_settings, save_settings
from themes import THEME_ORDER, THEMES, get_theme, init_theme_colors, reset_tty_palette
from tui_utils import decode_escape_sequence, safe_addstr, truncate


def _draw_wizard_box(
    stdscr: "curses.window",
    attrs: dict[str, int],
    step_label: str,
    title: str,
    subtitle: str | None,
    items: list[tuple[str, str]],
    selected_idx: int,
    scroll_offset: int,
    preview_theme_id: str | None = None,
    can_go_back: bool = False,
) -> int:
    """Отрисовывает экран мастера настройки. Возвращает число видимых строк."""
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()

    if max_y < 10 or max_x < 28:
        safe_addstr(stdscr, 0, 0, "botyaradm Setup: terminal too small", attrs["countdown"])
        stdscr.refresh()
        return 1

    box_w = min(74, max_x - 2)
    inner_w = box_w - 2
    left = max(1, (max_x - box_w) // 2)

    is_theme_step = preview_theme_id is not None
    preview_h = 6 if (is_theme_step and max_y >= 22) else 0
    sub_h = 1 if subtitle else 0
    header_h = 4  # шапка + заголовок шага
    footer_h = 2
    menu_chrome_h = 2
    spacers_h = 2

    fixed_h = header_h + sub_h + menu_chrome_h + preview_h + footer_h + spacers_h
    avail_items = max(1, max_y - fixed_h)
    visible_items = min(len(items), avail_items)

    if selected_idx < scroll_offset:
        scroll_offset = selected_idx
    elif selected_idx >= scroll_offset + visible_items:
        scroll_offset = max(0, selected_idx - visible_items + 1)
    max_scroll = max(0, len(items) - visible_items)
    scroll_offset = max(0, min(scroll_offset, max_scroll))

    total_h = fixed_h + visible_items
    y = max(0, (max_y - total_h) // 2)

    # ─── 1. Шапка мастера ─────────────────────────────
    top_border = "+" + "=" * inner_w + "+"
    safe_addstr(stdscr, y, left, top_border, attrs["border"])
    y += 1

    banner_left = " [ botyaradm Setup Wizard ]"
    banner_right = f"[{step_label}] "
    gap_banner = max(1, inner_w - len(banner_left) - len(banner_right))
    banner_mid = (banner_left + (" " * gap_banner) + banner_right)[:inner_w]
    safe_addstr(stdscr, y, left, "|", attrs["border"])
    safe_addstr(stdscr, y, left + 1, banner_mid, attrs["accent"])
    safe_addstr(stdscr, y, left + box_w - 1, "|", attrs["border"])
    y += 1

    safe_addstr(stdscr, y, left, top_border, attrs["border"])
    y += 1

    # ─── 2. Вопрос / подзаголовок ──────────────────────
    safe_addstr(stdscr, y, left, " > ", attrs["accent"])
    safe_addstr(
        stdscr,
        y,
        left + 3,
        truncate(title, box_w - 3),
        attrs["greeting"],
    )
    y += 1

    if subtitle:
        safe_addstr(
            stdscr,
            y,
            left,
            truncate(f"   {subtitle}", box_w),
            attrs["dim"],
        )
        y += 1

    y += 1

    # ─── 3. Список вариантов ───────────────────────────
    top_scroll = f" ^ +{scroll_offset} " if scroll_offset > 0 else ""
    list_title = (
        f"+-[ Тема {selected_idx + 1}/{len(items)} ]"
        if is_theme_step
        else "+-[ Варианты ]"
    )
    fill_top = max(0, box_w - len(list_title) - len(top_scroll) - 1)
    safe_addstr(
        stdscr,
        y,
        left,
        (list_title + ("-" * fill_top) + top_scroll + "+")[:box_w],
        attrs["border"],
    )
    y += 1

    end_idx = min(len(items), scroll_offset + visible_items)
    for i in range(scroll_offset, end_idx):
        label, desc = items[i]
        is_sel = i == selected_idx
        pointer = " >> " if is_sel else "    "
        key_tag = f"[{i + 1}] " if (not is_theme_step and i < 9) else (
            "[0] " if (not is_theme_step and i == 9) else ""
        )

        right_desc = truncate(desc, max(10, inner_w // 2 - 2)) if desc else ""
        avail_label = max(
            8,
            inner_w - len(pointer) - len(key_tag) - (len(right_desc) + 2 if right_desc else 1),
        )
        left_part = f"{pointer}{key_tag}{truncate(label, avail_label)}"
        gap = max(1, inner_w - len(left_part) - len(right_desc) - 1)

        safe_addstr(stdscr, y, left, "|", attrs["border"])
        if is_sel:
            row = (left_part + (" " * gap) + right_desc + " ")[:inner_w]
            if len(row) < inner_w:
                row += " " * (inner_w - len(row))
            safe_addstr(stdscr, y, left + 1, row, attrs["selected"])
        else:
            safe_addstr(stdscr, y, left + 1, left_part, attrs["unselected"])
            safe_addstr(
                stdscr,
                y,
                left + 1 + len(left_part),
                " " * gap,
                attrs["unselected"],
            )
            if right_desc:
                safe_addstr(
                    stdscr,
                    y,
                    left + 1 + len(left_part) + gap,
                    right_desc,
                    attrs["dim"],
                )
            safe_addstr(stdscr, y, left + box_w - 2, " ", attrs["unselected"])
        safe_addstr(stdscr, y, left + box_w - 1, "|", attrs["border"])
        y += 1

    hidden_below = len(items) - end_idx
    bot_scroll = f" v +{hidden_below} " if hidden_below > 0 else ""
    fill_bot = max(0, inner_w - len(bot_scroll))
    safe_addstr(
        stdscr,
        y,
        left,
        ("+" + ("-" * fill_bot) + bot_scroll + "+")[:box_w],
        attrs["border"],
    )
    y += 1

    # ─── 4. Живой предпросмотр темы ────────────────────
    if preview_h > 0 and preview_theme_id is not None:
        theme = get_theme(preview_theme_id)
        y += 1
        prev_hdr = f"+-[ Предпросмотр: {theme.name} ]"
        fill_p = max(0, box_w - len(prev_hdr) - 1)
        safe_addstr(
            stdscr,
            y,
            left,
            (prev_hdr + ("-" * fill_p) + "+")[:box_w],
            attrs["border"],
        )
        y += 1

        # Строка 1 превью: выбранный пункт
        p_left1 = " >> [1] Hyprland (Wayland)"
        p_right1 = "[Wayland] *last "
        p_gap1 = max(1, inner_w - len(p_left1) - len(p_right1))
        row1 = (p_left1 + (" " * p_gap1) + p_right1)[:inner_w]
        if len(row1) < inner_w:
            row1 += " " * (inner_w - len(row1))
        safe_addstr(stdscr, y, left, "|", attrs["border"])
        safe_addstr(stdscr, y, left + 1, row1, attrs["selected"])
        safe_addstr(stdscr, y, left + box_w - 1, "|", attrs["border"])
        y += 1

        # Строка 2 превью: обычный пункт + бейдж
        p_left2 = "    [2] XFCE"
        p_right2 = "[X11] "
        p_gap2 = max(1, inner_w - len(p_left2) - len(p_right2))
        safe_addstr(stdscr, y, left, "|", attrs["border"])
        safe_addstr(stdscr, y, left + 1, p_left2, attrs["unselected"])
        safe_addstr(
            stdscr,
            y,
            left + 1 + len(p_left2),
            " " * p_gap2,
            attrs["unselected"],
        )
        safe_addstr(
            stdscr,
            y,
            left + 1 + len(p_left2) + p_gap2,
            "[X11]",
            attrs["tag_x11"],
        )
        safe_addstr(stdscr, y, left + box_w - 2, " ", attrs["unselected"])
        safe_addstr(stdscr, y, left + box_w - 1, "|", attrs["border"])
        y += 1

        # Строка 3 превью: таймер
        p_timer = " [!] Автозапуск через 4 сек... [########..]"
        safe_addstr(stdscr, y, left, "|", attrs["border"])
        safe_addstr(
            stdscr,
            y,
            left + 1,
            truncate(p_timer, inner_w).ljust(inner_w),
            attrs["countdown"],
        )
        safe_addstr(stdscr, y, left + box_w - 1, "|", attrs["border"])
        y += 1

        safe_addstr(stdscr, y, left, "+" + ("-" * inner_w) + "+", attrs["border"])
        y += 1
    else:
        y += 1

    # ─── 5. Подвал с подсказками ───────────────────────
    if y < max_y - 1:
        safe_addstr(stdscr, y, left, "-" * box_w, attrs["dim"])
        y += 1
    if y < max_y:
        back_hint = "  [b/Backspace] Назад" if can_go_back else ""
        quick_hint = "  [1-9] Быстро" if not is_theme_step else "  [PgUp/PgDn] Страница"
        hints = f" [Up/Down, j/k] Выбор{quick_hint}  [Enter] Далее{back_hint}  [q/Esc] Выход"
        safe_addstr(stdscr, y, left, truncate(hints, box_w), attrs["dim"])

    stdscr.refresh()
    return visible_items


def _prompt_step(
    stdscr: "curses.window",
    theme_id: str,
    step_label: str,
    title: str,
    subtitle: str | None,
    items: list[tuple[str, str]],
    initial_idx: int = 0,
    is_theme_step: bool = False,
    can_go_back: bool = False,
) -> tuple[str, int]:
    """
    Универсальный экран выбора в мастере.
    Возвращает ("ok", idx), ("back", 0) или ("cancel", 0).
    """
    selected_idx = max(0, min(initial_idx, len(items) - 1))
    scroll_offset = 0

    active_theme = THEMES[THEME_ORDER[selected_idx]].id if is_theme_step else theme_id
    attrs = init_theme_colors(active_theme, stdscr)
    applied_theme = active_theme
    stdscr.timeout(-1)

    while True:
        preview_id = THEME_ORDER[selected_idx] if is_theme_step else None
        if is_theme_step and preview_id != applied_theme:
            attrs = init_theme_colors(preview_id, stdscr)
            applied_theme = preview_id

        visible_items = _draw_wizard_box(
            stdscr=stdscr,
            attrs=attrs,
            step_label=step_label,
            title=title,
            subtitle=subtitle,
            items=items,
            selected_idx=selected_idx,
            scroll_offset=scroll_offset,
            preview_theme_id=preview_id,
            can_go_back=can_go_back,
        )

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
            return ("cancel", 0)

        if can_go_back and key in (
            curses.KEY_BACKSPACE,
            127,
            8,
            ord("b"),
            ord("B"),
        ):
            return ("back", 0)

        if key in (curses.KEY_ENTER, 10, 13):
            return ("ok", selected_idx)

        if not is_theme_step:
            if ord("1") <= key <= ord("9"):
                idx = key - ord("1")
                if idx < len(items):
                    return ("ok", idx)
            elif key == ord("0") and len(items) >= 10:
                return ("ok", 9)

        if key in (curses.KEY_UP, ord("k"), ord("K")):
            selected_idx = (selected_idx - 1) % len(items)
        elif key in (curses.KEY_DOWN, ord("j"), ord("J")):
            selected_idx = (selected_idx + 1) % len(items)
        elif key in (curses.KEY_HOME, ord("g")):
            selected_idx = 0
        elif key in (curses.KEY_END, ord("G")):
            selected_idx = len(items) - 1
        elif key == curses.KEY_PPAGE:
            selected_idx = max(0, selected_idx - visible_items)
        elif key == curses.KEY_NPAGE:
            selected_idx = min(len(items) - 1, selected_idx + visible_items)

        if selected_idx < scroll_offset:
            scroll_offset = selected_idx
        elif selected_idx >= scroll_offset + visible_items:
            scroll_offset = max(0, selected_idx - visible_items + 1)


def _wizard_main(
    stdscr: "curses.window",
    users: list[str],
    initial_settings: dict[str, Any],
) -> dict[str, Any] | None:
    """Логика переходов между шагами мастера настройки."""
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

    multi_user = len(users) > 1
    result = dict(initial_settings)

    if not multi_user:
        result["ask_user_always"] = False
        result["default_user"] = users[0]

    # Список этапов зависит от числа пользователей:
    # >1 пользователь: ["ask_user_mode", ("default_user"), "password", "theme"]
    #  1 пользователь: ["password", "theme"]
    stage = "ask_user_mode" if multi_user else "password"
    total_main_steps = 3 if multi_user else 2

    while True:
        current_theme = str(result.get("theme", "botyaradm_classic"))

        if stage == "ask_user_mode":
            init_idx = 0 if result.get("ask_user_always", False) else 1
            action, idx = _prompt_step(
                stdscr=stdscr,
                theme_id=current_theme,
                step_label=f"Шаг 1/{total_main_steps}",
                title="Всегда спрашивать, какого пользователя использовать?",
                subtitle=f"Обнаружено пользователей в системе: {len(users)} ({', '.join(users[:4])})",
                items=[
                    ("Да, спрашивать при каждом запуске", "Меню выбора пользователя"),
                    ("Нет, использовать одного по умолчанию", "Быстрый вход без выбора"),
                ],
                initial_idx=init_idx,
                can_go_back=False,
            )
            if action == "cancel":
                return None
            if idx == 0:
                result["ask_user_always"] = True
                if result.get("default_user") not in users:
                    result["default_user"] = users[0]
                stage = "password"
            else:
                result["ask_user_always"] = False
                stage = "default_user"

        elif stage == "default_user":
            cur_def = result.get("default_user", users[0])
            init_idx = users.index(cur_def) if cur_def in users else 0
            action, idx = _prompt_step(
                stdscr=stdscr,
                theme_id=current_theme,
                step_label=f"Шаг 1/{total_main_steps}",
                title="Какого пользователя использовать по умолчанию?",
                subtitle="Этот пользователь будет выбираться автоматически",
                items=[(u, "Системный пользователь") for u in users],
                initial_idx=init_idx,
                can_go_back=True,
            )
            if action == "cancel":
                return None
            if action == "back":
                stage = "ask_user_mode"
                continue
            result["default_user"] = users[idx]
            stage = "password"

        elif stage == "password":
            step_num = 2 if multi_user else 1
            sub = (
                f"Найден 1 пользователь: {users[0]} (выбран автоматически)"
                if not multi_user
                else "Проверка системного пароля через PAM / su при каждом входе"
            )
            init_idx = 1 if result.get("require_password", False) else 0
            action, idx = _prompt_step(
                stdscr=stdscr,
                theme_id=current_theme,
                step_label=f"Шаг {step_num}/{total_main_steps}",
                title="Запрашивать пароль при входе?",
                subtitle=sub,
                items=[
                    ("Нет, запускать без пароля", "Быстрый старт сессии"),
                    ("Да, запрашивать системный пароль", "Дополнительная защита TTY"),
                ],
                initial_idx=init_idx,
                can_go_back=multi_user,
            )
            if action == "cancel":
                return None
            if action == "back":
                stage = "ask_user_mode" if result.get("ask_user_always") else "default_user"
                continue
            result["require_password"] = idx == 1
            stage = "theme"

        elif stage == "theme":
            step_num = 3 if multi_user else 2
            theme_items = [
                (THEMES[tid].name, THEMES[tid].description)
                for tid in THEME_ORDER
            ]
            cur_tid = result.get("theme", "botyaradm_classic")
            init_idx = THEME_ORDER.index(cur_tid) if cur_tid in THEME_ORDER else 0

            action, idx = _prompt_step(
                stdscr=stdscr,
                theme_id=current_theme,
                step_label=f"Шаг {step_num}/{total_main_steps}",
                title="Выбери тему оформления:",
                subtitle="Листай стрелками — цвета меняются в реальном времени!",
                items=theme_items,
                initial_idx=init_idx,
                is_theme_step=True,
                can_go_back=True,
            )
            if action == "cancel":
                return None
            if action == "back":
                stage = "password"
                continue

            result["theme"] = THEME_ORDER[idx]
            result["setup_completed"] = True
            return result


def run_setup_wizard(
    users: list[str],
    current_settings: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    Запускает интерактивный мастер первоначальной настройки.
    При успешном завершении сохраняет настройки в settings.json и возвращает их.
    Возвращает None если пользователь отменил настройку.
    """
    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        pass

    base = default_settings()
    if current_settings:
        base.update(current_settings)

    if not users:
        users = [str(base.get("default_user", "user"))]

    def _wrapped(stdscr: "curses.window") -> dict[str, Any] | None:
        try:
            return _wizard_main(stdscr, users, base)
        finally:
            try:
                stdscr.erase()
                stdscr.refresh()
            except curses.error:
                pass

    try:
        configured = curses.wrapper(_wrapped)
    finally:
        reset_tty_palette()
    if configured is None:
        return None

    save_settings(configured)
    return configured
