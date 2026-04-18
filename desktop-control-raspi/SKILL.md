---
name: desktop-control-raspi
version: 1.0.0
description: >
  Control the Raspberry Pi (LXDE) desktop via PyAutoGUI MCP. Implements a
  screenshot-reason-act-verify loop: take a screenshot, analyze what is
  visible, determine where to click or type, act, then immediately
  screenshot again to assess the result before proceeding. Use when the
  user asks to click, type, automate, or interact with any Linux GUI.
tags: [linux, raspberry-pi, raspi, lxde, desktop, automation, pyautogui, mcp, mouse, keyboard]
metadata:
  clawdbot:
    emoji: 🖥️
    requires:
      bins:
        - mcporter
env:
  DESKTOP_MCP_URL:
    description: URL of the PyAutoGUI MCP server running on localhost
    default: http://127.0.0.1:8765/mcp
---

# Desktop control — Raspberry Pi / LXDE (PyAutoGUI MCP)

Controls the Raspberry Pi desktop (LXDE) from OpenClaw via a PyAutoGUI MCP
server running locally. All commands run via `mcporter call` in a bash shell.
You MUST use bash to run these commands — they are CLI commands, not
special tool calls.

---

## Setup (run once per session)

### 1. Start the MCP server (if not already running)

```bash
# Check if server is running
curl -s http://127.0.0.1:8765/mcp > /dev/null && echo "Server running" || echo "Server not running"

# Start the server (if needed)
python3 -m pyautogui_mcp --transport http --host 127.0.0.1 --port 8765 &
sleep 2
```

### 2. Configure the mcporter server alias

Check if the `desktop` mcporter alias exists, and create it if missing:
```bash
mcporter list desktop 2>&1 || mcporter config add desktop --url "${DESKTOP_MCP_URL:-http://127.0.0.1:8765/mcp}" --allow-http --yes
```

### 3. Verify connectivity and get screen dimensions

```bash
mcporter call desktop.pyautogui_size
```

Returns `{"width": 1920, "height": 1080}` (or similar). Record these
values — you will need them for coordinate reasoning.

### 4. Add screenshot helper to PATH

```bash
export PATH="$PATH:$(dirname "$(find ~/.openclaw/workspace/skills/desktop-control-raspi/bin -name desktop-screenshot -type f 2>/dev/null)")"
```

### 5. Take an initial screenshot to understand current desktop state

```bash
desktop-screenshot /tmp/desktop_screenshot.png
```
Then read the saved image file to view it.

---

## Architecture — how calls work

Each `mcporter call` is an **independent HTTP request** to the MCP
server. The server runs PyAutoGUI locally. This has critical
implications:

- Each call is atomic and stateless. There is no session persistence
  between calls.
- **Mouse button state (mouseDown) does NOT persist** across separate
  calls. A `mouseDown` in one call is effectively released before the
  next call's `moveTo` executes. Only use `mouseDown`/`mouseUp` within
  the context of a single operation (like shape tools where the OS
  handles the drag internally).
- **Keyboard modifier state (keyDown) does NOT persist** across calls
  for the same reason. Use `hotkey` for key combinations.
- The `dragTo` and `drag` functions are atomic — they perform the full
  mouseDown → move → mouseUp within a single call. These are the
  reliable way to drag.

---

## Perception-Action Loop (REQUIRED)

Every desktop interaction MUST follow this loop. Never execute a blind
sequence of clicks. Every action must be preceded and followed by
observation.

### The two-pass observation model

A full-screen screenshot is 1920x1080 pixels but is displayed to you
at roughly 480px wide — a **4x downscale**. At that scale, toolbar
icons are ~8px across and individual buttons are indistinguishable.
You CANNOT reliably identify small UI elements from a full-screen
screenshot alone.

Every observation therefore requires **two passes**:

1. **SURVEY** — full-screen screenshot. Gives you the overall layout:
   which app is open, where the toolbar is, where the canvas is,
   roughly where menus and buttons are.
2. **ZOOM** — cropped region screenshot of the area you need to
   interact with. Gives you pixel-level detail: which icon is which,
   which tool is selected (highlighted), what text says, exact
   coordinates for clicking.

**You MUST zoom before clicking any UI element smaller than ~100px.**
Toolbars, ribbons, menus, dialog buttons, and icon grids all require
a zoom pass. Only large, unambiguous targets (a maximized canvas, a
large dialog button, the desktop background) can be clicked from a
survey screenshot alone.

