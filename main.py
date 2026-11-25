"""
main.py — Точка входа PyDM.

Порядок работы:
  1. Обнаружение установленных DE/WM
  2. Сортировка по истории использования
  3. Показ интерактивного меню
  4. Запуск выбранной сессии

Если что-то пошло не так — управление возвращается в shell,
пользователь остаётся в рабочем TTY.
"""

import sys
import os
import traceback

def main() -> None:
    """Главная функция PyDM."""

    # ─── Защита: не запускаемся внутри графической сессии ───
    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        print("[PyDM] Графическая сессия уже запущена!")
        print("[PyDM] PyDM предназначен для запуска из TTY.")
        sys.exit(0)

    # ─── Импорты внутри main() ───
    # Почему здесь, а не вверху?
    # Если rich / questionary не установлены,
    # ошибка импорта будет поймана try/except
    # и пользователь получит понятное сообщение,
    # а не крэш при boot.
    try:
        from detector import detect_sessions
        from history import get_last_used, sort_sessions
        from menu import show_menu
        from launcher import launch
    except ImportError as e:
        print(f"[PyDM] Ошибка импорта: {e}", file=sys.stderr)
        print(
            "[PyDM] Убедись что зависимости установлены:",
            file=sys.stderr,
        )
        print(
            "[PyDM]   pip install rich",
            file=sys.stderr,
        )
        print(
            "[PyDM] Возвращаю управление в TTY.",
            file=sys.stderr,
        )
        return  # Возврат в shell — безопасный fallback

    # ─── Шаг 1: Обнаружение DE/WM ───
    try:
        sessions = detect_sessions()
    except Exception as e:
        print(f"[PyDM] Ошибка обнаружения DE/WM: {e}", file=sys.stderr)
        print("[PyDM] Возвращаю управление в TTY.", file=sys.stderr)
        return

    if not sessions:
        print("[PyDM] Не найдено ни одной DE/WM!", file=sys.stderr)
        print("[PyDM] Возвращаю управление в TTY.", file=sys.stderr)
        return

    # ─── Шаг 2: Сортировка по истории ───
    # TTY всегда последний, поэтому сортируем всё кроме TTY,
    # а потом добавляем TTY обратно в конец
    from config import TTY_OPTION_EXEC

    tty_entry = None
    sortable = []

    for session in sessions:
        name, exec_cmd = session
        if exec_cmd == TTY_OPTION_EXEC:
            tty_entry = session
        else:
            sortable.append(session)

    try:
        sortable = sort_sessions(sortable)
    except Exception:
        # Если сортировка сломалась — используем как есть
        pass

    # Собираем обратно: отсортированные DE + TTY в конце
    if tty_entry is not None:
        sessions = sortable + [tty_entry]
    else:
        sessions = sortable

    # ─── Шаг 3: Определяем последнюю DE ───
    try:
        last_used_exec = get_last_used()
    except Exception:
        last_used_exec = None

    # ─── Шаг 4: Показываем меню ───
    try:
        result = show_menu(
            sessions=sessions,
            last_used_exec=last_used_exec,
        )
    except KeyboardInterrupt:
        # Ctrl+C — выходим чисто
        print()
        print("[PyDM] Прервано. Возвращаю управление в TTY.")
        return
    except Exception as e:
        print(f"\n[PyDM] Ошибка меню: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("[PyDM] Возвращаю управление в TTY.", file=sys.stderr)
        return

    # ─── Шаг 5: Обработка выбора ───
    if result is None:
        # Пользователь вышел (q / Ctrl+C)
        print()
        print("[PyDM] Выход. Приятной работы в TTY!")
        return

    display_name, exec_cmd = result

    # ─── Шаг 6: Запуск! ───
    try:
        launch(exec_cmd, display_name)
    except Exception as e:
        print(f"\n[PyDM] Ошибка запуска {display_name}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("[PyDM] Возвращаю управление в TTY.", file=sys.stderr)
        return

    # Если launch() вернулся (TTY option), просто выходим
    # shell продолжит работу


if __name__ == "__main__":
    main()
