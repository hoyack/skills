---
name: mines-game
description: >
  Play GNOME Mines (Minesweeper) to WIN using a Python solver for strategy,
  programmatic board reading for perception, and a strict state machine to
  prevent loops and misreads. The agent MUST use the solver script for every
  move decision — never guess visually. Requires desktop-control-mint skill.
metadata:
  clawdbot:
    emoji: "\U0001F4A3"
    requires:
      bins:
        - mcporter
        - desktop-screenshot
      skills:
        - desktop-control-mint
---

# GNOME Mines — Play to Win

This skill plays GNOME Mines using a **constraint-based solver** for
strategy and **programmatic pixel analysis** for board reading. The agent
does NOT rely on visual estimation for move decisions — the solver script
handles all logic.

**For less experienced agents:** Read the step-by-step guide at
`skills/mines-game/scripts/GUIDE.md` before starting. It explains every
command, every output field, and every common mistake in detail.

## Architecture overview

```
Screenshot --> mines_solver.py (read board + solve) --> JSON move recommendation
    |                                                        |
    v                                                        v
Verify hover --> Click target cell --> Screenshot --> Check result
    |                                                        |
    v                                                        v
Game state file (/tmp/mines_game_<id>.json) tracks everything
```

Every game session has:
- A **game ID** (unix timestamp) used for all file naming
- A **state file** (`/tmp/mines_game_<game_id>.json`) tracking moves,
  flags, reasoning, candidates, and board snapshots
- **Screenshots** named `/tmp/mines_<game_id>_<move>_<phase>.png`

---

## CRITICAL RULES (read before doing anything)

1. **NEVER choose a cell to click by visual inspection.** Always run the
   solver and follow its recommendation.
2. **ALWAYS take a screenshot and run the solver BEFORE every click.**
   No exceptions. No "I'll just click this one quickly."
3. **ALWAYS take a screenshot AFTER every click** and check for game over
   (red mine = lost, mine icons = lost). Do NOT continue clicking if the
   game is over.
4. **NEVER enter a loop.** If you've made the same type of action 3 times
   without progress, STOP and re-evaluate from scratch.
5. **Use timestamps for ALL screenshot filenames.** Format:
   `/tmp/mines_<game_id>_<move_number>_<phase>.png`
   where phase is: `board`, `hover`, `after`, `annotated`.
6. **Record every move** in the game state tracker with reasoning.
7. **NEVER declare victory unless you see the "Congratulations!" dialog.**
   The game is ONLY won when GNOME Mines shows the Congratulations popup
   with a "Player" text field. Having all safe cells revealed or all mines
   flagged is NOT proof of victory — only the Congratulations dialog is.
   See reference asset: `assets/states/09_game_over_win_congratulations.png`

---

## Setup (run once per session)

```bash
# 1. Ensure PATH includes desktop-screenshot
export PATH="$PATH:$(dirname "$(find ~/.openclaw/workspace/skills/desktop-control-mint/bin -name desktop-screenshot -type f 2>/dev/null)")"

# 2. Verify MCP connectivity
mcporter call mint.pyautogui_size

# 3. Set solver script path
SOLVER="$HOME/.openclaw/workspace/skills/mines-game/scripts/mines_solver.py"
```

---

## Screenshot naming convention

ALL screenshots use this format — no creative names, no random strings:

```
/tmp/mines_<game_id>_<move_number padded to 3 digits>_<phase>.png
```

| Phase       | When                                      |
|-------------|-------------------------------------------|
| `board`     | Full board capture before deciding a move |
| `hover`     | After moving mouse to target, before click|
| `after`     | Immediately after clicking                |
| `annotated` | Debug overlay from solver annotate command |

Examples:
```
/tmp/mines_1711843200_000_board.png    # Initial board, move 0
/tmp/mines_1711843200_001_board.png    # Board before move 1
/tmp/mines_1711843200_001_hover.png    # Hover verification, move 1
/tmp/mines_1711843200_001_after.png    # Result after move 1
/tmp/mines_1711843200_001_annotated.png # Debug overlay
```

---

