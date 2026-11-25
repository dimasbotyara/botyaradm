"""
menu.py — Интерактивное TUI-меню выбора DE/WM.

Используем questionary для навигации (стрелки, Enter, цифры)
и rich для красивого приветствия.

Возможности:
  - Навигация стрелками (↑↓) — questionary делает wrap-around сам
  - Быстрый выбор цифрами (1-9, 0 для 10-го)
  - Enter для подтверждения
  - Countdown с автовыбором последней DE/WM
  - Цвета: вопрос белый, выбранный bold blue, остальные голубые
"""

import signal
import threading
import time

import questionary
from questionary import Choice, Style
from rich.console import Console

from config import (
    AUTO_SELECT_TIMEOUT,
    COLOR_GREETING,
    USERNAME,
)
from greetings import get_greeting


# ─── Стиль questionary ────────────────────────────────
# question    — текст вопроса "Выбери DE/WM:"
# highlighted — пункт, на котором сейчас стоит курсор
# pointer     — стрелочка-указатель (▸)
# selected    — выбранный пункт после нажатия Enter
# text        — обычные (невыбранные) пункты
# instruction — подсказка в скобках
# answer      — текст ответа после выбора

_STYLE = Style(
    [
        ("question", "fg:white bold"),
        ("highlighted", "fg:blue bold"),
        ("pointer", "fg:blue bold"),
        ("selected", "fg:blue bold"),
        ("text", "fg:ansicyan"),
        ("instruction", "fg:white dim"),
        ("answer", "fg:blue bold"),
    ]
)


# ─── Таймер автозапуска ───────────────────────────────


