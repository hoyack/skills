---
name: draw-smiley-face
version: 1.1.0
description: >
  Draw a smiley face in MS Paint on the Windows desktop. Uses the
  desktop-control-windows skill for all mouse/keyboard/screenshot
  operations. Contains detailed step-by-step geometry, coordinates,
  tool selection procedures, and verification checks. Use when the
  user asks to draw a smiley face, happy face, or emoji face in Paint.
tags: [drawing, paint, smiley, art, windows, desktop]
metadata:
  clawdbot:
    emoji: 😊
    requires:
      bins:
        - mcporter
      skills:
        - desktop-control-windows
env:
  DESKTOP_MCP_URL:
    description: URL of the PyAutoGUI MCP server running on the Windows host
    required: true
---

# Draw a smiley face in MS Paint

This skill draws a smiley face in Microsoft Paint on Windows 11. It
depends on the `desktop-control-windows` skill for all desktop
interaction. Follow every step exactly — do not skip observations or
verifications.

---

## Prerequisites

Before starting, ensure:
1. The `desktop-control-windows` skill is set up and working
2. The mcporter `desktop` alias is configured
3. The `desktop-screenshot` helper is on PATH

Run the desktop-control-windows setup if needed:
```bash
mcporter list desktop 2>&1 || mcporter config add desktop --url "$DESKTOP_MCP_URL" --allow-http --yes
export PATH="$PATH:$(dirname "$(find ~/.openclaw/workspace/skills/desktop-control-windows/bin -name desktop-screenshot -type f 2>/dev/null)")"
```

---

## Overview

The smiley face consists of four elements drawn in order:

| Element      | Tool      | Method                        |
|--------------|-----------|-------------------------------|
| Face circle  | Oval shape | Single drag on bounding box  |
| Left eye     | Oval shape | Single drag, small circle    |
| Right eye    | Oval shape | Single drag, small circle    |
| Smile arc    | Pencil    | Chained dragTo segments      |

The oval shape tool is used for circles because it produces clean
results with a single drag. The pencil with chained `dragTo` is used
for the smile because it's a curved arc that shape tools can't produce.

---

## Step 0 — Open and maximize Paint

### 0a. Check if Paint is already open

```bash
mcporter call desktop.pyautogui_getWindowsWithTitle --args '{"title":"Paint"}'
```

If the result is an empty list `[]`, Paint is not open. Open it:

```bash
mcporter call desktop.pyautogui_hotkey --args '{"keys":["win","r"]}'
sleep 0.5
mcporter call desktop.pyautogui_typewrite --args '{"message":"mspaint"}'
sleep 0.2
mcporter call desktop.pyautogui_press --args '{"keys":["enter"]}'
sleep 2
```

### 0b. Bring Paint to the foreground

If Paint is open but not focused, you need to find and click it.
Check the active window first:

```bash
mcporter call desktop.pyautogui_getActiveWindowTitle
```

If it doesn't say "Paint", you must bring Paint forward. The most
reliable method is to scan taskbar icons:

```bash
# Click a taskbar position, check if Paint activates
mcporter call desktop.pyautogui_click --args '{"x":TASKBAR_X,"y":1060}'
sleep 0.3
mcporter call desktop.pyautogui_getActiveWindowTitle
```

Scan x positions in increments of 30px along the taskbar (y=1060)
until `getActiveWindowTitle` returns a string containing "Paint".

### 0c. Verify Paint is focused and take initial survey

```bash
mcporter call desktop.pyautogui_getActiveWindowTitle
# Must contain "Paint"

desktop-screenshot /tmp/paint_survey.png
```

Read the survey screenshot. Identify:
- Is Paint maximized or windowed?
- Where is the toolbar/ribbon?
- Where is the canvas?

If Paint is not maximized, maximize it. Do NOT use Win+Up (triggers
snap layout on Windows 11). Instead, double-click the title bar:

