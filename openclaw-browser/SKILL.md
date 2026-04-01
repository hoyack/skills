---
name: openclaw-browser
description: Browser automation using OpenClaw's built-in browser tool. Use when the user wants to navigate websites, check emails, access web applications, take screenshots, fill forms, or perform any web-based tasks. This skill controls a real Chrome/Chromium browser with persistent profiles.
---

# OpenClaw Browser Automation

Control a real Chrome/Chromium browser through the OpenClaw CLI to navigate websites, interact with web apps, take screenshots, and extract information.

## Prerequisites

- Browser tool must be enabled in OpenClaw config (`browser.enabled: true`)
- DISPLAY environment variable must be set (typically `:0.0`)
- OpenClaw CLI must be in PATH

## Basic Workflow

Always follow this sequence:

1. **Check browser status** → Start if needed → Navigate to URL → Take snapshot/screenshot
2. **Use snapshot refs** to interact with elements (click, type, etc.)
3. **Take screenshots** to verify state

## Essential Commands

### Check and Start Browser
```bash
export DISPLAY=:0.0
openclaw browser status
openclaw browser start  # If not running
```

### Navigation
```bash
openclaw browser navigate <URL>
openclaw browser open <URL>  # Opens in new tab
```

### Page Information
```bash
openclaw browser snapshot           # AI-friendly page structure with refs
openclaw browser screenshot         # Capture screenshot
openclaw browser screenshot --full-page
openclaw browser tabs               # List open tabs
```

### Interacting with Elements
Use refs from snapshot output:

```bash
openclaw browser click <ref>
openclaw browser type <ref> "text to type" [--submit]
openclaw browser fill --fields '[{"ref":"1","value":"text"}]'
openclaw browser press Enter
openclaw browser scrollintoview <ref>
```

### Form Actions
```bash
openclaw browser select <ref> "Option1" "Option2"
openclaw browser upload /path/to/file
```

### Waiting
```bash
openclaw browser wait --text "Expected text"
openclaw browser wait --selector "css-selector"
sleep 2  # Simple wait for page load
```

### JavaScript Execution
```bash
openclaw browser evaluate --fn '(el) => el.textContent' --ref <ref>
openclaw browser evaluate --fn '() => document.title'
```

## Common Workflows

### Access Email (Proton Mail Example)
```bash
export DISPLAY=:0.0
openclaw browser start
openclaw browser navigate https://mail.proton.me
sleep 3
openclaw browser snapshot  # Check if logged in
# If login page appears, user must log in manually (persistent profile will remember)
openclaw browser screenshot
```

### Read First Email
```bash
# After navigating to inbox
openclaw browser snapshot | grep -A5 "region.*Unread\|region.*message"
# Click on the first email region ref
openclaw browser click <ref>
sleep 2
openclaw browser snapshot  # Read content
openclaw browser screenshot
```

### General Web Task Pattern
```bash
# 1. Start/navigate
export DISPLAY=:0.0
openclaw browser status || openclaw browser start
openclaw browser navigate <URL>
sleep 2

# 2. Get page state
openclaw browser snapshot
openclaw browser screenshot

# 3. Interact using refs from snapshot
openclaw browser click <ref>
openclaw browser type <ref> "value"

# 4. Verify result
openclaw browser screenshot
```

## Important Notes

- **Persistent profiles**: The `openclaw` profile keeps logins/cookies between sessions
- **Refs are dynamic**: Element refs change with each snapshot - always use latest
- **Timing**: Add `sleep 2-3` after navigation for pages to load
- **Snapshots**: Use `snapshot` output to understand page structure and find refs
- **Screenshots**: Always take screenshots to verify visual state

## Troubleshooting

**Browser won't start (display error)**
- Check `DISPLAY=:0.0` is set
- Ensure X server is running: `ps aux | grep Xorg`

**Element not found**
- Take new snapshot - refs may have changed
- Page might still be loading - add sleep

**Login required on every visit**
- Use `openclaw` profile (default)
- Check "Keep me signed in" when logging in manually
