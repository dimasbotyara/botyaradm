"""
main.py — Точка входа botyaradm.

Порядок работы:
  1. Проверка графической сессии (DISPLAY / WAYLAND_DISPLAY)
  2. Очистка терминала до запуска интерфейса
  3. Первый запуск (или --setup): мастер настройки пользователя, пароля и темы
  4. (Опционально) выбор пользователя и проверка системного пароля
  5. Обнаружение DE/WM и сортировка по истории
  6. Интерактивное curses-меню и запуск выбранной сессии
  7. Очистка терминала после завершения
"""

import os
import sys
import traceback


def main(argv: list[str] | None = None) -> None:
    """Главная функция botyaradm."""
    args = argv if argv is not None else sys.argv[1:]
    force_wizard = "--setup" in args or "--wizard" in args

    # ─── Защита: не запускаемся внутри графической сессии ───
    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        print("[botyaradm] Графическая сессия уже запущена!")
        print("[botyaradm] botyaradm предназначен для запуска из TTY.")
        sys.exit(0)

    # ─── Импорты внутри main() ───
    try:
        from auth import get_system_users, verify_password
        from config import (
            CLEAR_TERMINAL,
            DEFAULT_THEME,
            TTY_OPTION_EXEC,
            WIZARD_OPTION_EXEC,
        )
        from detector import detect_sessions
        from history import get_last_used, sort_sessions
        from launcher import launch
        from menu import show_menu, show_password_prompt, show_user_menu
        from settings import is_setup_completed, load_settings
        from setup_wizard import run_setup_wizard
        from tui_utils import clear_terminal
    except ImportError as e:
        print(f"[botyaradm] Ошибка импорта: {e}", file=sys.stderr)
        print(
            "[botyaradm] Проверь целостность файлов botyaradm и поддержку curses в Python.",
            file=sys.stderr,
        )
        print(
            "[botyaradm] Возвращаю управление в TTY.",
            file=sys.stderr,
        )
        return

    # ─── Очистка экрана перед запуском ───
    if CLEAR_TERMINAL:
        clear_terminal()

    try:
        users = get_system_users()
        user_settings = load_settings()

        # ─── Шаг 1: Setup Wizard при первом запуске или --setup ───
        if force_wizard or not is_setup_completed():
            configured = run_setup_wizard(users, user_settings)
            if configured is None:
                if CLEAR_TERMINAL:
                    clear_terminal()
                return
            user_settings = configured

        theme_id = str(user_settings.get("theme", DEFAULT_THEME))
        ask_user_always = bool(user_settings.get("ask_user_always", False))
        require_password = bool(user_settings.get("require_password", False))

        # ─── Шаг 2: Выбор пользователя ───
        if len(users) == 1:
            selected_user = users[0]
        elif ask_user_always:
            chosen_user = show_user_menu(
                users=users,
                theme_id=theme_id,
                default_user=str(user_settings.get("default_user", users[0])),
            )
            if chosen_user is None:
                if CLEAR_TERMINAL:
                    clear_terminal()
                return
            selected_user = chosen_user
        else:
            default_user = str(user_settings.get("default_user", users[0]))
            selected_user = default_user if default_user in users else users[0]

        # ─── Шаг 3: Запрос пароля (если включено) ───
        if require_password:
            authenticated = show_password_prompt(
                username=selected_user,
                theme_id=theme_id,
                verify_fn=verify_password,
            )
            if not authenticated:
                if CLEAR_TERMINAL:
                    clear_terminal()
                return

        # ─── Шаг 4: Обнаружение DE/WM ───
        sessions = detect_sessions()
        if not sessions:
            if CLEAR_TERMINAL:
                clear_terminal()
            print("[botyaradm] Не найдено ни одной DE/WM!", file=sys.stderr)
            print("[botyaradm] Возвращаю управление в TTY.", file=sys.stderr)
            return

        tty_entry = None
        sortable = []
        for session in sessions:
            _name, exec_cmd = session
            if exec_cmd == TTY_OPTION_EXEC:
                tty_entry = session
            else:
                sortable.append(session)

        try:
            sortable = sort_sessions(sortable)
        except Exception:
            pass

        sessions = sortable + [tty_entry] if tty_entry is not None else sortable

        try:
            last_used_exec = get_last_used()
        except Exception:
            last_used_exec = None

        # ─── Шаг 5: Главное меню (с возможностью открыть [w] Настройки) ───
        while True:
            result = show_menu(
                sessions=sessions,
                last_used_exec=last_used_exec,
                username=selected_user,
                theme_id=theme_id,
            )

            if result is None:
                if CLEAR_TERMINAL:
                    clear_terminal()
                return

            display_name, exec_cmd = result

            if exec_cmd == WIZARD_OPTION_EXEC:
                updated = run_setup_wizard(users, user_settings)
                if updated is not None:
                    user_settings = updated
                    theme_id = str(user_settings.get("theme", DEFAULT_THEME))
                    if len(users) > 1 and not user_settings.get("ask_user_always"):
                        cand = str(user_settings.get("default_user", selected_user))
                        if cand in users:
                            selected_user = cand
                continue

            break

        # ─── Шаг 6: Запуск выбранной сессии ───
        launch(exec_cmd, display_name, username=selected_user)

        # Если launch() вернулся (TTY option) — экран уже очищен
        if CLEAR_TERMINAL:
            clear_terminal()

    except KeyboardInterrupt:
        if CLEAR_TERMINAL:
            clear_terminal()
        return
    except Exception as e:
        if CLEAR_TERMINAL:
            clear_terminal()
        print(f"[botyaradm] Ошибка: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("[botyaradm] Возвращаю управление в TTY.", file=sys.stderr)
        return


if __name__ == "__main__":
    main()