### The loop

```
LOOP:
  1. SURVEY    — full-screen screenshot → read the image
                 Identify: which app, window layout, approximate
                 location of the target area
  2. ZOOM      — cropped region screenshot of the target area
                 Identify: exact element positions, which tool/button
                 is selected, text labels, icon details
                 You may need MULTIPLE zooms if the area is complex
                 (e.g. zoom toolbar, then zoom a subsection of it)
  3. REASON    — from the zoomed view, determine exact coordinates
                 for the next action. State them explicitly.
  4. PLAN      — decide the single next action
  5. ACT       — execute that one action via mcporter call
  6. VERIFY    — zoom into the affected area again to confirm
                 the action had the expected effect
                 (e.g. did the tool highlight change? did the
                 shape appear on the canvas?)
                 if yes → continue to next step
                 if no  → re-examine and adjust
  REPEAT until the task is complete
```

### Zoom requirements by target type

| Target                        | Zoom required? | Recommended region size |
|-------------------------------|----------------|------------------------|
| Toolbar/ribbon icons          | **YES always** | 200-400px wide strip   |
| Menu items                    | **YES always** | 200-300px around menu  |
| Dialog buttons (OK/Cancel)    | **YES always** | 300px around dialog    |
| Color palette / swatches      | **YES always** | 200px around palette   |
| Canvas / large content area   | Only to verify | 300-400px around drawn content |
| Desktop background            | No             | —                      |
| Full-window click (to focus)  | No             | —                      |

### The toolbar mapping procedure

When you need to interact with a toolbar or ribbon (e.g. selecting a
tool, clicking a button in any app), follow this procedure:

1. **Survey** — full-screen screenshot to find the approximate toolbar
   position (e.g. "toolbar appears to be at y=55-110, x=0-800").
2. **Zoom the full toolbar** — take a region screenshot spanning the
   entire toolbar width with ~50px height.
   ```bash
   desktop-screenshot /tmp/toolbar.png --region 0,55,900,60
   ```
3. **Read the zoomed toolbar image.** Identify and label each visible
   section and icon. State what you see:
   "I see: File | Edit | [Save(highlighted)] [Open] | Tools..."
4. **If icons are still ambiguous**, zoom further into just that
   section (e.g. a 100x40px crop of just the tools area).
5. **Map coordinates.** For each icon you identified, note its
   approximate screen coordinate (region_x + crop_offset_x).
6. **Click the target** using the mapped coordinate.
7. **Zoom the toolbar again** to verify the correct tool is now
   highlighted/selected.

### When you may skip the zoom pass

- Clicking a large, unambiguous area (full canvas, desktop background)
- Re-clicking a coordinate you already verified in a previous zoom
- Batching `dragTo` calls that form a single drawn shape
- Setup commands (configuring mcporter, setting PATH)
- A `hotkey` immediately followed by a `sleep`

---

## Screenshots (primary observation tool)

Screenshots are the foundation of this skill. The MCP server returns
base64-encoded image data. Because full-screen screenshots exceed shell
output limits (~64KB), you MUST use the helper script.

### Using the helper script (REQUIRED)

The helper script `bin/desktop-screenshot` captures, decodes, and saves
screenshots in one step. Always use it instead of calling
`pyautogui_screenshot_encoded` directly.

```bash
# SURVEY: full screen screenshot
desktop-screenshot /tmp/desktop_screenshot.png

# ZOOM: cropped region for detail (x, y, width, height)
desktop-screenshot /tmp/toolbar.png --region 0,55,900,60
desktop-screenshot /tmp/canvas_check.png --region 750,450,300,200

# JPEG for faster capture when quality isn't critical
desktop-screenshot /tmp/shot.jpg --quality 50
```

After running the script, **read the saved image file** to view it.

### After every screenshot, explicitly state:

- What application or window is currently in focus
- What you can see (list specific UI elements, labels, icons)
- For zoomed screenshots: map each visible element to its screen
  coordinate (region offset + position in cropped image)
- What you intend to do next and why

### Coordinate grounding protocol (MANDATORY)

**Every click derived from a cropped screenshot MUST go through this
explicit conversion.** State the math out loud before clicking. This
is the #1 source of errors — do not skip it.