```bash
# Get Paint window position
mcporter call desktop.pyautogui_getWindowsWithTitle --args '{"title":"Paint"}'
# Double-click the title bar center to maximize
mcporter call desktop.pyautogui_doubleClick --args '{"x":TITLE_CENTER_X,"y":TITLE_Y}'
sleep 0.3
```

---

## Step 1 — Map the canvas

The canvas is the white rectangular area where you draw. You must
identify its exact boundaries before drawing anything.

### 1a. Find canvas bounds with pixel color scanning

Scan horizontally at the vertical center of the screen (y=540) to
find the left and right edges of the white canvas:

```bash
# Scan for left edge — find where white (255,255,255) starts
mcporter call desktop.pyautogui_pixel --args '{"x":400,"y":540}'
mcporter call desktop.pyautogui_pixel --args '{"x":450,"y":540}'
mcporter call desktop.pyautogui_pixel --args '{"x":500,"y":540}'
mcporter call desktop.pyautogui_pixel --args '{"x":550,"y":540}'
# ... continue until you find [255, 255, 255]
```

Do the same vertically at the horizontal center (x=960):

```bash
# Scan for top edge
mcporter call desktop.pyautogui_pixel --args '{"x":960,"y":200}'
mcporter call desktop.pyautogui_pixel --args '{"x":960,"y":250}'
mcporter call desktop.pyautogui_pixel --args '{"x":960,"y":300}'
mcporter call desktop.pyautogui_pixel --args '{"x":960,"y":350}'
# ... continue until you find [255, 255, 255]
```

Narrow down edges with tighter increments (10-20px) once you find
the approximate boundary.

### 1b. Record canvas bounds

After scanning, you should have:
- `canvas_left` — x coordinate of left edge of white area
- `canvas_right` — x coordinate of right edge
- `canvas_top` — y coordinate of top edge
- `canvas_bottom` — y coordinate of bottom edge

Calculate:
```
canvas_center_x = (canvas_left + canvas_right) / 2
canvas_center_y = (canvas_top + canvas_bottom) / 2
canvas_width = canvas_right - canvas_left
canvas_height = canvas_bottom - canvas_top
```

**Typical values for maximized Paint on 1920x1080:**
- canvas_left ≈ 540, canvas_right ≈ 1390
- canvas_top ≈ 330, canvas_bottom ≈ 880
- canvas_center ≈ (965, 605)
- canvas_size ≈ 850 x 550

These are approximate — you MUST scan to get actual values because
they depend on Paint's zoom level, ribbon state, and window size.

---

## Step 2 — Select the oval shape tool

This step REQUIRES the two-pass zoom observation from the
desktop-control-windows skill. Do NOT guess toolbar coordinates
from a full-screen screenshot.

### 2a. Survey the toolbar location

```bash
desktop-screenshot /tmp/survey.png
```

Read the image. Identify the approximate y-range of the ribbon/toolbar
(usually y ≈ 55-140 in maximized Paint). Note the approximate x-range
of the "Shapes" section label.

### 2b. Zoom the toolbar

Take a cropped screenshot of the entire toolbar strip:

```bash
desktop-screenshot /tmp/toolbar.png --region 0,55,900,60
```

Read the zoomed image. You should now be able to clearly see
individual icons. Identify and label each section:

```
Selection | Image | Tools: [Pencil] [Eraser] [ColorPicker] [Text] [Magnifier] | Shapes: [Line] [Curve] [Oval] [Rect] [RoundRect] [Triangle] ...
```

### 2c. Locate the oval icon and ground coordinates

The oval icon looks like a circle/ellipse outline (`O`). It is
typically the **3rd icon** in the Shapes section (after Line and
Curve).

Find the oval icon's position in the cropped image (in pixels from
the crop's top-left corner). Then perform the **mandatory coordinate
grounding** — state all values explicitly:

```
Crop region: --region 0,55,900,60
  → crop_origin = (0, 55)
Oval icon center in crop image: approximately pixel (635, 40)
  → screen_x = 0 + 635 = 635
  → screen_y = 55 + 40 = 95
  → screen coordinate = (635, 95)
```

