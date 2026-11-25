"""
detector.py — Автопоиск установленных DE/WM.

Сканирует:
  1. /usr/share/xsessions/*.desktop      (X11)
  2. /usr/share/wayland-sessions/*.desktop (Wayland)
  3. Известные команды из KNOWN_SESSIONS  (fallback)

Возвращает список кортежей (display_name, exec_cmd).
"""

import shutil
from configparser import ConfigParser
from pathlib import Path

from config import (
    KNOWN_SESSIONS,
    TTY_OPTION_EXEC,
    TTY_OPTION_NAME,
    WAYLAND_SESSION_DIRS,
    XSESSION_DIRS,
)


def _parse_desktop_file(path: Path) -> tuple[str, str] | None:
    """
    Парсит .desktop файл и извлекает Name и Exec.

    Args:
        path: Путь к .desktop файлу.

    Returns:
        (display_name, exec_cmd) или None если файл невалиден.
    """
    try:
        parser = ConfigParser(interpolation=None)
        # .desktop файлы — это INI-формат с секцией [Desktop Entry]
        # strict=False на случай дублирующихся ключей
        parser.read(str(path), encoding="utf-8")

        if not parser.has_section("Desktop Entry"):
            return None

        entry = parser["Desktop Entry"]

        # Пропускаем скрытые сессии
        if entry.get("Hidden", "false").lower() == "true":
            return None
        if entry.get("NoDisplay", "false").lower() == "true":
            return None

        name = entry.get("Name")
        exec_cmd = entry.get("Exec")

        if not name or not exec_cmd:
            return None

        # Убираем аргументы типа %F, %U и т.д. — они не нужны для DE
        # Но оставляем аргументы типа --replace
        exec_parts = []
        for part in exec_cmd.split():
            if part.startswith("%"):
                continue
            exec_parts.append(part)

        exec_cmd = " ".join(exec_parts).strip()

        if not exec_cmd:
            return None

        return (name.strip(), exec_cmd)

    except (OSError, KeyError, Exception):
        # Не можем прочитать / распарсить — просто пропускаем
        return None


def _scan_desktop_dirs(dirs: list[Path]) -> list[tuple[str, str]]:
    """
    Сканирует директории с .desktop файлами сессий.

    Args:
        dirs: Список директорий для сканирования.

    Returns:
        Список (display_name, exec_cmd).
    """
    results: list[tuple[str, str]] = []
    seen_execs: set[str] = set()

    for directory in dirs:
        if not directory.is_dir():
            continue

        try:
            desktop_files = sorted(directory.glob("*.desktop"))
        except OSError:
            continue

        for desktop_file in desktop_files:
            parsed = _parse_desktop_file(desktop_file)
            if parsed is None:
                continue

            name, exec_cmd = parsed

            # Дедупликация по exec_cmd
            if exec_cmd in seen_execs:
                continue
            seen_execs.add(exec_cmd)

            results.append((name, exec_cmd))

    return results


def _scan_known_commands() -> list[tuple[str, str]]:
    """
    Проверяет наличие известных DE/WM команд в PATH.

    Returns:
        Список (display_name, exec_cmd) для найденных команд.
    """
    results: list[tuple[str, str]] = []

    for exec_cmd, display_name in KNOWN_SESSIONS.items():
        # Берём первое слово как команду для проверки
        # (например "qtile start" → проверяем "qtile")
        binary = exec_cmd.split()[0]

        if shutil.which(binary) is not None:
            results.append((display_name, exec_cmd))

    return results


def _deduplicate(
    sessions: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    """
    Убирает дубликаты по exec_cmd, сохраняя порядок.
    Приоритет у первого вхождения (обычно из .desktop файла).
    """
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []

    for name, exec_cmd in sessions:
        if exec_cmd in seen:
            continue
        seen.add(exec_cmd)
        unique.append((name, exec_cmd))

    return unique


def detect_sessions() -> list[tuple[str, str]]:
    """
    Главная функция: находит все доступные DE/WM.

    Порядок приоритета:
      1. .desktop файлы (X11)
      2. .desktop файлы (Wayland)
      3. Известные команды (fallback для тех, что не нашлись)

    Всегда добавляет "Продолжить в TTY" как последний пункт.

    Returns:
        Список (display_name, exec_cmd).
        Последний элемент всегда TTY.
        Пустым быть не может (минимум — только TTY).
    """
    # Шаг 1: .desktop файлы
    from_desktop = _scan_desktop_dirs(XSESSION_DIRS + WAYLAND_SESSION_DIRS)

    # Шаг 2: Известные команды
    from_known = _scan_known_commands()

    # Шаг 3: Объединяем, .desktop файлы имеют приоритет
    combined = from_desktop + from_known
    sessions = _deduplicate(combined)

    # Шаг 4: Добавляем TTY как последний пункт (всегда!)
    sessions.append((TTY_OPTION_NAME, TTY_OPTION_EXEC))

    return sessions


def get_session_type(exec_cmd: str) -> str:
    """
    Определяет тип сессии: 'x11', 'wayland' или 'tty'.

    Логика:
      - Если exec_cmd — маркер TTY → 'tty'
      - Если .desktop найден в wayland-sessions → 'wayland'
      - Если команда из списка wayland-команд → 'wayland'
      - Иначе → 'x11'

    Args:
        exec_cmd: Команда запуска.

    Returns:
        'x11', 'wayland' или 'tty'.
    """
    if exec_cmd == TTY_OPTION_EXEC:
        return "tty"

    # Проверяем wayland-sessions .desktop
    for directory in WAYLAND_SESSION_DIRS:
        if not directory.is_dir():
            continue
        try:
            for desktop_file in directory.glob("*.desktop"):
                parsed = _parse_desktop_file(desktop_file)
                if parsed and parsed[1] == exec_cmd:
                    return "wayland"
        except OSError:
            continue

    # Проверяем известные Wayland команды
    wayland_keywords = [
        "wayland", "sway", "hyprland", "river",
        "labwc", "wayfire",
    ]
    exec_lower = exec_cmd.lower()
    for keyword in wayland_keywords:
        if keyword in exec_lower:
            return "wayland"

    return "x11"