## Game lifecycle — state machine

The agent MUST follow this state machine. Each state has exactly one
set of allowed transitions.

```
[START] --> [LAUNCH] --> [SELECT_DIFFICULTY] --> [INIT_GAME]
                                                      |
                                                      v
                              [GAME_OVER] <-- [PLAY_LOOP] <--+
                                  |               |          |
                                  v               +----------+
                              [DECIDE_RETRY]
```

### State: LAUNCH

```bash
# Kill any existing instance
wmctrl -c "Mines" 2>/dev/null; sleep 0.5

# Launch game
/usr/games/gnome-mines &
sleep 2

# Screenshot to see what state we're in
desktop-screenshot /tmp/mines_preflight.png
```

Read the screenshot. You should see either:
- The **difficulty selection menu** (4 cards) -> go to SELECT_DIFFICULTY
- An **active game board** -> go to INIT_GAME (game already in progress)

### State: SELECT_DIFFICULTY

Target: **Beginner (8x8, 10 mines)** unless user requests otherwise.

```bash
# Screenshot the menu
desktop-screenshot /tmp/mines_menu.png

# The Beginner card (8x8, 10 mines) is in the top-left quadrant.
# Use Python to find the exact center of the top-left card:
python3 -c "
from PIL import Image
img = Image.open('/tmp/mines_menu.png')
w, h = img.size
# Top-left card center is approximately at 1/4 width, 1/4 height
# but we scan for the card boundary to be precise
print(f'click_x={w // 4}')
print(f'click_y={h // 4}')
"

# Click the Beginner card
mcporter call mint.pyautogui_click --args '{"x":TARGET_X,"y":TARGET_Y}'
sleep 1

# Verify game started
desktop-screenshot /tmp/mines_verify_start.png
```

Verify from the screenshot that you see an 8x8 grid with "0/10" counter.

### State: INIT_GAME

Start a new game session with the solver:

```bash
# Create game session — returns game_id
GAME_OUTPUT=$(python3 $SOLVER new --rows 8 --cols 8)
GAME_ID=$(echo "$GAME_OUTPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['game_id'])")
echo "Game ID: $GAME_ID"
```

Set the move counter:
```bash
MOVE=0
```

Transition to PLAY_LOOP.

### State: PLAY_LOOP

This is the core gameplay loop. **Every iteration MUST follow ALL steps
in order. Do not skip any step.**

#### Step 1: Capture board

```bash
MOVE=$((MOVE + 1))
MOVE_PAD=$(printf "%03d" $MOVE)
BOARD_IMG="/tmp/mines_${GAME_ID}_${MOVE_PAD}_board.png"
desktop-screenshot "$BOARD_IMG"
```

Read the screenshot visually to get an overall sense of the board.

#### Step 2: Run solver

```bash
SOLVER_OUTPUT=$(python3 $SOLVER read "$BOARD_IMG" --game-id "$GAME_ID")
echo "$SOLVER_OUTPUT"
```

The solver returns JSON with:
- `state`: current game state (`playing`, `game_over_lose`, `game_over_win`)
- `board`: 2D array of cell states
- `board_pretty`: human-readable board
- `move`: recommended action with `row`, `col`, `confidence`, `reason`
- `move.all_safe`: list of ALL provably safe cells `[[r,c], ...]`
- `move.all_mines`: list of ALL confirmed mines `[[r,c], ...]`
- `target_coords`: screen `[x, y]` for the recommended cell
- `safe_coords`: map of `"r,c"` to `[x, y]` for ALL safe cells
- `mine_coords`: map of `"r,c"` to `[x, y]` for ALL mine cells
- `stats`: covered count, flag count, mine count

**CHECK THE STATE FIELD FIRST:**
- If `game_over_lose` or `game_over_win` -> transition to GAME_OVER
- If `menu` -> transition to SELECT_DIFFICULTY
- If `playing` -> continue

**CHECK THE MOVE RECOMMENDATION:**
- If `action: "click"` with `confidence: 1.0` -> provably safe, proceed
- If `action: "guess"` -> the solver has no safe moves. Look at
  `mine_probability`. If > 0.5, consider flagging known mines first.
