"""
launcher.py — Запуск выбранной DE/WM.

Поддерживает:
  - X11 через startx
  - Wayland напрямую
  - TTY (просто возврат в shell)
"""

import os
import subprocess
import sys
from pathlib import Path

from config import TTY_OPTION_EXEC
from detector import get_session_type
from history import record_launch


def _create_xinitrc(exec_cmd: str) -> Path:
    """
    Создаёт временный .xinitrc для startx.

    Пишет в ~/.xinitrc.pydm чтобы не трогать пользовательский ~/.xinitrc.

    Args:
        exec_cmd: Команда запуска DE/WM.

    Returns:
        Путь к созданному файлу.
    """
    xinitrc_path = Path.home() / ".xinitrc.pydm"

    content = f"""#!/bin/sh
# Сгенерировано PyDM — не редактируйте вручную!
# Этот файл перезаписывается при каждом запуске.

# Загружаем стандартные ресурсы X
if [ -f "$HOME/.Xresources" ]; then
    xrdb -merge "$HOME/.Xresources"
fi

if [ -f "$HOME/.xprofile" ]; then
    . "$HOME/.xprofile"
fi

# Запускаем DE/WM
exec {exec_cmd}
"""

    try:
        xinitrc_path.write_text(content, encoding="utf-8")
        xinitrc_path.chmod(0o755)
    except OSError as e:
        print(f"[PyDM] Ошибка создания xinitrc: {e}", file=sys.stderr)
        sys.exit(1)

    return xinitrc_path


def _launch_x11(exec_cmd: str) -> None:
    """
    Запускает X11 сессию через startx.

    Args:
        exec_cmd: Команда DE/WM для запуска.
    """
    xinitrc = _create_xinitrc(exec_cmd)

    # startx использует .xinitrc по умолчанию,
    # но мы явно указываем наш файл
    # exec заменяет текущий процесс — это важно!
    # Если не сделать exec, после закрытия DE
    # вернётся PyDM вместо TTY логина
    os.execvp("startx", ["startx", str(xinitrc)])


def _launch_wayland(exec_cmd: str) -> None:
    """
    Запускает Wayland сессию напрямую.

    Args:
        exec_cmd: Команда композитора (sway, hyprland, etc.)
    """
    # Устанавливаем XDG_SESSION_TYPE чтобы приложения знали
    os.environ["XDG_SESSION_TYPE"] = "wayland"

    # Разбиваем команду на части для exec
    parts = exec_cmd.split()
    os.execvp(parts[0], parts)


def _stay_in_tty() -> None:
    """
    Пользователь выбрал остаться в TTY.
    Просто выходим, shell продолжит работу.
    """
    print()
    print("[PyDM] Оставайся в TTY. Приятной работы!")
    print("[PyDM] Чтобы запустить PyDM снова: python ~/.config/pydm/main.py")
    print()
    # НЕ вызываем sys.exit(0) здесь, просто return
    # main.py сам решит что делать


def launch(exec_cmd: str, display_name: str) -> None:
    """
    Главная функция запуска.

    Определяет тип сессии и запускает соответствующим образом.
    Записывает выбор в историю перед запуском.

    Args:
        exec_cmd: Команда запуска.
        display_name: Человеко-читаемое название (для истории).
    """
    # Если TTY — не записываем в историю
    if exec_cmd == TTY_OPTION_EXEC:
        _stay_in_tty()
        return

    # Записываем в историю ДО запуска
    # (после exec процесс заменится и код дальше не выполнится)
    record_launch(exec_cmd, display_name)

    session_type = get_session_type(exec_cmd)

    if session_type == "wayland":
        _launch_wayland(exec_cmd)
    else:
        _launch_x11(exec_cmd)

    # Сюда мы не должны попасть (exec заменяет процесс)
    # Но если вдруг exec не сработал:
    print(
        f"[PyDM] Ошибка: не удалось запустить {display_name}",
        file=sys.stderr,
    )
    print(
        f"[PyDM] Команда: {exec_cmd}",
        file=sys.stderr,
    )
    sys.exit(1)
