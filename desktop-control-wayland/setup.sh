#!/usr/bin/env bash
# Setup script for the desktop-control-wayland skill
# Installs helper scripts into ~/.local/bin and ~/.openclaw/workspace

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_BIN="$HOME/.local/bin"
DEST_WORKSPACE="$HOME/.openclaw/workspace"

echo "=== OpenClaw Desktop Control Setup ==="

# Create directories
mkdir -p "$DEST_BIN"
mkdir -p "$DEST_WORKSPACE"

# Install screenshot backend
cp "$SCRIPT_DIR/openclaw-screenshot-gnome" "$DEST_BIN/openclaw-screenshot-gnome"
chmod +x "$DEST_BIN/openclaw-screenshot-gnome"
echo "Installed: $DEST_BIN/openclaw-screenshot-gnome"

# Install desktop CLI wrapper
cat > "$DEST_BIN/openclaw-desktop" << 'WRAPPER_EOF'
#!/bin/bash
# OpenClaw Desktop CLI - run desktop commands in graphical session context

# Get the environment from the gnome-session
for pid in $(pgrep -u $(id - u) gnome-session); do
    if [ -r /proc/$pid/environ ]; then
        eval "$(cat /proc/$pid/environ | tr '\0' '\n' | grep -E '^(DISPLAY|WAYLAND_DISPLAY|XDG_CURRENT_DESKTOP|DBUS_SESSION_BUS_ADDRESS|XDG_RUNTIME_DIR)=' | sed 's/^/export /')"
        break
    fi
done

# Set defaults if still not set
export DISPLAY="${DISPLAY:-:0}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export XDG_CURRENT_DESKTOP="${XDG_CURRENT_DESKTOP:-ubuntu:GNOME}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id - u)}"

# Ensure ydotoold is running for ydotool v1.x
if ! pgrep -x ydotoold > /dev/null 2>&1; then
    ydotoold &
    sleep 0.5
fi

CMD="$1"
shift

case "$CMD" in
    screenshot)
        OUTPUT="${1:-$HOME/.openclaw/workspace/screenshot_$(date +%Y%m%d_%H%M%S).png}"
        mkdir -p "$(dirname "$OUTPUT")"
        
        # Try GNOME Screencast service first (works on Wayland)
        if [ -x "$HOME/.local/bin/openclaw-screenshot-gnome" ]; then
            "$HOME/.local/bin/openclaw-screenshot-gnome" "$OUTPUT" 2>/dev/null && exit 0
        fi
        
        # Fallback to scrot (works on X11)
        if command -v scrot &> /dev/null; then
            scrot "$OUTPUT" && echo "$OUTPUT" && exit 0
        fi
        
        # Fallback to gnome-screenshot
        if command -v gnome-screenshot &> /dev/null; then
            timeout 5 gnome-screenshot -f "$OUTPUT" 2>/dev/null && echo "$OUTPUT" && exit 0
        fi
        
        echo "No screenshot backend available" >&2
        exit 1
        ;;
    mousemove)
        X="$1"
        Y="$2"
        ydotool mousemove "$X" "$Y"
        ;;
    click)
        ydotool click 0xC0
        ;;
    rightclick)
        ydotool click 0xC1
        ;;
    doubleclick)
        ydotool click 0xC0
        sleep 0.05
        ydotool click 0xC0
        ;;
    type)
        ydotool type "$*"
        ;;
    key)
        ydotool key "$1"
        ;;
    copy)
        echo "$*" | wl-copy
        ;;
    paste)
        wl-paste
        ;;
    *)
        echo "Usage: openclaw-desktop <command> [args...]"
        echo ""
        echo "Commands:"
        echo "  screenshot [output.png]  - Take screenshot"
        echo "  mousemove <x> <y>        - Move mouse to coordinates"
        echo "  click [button]           - Click (default: left)"
        echo "  rightclick               - Right click"
        echo "  doubleclick              - Double click"
        echo "  type <text>              - Type text"
echo "  key <keycode>            - Press key"
        echo "  copy <text>              - Copy to clipboard"
        echo "  paste                    - Paste from clipboard"
        exit 1
        ;;
esac
WRAPPER_EOF
chmod +x "$DEST_BIN/openclaw-desktop"
echo "Installed: $DEST_BIN/openclaw-desktop"

# Install Python helper
cp "$SCRIPT_DIR/desktop_helper.py" "$DEST_WORKSPACE/desktop_helper.py"
chmod +x "$DEST_WORKSPACE/desktop_helper.py"
echo "Installed: $DEST_WORKSPACE/desktop_helper.py"

# Create screenshots directory
mkdir -p "$DEST_WORKSPACE/screenshots"

echo ""
echo "=== Setup complete ==="
echo "Make sure ~/.local/bin is in your PATH."
echo "If not, add this to your ~/.bashrc:"
echo '  export PATH="$HOME/.local/bin:$PATH"'
echo ""
echo "Dependencies required:"
echo "  sudo apt install -y ydotool python3-dbus wl-clipboard scrot"
echo ""
echo "If ydotool fails with permission errors, add yourself to the input group:"
echo "  sudo usermod -a -G input \$USER"
echo "Then log out and back in."