**You MUST show this math.** Do not just write "clicking at (635, 95)"
without showing the crop origin and position-in-crop derivation.

If you cannot distinguish the oval from adjacent shapes, zoom
further into just the shapes area:

```bash
desktop-screenshot /tmp/shapes_zoom.png --region 590,85,100,25
```

Then re-derive coordinates from this new crop:
```
Crop region: --region 590,85,100,25
  → crop_origin = (590, 85)
Oval icon center in this crop: approximately pixel (45, 12)
  → screen coordinate = (590+45, 85+12) = (635, 97)
```

### 2d. Click the oval tool

```bash
mcporter call desktop.pyautogui_click --args '{"x":OVAL_SCREEN_X,"y":OVAL_SCREEN_Y}'
sleep 0.3
```

### 2e. VERIFY the oval is selected (MANDATORY — do not skip)

Take a **new** zoomed screenshot of the same toolbar area:

```bash
desktop-screenshot /tmp/tool_verify.png --region 590,85,100,25
```

Read the zoomed image. The selected tool has a visible **blue
highlight border** around it. Confirm:
- It IS the oval (circle shape), not a rectangle or triangle
- The highlight is on the correct icon
- No other tool appears highlighted instead

If the wrong tool is selected:
1. Re-examine the zoomed toolbar image
2. Identify which tool IS highlighted and where the oval actually is
3. Re-derive coordinates from the current crop (show the math)
4. Click the correct position
5. Zoom and verify again — do not proceed until confirmed

---

## Step 3 — Draw the face circle

### Pre-draw gate check

Before drawing, confirm all three conditions (from
desktop-control-windows skill). State each one explicitly:

```
[ ] TOOL CONFIRMED — "Oval tool confirmed selected, verified via
    zoomed screenshot at (CROP_REGION). Blue highlight visible on
    oval icon at screen coordinate (X, Y)."

[ ] CANVAS MEASURED — "Canvas bounds measured via pixel scanning:
    (canvas_left, canvas_top) to (canvas_right, canvas_bottom).
    Center at (canvas_center_x, canvas_center_y)."

[ ] CANVAS CLEAR — "No shape selection handles visible. Canvas is
    a clean white rectangle with no active selections."
```

If any condition is not met, go back and fix it before proceeding.

### 3a. Calculate bounding box

The face circle is centered on the canvas with radius proportional
to the canvas size. Use approximately 60% of the smaller canvas
dimension as the diameter:

```
face_radius = min(canvas_width, canvas_height) * 0.3
face_top_left_x = canvas_center_x - face_radius
face_top_left_y = canvas_center_y - face_radius
face_bottom_right_x = canvas_center_x + face_radius
face_bottom_right_y = canvas_center_y + face_radius
```

**Example with typical values:**
```
face_radius = 150
face_top_left = (815, 455)
face_bottom_right = (1115, 755)
```

### 3b. Click the canvas to establish drawing context

```bash
mcporter call desktop.pyautogui_click --args '{"x":CANVAS_CENTER_X,"y":CANVAS_CENTER_Y}'
sleep 0.2
```

### 3c. Draw the oval

Drag from the top-left to bottom-right corner of the bounding box.
Use mouseDown → moveTo → mouseUp (this works for shape tools because
the OS handles the drag state internally):

```bash
mcporter call desktop.pyautogui_mouseDown --args '{"x":FACE_TL_X,"y":FACE_TL_Y,"button":"left"}'
mcporter call desktop.pyautogui_moveTo --args '{"x":FACE_BR_X,"y":FACE_BR_Y,"duration":1.0}'
mcporter call desktop.pyautogui_mouseUp --args '{"x":FACE_BR_X,"y":FACE_BR_Y,"button":"left"}'
sleep 0.3
```

### 3d. Commit the shape

Click outside the shape selection handles to commit it:

