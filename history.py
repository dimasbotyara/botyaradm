"""
history.py — Управление историей запусков.
Хранит JSON с данными о том, когда и сколько раз
запускалась каждая DE/WM. Используется для сортировки.
"""

import json
import time
from pathlib import Path
from typing import Any

from config import HISTORY_FILE, PYDM_DIR


def _ensure_dir() -> None:
    """Создаёт директорию конфигурации если не существует."""
    PYDM_DIR.mkdir(parents=True, exist_ok=True)


def _load_raw() -> dict[str, Any]:
    """
    Загружает сырые данные из history.json.
    Возвращает пустой dict если файл не существует или повреждён.
    """
    if not HISTORY_FILE.exists():
        return {}

    try:
        text = HISTORY_FILE.read_text(encoding="utf-8")
        data = json.loads(text)
        if isinstance(data, dict):
            return data
        return {}
    except (json.JSONDecodeError, OSError, ValueError):
        # Файл повреждён — начинаем с чистого листа
        return {}


def _save_raw(data: dict[str, Any]) -> None:
    """Сохраняет данные в history.json атомарно."""
    _ensure_dir()

    # Пишем во временный файл, потом переименовываем —
    # это защищает от потери данных при сбое питания / крэше.
    tmp_path = HISTORY_FILE.with_suffix(".tmp")
    try:
        tmp_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        tmp_path.replace(HISTORY_FILE)  # Атомарная замена на Linux
    except OSError:
        # Если не удалось сохранить — не критично,
        # просто сортировка не обновится
        pass


def record_launch(exec_cmd: str, display_name: str) -> None:
    """
    Записывает факт запуска DE/WM.

    Args:
        exec_cmd: Команда запуска (ключ).
        display_name: Человеко-читаемое название.
    """
    data = _load_raw()

    if exec_cmd not in data:
        data[exec_cmd] = {
            "name": display_name,
            "count": 0,
            "last_used": 0,
        }

    data[exec_cmd]["name"] = display_name
    data[exec_cmd]["count"] = data[exec_cmd].get("count", 0) + 1
    data[exec_cmd]["last_used"] = time.time()

    _save_raw(data)


def get_last_used() -> str | None:
    """
    Возвращает exec_cmd последней запущенной DE/WM.
    None если истории нет.
    """
    data = _load_raw()
    if not data:
        return None

    # Находим запись с максимальным last_used
    best_cmd = None
    best_time = 0.0

    for cmd, info in data.items():
        t = info.get("last_used", 0)
        if t > best_time:
            best_time = t
            best_cmd = cmd

    return best_cmd


def sort_sessions(
    sessions: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    """
    Сортирует список сессий: чаще/недавно использованные — выше.

    Args:
        sessions: Список кортежей (display_name, exec_cmd).

    Returns:
        Отсортированный список в том же формате.
    """
    data = _load_raw()

    def sort_key(item: tuple[str, str]) -> tuple[float, int]:
        """Сортируем по last_used (убывание), потом по count (убывание)."""
        _name, cmd = item
        info = data.get(cmd, {})
        last = info.get("last_used", 0)
        count = info.get("count", 0)
        # Отрицательные значения потому что sort по возрастанию,
        # а нам нужно убывание
        return (-last, -count)

    return sorted(sessions, key=sort_key)