#### The formula

```
screen_x = crop_origin_x + element_position_in_crop_x
screen_y = crop_origin_y + element_position_in_crop_y
```

#### Required format

When you identify a click target from a zoomed screenshot, you MUST
state all four values explicitly before acting:

```
Crop region: --region 280,80,200,100
  → crop_origin = (280, 80)
Target element center in crop: (60, 30)
  → screen coordinate = (280+60, 80+30) = (340, 110)
Clicking at: (340, 110)
```

**Never write just "clicking at (340, 110)"** — always show the
crop origin and the position within the crop so the math can be
verified.

#### Common grounding mistakes

| Mistake | Example | Correct |
|---------|---------|---------|
| Using crop-relative coords as screen coords | Crop at (280,80), icon at crop pixel (60,30), clicking (60,30) | Click (340, 110) |
| Forgetting to add crop origin | "Icon is at pixel 60 in the toolbar crop" → clicks (60, 95) | Must add crop_origin_x: (280+60, 80+30) |
| Reusing coords from a different crop | Found icon in crop A at (340,110), but took a new crop B with different origin, still clicking (340,110) | Re-derive from crop B's origin |
| Estimating from full-screen screenshot | "The icon looks like it's around x=635" without zooming | Must zoom first, then derive exact coords |

### Screenshot strategy

| Purpose              | Type   | Example                                           |
|----------------------|--------|---------------------------------------------------|
| Understand layout    | Survey | `desktop-screenshot /tmp/screen.png`              |
| Identify toolbar icons | Zoom | `desktop-screenshot /tmp/tb.png --region 0,55,900,60` |
| Verify tool selected | Zoom   | `desktop-screenshot /tmp/tool.png --region 280,85,120,40` |
| Verify drawing result | Zoom  | `desktop-screenshot /tmp/draw.png --region 800,400,350,300` |
| Read dialog text     | Zoom   | `desktop-screenshot /tmp/dlg.png --region 350,200,400,200` |
| Find canvas bounds   | Pixel  | `mcporter call desktop.pyautogui_pixel --args '{"x":960,"y":350}'` |

---

## Coordinate reasoning

1. **Origin** (0,0) is top-left. x increases right, y increases down.
2. **1:1 pixel mapping.** The screen is 1920x1080. Screenshot images
   map 1:1 to screen pixels. If a button appears at pixel (350, 120)
   in the screenshot image, click at coordinates (350, 120). There is
   no scaling.
3. **Click the center** of the target element, not its edge.
4. **Zoom when uncertain.** Use a region screenshot before clicking:
   `desktop-screenshot /tmp/zoom.png --region x-100,y-100,200,200`
5. **Verify with pixel color:**
   ```bash
   mcporter call desktop.pyautogui_pixel --args '{"x":500,"y":300}'
   ```
   Returns `[R, G, B]`. White canvas = `[255, 255, 255]`,
   dark UI = `[39, 39, 39]`.
6. **Scan for boundaries.** To find canvas edges or UI boundaries,
   check pixel colors at intervals:
   ```bash
   # Find where white canvas starts vertically at x=960
   mcporter call desktop.pyautogui_pixel --args '{"x":960,"y":300}'
   mcporter call desktop.pyautogui_pixel --args '{"x":960,"y":350}'
   ```
7. **Check coordinates are on screen:**
   ```bash
   mcporter call desktop.pyautogui_onScreen --args '{"x":500,"y":300}'
   ```
8. **App canvas bounds — MUST measure, never estimate.** Do not
   eyeball canvas boundaries from a full-screen screenshot. The
   canvas position depends on window size, toolbar state,
   and whether a shape selection is active. You MUST scan pixel colors
   to find the actual white/content boundaries each time before
   drawing.

### Canvas bounds measurement procedure

Do not estimate canvas bounds from a full screenshot. Measure them:

```bash
# 1. Scan vertically at screen center to find top/bottom of white area
for y in 200 250 300 350 400; do
  mcporter call desktop.pyautogui_pixel --args "{\"x\":960,\"y\":$y}"
done
# White = [255,255,255]. First white pixel = canvas_top.

# 2. Continue scanning to find bottom
for y in 800 850 900 950; do
  mcporter call desktop.pyautogui_pixel --args "{\"x\":960,\"y\":$y}"
done
# Last white pixel = canvas_bottom.

# 3. Scan horizontally at canvas vertical center to find left/right
for x in 400 450 500 550 600; do
  mcporter call desktop.pyautogui_pixel --args "{\"x\":$x,\"y\":CANVAS_VMID}"
done
# First white pixel = canvas_left.

# 4. Narrow down with 10px increments once you find the boundary region
```