```bash
mcporter call desktop.pyautogui_click --args '{"x":CANVAS_LEFT+20,"y":CANVAS_TOP+20}'
sleep 0.3
```

### 3e. Verify the face circle

```bash
desktop-screenshot /tmp/face_check.png --region FACE_TL_X-20,FACE_TL_Y-20,FACE_WIDTH+40,FACE_HEIGHT+40
```

Read the zoomed image. You should see a clean black circle on a
white background. If not, undo with Ctrl+Z and retry from step 3c.

---

## Step 4 — Draw the eyes

The eyes are two small circles positioned symmetrically in the upper
third of the face.

### 4a. Re-check the pre-draw gate

After drawing the face circle and committing it, the state may have
changed. You MUST verify all three conditions again:

1. **Tool** — Zoom the toolbar. Is the oval tool still highlighted?
   Committing a shape sometimes deselects the tool.
   ```bash
   desktop-screenshot /tmp/tool_recheck.png --region 590,85,100,25
   ```
   If not selected, click it and verify again.

2. **Canvas** — Zoom the canvas area. Are the face circle's resize
   handles gone? If handles are still visible, click a neutral area
   and re-check.
   ```bash
   desktop-screenshot /tmp/canvas_state.png --region FACE_TL_X-30,FACE_TL_Y-30,FACE_WIDTH+60,50
   ```

3. **Bounds** — Canvas bounds should not have changed, but if Paint
   auto-scrolled or the zoom changed, re-scan.

### 4b. Calculate eye positions

```
eye_radius = face_radius * 0.1     # ~15px for a 150px face radius
eye_y_offset = face_radius * 0.25  # eyes are 25% up from center
eye_x_offset = face_radius * 0.35  # eyes are 35% out from center

left_eye_center_x = canvas_center_x - eye_x_offset
left_eye_center_y = canvas_center_y - eye_y_offset
right_eye_center_x = canvas_center_x + eye_x_offset
right_eye_center_y = canvas_center_y - eye_y_offset
```

Each eye's bounding box:
```
eye_tl_x = eye_center_x - eye_radius
eye_tl_y = eye_center_y - eye_radius
eye_br_x = eye_center_x + eye_radius
eye_br_y = eye_center_y + eye_radius
```

**Example with typical values:**
```
Left eye:  center (910, 567), bounding box (895, 552) → (925, 582)
Right eye: center (1020, 567), bounding box (1005, 552) → (1035, 582)
```

### 4c. Draw the left eye

```bash
mcporter call desktop.pyautogui_mouseDown --args '{"x":LEFT_EYE_TL_X,"y":LEFT_EYE_TL_Y,"button":"left"}'
mcporter call desktop.pyautogui_moveTo --args '{"x":LEFT_EYE_BR_X,"y":LEFT_EYE_BR_Y,"duration":0.5}'
mcporter call desktop.pyautogui_mouseUp --args '{"x":LEFT_EYE_BR_X,"y":LEFT_EYE_BR_Y,"button":"left"}'
sleep 0.3
```

Commit:
```bash
mcporter call desktop.pyautogui_click --args '{"x":CANVAS_LEFT+20,"y":CANVAS_TOP+20}'
sleep 0.3
```

### 4d. Draw the right eye

```bash
mcporter call desktop.pyautogui_mouseDown --args '{"x":RIGHT_EYE_TL_X,"y":RIGHT_EYE_TL_Y,"button":"left"}'
mcporter call desktop.pyautogui_moveTo --args '{"x":RIGHT_EYE_BR_X,"y":RIGHT_EYE_BR_Y,"duration":0.5}'
mcporter call desktop.pyautogui_mouseUp --args '{"x":RIGHT_EYE_BR_X,"y":RIGHT_EYE_BR_Y,"button":"left"}'
sleep 0.3
```

Commit:
```bash
mcporter call desktop.pyautogui_click --args '{"x":CANVAS_LEFT+20,"y":CANVAS_TOP+20}'
sleep 0.3
```

