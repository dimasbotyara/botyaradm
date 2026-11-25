"""
launcher.py — Запуск выбранной DE/WM.

Поддерживает:
  - X11 через startx
  - Wayland напрямую
  - TTY (просто возврат в shell)
  - Смену пользователя при запуске (если выбран другой пользователь)
"""

import os
import pwd
import shlex
import sys
from pathlib import Path

from config import CLEAR_TERMINAL, TTY_OPTION_EXEC
from detector import get_session_type
from history import record_launch
from tui_utils import clear_terminal


def _target_home(username: str | None) -> Path:
    """Возвращает домашнюю директорию целевого пользователя."""
    if username:
        try:
            return Path(pwd.getpwnam(username).pw_dir)
        except KeyError:
            pass
    return Path.home()


def _create_xinitrc(exec_cmd: str, username: str | None = None) -> Path:
    """
    Создаёт временный .xinitrc для startx.
    Пишет в ~/.xinitrc.pydm чтобы не трогать пользовательский ~/.xinitrc.
    """
    home_dir = _target_home(username)
    xinitrc_path = home_dir / ".xinitrc.pydm"

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
        if username and os.geteuid() == 0:
            pw = pwd.getpwnam(username)
            os.chown(xinitrc_path, pw.pw_uid, pw.pw_gid)
    except (OSError, KeyError) as e:
        print(f"[PyDM] Ошибка создания xinitrc: {e}", file=sys.stderr)
        sys.exit(1)

    return xinitrc_path


def _switch_user_as_root(username: str) -> None:
    """Переключает UID/GID и окружение на целевого пользователя (при запуске от root)."""
    pw = pwd.getpwnam(username)
    os.environ["HOME"] = pw.pw_dir
    os.environ["USER"] = pw.pw_name
    os.environ["LOGNAME"] = pw.pw_name
    if pw.pw_shell:
        os.environ["SHELL"] = pw.pw_shell

    os.initgroups(pw.pw_name, pw.pw_gid)
    os.setgid(pw.pw_gid)
    os.setuid(pw.pw_uid)
    try:
        os.chdir(pw.pw_dir)
    except OSError:
        pass


def _current_username() -> str:
    try:
        return pwd.getpwuid(os.getuid()).pw_name
    except KeyError:
        return os.environ.get("USER") or ""


def _launch_x11(exec_cmd: str, username: str | None = None) -> None:
    """Запускает X11 сессию через startx."""
    current = _current_username()
    xinitrc = _create_xinitrc(exec_cmd, username)

    if CLEAR_TERMINAL:
        clear_terminal()

    if username and username != current:
        if os.geteuid() == 0:
            _switch_user_as_root(username)
            os.execvp("startx", ["startx", str(xinitrc)])
        else:
            cmd_str = f"startx {shlex.quote(str(xinitrc))}"
            os.execvp("su", ["su", "-", username, "-c", cmd_str])
    else:
        os.execvp("startx", ["startx", str(xinitrc)])


def _launch_wayland(exec_cmd: str, username: str | None = None) -> None:
    """Запускает Wayland сессию напрямую."""
    current = _current_username()
    os.environ["XDG_SESSION_TYPE"] = "wayland"

    if CLEAR_TERMINAL:
        clear_terminal()

    if username and username != current:
        if os.geteuid() == 0:
            _switch_user_as_root(username)
            parts = exec_cmd.split()
            os.execvp(parts[0], parts)
        else:
            cmd_str = f"XDG_SESSION_TYPE=wayland exec {exec_cmd}"
            os.execvp("su", ["su", "-", username, "-c", cmd_str])
    else:
        parts = exec_cmd.split()
        os.execvp(parts[0], parts)


def _stay_in_tty() -> None:
    """Пользователь выбрал остаться в TTY."""
    if CLEAR_TERMINAL:
        clear_terminal()


def launch(
    exec_cmd: str,
    display_name: str,
    username: str | None = None,
) -> None:
    """
    Главная функция запуска.

    Определяет тип сессии и запускает соответствующим образом.
    Записывает выбор в историю перед запуском.
    """
    if exec_cmd == TTY_OPTION_EXEC:
        _stay_in_tty()
        return

    record_launch(exec_cmd, display_name)

    session_type = get_session_type(exec_cmd)

    if session_type == "wayland":
        _launch_wayland(exec_cmd, username=username)
    else:
        _launch_x11(exec_cmd, username=username)

    print(
        f"[PyDM] Ошибка: не удалось запустить {display_name}",
        file=sys.stderr,
    )
    print(
        f"[PyDM] Команда: {exec_cmd}",
        file=sys.stderr,
    )
    sys.exit(1)