- If `action: "none"` -> no moves available, game may be won or stuck

#### Step 3: Verify board reading

Before trusting the solver output, **cross-check the `board_pretty`
against what you see in the screenshot.** The solver reads pixels
programmatically, but color ambiguity (covered vs hover vs empty) can
cause misreads.

**Known color confusion problems:**
- Covered cell (dark gray ~186,189,182) vs hover (light gray ~211,215,207)
  vs empty revealed (light green ~228,237,199)
- When 1-2 dark covered cells are surrounded by light revealed cells
  ("island effect"), vision may misidentify them
- The solver uses pixel analysis which is more reliable than vision, but
  verify the `board_pretty` output looks reasonable

If the board looks wrong, run the annotate command for debugging:
```bash
python3 $SOLVER annotate "$BOARD_IMG" "/tmp/mines_${GAME_ID}_${MOVE_PAD}_annotated.png"
```

Then read the annotated image — it draws red grid lines and cell labels
so you can see exactly what the solver detected.

#### Step 4: Click safe cells (batch or single)

**Batch mode (recommended):** When the solver returns multiple safe cells
in `safe_coords`, click them ALL without re-solving. This is much faster.

```bash
# Extract all safe cell coordinates from safe_coords and click each one:
# safe_coords: {"2,0": [450,367], "2,6": [1175,367], "4,6": [1175,609]}
mcporter call mint.pyautogui_click --args '{"x":450,"y":367}'
sleep 0.2
mcporter call mint.pyautogui_click --args '{"x":1175,"y":367}'
sleep 0.2
mcporter call mint.pyautogui_click --args '{"x":1175,"y":609}'
sleep 0.5
# Then screenshot and re-run solver (back to Step 1)
```

**Single mode (with hover verification):** For the first move or when
extra caution is needed, verify hover before clicking:

```bash
TARGET_X=<from solver target_coords[0]>
TARGET_Y=<from solver target_coords[1]>
mcporter call mint.pyautogui_moveTo --args "{\"x\":$TARGET_X,\"y\":$TARGET_Y}"
sleep 0.3
```

#### Step 5: Verify hover

Take a screenshot to confirm the mouse is over the correct cell:

```bash
HOVER_IMG="/tmp/mines_${GAME_ID}_${MOVE_PAD}_hover.png"
desktop-screenshot "$HOVER_IMG"
```

**Read the hover screenshot and verify:**
1. You can see a lighter cell (hover effect) at the expected position
2. The hovered cell is COVERED (dark gray that lightened), not already
   revealed
3. The cell is at the correct grid position (row, col) that the solver
   recommended
4. The rest of the board looks the same as the pre-move screenshot

**If the hover looks wrong:**
- The mouse may be on the wrong cell or off the grid entirely
- Recalculate coordinates using the solver's coords command:
  ```bash
  python3 $SOLVER coords "$BOARD_IMG" ROW COL
  ```
- Move to the corrected position and re-verify

**DO NOT CLICK until hover is verified.**

#### Step 6: Click

```bash
mcporter call mint.pyautogui_click --args "{\"x\":$TARGET_X,\"y\":$TARGET_Y}"
sleep 0.5
```

#### Step 7: Record move in state tracker

```bash
python3 $SOLVER record --game-id "$GAME_ID" \
  --action click --row ROW --col COL \
  --reason "REASON_FROM_SOLVER" \
  --confidence CONFIDENCE
```

#### Step 8: Verify result

```bash
AFTER_IMG="/tmp/mines_${GAME_ID}_${MOVE_PAD}_after.png"
desktop-screenshot "$AFTER_IMG"
```

**Read the after-click screenshot and check:**

1. **RED MINE?** If you see any red cell with a mine icon, the game is
   OVER. You lost. Transition to GAME_OVER immediately.

2. **Mine icons visible?** Dark star/circle shapes on the board mean
   game over (all mines revealed on loss).

3. **Cell changed?** The target cell should now show either:
   - A number (1-8) on a colored background
   - Empty (cascade — multiple cells revealed at once)
   - The cell may have cascaded and revealed a large area

