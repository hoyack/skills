---
name: app-tear-down
version: 1.0.0
description: >
  Systematic methodology for tearing down any desktop application's UI
  into a complete, machine-readable skill reference. Produces a SKILL.md
  with cropped screenshot references for every icon, button, menu item,
  panel, and interactive element — so an automation agent can visually
  identify and operate any feature. Use when you need to create a new
  app skill from scratch by reverse-engineering an application's interface.
tags: [methodology, ui-mapping, reverse-engineering, desktop, automation, skill-creation]
metadata:
  clawdbot:
    emoji: 🔬
    requires:
      bins:
        - mcporter
      skills:
        - desktop-control-mint
env:
  DESKTOP_MCP_URL:
    description: URL of the PyAutoGUI MCP server running on Linux Mint (default http://127.0.0.1:8765/mcp)
    default: http://127.0.0.1:8765/mcp
---

# App Tear-Down — Systematic UI Reverse Engineering

This skill documents the complete methodology for tearing down any
desktop application's interface and producing a reusable skill reference.
The output is a SKILL.md file with cropped screenshot references, screen
coordinates, and operational documentation for every interactive element.

**Proven on:** MS Paint (Windows 11) — produced a 735-line reference
with 46 asset screenshots covering 8 ribbon sections, 3 menus, 21
shapes, 9 brush types, 22 preset colors, and all panels.

---

## Prerequisites

Before starting a tear-down, ensure:

1. The `desktop-control-mint` skill is set up and working
2. The `mcporter` mint alias is configured and connected
3. The `desktop-screenshot` helper is on PATH
4. The target application is **open and visible** on the Linux Mint desktop

```bash
# Verify connectivity
mcporter call mint.pyautogui_size

# Verify screenshot tool
export PATH="$PATH:$(dirname "$(find ~/.openclaw/workspace/skills/desktop-control-mint/bin -name desktop-screenshot -type f 2>/dev/null)")"
desktop-screenshot /tmp/test.png
```

---

## Phase 0 — Prepare the workspace

### 0a. Create the skill directory structure

Every app skill follows the same directory layout:

```bash
SKILL_DIR=~/.openclaw/workspace/skills/<app-name>

mkdir -p "$SKILL_DIR/assets/"{icons,menus,ribbon,colors,panels}
```

| Directory       | Contents |
|-----------------|----------|
| `assets/icons/` | App icon, window controls, title bar elements |
| `assets/menus/` | Every dropdown menu screenshot |
| `assets/ribbon/` | Toolbar/ribbon sections, tool icons, galleries |
| `assets/colors/` | Color palettes, swatches, pickers |
| `assets/panels/` | Side panels, status bars, docks, dialogs |

Adjust subdirectories to match the app. A code editor might need
`assets/sidebar/`, `assets/tabs/`, `assets/terminal/`. A 3D app might
need `assets/viewport/`, `assets/timeline/`, `assets/properties/`.

### 0b. Plan the tear-down scope

Before capturing anything, take a single full-screen survey screenshot
and identify the **UI zones** — the major visual regions of the
application window. Common zones:

| Zone type        | Examples |
|------------------|----------|
| Title bar        | App icon, window title, minimize/maximize/close |
| Menu bar         | File, Edit, View, Help, etc. |
| Toolbar/Ribbon   | Tool icons, grouped in sections with labels |
| Side panels      | Navigation, layers, properties, file explorer |
| Main workspace   | Canvas, editor, viewport, document area |
| Status bar       | Coordinates, zoom, file info, notifications |
| Dock/Taskbar     | Tabs, open documents, pinned tools |

Write down which zones exist and in what order you'll capture them
(top-to-bottom, left-to-right is natural).

---

## Phase 1 — Identify the application

### 1a. Capture the application icon

The app icon is the first thing an agent needs to find the application.
Capture it from three locations:

```bash
# Title bar icon (top-left of window)
desktop-screenshot $SKILL_DIR/assets/icons/app_icon.png --region 0,0,25,25

# Full title bar with app name
desktop-screenshot $SKILL_DIR/assets/icons/titlebar_full.png --region 0,0,500,30
```

### 1b. Record application identity

Document how to find and launch the application:

| Property       | How to determine |
|----------------|------------------|
| Window title   | `mcporter call mint.pyautogui_getActiveWindowTitle` |
| Process/launch | What command launches it (e.g., `gnome-calculator`, `code`, `xed`) |
| Window info    | `xwininfo -tree -root` or `wmctrl -lG` |

### 1c. Capture window controls

```bash
# Window controls (minimize, maximize, close) — top-right
desktop-screenshot $SKILL_DIR/assets/icons/window_controls.png --region 1830,0,90,25
```

---

## Phase 2 — Map the window layout

### 2a. Take the master survey

Take a full-screen screenshot as the master reference:

```bash
desktop-screenshot $SKILL_DIR/assets/ribbon/00_complete_header.png --region 0,0,1920,160
```

### 2b. Identify Y-ranges for each zone

Starting from the top of the window, determine where each zone begins
and ends. Use the **progressive crop technique**:

1. Start with a wide, tall crop of the entire header area
2. Read the image and estimate zone boundaries
3. Narrow the crop to confirm boundaries
4. Record the Y-ranges

```bash
# Start broad — full width, generous height
desktop-screenshot /tmp/header.png --region 0,0,1920,200

# Read the image, identify approximate zones, then zoom each one
desktop-screenshot /tmp/titlebar.png --region 0,0,1920,30
desktop-screenshot /tmp/menubar.png --region 0,25,1920,30
desktop-screenshot /tmp/toolbar.png --region 0,55,1920,140
```

### 2c. Record the zone map

Document the layout as an ASCII diagram and coordinate table:

```
┌──────────────────────────────────┐
│ [icon] App Title      [—] [□] [×]│  ← Title bar (y≈0-25)
├──────────────────────────────────┤
│ File  Edit  View  Help           │  ← Menu bar (y≈25-55)
├──────────────────────────────────┤
│ [tool icons in sections]         │  ← Toolbar (y≈55-190)
├──┬───────────────────────────────┤
│P │                               │
│A │      Main workspace           │  ← Workspace (y≈200-1000)
│N │                               │
├──┴───────────────────────────────┤
│ status info                      │  ← Status bar (y≈1000-1030)
└──────────────────────────────────┘
```

---

## Phase 3 — Tear down each zone

Work through zones **top-to-bottom, left-to-right**. For each zone,
follow the capture → identify → document cycle.

### The capture → identify → document cycle

This is the core loop of the tear-down. Repeat it for every element:

```
1. CAPTURE — Take a cropped screenshot of the zone/section
2. READ    — View the image, identify each interactive element
3. ZOOM    — If icons are too small, take a tighter crop
4. LABEL   — Name each element and describe its visual appearance
5. GROUND  — Calculate screen coordinates from crop position
6. RECORD  — Write the element into the SKILL.md table
7. SAVE    — Store the cropped screenshot as a reference asset
```

### Coordinate grounding (MANDATORY)

Every coordinate must be derived from a crop region, never guessed from
a full-screen image. Show the math explicitly:

```
Crop region: --region X_ORIGIN,Y_ORIGIN,WIDTH,HEIGHT
  → crop_origin = (X_ORIGIN, Y_ORIGIN)
Target element position in crop image: (pixel_x, pixel_y)
  → screen_x = X_ORIGIN + pixel_x
  → screen_y = Y_ORIGIN + pixel_y
  → screen coordinate = (screen_x, screen_y)
```

**Why this matters:** Full-screen screenshots are downscaled ~4x when
displayed, making individual icons ~6-8 pixels wide. A 1-pixel
misread at that scale is a 4-pixel error on screen — enough to click
the wrong tool.

---

## Phase 4 — Menus

### 4a. Enumerate menu items

For each menu in the menu bar (File, Edit, View, etc.):

```bash
# Click the menu to open it
mcporter call mint.pyautogui_click --args '{"x":MENU_X,"y":MENU_Y}'
sleep 0.5

# Capture the dropdown — start with generous height
desktop-screenshot $SKILL_DIR/assets/menus/<menu>_menu.png --region MENU_X-10,MENU_Y,250,400

# If the menu is taller than the crop, capture the bottom too
desktop-screenshot $SKILL_DIR/assets/menus/<menu>_menu_bottom.png --region MENU_X-10,BOTTOM_Y,250,200

# Close the menu
mcporter call mint.pyautogui_press --args '{"keys":["esc"]}'
sleep 0.3
```

### 4b. Handle submenus

Some menu items have a `>` arrow indicating a submenu. To capture:

```bash
# Hover over the item to expand the submenu
mcporter call mint.pyautogui_moveTo --args '{"x":ITEM_X,"y":ITEM_Y}'
sleep 0.8  # submenus need time to appear

# Capture the expanded area
desktop-screenshot $SKILL_DIR/assets/menus/<menu>_<item>_submenu.png --region ...
```

**Known difficulty:** Submenus can be finicky. If hovering doesn't
trigger expansion, try:
- Clicking the item instead of hovering
- Moving the mouse slowly toward the `>` arrow
- Increasing the sleep duration to 1-2 seconds

### 4c. Document each menu

For each menu, produce a table:

```markdown
| Item              | Shortcut     | Function |
|-------------------|--------------|----------|
| New               | Ctrl+N       | Create new document |
| Open              | Ctrl+O       | Open existing file |
| ...               | ...          | ... |
```

Record keyboard shortcuts shown next to menu items — these are
critical for automation (often faster and more reliable than clicking).

---

## Phase 5 — Toolbar / Ribbon

The toolbar is typically the most complex zone. It may have:
- **Sections** with labeled groups of icons
- **Multiple rows** of icons per section
- **Dropdown galleries** (e.g., shapes, brushes, fonts)
- **Split buttons** (top half = default action, bottom half/arrow = dropdown)

### 5a. Identify sections

Most toolbars have labeled sections. Take a wide crop that includes the
section label text:

```bash
# Full ribbon including section labels
desktop-screenshot /tmp/ribbon_labeled.png --region 0,55,1500,140
```

Read the image and identify section boundaries. Look for:
- Thin vertical separator lines between sections
- Section label text at the bottom of the ribbon
- Visual grouping of related icons

### 5b. Capture each section

For each labeled section, take a targeted crop:

```bash
desktop-screenshot $SKILL_DIR/assets/ribbon/NN_<section_name>.png \
  --region SECTION_LEFT,RIBBON_TOP,SECTION_WIDTH,RIBBON_HEIGHT
```

Number sections sequentially (`01_selection.png`, `02_image.png`, etc.)
so they sort in left-to-right order.

### 5c. Identify every icon in the section

Read the cropped section image. For each icon:

1. **Name it** — what does it look like? (e.g., "yellow pencil", "blue bucket with red drop")
2. **Describe its visual appearance** — this is what the agent matches against
3. **Determine its function** — what happens when you click it?
4. **Ground its coordinates** — derive screen position from crop
5. **Note any dropdown/gallery** — does it have a `v` arrow?

### 5d. Capture dropdown galleries

Many tools have expandable galleries (shapes, brushes, fonts, etc.):

```bash
# Click the dropdown arrow
mcporter call mint.pyautogui_click --args '{"x":DROPDOWN_X,"y":DROPDOWN_Y}'
sleep 0.5

# Capture the expanded gallery — use generous height
desktop-screenshot $SKILL_DIR/assets/ribbon/<name>_dropdown.png \
  --region GALLERY_X,GALLERY_Y,GALLERY_W,GALLERY_H

# Close the gallery
mcporter call mint.pyautogui_press --args '{"keys":["esc"]}'
```

For each item in the gallery, document:
- Its position in the grid (row, column)
- Its name and function
- A coordinate formula for clicking any item programmatically

### 5e. Document the grid formula

If a section has a grid of items (shapes, colors, etc.), derive a
formula so agents can click any item by index:

```
item_x = GRID_LEFT + (col - 1) * CELL_WIDTH
item_y = GRID_TOP  + (row - 1) * CELL_HEIGHT
```

---

## Phase 6 — Color palettes and specialized controls

### 6a. Capture color swatches

Color palettes need special attention:

```bash
# Full palette with both rows
desktop-screenshot $SKILL_DIR/assets/colors/palette_full.png --region ...

# Extended palette with Edit Colors / custom picker
desktop-screenshot $SKILL_DIR/assets/colors/palette_extended.png --region ...
```

### 6b. Document each color

For preset color grids, document:
- **Position** (row, column in the grid)
- **Color name** (human-readable)
- **Approximate RGB values** (for verification or programmatic use)

You can verify colors using the pixel sampling tool:

```bash
mcporter call mint.pyautogui_pixel --args '{"x":COLOR_X,"y":COLOR_Y}'
# Returns [R, G, B] — compare against expected values
```

### 6c. Document foreground/background selectors

Most drawing apps have a primary (foreground/Color 1) and secondary
(background/Color 2) color. Document:
- Which is active (usually indicated by a highlight ring)
- How to switch between them
- How each is used (left-click vs right-click, eraser color, etc.)

---

## Phase 7 — Panels and status bar

### 7a. Capture side panels

```bash
# Left panel (e.g., zoom slider, tool options)
desktop-screenshot $SKILL_DIR/assets/panels/left_panel.png --region 0,200,50,700

# Right panel (e.g., layers, properties)
desktop-screenshot $SKILL_DIR/assets/panels/right_panel.png --region 1870,200,50,700
```

### 7b. Capture the status bar

The status bar typically shows contextual information:

```bash
# Full status bar
desktop-screenshot $SKILL_DIR/assets/panels/status_bar.png --region 0,STATUSBAR_Y,1920,30

# Left portion (position/size info)
desktop-screenshot $SKILL_DIR/assets/panels/status_bar_left.png --region 0,STATUSBAR_Y,500,25

# Right portion (zoom/view controls)
desktop-screenshot $SKILL_DIR/assets/panels/status_bar_right.png --region 1400,STATUSBAR_Y,520,25
```

### 7c. Document panel elements

For each panel element, record:
- What it displays (coordinates, dimensions, zoom %, layer info)
- Whether it's interactive (sliders, buttons, dropdowns)
- How it changes based on tool/context

---

## Phase 8 — Workspace interaction

### 8a. Determine how to find the workspace bounds

The main workspace (canvas, editor, viewport) has dynamic bounds that
depend on window size, zoom, toolbar state, and panel visibility.
Document the procedure for measuring it:

```bash
# Pixel scanning for a white canvas
for y in START .. END step 50; do
  mcporter call mint.pyautogui_pixel --args "{\"x\":CENTER_X,\"y\":$y}"
done
# First occurrence of background color = workspace top
```

### 8b. Record typical workspace bounds

Provide approximate default values for the most common window state
(usually maximized at 1920x1080):

```
workspace_left   ≈ ...
workspace_right  ≈ ...
workspace_top    ≈ ...
workspace_bottom ≈ ...
```

**Always add the caveat:** "These are approximate — always measure."

---

## Phase 9 — Write the SKILL.md

### 9a. Document structure

The output SKILL.md should follow this structure:

```markdown
---
name: <app-name>
version: 1.0.0
description: >
  Comprehensive reference for <Application Name> on <Platform>.
  Maps every UI element with cropped screenshot references and
  screen coordinates.
tags: [<app>, <platform>, drawing/editing/etc, reference, ui-map]
metadata:
  clawdbot:
    emoji: <relevant emoji>
    requires:
      bins: [mcporter]
      skills: [desktop-control-mint]
env:
  DESKTOP_MCP_URL:
    description: URL of the PyAutoGUI MCP server
    required: true
---

# <App Name> — Complete UI Reference (<Platform>)

## Application identity
  - Window title, launch command, process name
  - App icon with screenshot reference

## Window layout
  - ASCII diagram of zones
  - Coordinate table with Y/X ranges

## Title bar and window controls
  - Table with element, coords, icon ref, function

## Menu bar
  - Quick access toolbar elements

## <Menu Name> menu (one section per menu)
  - Table: Item | Shortcut | Function

## Toolbar/Ribbon — Section by section
  (one subsection per labeled section)
  - Section screenshot reference
  - Table: Icon | Screen coords | Function | Visual description
  - Dropdown/gallery contents if applicable
  - Grid coordinate formulas if applicable

## Color palette
  - Color 1 / Color 2 explanation
  - Preset grid with colors and RGB values
  - Custom color picker

## Panels
  - Side panels, status bar, docks

## Workspace interaction
  - How to find workspace bounds
  - Typical default bounds

## Keyboard shortcuts reference
  - Table: Shortcut | Action

## Tool selection procedure
  - Step-by-step with coordinate grounding
  - Quick-reference coordinate table

## Common workflows
  - 3-5 example task recipes

## Asset file inventory
  - Directory tree of all screenshot assets

## Notes for automation agents
  - Critical gotchas, state changes, verification requirements
```

### 9b. Cross-reference screenshots

Every element table should reference its screenshot:

```markdown
![Section name](assets/ribbon/01_section.png)

| Icon | Screen coords | Function |
|------|---------------|----------|
| Tool name (visual desc) | (x, y) | What it does |
```

### 9c. Include automation gotchas

End with a numbered list of things that trip up automation agents:
- Tool state changes from keyboard shortcuts
- Selection handles that must be committed
- Modal dialogs that block interaction
- Dynamic bounds that must be measured
- Controls that only activate in certain modes

---

## Quality checklist

Before considering the tear-down complete, verify:

- [ ] **App icon captured** from title bar
- [ ] **Every menu** opened and every item documented
- [ ] **Every toolbar section** zoomed and every icon identified
- [ ] **Every dropdown/gallery** expanded and contents listed
- [ ] **Color palette** fully mapped with RGB values
- [ ] **All panels** captured (side panels, status bar, docks)
- [ ] **Workspace bounds** procedure documented with typical values
- [ ] **Keyboard shortcuts** compiled from menus + knowledge
- [ ] **Coordinate grounding** shown for at least the key tools
- [ ] **Grid formulas** provided for any icon/color grids
- [ ] **Asset inventory** tree matches actual files on disk
- [ ] **Automation gotchas** section addresses state management
- [ ] **All screenshots** saved in the correct `assets/` subdirectory

---

## Iteration and refinement

A first-pass tear-down captures the static UI. Over time, refine by:

1. **Using the skill** — when another skill (like `draw-smiley-face`)
   references the app skill, you'll discover which coordinates are
   wrong and which tools need deeper documentation.

2. **Testing interactions** — click each documented tool and verify the
   highlight appears. Screenshot after clicking to confirm coordinates.

3. **Documenting state changes** — some tools change behavior based on
   context (e.g., outline/fill dropdowns only activate when a shape
   tool is selected). Add these as discovered.

4. **Handling multiple window states** — the skill should note how
   coordinates shift when the window is windowed vs. maximized, when
   panels open/close, when toolbars collapse.

---

## Example: MS Paint tear-down timeline

The MS Paint tear-down followed this exact methodology. Here is the
sequence of operations performed:

| Step | Phase | Action | Assets produced |
|------|-------|--------|-----------------|
| 1 | 0 | Created `ms-paint/assets/{icons,menus,ribbon,colors,panels}` | Directory structure |
| 2 | 1 | Captured app icon from title bar | `app_icon.png`, `titlebar_full.png` |
| 3 | 2 | Took master survey screenshot (full screen) | `00_complete_header.png` |
| 4 | 2 | Identified 8 zones: title, menu, ribbon (3 rows), zoom slider, canvas, status bar | Zone map |
| 5 | 3 | Progressive crop of ribbon — started at 960px wide, expanded to 1920px, increased height from 75 to 140 until all rows + labels visible | `00_ribbon_master.png` |
| 6 | 3 | Zoomed each ribbon section individually (8 sections) | `01_selection.png` through `10_layers.png` |
| 7 | 4 | Opened File menu → captured top + bottom (menu was taller than initial crop) | `file_menu.png`, `file_menu_bottom.png` |
| 8 | 4 | Opened Edit menu → captured (3 items only) | `edit_menu.png` |
| 9 | 4 | Opened View menu → captured + attempted Zoom submenu | `view_menu.png` |
| 10 | 5 | Expanded Brushes dropdown → discovered 9 brush types (needed 650px height) | `brushes_dropdown.png` |
| 11 | 5 | Captured Shapes gallery → identified 21 shapes in 3 rows | `shapes_gallery.png`, `shapes_detail.png` |
| 12 | 5 | Zoomed outline/fill/size controls | `outline_fill_controls.png` |
| 13 | 6 | Captured color palette → 2 rows of 11 colors each + Color 1/2 | `palette_full.png`, `palette_extended.png` |
| 14 | 7 | Captured left zoom slider panel | `left_panel.png` |
| 15 | 7 | Captured status bar (left: coords + size, right: zoom controls) | `status_bar.png`, `status_bar_left.png`, `status_bar_right.png` |
| 16 | 8 | Documented canvas pixel-scanning procedure | In SKILL.md |
| 17 | 9 | Wrote 735-line SKILL.md with all tables, screenshots, formulas, workflows | `SKILL.md` |

**Total: 46 screenshot assets, ~2 hours of capture + documentation.**

### Key lessons learned

1. **Start broad, narrow progressively.** The first ribbon crop was too
   narrow (960px) and too short (75px). It took 3 iterations to get the
   full ribbon with all 3 icon rows + section labels. Start with
   full-width, generous-height crops.

2. **The ribbon had 3 rows, not 1.** Initial assumptions about toolbar
   layout were wrong. Always take tall enough crops to discover hidden
   rows.

3. **Section boundaries are tricky.** The x-coordinate boundaries
   between ribbon sections don't always align with where you'd expect.
   Look for the thin vertical separator lines and section label text.

4. **Dropdowns need generous height.** The Brushes dropdown was much
   taller than expected (9 items). Always start with 400-600px height
   for dropdown captures.

5. **Some controls are context-sensitive.** The outline/fill dropdowns
   only activate when a shape tool is selected. Document this for agents.

6. **"Colorful" was actually "Copilot."** Never assume a label from a
   downscaled screenshot. Always zoom to confirm text.

---

## Adapting to other applications

This methodology works for any application with a graphical interface.
Adjust the phases based on the app type:

| App type           | Key differences |
|--------------------|-----------------|
| Code editor (VS Code) | Sidebar (explorer, search, extensions), tabs, terminal panel, activity bar, command palette |
| Spreadsheet (LibreOffice Calc) | Formula bar, cell grid, sheet tabs, toolbar |
| 3D modeling (Blender) | Viewport controls, timeline, properties panel, many context menus |
| Web browser (Firefox/Chrome) | Tab bar, address bar, extensions, dev tools, right-click menus |
| Terminal (GNOME Terminal) | Tab bar, preferences, profiles, right-click menu |
| Photo editor (GIMP) | Tools panel (vertical), layers panel, options bar, filter menus |

For each, the core loop is the same:
**Capture → Identify → Zoom → Label → Ground → Record → Save**