Record the four values: `canvas_left`, `canvas_right`, `canvas_top`,
`canvas_bottom`. Calculate center and dimensions from these. These
are your ground-truth coordinates for all drawing operations.

---

## Window management

### Identify active window (do this before every action sequence)
```bash
mcporter call desktop.pyautogui_getActiveWindowTitle
```

### List all visible windows
```bash
mcporter call desktop.pyautogui_getAllTitles
```

### Find windows by title (substring match)
```bash
mcporter call desktop.pyautogui_getWindowsWithTitle --args '{"title":"Calculator"}'
```
Returns: `[{"left": 619, "top": 0, "width": 1309, "height": 1028}]`

### Find which window is at a screen coordinate
```bash
mcporter call desktop.pyautogui_getWindowsAt --args '{"x":500,"y":300}'
```

### Get full window object (position, size, state)
```bash
mcporter call desktop.pyautogui_getActiveWindow
mcporter call desktop.pyautogui_getAllWindows
```

### Bring a window to the foreground

There is no direct "activate window" function. Use one of these:
1. **Click the window's title bar** (use coordinates from `getWindowsWithTitle`)
2. **Alt+Tab** to cycle windows:
   ```bash
   mcporter call desktop.pyautogui_hotkey --args '{"keys":["alt","tab"]}'
   ```
3. **Click the window in the panel/taskbar** (identify position from screenshot)
4. **Launch the app** via Alt+F2 if it's not open:
   ```bash
   mcporter call desktop.pyautogui_hotkey --args '{"keys":["alt","f2"]}'
   # wait 0.5s
   mcporter call desktop.pyautogui_typewrite --args '{"message":"gnome-calculator"}'
   mcporter call desktop.pyautogui_press --args '{"keys":["enter"]}'
   ```

---

## Mouse

### Click
```bash
# Left click at coordinates
mcporter call desktop.pyautogui_click --args '{"x":500,"y":300}'

# Right click
mcporter call desktop.pyautogui_rightClick --args '{"x":500,"y":300}'

# Double click
mcporter call desktop.pyautogui_doubleClick --args '{"x":500,"y":300}'

# Triple click (select entire line of text)
mcporter call desktop.pyautogui_tripleClick --args '{"x":500,"y":300}'

# Middle click
mcporter call desktop.pyautogui_middleClick --args '{"x":500,"y":300}'

# Multiple clicks with interval
mcporter call desktop.pyautogui_click --args '{"x":500,"y":300,"clicks":3,"interval":0.1}'
```

### Move (no click)
```bash
# Absolute position
mcporter call desktop.pyautogui_moveTo --args '{"x":500,"y":300}'
mcporter call desktop.pyautogui_moveTo --args '{"x":500,"y":300,"duration":0.3}'

# Relative offset from current position
mcporter call desktop.pyautogui_move --args '{"xOffset":100,"yOffset":-50}'
mcporter call desktop.pyautogui_moveRel --args '{"xOffset":100,"yOffset":-50,"duration":0.2}'
```

### Get current mouse position
```bash
mcporter call desktop.pyautogui_position
```

### Scroll
```bash
# Vertical scroll (positive=up, negative=down)
mcporter call desktop.pyautogui_scroll --args '{"clicks":3}'
mcporter call desktop.pyautogui_scroll --args '{"clicks":-3,"x":500,"y":300}'

# Horizontal scroll (positive=right, negative=left)
mcporter call desktop.pyautogui_hscroll --args '{"clicks":3}'
mcporter call desktop.pyautogui_hscroll --args '{"clicks":-3,"x":500,"y":300}'
```

---

## Dragging

**CRITICAL: `duration` must be > 0 for all drag operations.** With
duration=0 (the default), the drag happens instantly and most apps
will not register it. Always set duration to at least 0.3 seconds.

### Single-segment drag (straight line)

`dragTo` is atomic — mouseDown, move, and mouseUp in one call.

