#!/usr/bin/env python3
"""
Desktop Control Helper for OpenClaw
Provides Python interface to desktop automation on Wayland/GNOME
"""

import subprocess
import time
import os
from pathlib import Path

# Default workspace directory
WORKSPACE_DIR = Path.home() / ".openclaw" / "workspace"
SCREENSHOTS_DIR = WORKSPACE_DIR / "screenshots"
DESKTOP_BIN = Path.home() / ".local" / "bin" / "openclaw-desktop"

# Ensure directories exist
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def screenshot(filename=None):
    """
    Take a screenshot and save to workspace.

    Args:
        filename: Optional filename, defaults to timestamp

    Returns:
        Path to the saved screenshot
    """
    if filename is None:
        filename = f"screenshot_{time.strftime('%Y%m%d_%H%M%S')}.png"

    output_path = SCREENSHOTS_DIR / filename

    cmd = [str(DESKTOP_BIN), "screenshot", str(output_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Screenshot failed: {result.stderr}")

    return str(output_path)


def mousemove(x, y):
    """
    Move mouse to absolute coordinates.

    Args:
        x: X coordinate (pixels from left)
        y: Y coordinate (pixels from top)
    """
    cmd = [str(DESKTOP_BIN), "mousemove", str(int(x)), str(int(y))]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Mouse move failed: {result.stderr}")


def click(button="left"):
    """
    Click the mouse.

    Args:
        button: "left", "right", "middle", or "double"
    """
    button_map = {
        "left": "click",
        "right": "rightclick",
        "middle": "click 0xC2",
        "double": "doubleclick"
    }

    cmd_str = button_map.get(button, "click")
    cmd = [str(DESKTOP_BIN)] + cmd_str.split()

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Click failed: {result.stderr}")


def type_text(text):
    """
    Type text.

    Args:
        text: Text to type
    """
    cmd = [str(DESKTOP_BIN), "type", text]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Type failed: {result.stderr}")


def copy_to_clipboard(text):
    """Copy text to clipboard"""
    cmd = [str(DESKTOP_BIN), "copy", text]
    subprocess.run(cmd, capture_output=True)


def paste_from_clipboard():
    """Read text from clipboard"""
    cmd = [str(DESKTOP_BIN), "paste"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


def click_at(x, y, button="left"):
    """
    Move to coordinates and click.

    Args:
        x: X coordinate
        y: Y coordinate
        button: Button to click (left/right/middle/double)
    """
    mousemove(x, y)
    time.sleep(0.05)  # Small delay for stability
    click(button)


def vision_loop(instruction, max_steps=5):
    """
    Execute a vision-based desktop automation task.

    This is a template for the vision loop pattern:
    1. Take screenshot
    2. Analyze (you implement this part with OpenClaw vision)
    3. Execute action
    4. Repeat

    Args:
        instruction: Description of what to accomplish
        max_steps: Maximum number of steps to take

    Returns:
        List of screenshot paths showing the progression
    """
    screenshots = []

    print(f"Starting vision loop: {instruction}")
    print(f"Max steps: {max_steps}")

    for step in range(max_steps):
        # Take screenshot
        path = screenshot(f"vision_step_{step:02d}.png")
        screenshots.append(path)
        print(f"Step {step}: Screenshot saved to {path}")

        # TODO: Analyze screenshot with OpenClaw vision
        # The user should look at this screenshot and decide next action
        print(f"  -> Analyze this screenshot and tell me the next action")

        # For now, we stop here - user needs to provide next action via chat
        break

    return screenshots


if __name__ == "__main__":
    # Demo/test mode
    print("Desktop Control Helper")
    print("=" * 50)
    print(f"Workspace: {WORKSPACE_DIR}")
    print(f"Screenshots: {SCREENSHOTS_DIR}")
    print(f"Desktop binary: {DESKTOP_BIN}")
    print()
    print("Available functions:")
    print("  screenshot(filename) - Take a screenshot")
    print("  mousemove(x, y) - Move mouse to coordinates")
    print("  click(button='left') - Click mouse button")
    print("  click_at(x, y, button='left') - Move and click")
    print("  type_text(text) - Type text")
    print("  copy_to_clipboard(text) - Copy to clipboard")
    print("  paste_from_clipboard() - Read from clipboard")
    print()
    print("Example:")
    print('  python3 -c "import desktop_helper; desktop_helper.screenshot()"')
