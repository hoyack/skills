# Desktop Control Skill

Automated desktop control for Ubuntu/GNOME on Wayland. Take screenshots, move the mouse, click, type text, and read the clipboard.

## Problem Solved

GNOME on Wayland intentionally blocks standard screenshot tools for security reasons:
- `gnome-screenshot` exits successfully but creates no file
- `grim` fails because Mutter doesn't support `wlr-screencopy`
- X11 capture (`scrot`, `maim`, `PIL.ImageGrab`) returns a **black screen**
- The desktop portal requires the calling app to have window focus

This skill solves the problem by using GNOME's internal **`org.gnome.Shell.Screencast`** D-Bus service with a custom `videoconvert ! pngenc` GStreamer pipeline.

## Quick Start

```bash
# 1. Install dependencies
sudo apt install -y ydotool python3-dbus wl-clipboard scrot

# 2. Add user to input group (for ydotool)
sudo usermod -a -G input $USER

# 3. Log out and back in

# 4. Run setup
bash skills/desktop-control-wayland/setup.sh

# 5. Test
~/.local/bin/openclaw-desktop screenshot
```

## Files in This Skill

| File | Purpose |
|------|---------|
| `SKILL.md` | OpenClaw skill metadata and usage reference |
| `README.md` | This file — setup and architecture documentation |
| `setup.sh` | One-shot bash installer for helper scripts |
| `openclaw-screenshot-gnome` | Python screenshot backend using GNOME Screencast |
| `desktop_helper.py` | Python module for automation workflows |

## Architecture

```
┌─────────────────┐     ┌──────────────────────────┐     ┌─────────────────┐
│  OpenClaw Chat  │────▶│  ~/.local/bin/openclaw-  │────▶│  ydotool        │
│                 │     │  desktop (bash wrapper)  │     │  (mouse/keyboard)
└─────────────────┘     └──────────────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────────────┐
                        │  openclaw-screenshot-    │
                        │  gnome (python3)         │
                        └──────────────────────────┘
                               │
                               ▼ D-Bus
                        ┌──────────────────────────┐
                        │  org.gnome.Shell.        │
                        │  Screencast              │
                        └──────────────────────────┘
                               │
                               ▼ GStreamer
                        ┌──────────────────────────┐
                        │  videoconvert ! pngenc   │
                        └──────────────────────────┘
```

## CLI Reference

### `openclaw-desktop screenshot [path]`
Captures the full screen and saves it as PNG.

### `openclaw-desktop mousemove <x> <y>`
Moves the cursor to absolute coordinates.

### `openclaw-desktop click`
Left mouse click.

### `openclaw-desktop rightclick`
Right mouse click.

### `openclaw-desktop doubleclick`
Double left click.

### `openclaw-desktop type "text"`
Types the given text.

### `openclaw-desktop copy "text"`
Copies text to the clipboard.

### `openclaw-desktop paste`
Reads text from the clipboard.

## Python API

```python
import sys
sys.path.insert(0, '/home/hoyack/.openclaw/workspace')
import desktop_helper

# Screenshot
path = desktop_helper.screenshot("step1.png")

# Click at coordinates
desktop_helper.click_at(500, 300)

# Type text
desktop_helper.type_text("Hello World")
```

## Troubleshooting

### Screenshot fails with "Session creation inhibited"
A previous screencast session got stuck inside the Mutter compositor. **Log out and back in** to clear it.

### ydotool fails with uinput errors
You are not in the `input` group. Run `sudo usermod -a -G input $USER` and log out/back in.

### Black screenshots
If you're on X11, `scrot` will work. If you're on Wayland, make sure `openclaw-screenshot-gnome` is installed and executable.

## Requirements

- Ubuntu 24.04+ with GNOME on Wayland
- `ydotool`
- `python3-dbus`
- `wl-clipboard`
- `scrot` (X11 fallback)
