#!/bin/bash
# ──────────────────────────────────────────────────────────
# fallback.sh — Аварийный запуск если Python/PyDM сломался.
#
# Вызывается из config.fish когда main.py завершился с ошибкой.
# Предлагает простое текстовое меню без зависимостей.
# ──────────────────────────────────────────────────────────

set -euo pipefail

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  [PyDM Fallback] Python-меню не запустилось!        ║"
echo "║  Используем аварийный режим.                        ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ─── Собираем доступные DE/WM ─────────────────────────────

declare -a NAMES=()
declare -a COMMANDS=()

# Функция: добавить если команда существует
add_if_exists() {
    local cmd="$1"
    local name="$2"
    local binary="${cmd%% *}"  # Первое слово = бинарник

    if command -v "$binary" &>/dev/null; then
        NAMES+=("$name")
        COMMANDS+=("$cmd")
    fi
}

# Проверяем известные DE/WM
add_if_exists "startxfce4"           "XFCE"
add_if_exists "i3"                   "i3wm"
add_if_exists "sway"                 "Sway (Wayland)"
add_if_exists "hyprland"             "Hyprland (Wayland)"
add_if_exists "openbox-session"      "Openbox"
add_if_exists "bspwm"               "bspwm"
add_if_exists "dwm"                  "dwm"
add_if_exists "awesome"             "Awesome"
add_if_exists "startplasma-x11"     "KDE Plasma (X11)"
add_if_exists "gnome-session"       "GNOME"
add_if_exists "cinnamon-session"    "Cinnamon"
add_if_exists "mate-session"        "MATE"
add_if_exists "startlxqt"           "LXQt"
add_if_exists "qtile start"         "Qtile"
add_if_exists "herbstluftwm"        "herbstluftwm"
add_if_exists "xmonad"              "XMonad"
add_if_exists "startfluxbox"        "Fluxbox"
add_if_exists "icewm-session"       "IceWM"
add_if_exists "river"               "River (Wayland)"
add_if_exists "wayfire"             "Wayfire (Wayland)"
add_if_exists "labwc"               "LabWC (Wayland)"

TOTAL=${#NAMES[@]}

if [ "$TOTAL" -eq 0 ]; then
    echo "  Не найдено ни одной DE/WM!"
    echo "  Оставайся в TTY."
    echo ""
    exit 0
fi

# ─── Показываем меню ──────────────────────────────────────

echo "  Доступные DE/WM:"
echo ""

for i in $(seq 0 $((TOTAL - 1))); do
    NUM=$((i + 1))
    echo "    ${NUM}) ${NAMES[$i]}"
done

echo "    0) Продолжить в TTY"
echo ""

# ─── Читаем выбор ─────────────────────────────────────────

read -r -p "  Выбор [1-${TOTAL}, 0=TTY]: " CHOICE

# TTY
if [ "$CHOICE" = "0" ] || [ -z "$CHOICE" ]; then
    echo ""
    echo "  Оставайся в TTY. Приятной работы!"
    echo ""
    exit 0
fi

# Валидация
if ! [[ "$CHOICE" =~ ^[0-9]+$ ]]; then
    echo "  Некорректный ввод. Оставайся в TTY."
    exit 0
fi

INDEX=$((CHOICE - 1))

if [ "$INDEX" -lt 0 ] || [ "$INDEX" -ge "$TOTAL" ]; then
    echo "  Номер вне диапазона. Оставайся в TTY."
    exit 0
fi

SELECTED_NAME="${NAMES[$INDEX]}"
SELECTED_CMD="${COMMANDS[$INDEX]}"

echo ""
echo "  Запускаю ${SELECTED_NAME}..."

# ─── Определяем X11 или Wayland ──────────────────────────

WAYLAND_KEYWORDS="sway hyprland river labwc wayfire wayland"
IS_WAYLAND=false

SELECTED_LOWER=$(echo "$SELECTED_CMD" | tr '[:upper:]' '[:lower:]')
for kw in $WAYLAND_KEYWORDS; do
    if echo "$SELECTED_LOWER" | grep -q "$kw"; then
        IS_WAYLAND=true
        break
    fi
done

if [ "$IS_WAYLAND" = true ]; then
    export XDG_SESSION_TYPE=wayland
    exec $SELECTED_CMD
else
    # Создаём временный xinitrc
    XINITRC="$HOME/.xinitrc.pydm"
    cat > "$XINITRC" << XINITRC_EOF
#!/bin/sh
# Сгенерировано PyDM fallback
[ -f "\$HOME/.Xresources" ] && xrdb -merge "\$HOME/.Xresources"
[ -f "\$HOME/.xprofile" ] && . "\$HOME/.xprofile"
exec ${SELECTED_CMD}
XINITRC_EOF
    chmod 755 "$XINITRC"
    exec startx "$XINITRC"
fi