```bash
# Move to start point, then drag to end point
mcporter call desktop.pyautogui_moveTo --args '{"x":500,"y":300}'
mcporter call desktop.pyautogui_dragTo --args '{"x":800,"y":400,"duration":0.5,"button":"left"}'
```

### Relative drag (by offset)
```bash
mcporter call desktop.pyautogui_drag --args '{"xOffset":200,"yOffset":100,"duration":0.5}'
mcporter call desktop.pyautogui_dragRel --args '{"xOffset":200,"yOffset":100,"duration":0.5}'
```

### Multi-segment drag (curves and complex paths)

**mouseDown state does NOT persist across separate mcporter calls.**
To draw curves or multi-point paths, chain `dragTo` calls. Each
`dragTo` starts from the current mouse position (the endpoint of the
previous call).

```bash
# Move to arc start
mcporter call desktop.pyautogui_moveTo --args '{"x":400,"y":300}'

# Chain dragTo segments — each starts where the previous ended
mcporter call desktop.pyautogui_dragTo --args '{"x":430,"y":330,"duration":0.2,"button":"left"}'
mcporter call desktop.pyautogui_dragTo --args '{"x":465,"y":340,"duration":0.2,"button":"left"}'
mcporter call desktop.pyautogui_dragTo --args '{"x":500,"y":330,"duration":0.2,"button":"left"}'
mcporter call desktop.pyautogui_dragTo --args '{"x":530,"y":300,"duration":0.2,"button":"left"}'
```

Use 6-8 segments for smooth curves. More segments = smoother result.

---

## Keyboard

### Type text
```bash
# typewrite sends individual key presses for each character
mcporter call desktop.pyautogui_typewrite --args '{"message":"Hello World"}'
mcporter call desktop.pyautogui_typewrite --args '{"message":"slow typing","interval":0.05}'

# write is an alias for typewrite
mcporter call desktop.pyautogui_write --args '{"message":"Hello World"}'
```

**Note:** `typewrite`/`write` only supports ASCII characters. For
Unicode text, use clipboard: type the text into a file, then use
`ctrl+c` / `ctrl+v`.

### Press a single key (or sequence of keys)
```bash
mcporter call desktop.pyautogui_press --args '{"keys":["enter"]}'
mcporter call desktop.pyautogui_press --args '{"keys":["tab"]}'
mcporter call desktop.pyautogui_press --args '{"keys":["esc"]}'
mcporter call desktop.pyautogui_press --args '{"keys":["f5"]}'

# Press a key multiple times
mcporter call desktop.pyautogui_press --args '{"keys":["tab"],"presses":3,"interval":0.1}'
```

### Hotkey combinations (simultaneous keys)
```bash
mcporter call desktop.pyautogui_hotkey --args '{"keys":["ctrl","c"]}'
mcporter call desktop.pyautogui_hotkey --args '{"keys":["ctrl","v"]}'
mcporter call desktop.pyautogui_hotkey --args '{"keys":["ctrl","z"]}'
mcporter call desktop.pyautogui_hotkey --args '{"keys":["ctrl","shift","s"]}'
mcporter call desktop.pyautogui_hotkey --args '{"keys":["alt","f4"]}'
mcporter call desktop.pyautogui_hotkey --args '{"keys":["alt","tab"]}'
mcporter call desktop.pyautogui_hotkey --args '{"keys":["win","r"]}'
```

### Hold keys (within a single call)
```bash
# hold keeps keys pressed for the duration of the call
mcporter call desktop.pyautogui_hold --args '{"keys":["shift"]}'
```

**Note:** `keyDown`/`keyUp` exist but their state does NOT persist
across separate mcporter calls. Use `hotkey` for key combinations
and `hold` when you need a modifier held during a single operation.

### Key names reference

| Category    | Keys                                                              |
|-------------|-------------------------------------------------------------------|
| Modifiers   | `ctrl` `shift` `alt` `win`                                       |
| Navigation  | `up` `down` `left` `right` `home` `end` `pageup` `pagedown`     |
| Actions     | `enter` `esc` `tab` `space` `backspace` `delete` `insert`        |
| Function    | `f1` `f2` `f3` `f4` `f5` `f6` `f7` `f8` `f9` `f10` `f11` `f12` |
| Other       | `printscreen` `capslock` `numlock` `scrolllock`                   |

