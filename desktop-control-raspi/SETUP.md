# Setup — desktop-control-raspi

Prerequisites and configuration for the Raspberry Pi / LXDE desktop control skill.

---

## What this skill does

Lets OpenClaw control your Raspberry Pi desktop (mouse, keyboard,
screenshots) from a local PyAutoGUI MCP server. The agent sees your
screen, reasons about what's visible, clicks/types, and verifies the
result — all through a perception-action loop.

---

## Prerequisites

### 1. Python + PyAutoGUI

You need Python with PyAutoGUI installed.

```bash
pip install pyautogui pillow
```

Verify it works:
```bash
python3 -c "import pyautogui; print(pyautogui.size())"
# Should print: Size(width=1920, height=1080) (or your screen resolution)
```

### 2. PyAutoGUI MCP server (by chigwell)

Install the HTTP-enabled MCP server:

```bash
pip install pyautogui-mcp
```

### 3. mcporter CLI

mcporter is the CLI tool that calls MCP servers.

```bash
npm install -g mcporter
```

Verify:
```bash
mcporter --version
```

### 4. Start the MCP server

```bash
python3 -m pyautogui_mcp --transport http --host 127.0.0.1 --port 8765 &
```

Verify it's running:
```bash
curl http://127.0.0.1:8765/mcp
```

---

## Configuration

### 1. Configure mcporter alias

```bash
mcporter config add desktop --url http://127.0.0.1:8765/mcp --allow-http --yes
```

### 2. Test connectivity

```bash
# Get screen size
mcporter call desktop.pyautogui_size

# Take a screenshot
./bin/desktop-screenshot /tmp/test.png
```

---

## Testing

### Quick connectivity test

```bash
# Configure mcporter alias
cd ~/.openclaw/workspace/skills/desktop-control-raspi
export PATH="$PATH:$PWD/bin"

# Get screen info
mcporter call desktop.pyautogui_size

# Take screenshot
desktop-screenshot /tmp/test.png
```

### Ask OpenClaw to test

> "Use the desktop-control-raspi skill to take a screenshot of my
> desktop and describe what you see."

If the agent can see your desktop, everything is working.

---

## Auto-start MCP server (optional)

Create a systemd user service to auto-start the MCP server:

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/pyautogui-mcp.service << 'EOF'
[Unit]
Description=PyAutoGUI MCP Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 -m pyautogui_mcp --transport http --host 127.0.0.1 --port 8765
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable pyautogui-mcp.service
systemctl --user start pyautogui-mcp.service
```

---

## File structure

```
desktop-control-raspi/
├── SKILL.md              ← Agent instructions (OpenClaw reads this)
├── SETUP.md              ← This file (human setup guide)
└── bin/
    └── desktop-screenshot  ← Screenshot capture helper script
```

- **SKILL.md** is what the OpenClaw agent reads. It contains the
  perception-action loop, API reference, and behavioral rules.
- **SETUP.md** (this file) is for humans setting up the prerequisites.
- The agent does NOT read SETUP.md — it only reads SKILL.md.
- **No config directory** — mcporter is configured dynamically via CLI

---

## Raspberry Pi / LXDE Specific Notes

### Display Environment

This skill is designed for **X11-based desktops**. Raspberry Pi OS
(Legacy/Bullseye) uses LXDE on X11 by default. If you're using
Wayland (Bookworm with labwc), you may need to switch to X11:

```bash
# Check your session type
echo $XDG_SESSION_TYPE

# If it says "wayland", you can switch to X11 in raspi-config:
sudo raspi-config
# Navigate to: Advanced Options > Wayland > X11
```

### LXDE Applications

Common LXDE applications on Raspberry Pi:

| App | Command | Description |
|-----|---------|-------------|
| Terminal | `lxterminal` | LXDE terminal emulator |
| File Manager | `pcmanfm` | Lightweight file manager |
| Text Editor | `mousepad` | Simple text editor |
| Browser | `chromium-browser` | Chromium web browser |
| Calculator | `galculator` or `gnome-calculator` | Calculator |
| Image Viewer | `gpicview` | Lightweight image viewer |

### Screen Resolution

Raspberry Pi screens vary. Common resolutions:
- Official 7" touchscreen: 800x480
- HDMI monitors: 1920x1080, 1280x720
- VNC sessions: varies

The skill auto-detects screen size via `pyautogui_size`.