### 4e. Verify both eyes

```bash
desktop-screenshot /tmp/eyes_check.png --region LEFT_EYE_TL_X-30,LEFT_EYE_TL_Y-20,RIGHT_EYE_BR_X-LEFT_EYE_TL_X+60,EYE_HEIGHT+40
```

You should see two small circles positioned symmetrically. If one is
missing or malformed, undo with Ctrl+Z and redraw just that eye.

---

## Step 5 — Draw the smile

The smile is a curved arc in the lower third of the face. Shape tools
cannot draw arcs, so we use the **pencil tool** with **chained
`dragTo` calls**.

### 5a. Select the pencil tool

First, zoom the toolbar to find the pencil icon:

```bash
desktop-screenshot /tmp/toolbar_pencil.png --region 0,55,900,60
```

The pencil icon is typically in the "Tools" section, to the left of
the eraser. It looks like a small pencil/pen icon. Click it:

```bash
mcporter call desktop.pyautogui_click --args '{"x":PENCIL_X,"y":PENCIL_Y}'
sleep 0.3
```

### 5b. Verify pencil is selected

```bash
desktop-screenshot /tmp/pencil_verify.png --region PENCIL_X-30,PENCIL_Y-15,60,30
```

The pencil should have a blue highlight border. If not, adjust and
re-click.

### 5c. Calculate smile geometry

The smile is a downward arc (a curve that dips below its endpoints).

```
smile_width = face_radius * 1.0    # spans the middle 50% of face
smile_y = canvas_center_y + face_radius * 0.15  # slightly below center
smile_depth = face_radius * 0.4    # how far the curve dips down
smile_segments = 6                  # number of dragTo segments

smile_left_x = canvas_center_x - smile_width / 2
smile_right_x = canvas_center_x + smile_width / 2
smile_left_y = smile_y
smile_right_y = smile_y
smile_bottom_y = smile_y + smile_depth
```

**Example with typical values:**
```
Smile endpoints: (890, 620) and (1040, 620)
Smile lowest point: (965, 680)
```

### 5d. Compute waypoints

Generate 7 points along the smile arc (start + 6 segments).
The arc follows a parabolic curve:

```
For segment i (0 to 6):
  t = i / 6                          # 0.0 to 1.0
  x = smile_left_x + t * smile_width
  y = smile_y + smile_depth * 4 * t * (1 - t)   # parabola
```

This produces a smooth downward arc. The `4 * t * (1-t)` factor
creates a parabola that peaks at t=0.5 (the midpoint).

**Example waypoints:**
```
Point 0: (890, 620)   ← start
Point 1: (915, 647)
Point 2: (940, 666)
Point 3: (965, 680)   ← deepest point
Point 4: (990, 666)
Point 5: (1015, 647)
Point 6: (1040, 620)  ← end
```

### 5e. Draw the smile with chained dragTo

First, move to the start point:

```bash
mcporter call desktop.pyautogui_moveTo --args '{"x":START_X,"y":START_Y}'
```

Then chain `dragTo` calls for each segment. Each `dragTo` is atomic
(does its own mouseDown → move → mouseUp) and starts from wherever
the mouse currently is:

```bash
mcporter call desktop.pyautogui_dragTo --args '{"x":POINT1_X,"y":POINT1_Y,"duration":0.2,"button":"left"}'
mcporter call desktop.pyautogui_dragTo --args '{"x":POINT2_X,"y":POINT2_Y,"duration":0.2,"button":"left"}'
mcporter call desktop.pyautogui_dragTo --args '{"x":POINT3_X,"y":POINT3_Y,"duration":0.2,"button":"left"}'
mcporter call desktop.pyautogui_dragTo --args '{"x":POINT4_X,"y":POINT4_Y,"duration":0.2,"button":"left"}'
mcporter call desktop.pyautogui_dragTo --args '{"x":POINT5_X,"y":POINT5_Y,"duration":0.2,"button":"left"}'
mcporter call desktop.pyautogui_dragTo --args '{"x":POINT6_X,"y":POINT6_Y,"duration":0.2,"button":"left"}'
```