Validate a key name:
```bash
mcporter call desktop.pyautogui_isValidKey --args '{"key":"enter"}'
```

---

## Timing and waits

```bash
mcporter call desktop.pyautogui_sleep --args '{"seconds":1}'
```

You can also use bash `sleep` between mcporter calls:
```bash
sleep 0.5
```

### Recommended wait times

| After...                        | Wait   |
|---------------------------------|--------|
| Alt+F2 (Run dialog)             | 0.5s   |
| Launching an application        | 1.5–2s |
| Clicking a menu item            | 0.3s   |
| Opening a dialog/modal          | 0.5–1s |
| Alt+Tab (window switch)         | 0.5s   |
| Typing text before pressing Enter | 0.2s |
| Shape tool drag completion      | 0.3s   |

---

## Launching applications

### Via Run dialog (Alt+F2 on LXDE)
```bash
mcporter call desktop.pyautogui_hotkey --args '{"keys":["alt","f2"]}'
sleep 0.5
mcporter call desktop.pyautogui_typewrite --args '{"message":"lxterminal"}'
sleep 0.2
mcporter call desktop.pyautogui_press --args '{"keys":["enter"]}'
sleep 2
mcporter call desktop.pyautogui_getActiveWindowTitle
```

Common app commands: `lxterminal`, `pcmanfm`, `mousepad`, `firefox`,
`chromium-browser`, `gnome-calculator`, `gimp`.

### Via LXDE menu
```bash
# Click the LXDE menu (typically at bottom-left)
# Then type to search
mcporter call desktop.pyautogui_typewrite --args '{"message":"calculator"}'
sleep 1
mcporter call desktop.pyautogui_press --args '{"keys":["enter"]}'
```

---

## Diagnostic tools

```bash
# Server health and PyAutoGUI availability
mcporter call desktop.pyautogui_diagnose

# List registered tools on the server
mcporter call desktop.pyautogui_tools

# System info (PyAutoGUI version, screen size, etc.)
mcporter call desktop.pyautogui_getInfo

# Check if coordinates are within screen bounds
mcporter call desktop.pyautogui_onScreen --args '{"x":500,"y":300}'

# Get pixel RGB color at a coordinate
mcporter call desktop.pyautogui_pixel --args '{"x":500,"y":300}'

# Check if pixel matches an expected color (with tolerance)
mcporter call desktop.pyautogui_pixelMatchesColor --args '{"x":500,"y":300,"expectedRGBColor":[255,255,255],"tolerance":10}'
```

---

## Error recovery

If an action does not produce the expected result:

1. **Do NOT retry the same action blindly.** Take a screenshot first.
2. **Take a screenshot and re-examine current state.** What changed?
3. **Check common failure modes:**
   - Did window focus shift? → Use `getActiveWindowTitle` to verify.
   - Did a dialog or popup appear? → Dismiss it or interact with it.
   - Did the window move or resize? → Re-identify coordinates.
   - Is the wrong tool selected? → Check toolbar state with a zoomed
     screenshot.
   - Did Ctrl+A or another shortcut change the tool mode? →
     Re-select the intended tool.
4. **Adjust coordinates or approach** based on what you actually see.
5. **If stuck after 3 attempts** at the same step, report the current
   screenshot to the user and ask for guidance. Do not blindly retry.

### Common issues and fixes

| Problem | Cause | Fix |
|---------|-------|-----|
| Drawing produces nothing | Wrong tool selected | Screenshot toolbar, click correct tool, click canvas |
| Drawing produces straight line only | Using mouseDown/moveTo/mouseUp across calls | Use chained `dragTo` calls instead |
| Click hits wrong element | Coordinates are off | Zoom in with region screenshot, use pixel color to verify |
| App doesn't respond to typing | Wrong window focused | `getActiveWindowTitle`, then click correct window |
| dragTo doesn't draw | duration is 0 (default) | Always set `"duration":0.3` or higher |

---

## Safety

- **Failsafe:** move mouse to corner (0,0) to abort PyAutoGUI automation
- **Never assume coordinates** from a previous session are still valid
- **Always verify active window** with `getActiveWindowTitle` before typing
  — typing into the wrong window can cause unintended actions
- **Always screenshot** before and after every action
- **Avoid destructive hotkeys** like Alt+F4 unless you are certain of
  the active window — it will close whatever is focused