class _CountdownTimer:
    """
    Таймер обратного отсчёта в отдельном потоке.

    Когда время истекает — посылает SIGINT,
    что заставляет questionary выбросить KeyboardInterrupt.
    Мы ловим его и делаем автовыбор.

    Если пользователь нажал любую клавишу и сделал выбор
    до истечения таймера — таймер отменяется.
    """

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout
        self.cancelled = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Запускает таймер в фоновом потоке."""
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,  # daemon — умрёт вместе с основным процессом
        )
        self._thread.start()

    def cancel(self) -> None:
        """Отменяет таймер (пользователь сделал выбор)."""
        self.cancelled = True

    def _run(self) -> None:
        """Тело фонового потока."""
        # Проверяем каждые 0.1 секунды — не отменили ли нас
        for _ in range(self.timeout * 10):
            if self.cancelled:
                return
            time.sleep(0.1)

        # Время вышло! Прерываем questionary
        if not self.cancelled:
            try:
                signal.raise_signal(signal.SIGINT)
            except (OSError, AttributeError):
                # Если raise_signal недоступен (старый Python)
                import os

                os.kill(os.getpid(), signal.SIGINT)


# ─── Построение списка пунктов ────────────────────────


def _build_choices(
    sessions: list[tuple[str, str]],
) -> list[Choice]:
    """
    Формирует список Choice для questionary.select().

    Каждый пункт получает:
      - shortcut_key: цифра для быстрого выбора
      - title: отображаемое название DE/WM
      - value: кортеж (name, exec_cmd) — возвращается при выборе

    Нумерация:
      1-9 для первых 9 пунктов
      0   для 10-го пункта
      Остальные без shortcut (маловероятно что будет >10 DE)

    Args:
        sessions: Список (display_name, exec_cmd).

    Returns:
        Список questionary.Choice.
    """
    choices: list[Choice] = []

    for i, (name, exec_cmd) in enumerate(sessions):
        # Определяем shortcut-клавишу
        if i < 9:
            shortcut = str(i + 1)
        elif i == 9:
            shortcut = "0"
        else:
            shortcut = None  # Больше 10 — без шортката

        choice = Choice(
            title=name,
            value=(name, exec_cmd),
            shortcut_key=shortcut,
        )
        choices.append(choice)

    return choices


# ─── Определение default-пункта ──────────────────────


def _find_default(
    sessions: list[tuple[str, str]],
    choices: list[Choice],
    last_used_exec: str | None,
) -> tuple[tuple[str, str] | None, tuple[str, str] | None]:
    """
    Находит пункт, соответствующий последней запущенной DE/WM.

    Возвращает:
      - default_value: value для questionary (кортеж, не строка!)
      - default_result: (name, exec_cmd) для автовыбора по таймауту

    Если last_used_exec не найден в списке — возвращает (None, None).
    """
    if last_used_exec is None:
        return None, None

    for i, (name, exec_cmd) in enumerate(sessions):
        if exec_cmd == last_used_exec:
            # Возвращаем value (кортеж), а НЕ title (строку)!
            return choices[i].value, (name, exec_cmd)

    return None, None


# ─── Главная функция ──────────────────────────────────


def show_menu(
    sessions: list[tuple[str, str]],
    last_used_exec: str | None = None,
) -> tuple[str, str] | None:
    """
    Показывает интерактивное меню и возвращает выбор пользователя.

    Что происходит:
      1. Печатается случайное приветствие (rich)
      2. Если есть последняя DE — показывается countdown
      3. questionary рисует меню с навигацией
      4. Пользователь выбирает стрелками/цифрами/Enter
      5. Если время вышло — автовыбор последней DE

    Args:
        sessions: Список (display_name, exec_cmd).
                  Последний элемент — "Продолжить в TTY".
        last_used_exec: exec_cmd последней использованной DE/WM.

    Returns:
        (display_name, exec_cmd) выбранной сессии.
        None если пользователь вышел (Ctrl+C).
    """
    console = Console()

    # ─── Приветствие ───────────────────────────────────
    greeting = get_greeting(USERNAME)
    console.print()
    console.print(f"  {greeting}", style=COLOR_GREETING)
    console.print()

    # ─── Строим пункты меню ────────────────────────────
    choices = _build_choices(sessions)

    # ─── Ищем default (последняя DE) ───────────────────
    default_value, default_result = _find_default(
        sessions, choices, last_used_exec
    )

    # ─── Countdown (если есть что автозапускать) ───────
    timer: _CountdownTimer | None = None

    if default_result is not None:
        default_name = default_result[0]
        console.print(
            f"  [dim white]⏱  Автозапуск"
            f" [bold blue]{default_name}[/bold blue]"
            f" через {AUTO_SELECT_TIMEOUT} сек...[/dim white]"
        )
        console.print(
            "  [dim white]Нажми любую клавишу для отмены[/dim white]"
        )
        console.print()

        timer = _CountdownTimer(AUTO_SELECT_TIMEOUT)

    # ─── Запускаем questionary ─────────────────────────
    try:
        # Стартуем таймер (если есть)
        if timer is not None:
            timer.start()

        result = questionary.select(
            message="Выбери DE/WM:",
            choices=choices,
            default=default_value,
            style=_STYLE,
            qmark="▸",
            instruction="(↑↓ навигация, 1-9 быстрый выбор, Enter ОК)",
            use_shortcuts=True,
        ).ask()

        # Пользователь сделал выбор — отменяем таймер
        if timer is not None:
            timer.cancel()

        # questionary.ask() возвращает None при Ctrl+C
        if result is None:
            return None

        return result

    except KeyboardInterrupt:
        # Сюда попадаем в двух случаях:
        # 1) Таймер истёк и послал SIGINT → автовыбор
        # 2) Пользователь реально нажал Ctrl+C → выход

        if timer is not None and not timer.cancelled:
            # Случай 1: таймер сработал — автовыбор
            timer.cancel()
            console.print()
            console.print(
                f"  [bold blue]⏱  Автозапуск:"
                f" {default_result[0]}[/bold blue]"
            )
            console.print()
            return default_result
        else:
            # Случай 2: реальный Ctrl+C — выход
            console.print()
            return None
