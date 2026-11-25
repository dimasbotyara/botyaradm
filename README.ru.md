<p align="center">
  <img src="assets/banner-ru.svg" alt="Баннер botyaradm" width="100%"/>
</p>

<p align="center">
  <a href="README.md">🇬🇧 English</a> | <strong>🇷🇺 Русский</strong>
</p>

---

# 🖥️ botyaradm

**botyaradm** — лёгкий, быстрый и уютный **TTY дисплей-менеджер / лаунчер сессий** для Linux на чистом Python с использованием встроенной библиотеки `curses`.

Работает напрямую на **системном Python** и не требует **ни одной внешней зависимости** — никаких `venv`, `pyenv`, `pip install` и поломок при обновлении Python или системы! 🚀

---

## ✨ Возможности

- 🧱 **Ноль сторонних зависимостей** — только стандартная библиотека Python (`curses`, `json`, `pathlib`, `configparser`, `shutil`, `pwd`).
- 🎨 **Стильный ASCII TUI на `curses` и 25 тем оформления** — аккуратные ASCII-рамки, логотип, теги типа сессии (`[X11]`, `[Wayland]`, `[TTY]`), часы и адаптивная вёрстка для больших терминалов и классического Linux TTY 80×24. Встроены 25 тем (**Ayu Dark/Mirage/Light**, **Gruvbox Dark/Material/Light**, **Pacman (Arch Linux)**, **Catppuccin**, **Dracula**, **Nord**, **Tokyo Night**, **One Dark**, **Monokai Pro**, **Solarized**, **Everforest**, **Kanagawa**, **Rosé Pine**, **Synthwave '84**, **Cyberpunk**, **Matrix**, **Oxocarbon**, **Amber CRT**, **Monochrome**) с поддержкой 256 цветов и fallback на 8 цветов!
- 🧙 **Мастер настройки при первом запуске (Setup Wizard)** — открывается автоматически при старте (или по клавише `w` / флагу `--setup`):
  - **Выбор пользователя**: если в системе больше одного пользователя, спрашивает, выбирать ли его при каждом входе или использовать одного по умолчанию (если пользователь один — выбирается автоматически).
  - **Запрос пароля**: по желанию проверяет системный пароль (через PAM / `su`) перед запуском меню.
  - **Живой предпросмотр тем**: переключение всех 25 тем в реальном времени прямо при прокрутке.
- 🧹 **Очистка терминала до и после работы** — очищает экран перед запуском TUI и после выхода или старта сессии.
- 🔍 **Автопоиск DE/WM** — сканирует `/usr/share/xsessions/*.desktop`, `/usr/share/wayland-sessions/*.desktop`, а также проверяет 35+ известных команд из `KNOWN_SESSIONS` в `PATH`.
- ⚡ **Умная история и сортировка** — атомарно сохраняет счётчик запусков и время последнего использования в `~/.config/botyaradm/history.json`, поднимая частые и недавние сессии наверх списка.
- ⏱️ **Живой таймер автозапуска** — автоматически запускает последнюю использованную DE/WM после настраиваемой паузы (по умолчанию `5` секунд) с ASCII-прогресс-баром (`[########..]`); отменяется любой клавишей.
- 💬 **100+ приветствий по времени суток** — неповторяющиеся случайные фразы для ночи, раннего утра, утра, дня, вечера и позднего вечера.
- 🚀 **Поддержка X11, Wayland и TTY**:
  - **X11**: создаёт `~/.xinitrc.botyaradm` (подгружая `~/.Xresources` и `~/.xprofile`, не трогая ваш `~/.xinitrc`) и передаёт управление через `startx`.
  - **Wayland**: выставляет `XDG_SESSION_TYPE=wayland` и запускает композитор напрямую.
  - **TTY**: аккуратно возвращает управление в shell.
- 🛡️ **Аварийный Bash-режим** — в комплекте есть [`fallback.sh`](fallback.sh) без зависимости от Python на случай сбоя.

---

## 📁 Структура проекта

```text
botyaradm/
├── assets/
│   ├── banner-en.svg    # 🎨 Английский баннер для README
│   └── banner-ru.svg    # 🎨 Русский баннер для README
├── main.py              # 🚪 Точка входа, очистка терминала и общий сценарий
├── menu.py              # 🖥️ Интерактивный curses TUI (сессии, выбор юзера, пароль)
├── setup_wizard.py      # 🧙 Мастер настройки с живым предпросмотром тем
├── themes.py            # 🎨 25 цветовых тем (256 цветов + 8-цветный TTY fallback)
├── auth.py              # 🔐 Поиск пользователей системы и проверка пароля (PAM/su)
├── settings.py          # 💾 Сохранение настроек (~/.config/botyaradm/settings.json)
├── tui_utils.py         # 🧹 Очистка терминала и общие утилиты curses
├── detector.py          # 🔍 Поиск .desktop файлов и бинарников в PATH
├── history.py           # 📊 Атомарная история запусков и сортировка
├── launcher.py          # 🚀 Запуск сессий (startx / Wayland / TTY)
├── greetings.py         # 💬 100+ приветствий по времени суток
├── config.py            # ⚙️ Настройки пользователя, таймаута, путей и TUI
├── fallback.sh          # 🛟 Аварийное bash-меню при ошибке Python
└── LICENSE              # 📄 Лицензия MIT
```

---

## 📦 Требования

- 🐍 **Python 3.10+** (системный Python со стандартным модулем `curses` — без `venv` и `pip`)
- 🖼️ **Для X11-сессий**: `startx` (`xorg-xinit`)
- 🪟 **Для Wayland-сессий**: установленный Wayland-композитор (например, `hyprland`, `sway`, `river`, `labwc`, `wayfire`)

---

## 📍 Куда рекомендовано устанавливать

Выбор пути зависит от того, как вы планируете запускать `botyaradm`:

| Сценарий | Рекомендуемый путь | Почему так удобнее |
| --- | --- | --- |
| 👤 **Один пользователь / Autologin на `tty1`** *(рекомендуется)* | `~/.config/botyaradm` | Всё хранится в вашей пользовательской папке конфигов рядом с `~/.config/fish`, не нужен `sudo`. |
| 👥 **Несколько пользователей / Общесистемный DM** | `/opt/botyaradm` | Единая установка, доступная всем пользователям и системному `systemd`-сервису. |

---

## 🛠️ Туториал по установке и автозапуску

### Шаг 1: Скачивание проекта

Для одного пользователя (рекомендуемый вариант):

```bash
git clone https://github.com/dimasbotyara/botyaradm.git ~/.config/botyaradm
chmod +x ~/.config/botyaradm/fallback.sh
```

Проверьте, что системный Python доступен (никакой `.venv` или `pyenv` создавать не нужно!):

```bash
python3 --version
```

> 💡 При первом запуске автоматически откроется **Setup Wizard**: он настроит выбор пользователя, запрос пароля и тему оформления. Открыть мастер снова можно в любой момент клавишей `w` из главного меню или командой `python3 ~/.config/botyaradm/main.py --setup`.

---

### Способ 1: Autologin на `tty1` + Fish *(как на Arch Linux, рекомендуется)* 🐟

Классический и максимально удобный вариант: `systemd` автоматически логинит вас в `tty1`, а `fish` сразу запускает `botyaradm` (с аварийным откатом на `fallback.sh` и `startx`).

#### 1.1 Настройка автологина на `tty1` через `systemd`

Выполните:

```bash
sudo systemctl edit getty@tty1
```

В открывшемся файле пропишите (заменив `your_username` на имя вашего пользователя):

```ini
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin your_username --noclear %I $TERM
```

#### 1.2 Настройка `~/.config/fish/config.fish`

Добавьте чистый блок автозапуска на `tty1` (без лишних путей `pyenv`/`.venv`):

```fish
if status is-interactive
    # Команды для интерактивных сессий
end

if status is-login
    if test -z "$DISPLAY" -a -z "$WAYLAND_DISPLAY" -a "$XDG_VTNR" = "1"
        set -l BOTYARADM_DIR "$HOME/.config/botyaradm"
        set -l BOTYARADM_MAIN "$BOTYARADM_DIR/main.py"
        set -l BOTYARADM_FALLBACK "$BOTYARADM_DIR/fallback.sh"

        if command -q python3; and test -f "$BOTYARADM_MAIN"
            # Запускаем TUI-меню на системном Python
            python3 "$BOTYARADM_MAIN"

            # Если Python упал с ошибкой — запускаем bash fallback
            if test $status -ne 0; and test -f "$BOTYARADM_FALLBACK"
                bash "$BOTYARADM_FALLBACK"
            end
        else if test -f "$BOTYARADM_FALLBACK"
            # Python не найден — запускаем bash fallback
            bash "$BOTYARADM_FALLBACK"
        else
            # Совсем ничего нет — классический startx
            echo "[botyaradm] Ни Python, ни fallback.sh не найдены."
            echo "[botyaradm] Запускаю startx напрямую..."
            exec startx
        end
    end
end
```

---

### Способ 2: Autologin на `tty1` + Bash / Zsh 🐚

Если вы используете `bash` (`~/.bash_profile`) или `zsh` (`~/.zprofile`), включите автологин `getty@tty1` (см. шаг 1.1 выше) и добавьте:

```bash
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ] && [ "${XDG_VTNR:-0}" -eq 1 ]; then
    BOTYARADM_DIR="$HOME/.config/botyaradm"
    if command -v python3 >/dev/null 2>&1 && [ -f "$BOTYARADM_DIR/main.py" ]; then
        python3 "$BOTYARADM_DIR/main.py" || bash "$BOTYARADM_DIR/fallback.sh"
    elif [ -f "$BOTYARADM_DIR/fallback.sh" ]; then
        bash "$BOTYARADM_DIR/fallback.sh"
    else
        exec startx
    fi
fi
```

---

### Способ 3: Системный `systemd`-сервис (без shell-autologin) ⚙️

Если хочется использовать `botyaradm` как **полноценный многопользовательский дисплей-менеджер** на `tty1` (особенно удобно вместе с выбором пользователя и проверкой пароля в Setup Wizard):

1. Установите проект в `/opt/botyaradm`:
   ```bash
   sudo git clone https://github.com/dimasbotyara/botyaradm.git /opt/botyaradm
   sudo chmod +x /opt/botyaradm/fallback.sh
   ```
2. Создайте файл `/etc/systemd/system/botyaradm.service`:
   ```ini
   [Unit]
   Description=botyaradm TTY Display Manager
   After=systemd-user-sessions.service plymouth-quit-wait.service
   Conflicts=getty@tty1.service

   [Service]
   Type=idle
   ExecStart=/usr/bin/python3 /opt/botyaradm/main.py
   StandardInput=tty
   StandardOutput=tty
   TTYPath=/dev/tty1
   TTYReset=yes
   TTYVHangup=yes
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```
3. Включите сервис (убедитесь, что другие DM вроде `gdm`/`sddm`/`lightdm` отключены):
   ```bash
   sudo systemctl disable getty@tty1
   sudo systemctl enable botyaradm.service
   ```

---

### Способ 4: Ручной запуск из любого TTY 💻

Запустить `botyaradm` вручную можно из любой консоли (TTY):

```bash
python3 ~/.config/botyaradm/main.py
```

При желании можно добавить короткий алиас в конфиг оболочки (например, для Fish: `alias dm="python3 ~/.config/botyaradm/main.py"`).

---

## ⌨️ Управление

| Клавиша | Действие |
| --- | --- |
| `↑` / `↓` или `k` / `j` | Перемещение по списку (с зацикливанием) |
| `1` – `9`, `0` | Быстрый запуск пунктов 1–10 |
| `Home` / `End` или `g` / `G` | Переход в начало / конец списка |
| `PgUp` / `PgDn` | Пролистывание на страницу вверх / вниз |
| `Enter` | Запустить выбранную DE/WM |
| `w` | Повторно открыть мастер настройки (юзер, пароль, тема) |
| `Любая клавиша` (при таймере) | Отменить автозапуск |
| `q` / `Esc` / `Ctrl+C` | Выйти в TTY |

---

## ⚙️ Конфигурация (`config.py`)

Основные параметры в [`config.py`](config.py):

- `USERNAME` — запасное имя пользователя до прохождения мастера настройки.
- `AUTO_SELECT_TIMEOUT` — задержка в секундах перед автозапуском последней сессии (`0` отключает автозапуск).
- `SHOW_ASCII_LOGO` — показывать или скрывать ASCII-логотип в шапке.
- `SHOW_SESSION_TYPE` — отображать бейджи `[X11]`, `[Wayland]`, `[TTY]`.
- `SHOW_STATUS_BAR` — отображать строку с временем, пользователем и числом сессий.
- `CLEAR_TERMINAL` — очистка терминала до запуска и после выхода (`True` / `False`).
- `DEFAULT_THEME` — тема по умолчанию до прохождения мастера настройки (`"botyaradm_classic"`).
- `KNOWN_SESSIONS` — словарь резервных команд DE/WM на случай отсутствия `.desktop` файлов.

---

## 📄 Лицензия

Проект распространяется под лицензией [MIT](LICENSE).