4. **Board unchanged?** If nothing changed, the click may have missed.
   Re-verify coordinates and try again (max 2 retries).

Run the solver on the after-screenshot to get the updated state:
```bash
python3 $SOLVER read "$AFTER_IMG" --game-id "$GAME_ID"
```

If `state` is still `playing`, loop back to Step 1.
If `state` is `game_over_lose` or `game_over_win`, transition to GAME_OVER.

### State: GAME_OVER

```bash
# Take a screenshot to verify the final state
desktop-screenshot "/tmp/mines_${GAME_ID}_final.png"

# Record final state
python3 $SOLVER status --game-id "$GAME_ID"
```

**VICTORY VERIFICATION (MANDATORY):**
You may ONLY declare victory if you see the **"Congratulations!"** dialog
popup from GNOME Mines. This dialog appears as a centered overlay with:
- The word "Congratulations!" at the top
- A "Personal Best" time entry table
- A "Player" text input field

**Reference screenshots:**
- `assets/states/09_game_over_win_congratulations.png` — the congrats dialog
- `assets/states/10_congratulations_with_best_times.png` — dialog with times

**Do NOT declare victory based on:**
- The solver saying no covered cells remain
- All mines appearing to be flagged
- The solver returning `action: "none"`
- Your own visual estimate that the board looks complete

These conditions can be met while the game is still in progress (e.g.,
a misread board). The Congratulations dialog is the ONLY ground truth.

If **won** (Congratulations dialog visible):
1. The dialog has a "Player" text field already selected/highlighted.
2. Select all existing text and type the model name:
   ```bash
   mcporter call mint.pyautogui_hotkey --args '{"keys":["ctrl","a"]}'
   sleep 0.2
   mcporter call mint.pyautogui_typewrite --args '{"message":"MODEL_NAME_HERE","interval":0.03}'
   sleep 0.3
   ```
3. Press Tab then Enter to dismiss the dialog:
   ```bash
   mcporter call mint.pyautogui_press --args '{"keys":["tab"]}'
   sleep 0.2
   mcporter call mint.pyautogui_press --args '{"keys":["enter"]}'
   ```
4. Take a final screenshot to confirm the dialog is closed.
5. Report victory and game stats.

If **lost** (red mine visible): Report loss and what went wrong (check
last move in state file).

### State: DECIDE_RETRY

Ask the user if they want to play again. If yes:
- Click "Play Again" button (right side of screen after game over)
- Go back to INIT_GAME with a new game ID

---

## Color reference (GNOME Mines on Linux Mint)

Understanding the colors is critical because the game has confusingly
similar shades. The solver handles this programmatically, but you need
to understand it for visual verification.

| Element                | RGB (approximate)    | Visual description    |
|------------------------|---------------------|-----------------------|
| Covered cell           | (186, 189, 182)     | Medium gray           |
| Covered + hover        | (211, 215, 207)     | Light gray            |
| Revealed empty (0)     | (228, 237, 199)     | Light yellow-green    |
| Number 1 background    | (210, 232, 170)     | Light green           |
| Number 2 background    | (232, 226, 170)     | Yellow/tan            |
| Number 3 background    | (226, 195, 152)     | Orange                |
| Flag on covered        | Dark icon on gray   | Flag shape on (186,189,182) |
| Mine (game over)       | Dark circle on gray | Star/circle on light bg |
| Exploded mine (red)    | (210, 60, 60)       | Bright red background |
| Grid border/gap        | (200, 200, 195)     | Thin light line       |
| Window background      | (222, 221, 218)     | Off-white             |

### The "island effect" problem

When most of the board is revealed (light colors) and only 1-2 cells
remain covered (dark gray), those dark cells can be hard to spot in a
scaled-down screenshot. The solver's pixel analysis handles this
correctly because it checks exact RGB values at calculated cell centers.

**If you suspect the solver misread the board**, use the annotate command
to generate a debug overlay, then visually confirm.

---

## The solver script

