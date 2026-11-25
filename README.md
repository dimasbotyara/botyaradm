<p align="center">
  <img src="assets/banner-en.svg" alt="botyaradm banner" width="100%"/>
</p>

<p align="center">
  <strong>🇬🇧 English</strong> | <a href="README.ru.md">🇷🇺 Русский</a>
</p>

---

# 🖥️ botyaradm

**botyaradm** is a lightweight, fast, and cozy **TTY display manager / session launcher** for Linux written in pure Python using the built-in `curses` library.

It runs directly on **system Python** with **zero third-party dependencies** — no `venv`, no `pyenv`, no `pip install`, and nothing to break when Python or system packages upgrade! 🚀

---

## ✨ Features

- 🧱 **Zero External Dependencies** — built purely on the Python standard library (`curses`, `json`, `pathlib`, `configparser`, `shutil`, `pwd`).
- 🎨 **Clean ASCII `curses` TUI & 25 Color Themes** — renders crisp ASCII box borders, logo, session type badges (`[X11]`, `[Wayland]`, `[TTY]`), live clock, and adaptive layout for both large terminals and classic 80×24 Linux TTYs. Includes 25 built-in themes (**Ayu Dark/Mirage/Light**, **Gruvbox Dark/Material/Light**, **Pacman (Arch Linux)**, **Catppuccin**, **Dracula**, **Nord**, **Tokyo Night**, **One Dark**, **Monokai Pro**, **Solarized**, **Everforest**, **Kanagawa**, **Rosé Pine**, **Synthwave '84**, **Cyberpunk**, **Matrix**, **Oxocarbon**, **Amber CRT**, **Monochrome**) with 256-color and 8-color TTY fallback!
- 🧙 **Interactive First-Run Setup Wizard** — automatically launches on first run (or anytime via `w` / `--setup`):
  - **User selection mode**: if multiple human users exist, choose whether to always ask on login or pick a default user (with 1 user, it is selected automatically).
  - **Password prompt**: optionally require system password verification (via PAM / `su`) before showing the session menu.
  - **Live theme preview**: browse all 25 themes with instant live recoloring.
- 🧹 **Clean Terminal Before & After** — clears the terminal before starting the TUI and cleanly clears it upon exiting or launching a session.
- 🔍 **Automatic DE/WM Detection** — scans `/usr/share/xsessions/*.desktop`, `/usr/share/wayland-sessions/*.desktop`, and falls back to 35+ known DE/WM binaries in `PATH` (`KNOWN_SESSIONS`).
- ⚡ **Smart History & Sorting** — atomically tracks launch counts and timestamps in `~/.config/botyaradm/history.json`, placing your most recently and frequently used sessions at the top.
- ⏱️ **Live Auto-Launch Countdown** — automatically starts your last used DE/WM after a configurable timeout (default `5` seconds) with a real-time ASCII progress bar (`[########..]`); press any key to cancel.
- 💬 **100+ Time-of-Day Greetings** — displays non-repeating Russian greetings tailored to night, early morning, morning, day, evening, and late evening.
- 🚀 **X11, Wayland & TTY Support**:
  - **X11**: generates `~/.xinitrc.botyaradm` (loading `~/.Xresources` and `~/.xprofile` without touching your `~/.xinitrc`) and replaces the process via `startx`.
  - **Wayland**: exports `XDG_SESSION_TYPE=wayland` and executes the compositor directly.
  - **TTY**: drops cleanly back into your shell anytime.
- 🛡️ **Built-in Bash Emergency Fallback** — includes [`fallback.sh`](fallback.sh) with zero Python dependencies in case Python fails to start.

---

## 📁 Project Structure

```text
botyaradm/
├── assets/
│   ├── banner-en.svg    # 🎨 English README banner
│   └── banner-ru.svg    # 🎨 Russian README banner
├── main.py              # 🚪 Entry point, terminal clear & flow orchestration
├── menu.py              # 🖥️ Interactive curses TUI (sessions, user picker, password)
├── setup_wizard.py      # 🧙 First-run setup wizard with live theme preview
├── themes.py            # 🎨 25 color themes (256-color + 8-color TTY fallback)
├── auth.py              # 🔐 System user detection & PAM/su password check
├── settings.py          # 💾 Persistent settings (~/.config/botyaradm/settings.json)
├── tui_utils.py         # 🧹 Terminal clearing & shared curses helpers
├── detector.py          # 🔍 .desktop scanner & X11/Wayland/PATH detection
├── history.py           # 📊 Atomic launch history & session sorting
├── launcher.py          # 🚀 Session launcher (startx / Wayland / TTY)
├── greetings.py         # 💬 100+ time-of-day greetings
├── config.py            # ⚙️ User, timeout, paths, and curses UI settings
├── fallback.sh          # 🛟 Emergency bash menu if Python fails
└── LICENSE              # 📄 MIT License
```

---

## 📦 Requirements

- 🐍 **Python 3.10+** (system Python with standard `curses` module — no `venv` or `pip` needed)
- 🖼️ **For X11 sessions**: `startx` (`xorg-xinit`)
- 🪟 **For Wayland sessions**: your Wayland compositor (e.g. `hyprland`, `sway`, `river`, `labwc`, `wayfire`)

---

## 📍 Where to Install (Recommended Paths)

Choose the installation directory based on how you use your machine:

| Scenario | Recommended Path | Notes |
| --- | --- | --- |
| 👤 **Single user / TTY1 autologin** *(recommended)* | `~/.config/botyaradm` | Keeps everything neat inside your user config directory alongside `~/.config/fish`, no `sudo` required. |
| 👥 **Multi-user / System-wide DM** | `/opt/botyaradm` | Accessible by all system users and root `systemd` services. |

---

## 🛠️ Installation & Autologin Tutorial

### Step 1: Clone the Repository

For a single-user setup (recommended):

```bash
git clone https://github.com/dimasbotyara/botyaradm.git ~/.config/botyaradm
chmod +x ~/.config/botyaradm/fallback.sh
```

Verify system Python works (no virtual environment required):

```bash
python3 --version
```

> 💡 On the first launch, `botyaradm` will automatically start the **Setup Wizard** to configure user selection, optional password prompt, and your favorite theme. You can always re-open it later by pressing `w` in the menu or running `python3 ~/.config/botyaradm/main.py --setup`.

---

### Method 1: TTY1 Autologin + Fish Shell *(Recommended)* 🐟

This is the cleanest setup for personal workstations (e.g. Arch Linux): `systemd` logs you into `tty1` automatically, and `fish` launches `botyaradm` on login.

#### 1.1 Enable `tty1` autologin in `systemd`

Run:

```bash
sudo systemctl edit getty@tty1
```

Add the following (replace `your_username` with your Linux username):

```ini
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin your_username --noclear %I $TERM
```

#### 1.2 Add `botyaradm` to `~/.config/fish/config.fish`

```fish
if status is-interactive
    # Commands to run in interactive sessions can go here
end

if status is-login
    if test -z "$DISPLAY" -a -z "$WAYLAND_DISPLAY" -a "$XDG_VTNR" = "1"
        set -l BOTYARADM_DIR "$HOME/.config/botyaradm"
        set -l BOTYARADM_MAIN "$BOTYARADM_DIR/main.py"
        set -l BOTYARADM_FALLBACK "$BOTYARADM_DIR/fallback.sh"

        if command -q python3; and test -f "$BOTYARADM_MAIN"
            python3 "$BOTYARADM_MAIN"

            # If Python exited with an error, fall back to bash menu
            if test $status -ne 0; and test -f "$BOTYARADM_FALLBACK"
                bash "$BOTYARADM_FALLBACK"
            end
        else if test -f "$BOTYARADM_FALLBACK"
            bash "$BOTYARADM_FALLBACK"
        else
            echo "[botyaradm] Neither Python nor fallback.sh found."
            echo "[botyaradm] Starting startx directly..."
            exec startx
        end
    end
end
```

---

### Method 2: TTY1 Autologin + Bash / Zsh 🐚

If you use `bash` (`~/.bash_profile`) or `zsh` (`~/.zprofile`), enable `getty@tty1` autologin as shown above and add:

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

### Method 3: System-Wide `systemd` Service (No Shell Autologin) ⚙️

If you want `botyaradm` to act as a **true multi-user display manager** on `tty1` (great with the Setup Wizard's *Ask user on login* + *Password prompt* options):

1. Install into `/opt/botyaradm`:
   ```bash
   sudo git clone https://github.com/dimasbotyara/botyaradm.git /opt/botyaradm
   sudo chmod +x /opt/botyaradm/fallback.sh
   ```
2. Create `/etc/systemd/system/botyaradm.service`:
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
3. Enable the service (make sure no conflicting DM like `gdm`/`sddm`/`lightdm` is enabled):
   ```bash
   sudo systemctl disable getty@tty1
   sudo systemctl enable botyaradm.service
   ```

---

### Method 4: Manual Launch from Any TTY 💻

You can always launch `botyaradm` manually whenever you're in a TTY:

```bash
python3 ~/.config/botyaradm/main.py
```

Or add a convenient alias in your shell config (`fish`: `alias dm="python3 ~/.config/botyaradm/main.py"`).

---

## ⌨️ Controls

| Key | Action |
| --- | --- |
| `↑` / `↓` or `k` / `j` | Move selection up / down (with wrap-around) |
| `1` – `9`, `0` | Quick-launch items 1–10 immediately |
| `Home` / `End` or `g` / `G` | Jump to first / last item |
| `PgUp` / `PgDn` | Scroll page up / down |
| `Enter` | Launch selected DE/WM |
| `w` | Re-open Setup Wizard (user, password, theme) |
| `Any key` (during timer) | Cancel auto-launch countdown |
| `q` / `Esc` / `Ctrl+C` | Exit cleanly into TTY |

---

## ⚙️ Configuration (`config.py`)

Key options in [`config.py`](config.py):

- `USERNAME` — fallback name used before Setup Wizard selects a system user.
- `AUTO_SELECT_TIMEOUT` — seconds before auto-launching the last used session (`0` disables auto-launch).
- `SHOW_ASCII_LOGO` — toggle the ASCII header banner in the TUI.
- `SHOW_SESSION_TYPE` — show `[X11]`, `[Wayland]`, and `[TTY]` tags.
- `SHOW_STATUS_BAR` — show clock, username, and detected session count.
- `CLEAR_TERMINAL` — clear the terminal before startup and after exit (`True` / `False`).
- `DEFAULT_THEME` — default theme ID before running the Setup Wizard (`"botyaradm_classic"`).
- `KNOWN_SESSIONS` — fallback command-to-name dictionary for DEs/WMs without `.desktop` files.

---

## 📄 License

Licensed under the [MIT License](LICENSE).
