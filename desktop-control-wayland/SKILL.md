---
name: desktop-control-wayland
description: 'Control the Ubuntu/GNOME desktop on Wayland. Take screenshots, move mouse, click, and type. Uses ydotool for input simulation and GNOME Screencast service for screenshots (Wayland-compatible). Requires: ydotool, python3-dbus, wl-clipboard installed. IMPORTANT: Must run from the graphical session (SSH sessions need the wrapper).'
metadata:
  {
    "openclaw":
      {
        "emoji": "🖥️",
        "requires": { "anyBins": ["ydotool", "python3"] },
        "install":
          [
            {
              "id": "ydotool",
              "kind": "apt",
              "package": "ydotool",
              "bins": ["ydotool"],
              "label": "Install ydotool for Wayland input simulation",
            },
            {
              "id": "python3-dbus",
              "kind": "apt",
              "package": "python3-dbus",
              "bins": [],
              "label": "Install python3-dbus for screenshot D-Bus calls",
            },
            {
              "id": "wl-clipboard",
              "kind": "apt",
              "package": "wl-clipboard",
              "bins": ["wl-copy", "wl-paste"],
              "label": "Install wl-clipboard for clipboard access",
            },
            {
              "id": "scrot",
              "kind": "apt",
              "package": "scrot",
              "bins": ["scrot"],
              "label": "Install scrot as X11 screenshot fallback",
            },
          ],
      },
  }
---

# Desktop Control (Wayland/GNOME)

Control your Ubuntu/GNOME desktop programmatically. Take screenshots, move the mouse, click, type text, and read the clipboard.

## How It Works

- **Screenshots**: Uses `org.gnome.Shell.Screencast` D-Bus service with a custom `videoconvert ! pngenc` GStreamer pipeline. This is the only reliable method on GNOME/Wayland because standard tools (`gnome-screenshot`, `grim`, X11 capture) fail due to compositor security restrictions.
- **Mouse/Keyboard**: Uses `ydotool` which works at the kernel level and supports both Wayland and X11.
- **Clipboard**: Uses `wl-clipboard` (`wl-copy` / `wl-paste`).

## Prerequisites

Install required tools:

```bash
sudo apt install -y ydotool python3-dbus wl-clipboard scrot
```

Add your user to the `input` group (needed for ydotool):

```bash
sudo usermod -a -G input $USER
# Log out and back in for this to take effect
```

## Setup

Run the setup script to install the helper tools into `~/.local/bin`:

```bash
bash skills/desktop-control-wayland/setup.sh
```

This installs:
- `~/.local/bin/openclaw-desktop` — main CLI wrapper
- `~/.local/bin/openclaw-screenshot-gnome` — screenshot backend for GNOME/Wayland
- `~/.openclaw/workspace/desktop_helper.py` — Python helper module

## Commands Reference

### Screenshot

Take a screenshot and save to workspace:

```bash
~/.local/bin/openclaw-desktop screenshot
```

With custom path:

```bash
~/.local/bin/openclaw-desktop screenshot /home/hoyack/.openclaw/workspace/my_screenshot.png
```

### Mouse Control

**Move mouse to coordinates (x, y):**

```bash
~/.local/bin/openclaw-desktop mousemove 960 540
```

**Left click:**

```bash
~/.local/bin/openclaw-desktop click
```

**Right click:**

```bash
~/.local/bin/openclaw-desktop rightclick
```

**Double click:**

```bash
~/.local/bin/openclaw-desktop doubleclick
```

### Typing

**Type text:**

```bash
~/.local/bin/openclaw-desktop type "Hello World"
```

### Clipboard

**Copy text to clipboard:**

```bash
~/.local/bin/openclaw-desktop copy "text to copy"
```

**Read clipboard:**

```bash
~/.local/bin/openclaw-desktop paste
```

## Vision Loop Pattern

The typical interaction loop for desktop automation:

1. **Take screenshot**
2. **Analyze with vision model** (send image to OpenClaw)
3. **Execute action** (click, type, etc.)
4. **Repeat**

### Example Workflow

```bash
# Step 1: Capture screen
~/.local/bin/openclaw-desktop screenshot /home/hoyack/.openclaw/workspace/current_state.png

# Step 2: Analyze with vision (in OpenClaw chat)
# "Look at current_state.png and tell me where to click to open Firefox"
# Response: "Click at coordinates (120, 45)"

# Step 3: Execute the action
~/.local/bin/openclaw-desktop mousemove 120 45
~/.local/bin/openclaw-desktop click

# Step 4: Wait and capture result
sleep 1
~/.local/bin/openclaw-desktop screenshot /home/hoyack/.openclaw/workspace/after_click.png
```

## Interactive Session Mode

For long-running desktop automation, start OpenClaw from within your graphical session:

1. Open a terminal in GNOME (Ctrl+Alt+T)
2. Run: `openclaw`
3. Now all desktop commands will work directly

## Important Notes

- **Session Context**: Screenshots and input require access to your graphical session. If using SSH, the helper script attempts to detect the graphical session environment.

- **Permissions**: ydotool uses `/dev/uinput` which requires the `input` group. A udev rule has been set up:
  ```
  sudo usermod -a -G input $USER
  ```
  You must log out and back in for group changes to take effect.

- **Screenshots on Wayland**: Standard tools like `gnome-screenshot`, `grim`, and X11 capture return black images or fail silently on GNOME/Wayland. The `openclaw-screenshot-gnome` script uses GNOME's internal `org.gnome.Shell.Screencast` service, which is the only reliable automated method.

- **Coordinates**: All coordinates are absolute screen positions. Common screen sizes:
  - 1920x1080 (Full HD): center is 960, 540
  - 2560x1440 (QHD): center is 1280, 720
  - 3840x2160 (4K): center is 1920, 1080

- **Timing**: Add small delays between actions when needed:
  ```bash
  ~/.local/bin/openclaw-desktop mousemove 500 300
  sleep 0.1
  ~/.local/bin/openclaw-desktop click
  ```

## Python Helper Script

For more complex automation, use the Python helper:

```python
# ~/.openclaw/workspace/desktop_helper.py
import sys
sys.path.insert(0, '/home/hoyack/.openclaw/workspace')
import desktop_helper

# Take screenshot
path = desktop_helper.screenshot()

# Move mouse and click
desktop_helper.click_at(500, 300)

# Type text
desktop_helper.type_text("Hello World")
```

## Safety

- Always verify coordinates before clicking
- Screenshots are saved to workspace for review
- Never share screenshots containing sensitive information
- Test mouse positions on non-destructive UI elements first
