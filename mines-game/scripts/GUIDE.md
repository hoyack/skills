# Mines Solver — Agent Guide

This guide teaches AI agent bots how to use `mines_solver.py` to play
GNOME Mines (Minesweeper) and **win**. Follow every step exactly.

---

## What this script does

The script has three jobs:

1. **Reads the board** from a screenshot using pixel analysis (not vision)
2. **Solves** for which cells are safe and which are mines
3. **Tracks game state** so you don't forget what happened

You MUST use this script for every move decision. Never guess visually.

---

## Quick start — minimum commands to play a game

```bash
# Set up
SOLVER="$HOME/.openclaw/workspace/skills/mines-game/scripts/mines_solver.py"
export PATH="$PATH:$HOME/.openclaw/workspace/skills/desktop-control-mint/bin"

# 1. Launch game and select Beginner difficulty (do this yourself)
/usr/games/gnome-mines &
sleep 2
# Click the "8 x 8 / 10 mines" card

# 2. Create a game session
GAME_ID=$(python3 $SOLVER new --rows 8 --cols 8 | python3 -c "import sys,json; print(json.load(sys.stdin)['game_id'])")

# 3. Take screenshot
desktop-screenshot /tmp/mines_${GAME_ID}_001_board.png

# 4. Read board + get best move
python3 $SOLVER read /tmp/mines_${GAME_ID}_001_board.png --game-id $GAME_ID

# 5. The output tells you EXACTLY where to click (target_coords field)
# 6. Click there, screenshot, repeat from step 3
```

---

## Understanding the output

When you run `python3 $SOLVER read screenshot.png`, the output looks like:

```json
{
  "state": "playing",
  "grid": {"rows": 8, "cols": 8, "bounds": [392,67,1357,1031], "cell_size": [121,121]},
  "board": [["C","1","E","E","E","E","1","C"], ...],
  "board_pretty": " C  1  E  E  E  E  1  C\n ...",
  "stats": {"total_mines": 10, "covered": 34, "flags": 0, "revealed": 30},
  "move": {
    "action": "click",
    "row": 4,
    "col": 6,
    "confidence": 1.0,
    "reason": "Provably safe cell at (4,6)",
    "all_safe": [[2,0],[2,6],[2,7],[3,6],[4,6],[6,4],[6,5],[6,6]],
    "all_mines": [[2,5],[5,1]]
  },
  "target_coords": [1175, 609],
  "safe_coords": {"2,0": [450,367], "2,6": [1175,367], ...},
  "mine_coords": {"2,5": [1055,367], "5,1": [571,729]}
}
```

### Fields you MUST check (in order):

| Field | What to check | What it means |
|-------|---------------|---------------|
| `state` | Is it "playing"? | If "game_over_lose" or "game_over_win", STOP. |
| `move.action` | "click", "guess", or "none" | "click" = safe. "guess" = risky. "none" = done. |
| `move.confidence` | 1.0 = certain, <1.0 = guess | Only click guesses if no safe moves exist. |
| `target_coords` | [x, y] screen coordinates | Pass these directly to pyautogui_click. |
| `move.all_safe` | List of [row, col] pairs | ALL provably safe cells. Click them ALL. |
| `move.all_mines` | List of [row, col] pairs | ALL confirmed mines. Flag these (right-click). |
| `safe_coords` | Map of "r,c" to [x, y] | Screen coordinates for each safe cell. |
| `mine_coords` | Map of "r,c" to [x, y] | Screen coordinates for each mine cell. |

### Cell codes in the board:

| Code | Meaning | Can you click it? |
|------|---------|-------------------|
| `C` | Covered (gray, unclicked) | Yes |
| `E` | Empty (revealed, 0 neighbors) | No (already revealed) |
| `1`-`8` | Number (revealed) | No (already revealed) |
| `F` | Flag (right-clicked) | No (already flagged) |
| `M` | Mine icon (game over) | GAME IS OVER |
| `X` | Exploded mine (red) | GAME IS OVER |

---

## The complete move cycle

Every single move must follow ALL of these steps. No shortcuts.

### Step 1: Screenshot

```bash
MOVE=$((MOVE + 1))
BOARD_IMG="/tmp/mines_${GAME_ID}_$(printf '%03d' $MOVE)_board.png"
desktop-screenshot "$BOARD_IMG"
```

### Step 2: Read + Solve

```bash
RESULT=$(python3 $SOLVER read "$BOARD_IMG" --game-id "$GAME_ID")
echo "$RESULT"
```