Path: `skills/mines-game/scripts/mines_solver.py`

### Commands

| Command    | Purpose                                          |
|------------|--------------------------------------------------|
| `new`      | Start a new game session, returns game_id        |
| `read`     | Read board from screenshot + solve + update state|
| `solve`    | Solve from a manually-entered board string       |
| `record`   | Record a move with reasoning in state file       |
| `status`   | View full game state (moves, flags, candidates)  |
| `state`    | Quick game state detection from screenshot       |
| `annotate` | Draw debug grid overlay on screenshot            |
| `coords`   | Get screen (x,y) for a grid cell (row,col)       |

### How the solver decides moves

1. **Constraint satisfaction**: For each numbered cell, count adjacent
   flags and covered cells. If `number == flags`, all remaining covered
   neighbors are safe. If `number - flags == covered_count`, all covered
   neighbors are mines.

2. **Subset analysis**: If constraint A's covered cells are a subset of
   constraint B's, the difference can be deduced as safe or mines.

3. **Probability estimation**: When no cell is provably safe, estimate
   mine probability for each covered cell using local constraints and
   global mine density. Choose the lowest-probability cell.

4. **Information gain**: Among equally-safe cells, prefer those adjacent
   to more numbered cells (reveals more useful constraints).

### Game state file

Each game writes `/tmp/mines_game_<game_id>.json` containing:

```json
{
  "game_id": "1711843200",
  "status": "playing",
  "difficulty": "beginner",
  "move_number": 5,
  "moves": [
    {
      "move_number": 1,
      "action": "click",
      "row": 4, "col": 4,
      "reason": "First move -- center cell for maximum cascade",
      "confidence": 0.85,
      "result": "cascade"
    }
  ],
  "flags": [
    {"row": 1, "col": 2, "reason": "Constraint: 1 at (1,1) satisfied", "move_number": 3}
  ],
  "candidates": [
    {"row": 2, "col": 0, "action": "click", "confidence": 1.0, "reason": "Provably safe"}
  ],
  "known_mines": [[1, 2]],
  "known_safe": [[2, 0], [2, 1]],
  "board_snapshots": [],
  "screenshots": []
}
```

This file is the agent's memory for the current game. It prevents:
- Repeating moves already made
- Losing track of which cells are flagged and why
- Forgetting solver recommendations between turns

---

## Strategy guide

### First move

Always click the **center cell** (or near-center). Statistically this
produces the largest cascade on an 8x8 beginner board, giving the most
information for subsequent moves.

### After the first cascade

1. Run the solver — it will find all provably safe cells
2. Click them one at a time, verifying each result
3. After each click that reveals new numbers, re-run the solver
   (new constraints may unlock more safe cells)

### When the solver says "guess"

This means no cell is provably safe. The solver picks the cell with the
lowest mine probability. Before clicking a guess:

1. Check `mine_probability` in the solver output
2. If probability > 0.4, consider whether flagging known mines first
   might unlock new constraints
3. Flag all cells the solver identified as `all_mines`
4. Re-run the solver — flagging mines may reveal new safe cells
5. If still no safe cells, proceed with the guess

### Flagging strategy

The solver reports `all_mines` — cells it has proven contain mines.
Flag these BEFORE making a guess move:

```bash
# Right-click to place flag
mcporter call mint.pyautogui_rightClick --args "{\"x\":$FLAG_X,\"y\":$FLAG_Y}"

# Record the flag
python3 $SOLVER record --game-id "$GAME_ID" \
  --action flag --row ROW --col COL \
  --reason "Solver proved mine via constraint at (R,C)=N"
```

### Endgame (few cells remaining)

The last few cells are the hardest. The solver's subset analysis helps
but sometimes the remaining cells are a pure coin flip. In that case:
- The solver will report `action: "guess"` with the best odds
- Accept the risk and click — there's no way to determine the answer
  without guessing

---

## Loop prevention

The agent MUST NOT:
- Click the same cell twice in the same game
- Take more than 3 screenshots without making a move
- Run the solver more than 3 times on the same board state without acting
- Continue playing after the solver reports `game_over_lose` or `game_over_win`

