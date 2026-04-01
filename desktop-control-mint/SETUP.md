# Setup — desktop-control-mint

Prerequisites and configuration for the Linux Mint desktop control skill.

---

## What this skill does

Lets OpenClaw control your Linux Mint desktop (mouse, keyboard,
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
# Should print: Size(width=1920, height=1080)
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
mcporter config add mint --url http://127.0.0.1:8765/mcp --allow-http --yes
```

### 2. Test connectivity

```bash
# Get screen size
mcporter call mint.pyautogui_size

# Take a screenshot
./bin/desktop-screenshot /tmp/test.png
```

---

## Testing

### Quick connectivity test

```bash
# Configure mcporter alias
cd ~/.openclaw/workspace/skills/desktop-control-mint
export PATH="$PATH:$PWD/bin"

# Get screen info
mcporter call mint.pyautogui_size

# Take screenshot
desktop-screenshot /tmp/test.png
```

### Ask OpenClaw to test

> "Use the desktop-control-mint skill to take a screenshot of my
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
ExecStart=%h/miniconda3/bin/python -m pyautogui_mcp --transport http --host 127.0.0.1 --port 8765
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
desktop-control-mint/
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