### Step 3: Check if game is over

Look at the `state` field in the output:
- `"playing"` → Continue to step 4
- `"game_over_lose"` → STOP. You hit a mine. Game over.
- `"game_over_win"` → STOP. You won!
- `"menu"` → You're on the difficulty selection screen
- `"dialog"` → A popup is open. Dismiss it with Escape.

**If you skip this check and keep clicking after game over, you will
get stuck in an infinite loop.**

### Step 4: Get the target coordinates

From the JSON output, extract `target_coords`:
```python
import json
data = json.loads(result_string)
x, y = data["target_coords"]
```

Or use `safe_coords` to get coordinates for ALL safe cells at once.

### Step 5: Move mouse and verify hover

```bash
mcporter call mint.pyautogui_moveTo --args "{\"x\":$X,\"y\":$Y}"
sleep 0.3
desktop-screenshot "/tmp/mines_${GAME_ID}_$(printf '%03d' $MOVE)_hover.png"
```

Look at the hover screenshot. You should see ONE cell that's slightly
lighter than the others. That's where your mouse is. Verify it's over
the correct cell (a covered/gray cell, not an already-revealed one).

### Step 6: Click

```bash
mcporter call mint.pyautogui_click --args "{\"x\":$X,\"y\":$Y}"
sleep 0.5
```

### Step 7: Verify result

```bash
AFTER_IMG="/tmp/mines_${GAME_ID}_$(printf '%03d' $MOVE)_after.png"
desktop-screenshot "$AFTER_IMG"
```

**Look at the screenshot. Check for RED cells. If you see any red,
the game is OVER — you hit a mine. STOP immediately.**

### Step 8: Record the move

```bash
python3 $SOLVER record --game-id "$GAME_ID" \
    --action click --row $ROW --col $COL \
    --reason "Provably safe" --confidence 1.0
```

### Step 9: Go back to Step 1

---

## Clicking multiple safe cells

When the solver returns multiple safe cells in `all_safe`, you can
click them all without re-running the solver. Use `safe_coords`:

```bash
# The solver returned safe_coords like:
# {"2,0": [450,367], "2,6": [1175,367], "4,6": [1175,609], ...}

# Click each one:
mcporter call mint.pyautogui_click --args '{"x":450,"y":367}'
sleep 0.2
mcporter call mint.pyautogui_click --args '{"x":1175,"y":367}'
sleep 0.2
mcporter call mint.pyautogui_click --args '{"x":1175,"y":609}'
sleep 0.2
# ... etc.

# THEN take a screenshot and re-run the solver to get the next batch
```

**After clicking the batch, you MUST screenshot and re-run the solver.**
New numbers may have been revealed, enabling more deductions.

---

## When the solver says "guess"

This means no cell is provably safe. Before clicking a guess:

1. **Flag all known mines first.** The solver's `all_mines` list tells
   you which cells are mines. Right-click them:
   ```bash
   mcporter call mint.pyautogui_rightClick --args "{\"x\":$MINE_X,\"y\":$MINE_Y}"
   ```

2. **Re-run the solver** after flagging. Sometimes flagging mines
   unlocks new constraint deductions and reveals safe cells.