**Self-check after every 5 moves:**
```bash
# View game state to verify progress
python3 $SOLVER status --game-id "$GAME_ID"
```

Check that:
- `move_number` is increasing
- `covered` count is decreasing (or flags are increasing)
- `status` is still `playing`
- Last few moves had different `(row, col)` targets

If progress has stalled, take a fresh screenshot, run annotate to debug
the board reading, and re-evaluate.

---

## Troubleshooting

### Solver says "Could not read board"

The grid detection failed. Possible causes:
- Window is not focused or is minimized
- A dialog box is covering the board
- The game is showing the difficulty menu, not a board

Fix: Take a screenshot, verify visually, dismiss any dialogs, and retry.

### Solver board reading looks wrong

Run annotate to see what the solver detected:
```bash
python3 $SOLVER annotate "$BOARD_IMG" "/tmp/mines_debug.png"
```

If the grid lines are misaligned, the grid detection may have been
confused by the window border. The solver will refine on subsequent
reads as more cells are revealed (more color variation to detect).

### Clicks not registering

1. Check window focus: `mcporter call mint.pyautogui_getActiveWindowTitle`
2. If not "Mines", click the window title bar to focus it
3. Verify coordinates with hover before clicking
4. Check that MCP server is responding: `mcporter call mint.pyautogui_size`

### Agent keeps clicking after game over

This is the #1 failure mode. The agent MUST check for red mines in
every after-click screenshot. The solver's `state` field will report
`game_over_lose` if it detects red pixels or multiple mine icons.

If you suspect the game is over but the solver says `playing`, scan
the board visually for:
- Red cells (exploded mine)
- Dark circle/star icons (revealed mines)
- "Play Again" button replacing "Start Over" on the right side

---

## Assets (visual reference only)

```
skills/mines-game/assets/
+-- states/
|   +-- 00_difficulty_select.png    # Menu with 4 difficulty cards
|   +-- 01_game_start_8x8.png      # Fresh 8x8 board (all covered)
|   +-- 02_first_move.png          # Board after first click (cascade)
|   +-- 03_game_in_progress.png    # Mid-game board
|   +-- 04_start_over_clicked.png  # Start Over confirmation dialog
|   +-- 05_start_over_confirmation_dialog.png
|   +-- 06_game_restarted.png
|   +-- 07_game_over_lose.png      # Lost game (red mine + all mines shown)
|   +-- 08_best_times_dialog.png   # Best Times popup
|   +-- 09_game_over_win_congratulations.png  # WIN: Congratulations dialog
|   +-- 10_congratulations_with_best_times.png # WIN: dialog with times list
+-- grid/
|   +-- hover_cell.png             # Hover effect on covered cell
|   +-- flag_placed.png            # Flag on cell + flag counter
+-- ui/
    +-- titlebar_full.png          # Window titlebar
```

**IMPORTANT: Asset 09 is the victory confirmation screenshot.** The agent
MUST see this "Congratulations!" dialog before declaring a win. If you do
not see this dialog, the game is NOT won — do not report victory.

Use these to understand what each game state looks like. Do NOT extract
coordinates from them — always calculate dynamically from live screenshots.

---

## Quick reference — the complete move cycle

```
1. SCREENSHOT  -> /tmp/mines_<gid>_<NNN>_board.png
2. SOLVER READ -> python3 $SOLVER read <img> --game-id <gid>
3. CHECK STATE -> if game_over, STOP
4. VERIFY BOARD -> cross-check board_pretty with screenshot
5. MOVE MOUSE  -> mcporter moveTo target_coords
6. HOVER CHECK -> screenshot, verify correct cell highlighted
7. CLICK       -> mcporter click target_coords
8. RECORD MOVE -> python3 $SOLVER record ...
9. SCREENSHOT  -> /tmp/mines_<gid>_<NNN>_after.png
10. CHECK RESULT -> if red mine or mine icons, STOP (game over)
11. REPEAT from 1
```

Every step is mandatory. No shortcuts. The solver does the thinking;
the agent does the clicking and verifying.
