"""
auth.py — Поиск пользователей системы и проверка пароля без сторонних библиотек.
"""

import ctypes
import ctypes.util
import os
import pty
import pwd
import select
import shutil
import subprocess
import time
from pathlib import Path

_NOLOGIN_SHELLS = {"nologin", "false", "sync", "halt", "shutdown"}


def get_current_username() -> str:
    """Возвращает имя текущего пользователя процесса."""
    try:
        return pwd.getpwuid(os.getuid()).pw_name
    except KeyError:
        return os.environ.get("USER") or os.environ.get("LOGNAME") or "user"


def get_system_users() -> list[str]:
    """
    Возвращает список реальных пользователей системы (UID >= 1000 и текущий).
    Текущий пользователь ставится первым, остальные отсортированы по UID.
    """
    current = get_current_username()
    current_uid = os.getuid()
    candidates: list[tuple[int, str]] = []

    try:
        entries = pwd.getpwall()
    except OSError:
        return [current]

    for entry in entries:
        shell_name = Path(entry.pw_shell).name if entry.pw_shell else ""
        if shell_name in _NOLOGIN_SHELLS or not entry.pw_shell:
            if entry.pw_uid != current_uid:
                continue

        is_human = 1000 <= entry.pw_uid < 65534
        if is_human or entry.pw_uid == current_uid:
            candidates.append((entry.pw_uid, entry.pw_name))

    if not candidates:
        return [current]

    candidates.sort(key=lambda item: (item[1] != current, item[0], item[1]))

    users: list[str] = []
    seen: set[str] = set()
    for _uid, name in candidates:
        if name not in seen:
            seen.add(name)
            users.append(name)

    return users or [current]


def _verify_via_pam(username: str, password: str) -> bool | None:
    """
    Проверяет пароль через libpam.so.0 (PAM).
    Возвращает True/False или None если libpam недоступен.
    """
    pam_path = ctypes.util.find_library("pam")
    c_path = ctypes.util.find_library("c")
    if not pam_path or not c_path:
        return None

    try:
        libpam = ctypes.CDLL(pam_path)
        libc = ctypes.CDLL(c_path)
    except OSError:
        return None

    class PamMessage(ctypes.Structure):
        _fields_ = [("msg_style", ctypes.c_int), ("msg", ctypes.c_char_p)]

    class PamResponse(ctypes.Structure):
        _fields_ = [("resp", ctypes.c_char_p), ("resp_retcode", ctypes.c_int)]

    conv_func_type = ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.POINTER(PamMessage)),
        ctypes.POINTER(ctypes.POINTER(PamResponse)),
        ctypes.c_void_p,
    )

    class PamConv(ctypes.Structure):
        _fields_ = [("conv", conv_func_type), ("appdata_ptr", ctypes.c_void_p)]

    libc.calloc.restype = ctypes.c_void_p
    libc.calloc.argtypes = [ctypes.c_size_t, ctypes.c_size_t]
    libc.malloc.restype = ctypes.c_void_p
    libc.malloc.argtypes = [ctypes.c_size_t]

    pw_bytes = password.encode("utf-8", errors="replace") + b"\x00"

    @conv_func_type
    def _conv(n_messages, messages, p_response, _app_data):
        if n_messages <= 0:
            return 19  # PAM_CONV_ERR
        ptr = libc.calloc(n_messages, ctypes.sizeof(PamResponse))
        if not ptr:
            return 19
        arr = ctypes.cast(ptr, ctypes.POINTER(PamResponse))
        for i in range(n_messages):
            style = messages[i].contents.msg_style
            if style in (1, 2):  # PAM_PROMPT_ECHO_OFF / PAM_PROMPT_ECHO_ON
                c_str = libc.malloc(len(pw_bytes))
                if not c_str:
                    return 19
                ctypes.memmove(c_str, pw_bytes, len(pw_bytes))
                arr[i].resp = ctypes.cast(c_str, ctypes.c_char_p)
                arr[i].resp_retcode = 0
        p_response[0] = arr
        return 0

    conv = PamConv(_conv, None)

    for service in (b"login", b"system-auth", b"passwd"):
        handle = ctypes.c_void_p()
        rc = libpam.pam_start(
            service,
            username.encode("utf-8"),
            ctypes.byref(conv),
            ctypes.byref(handle),
        )
        if rc != 0:
            continue
        try:
            auth_rc = libpam.pam_authenticate(handle, 0)
            libpam.pam_end(handle, auth_rc)
            return auth_rc == 0
        except Exception:
            libpam.pam_end(handle, rc)
            return None

    return None


def _verify_via_su(username: str, password: str) -> bool:
    """
    Проверяет пароль через `su -c true <username>` в PTY с локалью C.
    """
    su_bin = shutil.which("su")
    if not su_bin:
        return False

    master, slave = pty.openpty()
    env = {
        "LC_ALL": "C",
        "LANG": "C",
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
    }

    try:
        proc = subprocess.Popen(
            [su_bin, "-c", "true", username],
            stdin=slave,
            stdout=slave,
            stderr=slave,
            env=env,
            start_new_session=True,
            close_fds=True,
        )
    except OSError:
        os.close(master)
        os.close(slave)
        return False

    os.close(slave)

    buf = b""
    sent = False
    deadline = time.monotonic() + 8.0

    try:
        while time.monotonic() < deadline:
            r, _, _ = select.select([master], [], [], 0.1)
            if r:
                try:
                    chunk = os.read(master, 1024)
                    if not chunk:
                        break
                    buf += chunk
                    if not sent and b"password" in buf.lower():
                        os.write(master, password.encode("utf-8") + b"\n")
                        sent = True
                except OSError:
                    break
            if proc.poll() is not None:
                break

        rc = proc.wait(timeout=3)
        return rc == 0 and sent
    except Exception:
        try:
            proc.kill()
        except OSError:
            pass
        return False
    finally:
        try:
            os.close(master)
        except OSError:
            pass


def verify_password(username: str, password: str) -> bool:
    """
    Проверяет системный пароль пользователя `username`.
    """
    current = get_current_username()

    # Для текущего пользователя или от имени root проверяем через PAM,
    # чтобы su не пропускал проверку по pam_rootok / совпадению UID.
    if username == current or os.geteuid() == 0:
        pam_result = _verify_via_pam(username, password)
        if pam_result is not None:
            return pam_result

    # Для переключения на другого пользователя от обычного UID используем su.
    return _verify_via_su(username, password)