3. **If still no safe cells**, click the guess. The solver picks the
   cell with the lowest mine probability. Check `mine_probability` —
   lower is better (0.1 = 10% chance it's a mine).

---

## Debugging: when things go wrong

### The solver says "Could not detect grid"

The grid detection failed. Causes:
- The game is showing the difficulty menu (no grid to detect)
- A dialog is covering the board
- The window is minimized or not focused

Fix: Take a screenshot, look at it, dismiss any dialogs, and retry.

### The board looks wrong

Run the annotate command to see what the solver detected:
```bash
python3 $SOLVER annotate /tmp/board.png /tmp/debug.png
```
View `/tmp/debug.png`. It shows red grid lines and cell labels. If the
grid lines are wrong, the grid detection failed.

### The solver finds no safe cells on a board with obvious safe cells

The board reading might be wrong. Common causes:
- A "3" was read as "2" (or vice versa) — colors are similar
- An empty cell was read as covered (or vice versa)
- A number was missed entirely

Check `board_pretty` against what you see in the screenshot. If they
don't match, the pixel analysis has a bug. Report the screenshot.

### The agent keeps clicking after game over

This is the #1 failure mode. You MUST check the `state` field after
every `read` command. If it says anything other than "playing", STOP.

Also visually check every post-click screenshot for:
- **Red cells** (exploded mine)
- **Dark star/circle icons** (revealed mines)
- **"Play Again" button** on the right side (replaces "Start Over")

---

## Screenshot naming convention

ALL screenshots must use this format:
```
/tmp/mines_<game_id>_<move_number_padded_to_3>_<phase>.png
```

| Phase | When |
|-------|------|
| `board` | Before deciding a move |
| `hover` | After moving mouse, before clicking |
| `after` | After clicking |
| `annotated` | Debug overlay from solver |

Examples:
```
/tmp/mines_1711843200_001_board.png
/tmp/mines_1711843200_001_hover.png
/tmp/mines_1711843200_001_after.png
/tmp/mines_1711843200_001_annotated.png
```

This naming lets you trace exactly what happened on each move.

---

## All commands reference

### `new` — Start a new game

```bash
python3 $SOLVER new --rows 8 --cols 8
# Optional: --mines 10 (auto-detected from grid size)
```
Returns: `game_id`, `state_file` path

### `read` — Read board + solve (THE MAIN COMMAND)

```bash
python3 $SOLVER read /tmp/screenshot.png --game-id 12345
```
Returns: board state, recommended move, screen coordinates for all
safe cells and mines

### `solve` — Solve from a text board (no screenshot)

```bash
python3 $SOLVER solve "C,1,E,E;C,2,1,C;C,C,C,C" --mines 3
```
Useful when you already know the board state and don't need pixel
analysis. Same solve output as `read`.

### `record` — Record a move

```bash
python3 $SOLVER record --game-id 12345 --action click --row 3 --col 4 \
    --reason "Provably safe" --confidence 1.0 --result safe
```
Actions: `click`, `flag`, `unflag`
Results: `pending`, `safe`, `mine_hit`, `cascade`

### `status` — View game history

```bash
python3 $SOLVER status --game-id 12345
```
Shows all moves, flags, candidates, known mines/safe cells.

### `state` — Quick state check

```bash
python3 $SOLVER state /tmp/screenshot.png
```
Just returns the game state (playing/game_over/menu/dialog). Faster
than `read` when you only need to check if the game is over.

### `annotate` — Debug overlay

```bash
python3 $SOLVER annotate /tmp/board.png /tmp/debug.png
```
Draws red grid lines and cell labels on the screenshot.

### `coords` — Get screen position for a cell

```bash
python3 $SOLVER coords /tmp/board.png 3 4
```
Returns `screen_x`, `screen_y` for cell (row=3, col=4).

---

## Known failure mode: number misreads

The most dangerous bug is when the solver misreads a number. For
example, reading a "4" as a "3" means the solver thinks one FEWER mine
is around that cell, and may incorrectly mark a mine as "safe".

**How to detect this:** After each `read`, check `board_pretty` against
the screenshot. Pay special attention to:
- Cells with orange backgrounds — these are 3s and 4s, which have
  similar colors. The B (blue) channel distinguishes them:
  - Number 3: B around 170-185
  - Number 4: B around 130-150
- Any cell where the solver returns a "guess" when you expected safe
  cells — this might mean a number was misread

**If you suspect a misread:** Use the `annotate` command to see what
the solver detected, and compare visually.

---

## Common mistakes to avoid

1. **Clicking without running the solver.** The solver exists so you
   don't have to guess. Use it for EVERY move.

2. **Not checking `state` after each read.** If the game is over and
   you keep clicking, you'll loop forever.

3. **Clicking revealed cells.** Only click cells marked 'C' (covered).
   Clicking a number or empty cell does nothing.

4. **Not re-running solver after batch clicks.** Each click can reveal
   new numbers that change the constraint analysis. Always re-solve.

5. **Guessing when the solver has safe cells.** If `all_safe` is not
   empty, click those first. Only guess when forced to.

6. **Using creative screenshot filenames.** Stick to the naming
   convention. It helps you debug later.

7. **Not flagging mines before guessing.** Flagging known mines can
   unlock new safe cell deductions via constraint propagation.

8. **Declaring victory without seeing the Congratulations dialog.**
   The game is ONLY won when GNOME Mines shows a "Congratulations!"
   popup dialog. Do NOT declare victory just because the solver says
   no covered cells remain, or because all mines appear flagged, or
   because the solver returns `action: "none"`. These conditions can
   occur due to board misreads while the game is still in progress.
   You MUST take a screenshot and visually confirm the Congratulations
   dialog is present before reporting a win.
   Reference: `assets/states/09_game_over_win_congratulations.png`