### 5f. Verify the smile

```bash
desktop-screenshot /tmp/smile_check.png --region SMILE_LEFT_X-20,SMILE_LEFT_Y-20,SMILE_WIDTH+40,SMILE_DEPTH+40
```

You should see a curved arc. If it looks like a straight line,
something went wrong with the dragTo chain — undo and check:
1. Did each dragTo have `"duration":0.2` or greater?
2. Was the pencil tool actually selected? (zoom to verify)
3. Was the first `moveTo` correctly positioned at the start point?

---

## Step 6 — Final verification

### 6a. Take a full survey screenshot

```bash
desktop-screenshot /tmp/smiley_final.png
```

Read the image. You should see a face with two eyes and a smile
visible even at the downscaled full-screen view.

### 6b. Zoom into the face for detail

```bash
desktop-screenshot /tmp/smiley_zoom.png --region FACE_TL_X-20,FACE_TL_Y-20,FACE_WIDTH+40,FACE_HEIGHT+40
```

Verify all four elements:
- [ ] Face circle — clean, closed oval
- [ ] Left eye — small circle, positioned in upper-left quadrant of face
- [ ] Right eye — small circle, symmetric with left eye
- [ ] Smile — curved arc in lower half of face, curving downward

### 6c. Report to user

Present the zoomed screenshot to the user and describe what was drawn.
If any element is missing or malformed, state which one and offer to
fix it.

---

## Recovery procedures

### Wrong tool selected
1. Zoom the toolbar to identify what's actually selected
2. Click the correct tool
3. Zoom the toolbar again to verify
4. Continue from where you left off

### Shape drew in wrong position
1. Ctrl+Z to undo the last shape
2. Re-scan canvas bounds (they may have shifted)
3. Recalculate coordinates
4. Redraw

### Smile drew as straight line
This means `dragTo` segments aren't connecting properly. Check:
1. Was the pencil tool selected? (Ctrl+A or clicking a shape tool
   may have switched away from it)
2. Did each `dragTo` have `duration > 0`?
3. Try increasing duration to 0.3 per segment

### Canvas is not blank (previous drawing exists)
Open a new canvas:
```bash
mcporter call desktop.pyautogui_hotkey --args '{"keys":["ctrl","n"]}'
sleep 0.5
# If "Save changes?" dialog appears, click "Don't Save"
mcporter call desktop.pyautogui_getActiveWindowTitle
# Check if dialog appeared, handle it if needed
```

### Tool state lost after Ctrl+A or Ctrl+Z
Any selection-related shortcut (Ctrl+A, Ctrl+C) switches Paint to
the Selection tool. You MUST re-select your drawing tool:
1. Zoom the toolbar to confirm Selection is active
2. Click the oval or pencil tool as needed
3. Zoom to verify
4. Click the canvas once to re-establish drawing context

---

## Geometry reference

All proportions relative to `face_radius` (R):

```
FACE CIRCLE
  center:  (canvas_center_x, canvas_center_y)
  radius:  R = min(canvas_width, canvas_height) * 0.3

EYES
  radius:  R * 0.10
  y offset from center:  R * 0.25 (upward)
  x offset from center:  R * 0.35 (outward, symmetric)

SMILE ARC
  y position:  canvas_center_y + R * 0.15
  width:       R * 1.0 (total horizontal span)
  depth:       R * 0.40 (how far it curves down)
  segments:    6 chained dragTo calls
  curve:       y = base_y + depth * 4 * t * (1 - t)  where t = 0..1
```

Visual layout (not to scale):
```
       ┌─────────────────────┐
       │                     │
       │    O           O    │  ← eyes
       │                     │
       │       ╲_____╱       │  ← smile
       │                     │
       └─────────────────────┘
```
