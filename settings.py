"""
settings.py — Хранение и загрузка настроек botyaradm (~/.config/botyaradm/settings.json).
"""

import json
from typing import Any

from config import BOTYARADM_DIR, DEFAULT_THEME, SETTINGS_FILE, USERNAME


def default_settings() -> dict[str, Any]:
    """Возвращает словарь настроек по умолчанию."""
    return {
        "setup_completed": False,
        "ask_user_always": False,
        "default_user": USERNAME,
        "require_password": False,
        "theme": DEFAULT_THEME,
    }


def settings_exists() -> bool:
    """Проверяет существование файла настроек."""
    return SETTINGS_FILE.is_file()


def load_settings() -> dict[str, Any]:
    """
    Загружает настройки из settings.json.
    При отсутствии или повреждении файла возвращает значения по умолчанию.
    """
    defaults = default_settings()
    if not SETTINGS_FILE.is_file():
        return defaults

    try:
        raw = SETTINGS_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return defaults
    except (OSError, json.JSONDecodeError, ValueError):
        return defaults

    merged = dict(defaults)
    for key in defaults:
        if key in data:
            merged[key] = data[key]
    return merged


def is_setup_completed() -> bool:
    """Возвращает True, если мастер первоначальной настройки уже пройден."""
    if not settings_exists():
        return False
    return bool(load_settings().get("setup_completed", False))


def save_settings(data: dict[str, Any]) -> None:
    """Атомарно сохраняет настройки в settings.json."""
    BOTYARADM_DIR.mkdir(parents=True, exist_ok=True)
    payload = default_settings()
    payload.update(data)

    tmp_path = SETTINGS_FILE.with_suffix(".tmp")
    try:
        tmp_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        tmp_path.replace(SETTINGS_FILE)
    except OSError:
        pass
