# Setup — desktop-control-windows

Prerequisites and configuration for the Windows desktop control skill.

---

## What this skill does

Lets openclaw control your Windows 11 desktop (mouse, keyboard,
screenshots) from WSL via a PyAutoGUI MCP server running on the
Windows host. The agent sees your screen, reasons about what's visible,
clicks/types, and verifies the result — all through a perception-action
loop.

---

## Prerequisites

### 1. Python + PyAutoGUI on the Windows host

The MCP server runs **on Windows** (not WSL). You need Python with
PyAutoGUI installed on the Windows side.

```powershell
# In a Windows PowerShell or CMD terminal:
pip install pyautogui pillow
```

Verify it works:
```powershell
python -c "import pyautogui; print(pyautogui.size())"
# Should print: Size(width=1920, height=1080)
```

### 2. PyAutoGUI MCP server

You need an MCP server that exposes PyAutoGUI functions over HTTP.
This server must be running on the Windows host and accessible from
WSL over the network.

Start the server on Windows:
```powershell
python -m pyautogui_mcp --transport http --host 0.0.0.0 --port 8000
```

Install the MCP server package if not already installed:
```powershell
pip install pyautogui-mcp
```

Verify it's reachable from WSL:
```bash
curl http://<WINDOWS_IP>:8000/mcp
```

### 3. mcporter CLI (on WSL)

mcporter is the CLI tool that calls MCP servers. It must be installed
in your WSL environment.

```bash
which mcporter  # Should return a path
mcporter --help  # Should show usage
```

If not installed, install via npm:
```bash
npm install -g mcporter
```

### 4. Network connectivity

WSL must be able to reach the Windows host on the MCP server port.
Find your Windows host IP:

```powershell
# On Windows:
ipconfig | findstr "IPv4"
```

Or from WSL:
```bash
# The Windows host IP on the WSL vEthernet adapter
cat /etc/resolv.conf | grep nameserver | awk '{print $2}'
```

Test connectivity:
```bash
curl http://<WINDOWS_IP>:8000/mcp
```

---

## Configuration

### 1. Add the skill to openclaw.json

Edit `~/.openclaw/openclaw.json` and add the skill entry under
`skills.entries`:

```json
"desktop-control-windows": {
  "enabled": true,
  "env": {
    "DESKTOP_MCP_URL": "http://<WINDOWS_IP>:8000/mcp"
  }
}
```

Replace `<WINDOWS_IP>` with your Windows host's IP address.

### 2. Restart the gateway

```bash
openclaw gateway restart
```

### 3. Verify the skill is registered

```bash
openclaw skills list | grep desktop-control-windows
```

You should see: `✓ ready │ 📦 desktop-control-windows`

---

## Testing

### Quick connectivity test from WSL

```bash
# Configure mcporter alias (the skill does this automatically, but
# you can do it manually to test)
mcporter config add desktop --url "$DESKTOP_MCP_URL" --allow-http --yes

# Get screen size
mcporter call desktop.pyautogui_size

# Take a screenshot
./bin/desktop-screenshot /tmp/test.png
# Then open /tmp/test.png to verify you see your Windows desktop
```

### Ask openclaw to test

> "Use the desktop-control-windows skill to take a screenshot of
> my Windows desktop and describe what you see."

If the agent can see your desktop, everything is working.

---

## Troubleshooting

| Problem | Check |
|---------|-------|
| `mcporter list desktop` shows nothing | Run the config add command manually (see Testing above) |
| Screenshot returns empty/error | Is the MCP server running on Windows? Check with `curl` |
| Can't reach Windows IP from WSL | Check firewall rules; Windows Defender may block the port |
| PyAutoGUI fails on server | Run `python -c "import pyautogui"` on Windows to check |
| Screenshots work but clicks don't | PyAutoGUI may need to run as Administrator on Windows |
| Agent can't find the screenshot helper | Run `export PATH="$PATH:$(pwd)/bin"` from the skill directory |

---

## File structure

```
desktop-control-windows/
├── SKILL.md              ← Agent instructions (openclaw reads this)
├── SETUP.md              ← This file (human setup guide)
└── bin/
    └── desktop-screenshot  ← Screenshot capture helper script
```

- **SKILL.md** is what the openclaw agent reads. It contains the
  perception-action loop, API reference, and behavioral rules.
- **SETUP.md** (this file) is for humans setting up the prerequisites.
- The agent does NOT read SETUP.md — it only reads SKILL.md.
- **No config directory** — mcporter is configured dynamically via CLI
