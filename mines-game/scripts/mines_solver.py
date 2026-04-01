#!/usr/bin/env python3
"""
GNOME Mines Solver — Board reader, constraint solver, and game state tracker.

This script is the brain behind the mines-game skill. It reads the board
from a screenshot using pixel analysis, solves for safe/mine cells using
constraint satisfaction, and tracks game state across moves.

=============================================================================
ARCHITECTURE
=============================================================================

  Screenshot (PNG)
       |
       v
  BoardReader           -- Finds the grid, reads each cell's state
       |
       v
  MinesSolver           -- Constraint satisfaction + probability estimation
       |
       v
  JSON output           -- Best move, all safe cells, all confirmed mines,
                           target screen coordinates
       |
       v
  GameStateTracker      -- Persists moves, flags, reasoning to JSON file

=============================================================================
CELL STATES
=============================================================================

  C = Covered (unclicked, dark gray)
  E = Empty   (revealed, 0 adjacent mines, neutral light gray)
  1-8 = Number (revealed, N adjacent mines, colored background)
  F = Flag    (right-clicked, flag icon on dark gray)
  M = Mine    (game over only: dark mine icon on light background)
  X = Exploded mine (game over only: red background)
  ? = Unknown (reader could not determine — indicates a bug)

=============================================================================
COLOR REFERENCE (GNOME Mines on Linux Mint, 1920x1080)
=============================================================================

  Cell type          | Center pixel RGB      | Background corner RGB
  -------------------|-----------------------|----------------------
  Covered            | (186, 189, 182)       | (186, 189, 182)
  Covered + hover    | (211, 215, 207)       | (211, 215, 207)
  Empty (0)          | (222, 222, 220)       | (222, 222, 220)
  Number 1           | (46, 52, 54) [text]   | (221, 250, 195) [green]
  Number 2           | (46-135) [text]       | (236, 237, 191) [yellow]
  Number 3           | (46-100) [text]       | (237, 218, 180) [orange, B~180]
  Number 4           | dark or bg-colored    | (237, 195, 138) [deep orange, B~138]
  Number 5+          | dark or bg-colored    | (R>210, G<195, B<120) [red-orange]
  Flag               | dark icon pixels      | (186, 189, 182) [gray]
  Mine (game over)   | dark icon pixels      | (222+, 222+, 220+) [light]
  Exploded mine      | (210, 60, 60)         | red everywhere
  Grid gap           | (246, 245, 244)       | — (4px wide bright band)
  Window background  | (246, 245, 244) or    | — (outside grid area)
                     | (219, 215, 211)       |

  KEY INSIGHT: The grid gaps between cells are bright bands of
  RGB ~(246, 245, 244), exactly 4 pixels wide. The first gap (between
  the title bar and row 0) can be wider (~20px). These gaps are the
  most reliable way to find cell boundaries.

  KEY INSIGHT: Number cells have DARK TEXT at center but COLORED
  BACKGROUNDS at corners. To distinguish numbers from mines/flags,
  always check the background color at an offset from center.
  - Green background (G > R, G > 230) = number 1
  - Yellow background (R > 220, G > 220, B < 200) = number 2
  - Orange background (R > G + 10) = number 3+
  - Gray background (186, 189, 182) = flag on covered cell
  - Neutral light bg (222+) = mine icon (game over only)

=============================================================================
COMMANDS
=============================================================================

  new       Start a new game session. Returns game_id.
  read      Read board from screenshot, solve, return best move.
  solve     Solve from a manually-entered board string.
  record    Record a move (click/flag) with reasoning.
  status    View full game state history.
  state     Quick game state detection from screenshot.
  annotate  Draw debug grid overlay on screenshot.
  coords    Get screen (x,y) for a grid cell (row,col).

=============================================================================
USAGE EXAMPLES
=============================================================================

  # 1. Start a new game session:
  python3 mines_solver.py new --rows 8 --cols 8
  # Returns: {"game_id": "1711843200", ...}

  # 2. Take a screenshot and read the board:
  python3 mines_solver.py read /tmp/mines_board.png --game-id 1711843200
  # Returns: board state, recommended move, target screen coordinates

  # 3. Record that you clicked the recommended cell:
  python3 mines_solver.py record --game-id 1711843200 \\
      --action click --row 4 --col 4 --reason "Provably safe"

  # 4. Solve from a board string (no screenshot needed):
  python3 mines_solver.py solve \\
      "C,1,E,E;C,2,1,E;C,C,C,C;C,C,C,C" --mines 3

  # 5. Debug: annotate a screenshot with grid overlay:
  python3 mines_solver.py annotate /tmp/board.png /tmp/debug.png
  # Then view /tmp/debug.png to see the grid lines and cell labels

=============================================================================
IMPORTANT NOTES FOR AGENT BOTS
=============================================================================

  1. ALWAYS use the solver for move decisions. Never guess visually.

  2. The solver's "read" command does THREE things at once:
     - Reads the board from the screenshot
     - Solves for safe/mine cells
     - Returns the best move with screen coordinates
     You do NOT need to call "solve" separately after "read".

  3. The "target_coords" field in the output is [x, y] screen
     coordinates you can pass directly to pyautogui_click.

  4. The "all_safe" list contains ALL provably safe cells, not just
     the recommended one. You can click them all in sequence.

  5. The "all_mines" list contains ALL confirmed mines. You should
     right-click (flag) these before making guess moves.

  6. If "action" is "guess", the solver found NO provably safe cells.
     Check "mine_probability" — lower is better. Consider flagging
     known mines first, as this can unlock new safe cells.

  7. ALWAYS check the "state" field FIRST. If it says "game_over_lose"
     or "game_over_win", STOP PLAYING. Do not click anything.

  8. Screenshot naming convention:
     /tmp/mines_<game_id>_<move_NNN>_<phase>.png
     Phases: board, hover, after, annotated

Game state files: /tmp/mines_game_<game_id>.json
"""

import sys
import json
import time
import argparse
from pathlib import Path
from typing import Optional, Tuple, List

try:
    from PIL import Image, ImageDraw
except ImportError:
    print(json.dumps({"error": "Pillow not installed. Run: pip install Pillow"}),
          file=sys.stderr)
    sys.exit(1)


# ==========================================================================
# Game state tracker
# ==========================================================================

GAME_STATE_DIR = Path("/tmp")
GAME_STATE_PREFIX = "mines_game_"


class GameStateTracker:
    """Tracks the state of a single Mines game session.

    Creates a JSON file at /tmp/mines_game_<game_id>.json that records:
    - Move history with reasoning and results
    - Flag placements with constraint explanations
    - Current candidate moves from the solver
    - Board snapshots after each move
    - Screenshot file paths
    - Known mine and safe cell lists

    Each game gets a unique ID (unix timestamp at game start).
    Multiple concurrent games are supported via separate files.
    State does NOT persist between games — only within a single game.

    USAGE FOR AGENTS:
        # At game start:
        tracker = GameStateTracker()  # auto-generates game_id
        tracker.set_difficulty(8, 8, 10)

        # After each solver run:
        tracker.record_screenshot("/tmp/mines_123_001_board.png")
        tracker.record_board_snapshot(board_2d_list)
        tracker.update_known_cells(safe_list, mine_list)

        # After each click:
        tracker.record_move("click", row, col, "Provably safe", 1.0)

        # After verifying result:
        tracker.update_last_move_result("safe")  # or "mine_hit", "cascade"

        # To check current state:
        summary = tracker.get_summary()
    """

    def __init__(self, game_id: Optional[str] = None):
        if game_id is None:
            game_id = str(int(time.time()))
        self.game_id = game_id
        self.state_file = GAME_STATE_DIR / f"{GAME_STATE_PREFIX}{game_id}.json"
        self.state = self._load_or_create()

    def _load_or_create(self):
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {
            "game_id": self.game_id,
            "created_at": int(time.time()),
            "difficulty": None,
            "grid_size": None,
            "total_mines": None,
            "status": "starting",
            "move_number": 0,
            "moves": [],
            "flags": [],
            "candidates": [],
            "board_snapshots": [],
            "screenshots": [],
            "known_mines": [],
            "known_safe": [],
            "last_error": None,
        }

    def save(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def set_difficulty(self, rows, cols, mines):
        self.state["grid_size"] = [rows, cols]
        self.state["total_mines"] = mines
        if rows == 8 and cols == 8:
            self.state["difficulty"] = "beginner"
        elif rows == 16 and cols == 16:
            self.state["difficulty"] = "intermediate"
        elif rows == 16 and cols == 30:
            self.state["difficulty"] = "expert"
        else:
            self.state["difficulty"] = "custom"
        self.state["status"] = "playing"
        self.save()

    def record_screenshot(self, path: str):
        self.state["screenshots"].append({
            "path": path,
            "timestamp": int(time.time()),
            "move_number": self.state["move_number"],
        })
        self.save()

    def record_move(self, action: str, row: int, col: int, reason: str,
                    confidence: float = 1.0, result: str = "pending"):
        self.state["move_number"] += 1
        move = {
            "move_number": self.state["move_number"],
            "timestamp": int(time.time()),
            "action": action,
            "row": row,
            "col": col,
            "reason": reason,
            "confidence": confidence,
            "result": result,
        }
        self.state["moves"].append(move)
        if action == "flag":
            self.state["flags"].append({
                "row": row, "col": col,
                "reason": reason,
                "move_number": self.state["move_number"],
            })
            if [row, col] not in self.state["known_mines"]:
                self.state["known_mines"].append([row, col])
        self.save()

    def update_last_move_result(self, result: str):
        if self.state["moves"]:
            self.state["moves"][-1]["result"] = result
            if result == "mine_hit":
                self.state["status"] = "lost"
            self.save()

    def set_candidates(self, candidates: list):
        self.state["candidates"] = candidates
        self.save()

    def record_board_snapshot(self, board: list):
        self.state["board_snapshots"].append({
            "move_number": self.state["move_number"],
            "timestamp": int(time.time()),
            "board": board,
        })
        if len(self.state["board_snapshots"]) > 10:
            self.state["board_snapshots"] = self.state["board_snapshots"][-10:]
        self.save()

    def update_known_cells(self, safe: list, mines: list):
        for cell in safe:
            if cell not in self.state["known_safe"]:
                self.state["known_safe"].append(cell)
        for cell in mines:
            if cell not in self.state["known_mines"]:
                self.state["known_mines"].append(cell)
        self.save()

    def set_game_over(self, won: bool):
        self.state["status"] = "won" if won else "lost"
        self.save()

    def get_summary(self):
        s = self.state
        last_move = s["moves"][-1] if s["moves"] else None
        return {
            "game_id": s["game_id"],
            "status": s["status"],
            "difficulty": s["difficulty"],
            "move_number": s["move_number"],
            "total_mines": s["total_mines"],
            "flags_placed": len(s["flags"]),
            "known_mines": len(s["known_mines"]),
            "known_safe": len(s["known_safe"]),
            "last_move": last_move,
            "candidates": s["candidates"],
            "state_file": str(self.state_file),
        }


# ==========================================================================
# Color constants
# ==========================================================================

# Grid gap color — the bright 4px bands between cells.
# This is the MOST RELIABLE feature for detecting grid structure.
GAP_COLOR_MIN = 240   # All channels >= this = gap pixel
GAP_WIDTH_MIN = 2     # Minimum gap width in pixels
GAP_WIDTH_MAX = 8     # Maximum gap width (first/last gap can be wider)
GAP_FIRST_MAX = 30    # The top/left border gap can be up to this wide

# Cell background colors (at corner offsets, away from text)
# Covered cell (unclicked)
BG_COVERED = (186, 189, 182)
# Empty revealed (0 adjacent mines)
BG_EMPTY = (222, 222, 220)
# Number backgrounds
BG_NUM_1 = (221, 250, 195)   # green
BG_NUM_2 = (236, 237, 191)   # yellow
BG_NUM_3 = (237, 218, 180)   # orange

# Window background (outside grid) — same bright as gap
BG_WINDOW = (246, 245, 244)


def _is_gap_pixel(r, g, b) -> bool:
    """Return True if this pixel is part of a grid gap or window background."""
    return r >= GAP_COLOR_MIN and g >= GAP_COLOR_MIN and b >= (GAP_COLOR_MIN - 6)


def _is_covered_pixel(r, g, b) -> bool:
    """Return True if this pixel matches the covered cell color."""
    return (170 < r < 200 and 175 < g < 205 and 165 < b < 195)


def _is_empty_pixel(r, g, b) -> bool:
    """Return True if this pixel matches the empty revealed cell color.

    The empty cell color is (222, 222, 220) — all three channels nearly
    equal and close to 222. The titlebar is (219, 215, 211) which has
    more spread between channels, so we require channels to be within
    8 of each other to exclude it.
    """
    return (218 < r < 228 and 218 < g < 228 and 216 < b < 226
            and abs(r - g) < 8 and abs(g - b) < 8)


def _is_red_mine(r, g, b) -> bool:
    """Return True if this pixel is a red exploded mine."""
    return r > 180 and g < 100 and b < 100


# ==========================================================================
# Board reader
# ==========================================================================

class BoardReader:
    """Reads the GNOME Mines board from a screenshot image.

    The reader works in three stages:
    1. detect_grid() — finds all cell boundaries by scanning for gap bands
    2. read_board()  — reads each cell's state from pixel colors
    3. detect_game_state() — determines if we're playing, won, or lost

    HOW GRID DETECTION WORKS:
    Grid gaps in GNOME Mines are bright bands of ~(246,245,244), exactly
    4px wide, separating cells. The reader scans horizontally and vertically
    for these bands to find all cell boundaries. This works even when all
    cells are the same color (initial board).

    HOW CELL READING WORKS:
    For each cell, we sample two positions:
    - CENTER: The middle of the cell. May contain text (dark) or be uniform.
    - CORNER: An offset from center (40px in both axes). Always shows the
      cell's background color, unobstructed by text.

    The corner color determines the cell type:
    - Gray (186,189,182) → Covered. Then check center for flag icon.
    - Neutral (222,222,220) → Empty revealed (0 neighbors).
    - Green (G > R+10, G > 230) → Number 1.
    - Yellow (R > 220, G > 220, B < 200) → Number 2.
    - Orange (R > G+10) → Number 3 or higher.
    - Red (R > 180, G < 100) → Exploded mine (game over).

    USAGE FOR AGENTS:
        reader = BoardReader(Image.open("/tmp/screenshot.png"))
        if not reader.detect_grid():
            print("ERROR: Could not find grid")

        board = reader.read_board()
        # board is a 2D list like [['C','1','E',...], ...]

        state = reader.detect_game_state(board)
        # state is 'playing', 'game_over_lose', 'game_over_win', etc.

        # Get screen coordinates for a cell:
        x, y = reader.get_cell_center(row, col)
    """

    def __init__(self, img: Image.Image):
        self.img = img.convert("RGB")
        self.width, self.height = self.img.size
        # Grid geometry (populated by detect_grid)
        self.grid_bounds = None    # (left, top, right, bottom) of cell area
        self.cell_size = None      # (width, height) of a single cell
        self.rows = 0
        self.cols = 0
        self.row_starts: List[int] = []  # y-coordinate where each row starts
        self.col_starts: List[int] = []  # x-coordinate where each column starts

    def detect_grid(self) -> bool:
        """Find all cell boundaries by scanning for gap bands.

        Returns True if a valid grid was detected, False otherwise.
        After calling this, self.rows, self.cols, self.row_starts,
        self.col_starts, self.cell_size, and self.grid_bounds are set.

        ALGORITHM:
        1. Find the grid's left edge: scan rightward at screen center-y
           for the first non-gap pixel.
        2. Scan vertically through the grid to find horizontal gap bands.
        3. Scan horizontally through the grid to find vertical gap bands.
        4. Gap bands define cell boundaries. N gaps = N+1 cells (but the
           first and last gaps are the grid edges, so N-1 interior gaps
           = N cells).
        """
        img = self.img
        w, h = self.width, self.height

        # Step 1: Find approximate grid area.
        # Scan vertically at x = w/3 (avoids right-side UI panel) to find
        # the first and last CELL pixels (covered, empty, or numbered).
        # We can't just look for "non-gap" because the titlebar and other
        # UI elements are also non-gap but are not cells.
        scan_x = w // 3
        first_cell_y = None
        last_cell_y = None
        for y in range(30, h - 30):
            r, g, b = img.getpixel((scan_x, y))[:3]
            # A pixel is a cell if it's covered gray, empty gray, or
            # a colored number background. NOT if it's a gap, window bg,
            # or titlebar.
            is_cell = (_is_covered_pixel(r, g, b) or
                       _is_empty_pixel(r, g, b) or
                       (r > 150 and g > 150 and b < 220 and
                        not _is_gap_pixel(r, g, b) and
                        not (210 < r < 225 and 210 < g < 225 and 205 < b < 220)))
            if is_cell:
                if first_cell_y is None:
                    first_cell_y = y
                last_cell_y = y

        if first_cell_y is None or last_cell_y is None:
            return False

        # Step 2: Find horizontal gaps (= row boundaries).
        # Scan vertically at scan_x from above the first cell to below
        # the last cell, looking for bright bands.
        h_gaps = self._find_gaps_along_axis(
            scan_x, max(0, first_cell_y - 30), min(h - 1, last_cell_y + 30),
            axis='vertical'
        )

        if len(h_gaps) < 2:
            return False

        # The first gap is the top border (between titlebar and row 0).
        # The last gap is the bottom border (below last row).
        # Interior gaps separate rows.
        self.row_starts = []
        for i in range(len(h_gaps) - 1):
            _, gap_end = h_gaps[i]
            self.row_starts.append(gap_end + 1)
        # Number of rows = number of interior spaces
        self.rows = len(self.row_starts)

        # Step 3: Find the grid's horizontal extent.
        # Scan horizontally at the center of row 0 to find grid edges.
        if self.rows == 0:
            return False
        row0_center_y = self.row_starts[0] + 50  # ~middle of first row
        if self.rows > 1:
            row0_center_y = (self.row_starts[0] + self.row_starts[1]) // 2

        first_cell_x = None
        last_cell_x = None
        for x in range(0, w):
            r, g, b = img.getpixel((x, row0_center_y))[:3]
            if not _is_gap_pixel(r, g, b):
                if first_cell_x is None:
                    first_cell_x = x
                last_cell_x = x

        if first_cell_x is None:
            return False

        # Step 4: Find vertical gaps (= column boundaries).
        v_gaps = self._find_gaps_along_axis(
            row0_center_y, max(0, first_cell_x - 30),
            min(w - 1, last_cell_x + 30),
            axis='horizontal'
        )

        if len(v_gaps) < 2:
            return False

        self.col_starts = []
        for i in range(len(v_gaps) - 1):
            _, gap_end = v_gaps[i]
            self.col_starts.append(gap_end + 1)
        self.cols = len(self.col_starts)

        if self.cols == 0:
            return False

        # Compute cell size from the first cell span.
        if self.rows >= 2:
            cell_h = self.row_starts[1] - self.row_starts[0]
        else:
            cell_h = (h_gaps[-1][0] - self.row_starts[0])
        if self.cols >= 2:
            cell_w = self.col_starts[1] - self.col_starts[0]
        else:
            cell_w = (v_gaps[-1][0] - self.col_starts[0])

        self.cell_size = (cell_w, cell_h)

        # Grid bounds = bounding box of all cells
        grid_left = self.col_starts[0]
        grid_top = self.row_starts[0]
        grid_right = self.col_starts[-1] + cell_w - 1
        grid_bottom = self.row_starts[-1] + cell_h - 1
        self.grid_bounds = (grid_left, grid_top, grid_right, grid_bottom)

        return True

    def _find_gaps_along_axis(self, fixed_coord: int, start: int, end: int,
                              axis: str) -> List[Tuple[int, int]]:
        """Scan along one axis to find bright gap bands.

        Args:
            fixed_coord: The fixed coordinate (x for vertical scan, y for horizontal).
            start, end: Range to scan along the moving axis.
            axis: 'vertical' (scan y at fixed x) or 'horizontal' (scan x at fixed y).

        Returns:
            List of (gap_start, gap_end) tuples.
        """
        gaps = []
        in_gap = False
        gap_start = 0

        for pos in range(start, end + 1):
            if axis == 'vertical':
                r, g, b = self.img.getpixel((fixed_coord, pos))[:3]
            else:
                r, g, b = self.img.getpixel((pos, fixed_coord))[:3]

            is_gap = _is_gap_pixel(r, g, b)

            if is_gap and not in_gap:
                gap_start = pos
                in_gap = True
            elif not is_gap and in_gap:
                gap_end = pos - 1
                gap_width = gap_end - gap_start + 1
                # Accept gaps of reasonable width
                if gap_width <= GAP_FIRST_MAX:
                    gaps.append((gap_start, gap_end))
                in_gap = False

        # Handle trailing gap (grid bottom/right border)
        if in_gap:
            gap_end = end
            gap_width = gap_end - gap_start + 1
            if gap_width <= GAP_FIRST_MAX:
                gaps.append((gap_start, gap_end))

        return gaps

    def get_cell_center(self, row: int, col: int) -> Optional[Tuple[int, int]]:
        """Return (x, y) screen coordinates for the center of cell (row, col).

        USAGE FOR AGENTS:
            x, y = reader.get_cell_center(3, 4)
            # Use x, y with pyautogui_click or pyautogui_moveTo
        """
        if not self.row_starts or not self.col_starts or self.cell_size is None:
            return None
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return None
        cw, ch = self.cell_size
        x = self.col_starts[col] + cw // 2
        y = self.row_starts[row] + ch // 2
        return (x, y)

    def read_cell(self, row: int, col: int) -> str:
        """Read the state of a single cell.

        Returns one of: 'C', 'F', 'E', '1'-'8', 'M', 'X', '?'

        ALGORITHM:
        1. Sample the CENTER pixel of the cell.
        2. Sample a CORNER pixel (offset +40, +40 from center) to see
           the background color unobstructed by text.
        3. Use the corner color to determine cell type:
           - Covered gray → check for flag icon → 'C' or 'F'
           - Empty neutral gray → 'E'
           - Green/yellow/orange → number cell → determine which number
           - Red → exploded mine 'X'
        4. If center is dark and corner is colored, it's a number.
           The corner color determines which number (1, 2, 3, 4+).
        """
        center_pos = self.get_cell_center(row, col)
        if center_pos is None:
            return '?'

        cx, cy = center_pos
        cw, ch = self.cell_size

        # Sample center and corner
        center_rgb = self.img.getpixel((cx, cy))[:3]
        cr, cg, cb = center_rgb

        # Corner offset: 40% of cell size, clamped to image bounds
        corner_dx = min(40, int(cw * 0.35))
        corner_dy = min(40, int(ch * 0.35))
        corner_x = min(cx + corner_dx, self.width - 1)
        corner_y = min(cy + corner_dy, self.height - 1)
        bg_rgb = self.img.getpixel((corner_x, corner_y))[:3]
        br, bg, bb = bg_rgb

        # --- Check for red exploded mine (game over) ---
        if _is_red_mine(cr, cg, cb) or _is_red_mine(br, bg, bb):
            return 'X'

        # --- Check if corner is covered gray ---
        if _is_covered_pixel(br, bg, bb):
            # Cell background is covered gray.
            # Check if there's a flag icon (dark pixels at center).
            return self._check_for_flag(cx, cy, cw, ch)

        # --- Check if corner is empty neutral gray ---
        if _is_empty_pixel(br, bg, bb):
            # Could be truly empty, OR could have very faint content.
            # Check center for dark text.
            if self._has_dark_text(cx, cy, cw, ch):
                # This shouldn't happen for empty cells, but could be
                # a mine icon on game-over (neutral bg + dark icon).
                return 'M'
            return 'E'

        # --- Check if center is dark (= text or icon) ---
        if cr < 150 and cg < 150 and cb < 150:
            # Dark center + colored background = NUMBER cell.
            return self._classify_number(br, bg, bb)

        # --- Colored background without dark center ---
        # The center pixel landed on the colored background between text strokes.
        # Still a number cell — classify by background.
        if br > 200 and bg > 150:
            return self._classify_number(br, bg, bb)

        # --- Hover state (slightly lighter than covered) ---
        if (200 < cr < 220 and 200 < cg < 220 and 195 < cb < 215):
            return 'C'  # Treat hover as covered

        # --- Gap or window background (shouldn't happen for a valid cell) ---
        if _is_gap_pixel(cr, cg, cb):
            return '?'

        # Fallback
        return '?'

    def _check_for_flag(self, cx: int, cy: int, cw: int, ch: int) -> str:
        """Check if a covered cell has a flag icon.

        Flags have significant dark pixels (the flag icon) on a covered
        gray background. We sample a grid of pixels around center and
        count how many are dark.

        Returns 'F' if flag detected, 'C' otherwise.
        """
        dark_count = 0
        total = 0
        radius = int(min(cw, ch) * 0.25)
        step = max(2, radius // 5)
        for dy in range(-radius, radius + 1, step):
            for dx in range(-radius, radius + 1, step):
                sx = cx + dx
                sy = cy + dy
                if 0 <= sx < self.width and 0 <= sy < self.height:
                    pr, pg, pb = self.img.getpixel((sx, sy))[:3]
                    total += 1
                    if pr < 100 and pg < 100 and pb < 100:
                        dark_count += 1

        if total > 0 and dark_count / total > 0.12:
            return 'F'
        return 'C'

    def _has_dark_text(self, cx: int, cy: int, cw: int, ch: int) -> bool:
        """Check if a cell has dark text/icon pixels at its center."""
        dark_count = 0
        total = 0
        radius = int(min(cw, ch) * 0.2)
        step = max(2, radius // 4)
        for dy in range(-radius, radius + 1, step):
            for dx in range(-radius, radius + 1, step):
                sx = cx + dx
                sy = cy + dy
                if 0 <= sx < self.width and 0 <= sy < self.height:
                    pr, pg, pb = self.img.getpixel((sx, sy))[:3]
                    total += 1
                    if pr < 100 and pg < 100 and pb < 100:
                        dark_count += 1
        return total > 0 and dark_count / total > 0.05

    def _classify_number(self, br: int, bg: int, bb: int) -> str:
        """Determine which number (1-8) based on background corner color.

        Color thresholds (measured from GNOME Mines):
          1: Green  — G dominant, G > R+10, B around 195
             Example: (221, 250, 195)
          2: Yellow — R and G both high (~236), B around 191
             Example: (236, 237, 191)
          3: Orange — R > G by 10-40, B around 170-185
             Example: (237, 218, 180)
          4: Deep orange — R > G, B drops below 165
             Example: (237, 195, 138)
          5+: Even deeper orange/red — B very low

        The BLUE channel is the most reliable discriminator between
        3 and 4. Number 3 has B around 170-185; number 4 has B below 165.
        This distinction is CRITICAL: misreading 4 as 3 causes the solver
        to undercount mines around a cell, leading to marking mine cells
        as "safe" and losing the game.

        Returns '1', '2', '3', '4', or '5'.
        """
        # --- Orange family: R > G (numbers 3, 4, 5+) ---
        if br > bg + 10 and br > 210:
            # Use B channel to distinguish 3 vs 4 vs 5+
            if bb < 120:
                return '5'
            if bb < 165:
                return '4'  # Deep orange, B=130-165
            return '3'      # Normal orange, B=165-190

        # --- Green family: G dominant (number 1) ---
        if bg > br + 10 and bg > 220:
            return '1'

        # --- Yellow family: R and G both high (number 2) ---
        if br > 220 and bg > 220 and bb < 200:
            return '2'

        # --- Fallback heuristics ---
        if bg > br:
            return '1'
        return '2'

    def read_board(self) -> Optional[List[List[str]]]:
        """Read the entire board. Returns a 2D list of cell states.

        Must call detect_grid() first.

        Returns None if grid has not been detected.

        USAGE FOR AGENTS:
            reader = BoardReader(img)
            reader.detect_grid()
            board = reader.read_board()
            # board[row][col] is one of: 'C','E','1'-'8','F','M','X','?'
        """
        if self.rows == 0 or self.cols == 0:
            return None
        board = []
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                row.append(self.read_cell(r, c))
            board.append(row)
        return board

    def detect_game_state(self, board: Optional[List[List[str]]] = None) -> str:
        """Detect what state the game is in.

        Returns one of:
          'playing'         — game is in progress
          'game_over_lose'  — hit a mine (red cell visible)
          'game_over_win'   — all non-mine cells revealed
          'menu'            — difficulty selection screen
          'dialog'          — modal dialog (Best Times, etc.)
          'unknown'         — could not determine

        IMPORTANT FOR AGENTS: Check this AFTER every click. If the
        result is 'game_over_lose' or 'game_over_win', STOP PLAYING.
        """
        img = self.img
        w, h = self.width, self.height

        # Check for dialog overlay (dark pixels at screen center)
        center_px = img.getpixel((w // 2, h // 2))[:3]
        if all(c < 60 for c in center_px):
            return 'dialog'

        # If no grid detected, might be difficulty menu
        if self.rows == 0 or self.cols == 0:
            return 'menu'

        # Read board if not provided
        if board is None:
            board = self.read_board()
        if board is None:
            return 'unknown'

        # Check for red mines (game over lose)
        for row in board:
            for cell in row:
                if cell == 'X':
                    return 'game_over_lose'

        # Check for revealed mines (game over — multiple mine icons)
        mine_count = sum(1 for row in board for cell in row if cell == 'M')
        if mine_count >= 3:
            return 'game_over_lose'

        # Check for win: no covered cells remain (only flags and revealed)
        covered = sum(1 for row in board for cell in row if cell == 'C')
        flags = sum(1 for row in board for cell in row if cell == 'F')
        if covered == 0 and flags > 0:
            return 'game_over_win'

        # Check for win: remaining covered = remaining mines
        total_mines = _get_mines_for_grid(self.rows, self.cols)
        if covered == total_mines - flags and covered > 0:
            # All remaining covered cells are mines — game won
            return 'game_over_win'

        return 'playing'


# ==========================================================================
# Constraint-based solver
# ==========================================================================

class MinesSolver:
    """Constraint satisfaction solver for Minesweeper.

    ALGORITHM:
    1. Basic constraint: For each numbered cell, count adjacent flags and
       covered cells. If number == flags, all remaining covered are safe.
       If number - flags == covered_count, all covered are mines.
    2. Subset analysis: If one numbered cell's constraint covers a subset
       of another's, the difference can be deduced.
    3. Probability estimation: When no cell is provably safe, estimate
       mine probability for each covered cell and pick the safest.

    USAGE FOR AGENTS:
        solver = MinesSolver(board_2d_list, total_mines=10)
        move = solver.get_best_move()
        # move = {
        #   "action": "click",     # or "guess" or "none"
        #   "row": 3, "col": 4,
        #   "confidence": 1.0,     # 1.0 = provably safe
        #   "reason": "Provably safe cell at (3,4)",
        #   "all_safe": [[3,4], [5,2], ...],   # ALL safe cells
        #   "all_mines": [[1,0], [2,5], ...],  # ALL confirmed mines
        # }
    """

    def __init__(self, board: list, total_mines: int):
        self.board = board
        self.rows = len(board)
        self.cols = len(board[0]) if board else 0
        self.total_mines = total_mines
        self.safe_cells = set()
        self.mine_cells = set()

    def get_adjacent(self, r, c):
        adj = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    adj.append((nr, nc))
        return adj

    def solve(self):
        """Run constraint satisfaction. Returns dict with 'safe' and 'mines' lists."""
        changed = True
        passes = 0
        while changed and passes < 30:
            changed = False
            passes += 1

            for r in range(self.rows):
                for c in range(self.cols):
                    cell = self.board[r][c]
                    if cell not in '12345678':
                        continue

                    value = int(cell)
                    adj = self.get_adjacent(r, c)
                    adj_covered = [(ar, ac) for ar, ac in adj
                                   if self.board[ar][ac] == 'C'
                                   and (ar, ac) not in self.mine_cells]
                    adj_flags = sum(1 for ar, ac in adj
                                   if self.board[ar][ac] == 'F'
                                   or (ar, ac) in self.mine_cells)
                    remaining = value - adj_flags

                    if remaining < 0:
                        continue

                    if remaining == 0:
                        for ar, ac in adj_covered:
                            if (ar, ac) not in self.safe_cells:
                                self.safe_cells.add((ar, ac))
                                changed = True

                    if remaining == len(adj_covered) and len(adj_covered) > 0:
                        for ar, ac in adj_covered:
                            if (ar, ac) not in self.mine_cells:
                                self.mine_cells.add((ar, ac))
                                changed = True

        self._subset_analysis()

        return {
            "safe": sorted(self.safe_cells),
            "mines": sorted(self.mine_cells),
        }

    def _subset_analysis(self):
        """Advanced: if constraint A is a subset of B, deduce the difference."""
        constraints = []
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.board[r][c]
                if cell not in '12345678':
                    continue
                value = int(cell)
                adj = self.get_adjacent(r, c)
                covered = frozenset((ar, ac) for ar, ac in adj
                                    if self.board[ar][ac] == 'C'
                                    and (ar, ac) not in self.mine_cells
                                    and (ar, ac) not in self.safe_cells)
                flags = sum(1 for ar, ac in adj
                            if self.board[ar][ac] == 'F'
                            or (ar, ac) in self.mine_cells)
                remaining = value - flags
                if len(covered) > 0 and remaining >= 0:
                    constraints.append((covered, remaining))

        changed = True
        while changed:
            changed = False
            for i, (set_a, mines_a) in enumerate(constraints):
                for j, (set_b, mines_b) in enumerate(constraints):
                    if i == j or not (set_a < set_b):
                        continue
                    diff = set_b - set_a
                    diff_mines = mines_b - mines_a
                    if diff_mines == 0:
                        for cell in diff:
                            if cell not in self.safe_cells:
                                self.safe_cells.add(cell)
                                changed = True
                    elif diff_mines == len(diff):
                        for cell in diff:
                            if cell not in self.mine_cells:
                                self.mine_cells.add(cell)
                                changed = True

    def get_best_move(self) -> dict:
        """Return the best move. See class docstring for output format."""
        self.solve()

        if self.safe_cells:
            best = max(self.safe_cells, key=lambda rc: self._info_score(*rc))
            return {
                "action": "click",
                "row": best[0], "col": best[1],
                "confidence": 1.0,
                "reason": f"Provably safe cell at ({best[0]},{best[1]})",
                "all_safe": sorted([list(s) for s in self.safe_cells]),
                "all_mines": sorted([list(m) for m in self.mine_cells]),
            }

        covered = [(r, c) for r in range(self.rows) for c in range(self.cols)
                    if self.board[r][c] == 'C'
                    and (r, c) not in self.mine_cells
                    and (r, c) not in self.safe_cells]

        if not covered:
            return {
                "action": "none", "row": -1, "col": -1,
                "confidence": 0.0,
                "reason": "No covered cells remaining",
                "all_safe": [],
                "all_mines": sorted([list(m) for m in self.mine_cells]),
            }

        probs = {(r, c): self._estimate_mine_probability(r, c) for r, c in covered}
        best = min(covered, key=lambda rc: (probs[rc], -self._info_score(*rc)))
        prob = probs[best]

        return {
            "action": "guess",
            "row": best[0], "col": best[1],
            "confidence": round(1.0 - prob, 3),
            "mine_probability": round(prob, 3),
            "reason": f"Best guess at ({best[0]},{best[1]}) with {prob:.1%} mine probability",
            "all_safe": sorted([list(s) for s in self.safe_cells]),
            "all_mines": sorted([list(m) for m in self.mine_cells]),
        }

    def _info_score(self, r, c):
        adj = self.get_adjacent(r, c)
        score = 0
        for ar, ac in adj:
            if self.board[ar][ac] in '12345678':
                score += 1
            elif self.board[ar][ac] == 'C':
                score += 0.1
        return score

    def _estimate_mine_probability(self, r, c):
        adj = self.get_adjacent(r, c)
        numbered = [(ar, ac) for ar, ac in adj if self.board[ar][ac] in '12345678']

        if not numbered:
            total_covered = sum(1 for row in self.board for cell in row if cell == 'C')
            total_flags = sum(1 for row in self.board for cell in row if cell == 'F')
            remaining_mines = self.total_mines - total_flags - len(self.mine_cells)
            remaining_covered = total_covered - len(self.mine_cells) - len(self.safe_cells)
            if remaining_covered <= 0:
                return 0.5
            return remaining_mines / remaining_covered

        max_prob = 0.0
        for ar, ac in numbered:
            value = int(self.board[ar][ac])
            adj2 = self.get_adjacent(ar, ac)
            flags = sum(1 for a2r, a2c in adj2
                        if self.board[a2r][a2c] == 'F' or (a2r, a2c) in self.mine_cells)
            cov = [(a2r, a2c) for a2r, a2c in adj2
                   if self.board[a2r][a2c] == 'C'
                   and (a2r, a2c) not in self.mine_cells
                   and (a2r, a2c) not in self.safe_cells]
            remaining = value - flags
            if len(cov) > 0 and remaining > 0:
                max_prob = max(max_prob, remaining / len(cov))
        return max_prob

    def get_first_move(self):
        """Strategy for the very first move (all cells covered).

        Center or near-center gives the best chance of a large cascade.
        On beginner (8x8, 10 mines), the center has ~84% chance of
        being safe and often reveals 20+ cells in one click.
        """
        center_r = self.rows // 2
        center_c = self.cols // 2
        return {
            "action": "click",
            "row": center_r, "col": center_c,
            "confidence": 0.85,
            "reason": f"First move: center cell ({center_r},{center_c}) for maximum cascade",
            "all_safe": [], "all_mines": [],
        }


# ==========================================================================
# Board string parser
# ==========================================================================

def parse_board_string(s: str) -> List[List[str]]:
    """Parse board from string format.

    Format: rows delimited by ';', cells within a row delimited by ','.

    Example:
        "C,1,E,E;C,2,1,C;C,C,C,C"
        → [['C','1','E','E'], ['C','2','1','C'], ['C','C','C','C']]

    Cell codes: C=covered, E=empty, F=flag, 1-8=number, M=mine, X=exploded
    """
    rows = s.strip().split(';')
    return [[c.strip() for c in row.split(',')] for row in rows]


# ==========================================================================
# Annotator (debug overlay)
# ==========================================================================

def annotate_board(img_path: str, output_path: str, reader: BoardReader,
                   board: Optional[List[List[str]]]) -> None:
    """Draw grid overlay and cell labels on the screenshot for debugging.

    Creates an annotated image showing:
    - Red grid lines at detected cell boundaries
    - Cell state labels at each cell center
    - Color-coded: green for safe, red for flags/mines, gray for covered

    USAGE FOR AGENTS:
        python3 mines_solver.py annotate /tmp/board.png /tmp/debug.png
        # Then view /tmp/debug.png to verify grid detection is correct
    """
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    if reader.grid_bounds is None:
        img.save(output_path)
        return

    left, top, right, bottom = reader.grid_bounds

    # Draw grid lines
    if reader.cell_size:
        cw, ch = reader.cell_size
        for c in range(reader.cols + 1):
            x = reader.col_starts[c] if c < reader.cols else right + 1
            draw.line([(x, top), (x, bottom)], fill=(255, 0, 0), width=2)
        for r in range(reader.rows + 1):
            y = reader.row_starts[r] if r < reader.rows else bottom + 1
            draw.line([(left, y), (right, y)], fill=(255, 0, 0), width=2)

    # Label cells
    if board:
        colors = {
            'C': (200, 200, 200), 'E': (100, 255, 100),
            'F': (255, 100, 100), 'M': (255, 50, 50),
            'X': (255, 0, 0), '?': (255, 255, 0),
        }
        for r in range(len(board)):
            for c in range(len(board[r])):
                center = reader.get_cell_center(r, c)
                if center:
                    x, y = center
                    label = board[r][c]
                    color = colors.get(label, (0, 255, 0))
                    draw.text((x - 5, y - 8), label, fill=color)

    img.save(output_path)


# ==========================================================================
# CLI commands
# ==========================================================================

def _get_mines_for_grid(rows, cols):
    """Determine total mines from standard GNOME Mines grid sizes."""
    if rows == 8 and cols == 8:
        return 10
    elif rows == 16 and cols == 16:
        return 40
    elif rows == 16 and cols == 30:
        return 99
    return max(1, (rows * cols) // 5)


def cmd_new(args):
    tracker = GameStateTracker()
    mines = args.mines if args.mines else _get_mines_for_grid(args.rows, args.cols)
    tracker.set_difficulty(args.rows, args.cols, mines)
    print(json.dumps({
        "game_id": tracker.game_id,
        "state_file": str(tracker.state_file),
        "difficulty": tracker.state["difficulty"],
        "grid_size": [args.rows, args.cols],
        "total_mines": mines,
    }, indent=2))


def cmd_read(args):
    img = Image.open(args.image)
    reader = BoardReader(img)
    grid_ok = reader.detect_grid()

    tracker = GameStateTracker(args.game_id) if args.game_id else None

    if not grid_ok:
        result = {"state": "menu", "error": "Could not detect grid",
                  "grid_bounds": None}
        if tracker:
            tracker.state["last_error"] = "Could not detect grid"
            tracker.save()
            result["game_id"] = tracker.game_id
        print(json.dumps(result, indent=2))
        return

    board = reader.read_board()
    if board is None:
        print(json.dumps({"state": "unknown", "error": "Could not read board"}))
        return

    state = reader.detect_game_state(board)
    total_mines = _get_mines_for_grid(reader.rows, reader.cols)
    total_cells = reader.rows * reader.cols

    if tracker and tracker.state["grid_size"] is None:
        tracker.set_difficulty(reader.rows, reader.cols, total_mines)
    if tracker:
        tracker.record_screenshot(args.image)
        tracker.record_board_snapshot(board)

    # Handle game-over
    if state in ('game_over_lose', 'game_over_win'):
        if tracker:
            tracker.set_game_over(state == 'game_over_win')
        output = {
            "state": state,
            "grid": {"rows": reader.rows, "cols": reader.cols,
                     "bounds": list(reader.grid_bounds),
                     "cell_size": list(reader.cell_size)},
            "board": board,
            "board_pretty": "\n".join(" ".join(f"{c:>2}" for c in row) for row in board),
            "move": {"action": "none", "row": -1, "col": -1,
                     "reason": f"Game over: {'lost' if 'lose' in state else 'won'}"},
        }
        if tracker:
            output["game_id"] = tracker.game_id
            output["game_summary"] = tracker.get_summary()
        print(json.dumps(output, indent=2))
        return

    # Solve
    covered = sum(1 for row in board for c in row if c == 'C')
    solver = MinesSolver(board, total_mines)
    move = solver.get_first_move() if covered == total_cells else solver.get_best_move()

    if tracker:
        tracker.update_known_cells(move.get("all_safe", []), move.get("all_mines", []))
        candidates = []
        for s in move.get("all_safe", [])[:5]:
            center = reader.get_cell_center(s[0], s[1])
            candidates.append({"row": s[0], "col": s[1], "action": "click",
                               "confidence": 1.0, "reason": "Provably safe",
                               "screen_coords": list(center) if center else None})
        if not candidates and move["action"] == "guess":
            center = reader.get_cell_center(move["row"], move["col"])
            candidates.append({"row": move["row"], "col": move["col"],
                               "action": "guess", "confidence": move.get("confidence", 0),
                               "reason": move["reason"],
                               "screen_coords": list(center) if center else None})
        tracker.set_candidates(candidates)

    target_coords = reader.get_cell_center(move["row"], move["col"]) if move["row"] >= 0 else None

    # Build coordinate map for ALL safe cells
    safe_coords = {}
    for s in move.get("all_safe", []):
        center = reader.get_cell_center(s[0], s[1])
        if center:
            safe_coords[f"{s[0]},{s[1]}"] = list(center)

    mine_coords = {}
    for m in move.get("all_mines", []):
        center = reader.get_cell_center(m[0], m[1])
        if center:
            mine_coords[f"{m[0]},{m[1]}"] = list(center)

    output = {
        "state": state,
        "grid": {"rows": reader.rows, "cols": reader.cols,
                 "bounds": list(reader.grid_bounds),
                 "cell_size": list(reader.cell_size)},
        "board": board,
        "board_pretty": "\n".join(" ".join(f"{c:>2}" for c in row) for row in board),
        "stats": {
            "total_mines": total_mines,
            "covered": covered,
            "flags": sum(1 for row in board for c in row if c == 'F'),
            "revealed": total_cells - covered - sum(1 for row in board for c in row if c == 'F'),
        },
        "move": move,
        "target_coords": list(target_coords) if target_coords else None,
        "safe_coords": safe_coords,
        "mine_coords": mine_coords,
    }
    if tracker:
        output["game_id"] = tracker.game_id
        output["game_summary"] = tracker.get_summary()

    print(json.dumps(output, indent=2))


def cmd_solve(args):
    board = parse_board_string(args.board)
    solver = MinesSolver(board, args.mines)
    move = solver.get_best_move()

    tracker = GameStateTracker(args.game_id) if args.game_id else None
    if tracker:
        tracker.record_board_snapshot(board)
        tracker.update_known_cells(move.get("all_safe", []), move.get("all_mines", []))

    output = {
        "board": board,
        "board_pretty": "\n".join(" ".join(f"{c:>2}" for c in row) for row in board),
        "move": move,
    }
    if tracker:
        output["game_id"] = tracker.game_id
    print(json.dumps(output, indent=2))


def cmd_record(args):
    tracker = GameStateTracker(args.game_id)
    tracker.record_move(
        action=args.action, row=args.row, col=args.col,
        reason=args.reason or "",
        confidence=args.confidence if args.confidence else 1.0,
        result=args.result or "pending",
    )
    print(json.dumps(tracker.get_summary(), indent=2))


def cmd_status(args):
    tracker = GameStateTracker(args.game_id)
    output = tracker.get_summary()
    output["full_state"] = tracker.state
    print(json.dumps(output, indent=2))


def cmd_state(args):
    img = Image.open(args.image)
    reader = BoardReader(img)
    grid_ok = reader.detect_grid()
    board = reader.read_board() if grid_ok else None
    state = reader.detect_game_state(board) if grid_ok else 'menu'
    print(json.dumps({
        "state": state,
        "grid_bounds": list(reader.grid_bounds) if reader.grid_bounds else None,
        "grid_size": [reader.rows, reader.cols] if reader.rows > 0 else None,
    }, indent=2))


def cmd_annotate(args):
    img = Image.open(args.image)
    reader = BoardReader(img)
    reader.detect_grid()
    board = reader.read_board()
    annotate_board(args.image, args.output, reader, board)
    print(json.dumps({
        "annotated": args.output,
        "grid_size": [reader.rows, reader.cols],
        "grid_bounds": list(reader.grid_bounds) if reader.grid_bounds else None,
    }, indent=2))


def cmd_coords(args):
    img = Image.open(args.image)
    reader = BoardReader(img)
    reader.detect_grid()
    center = reader.get_cell_center(args.row, args.col)
    print(json.dumps({
        "row": args.row, "col": args.col,
        "screen_x": center[0] if center else None,
        "screen_y": center[1] if center else None,
    }, indent=2))


# ==========================================================================
# CLI entry point
# ==========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="GNOME Mines Solver — board reader, constraint solver, game state tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s new --rows 8 --cols 8
  %(prog)s read /tmp/screenshot.png --game-id 1711843200
  %(prog)s solve "C,1,E;C,2,C;C,C,C" --mines 2
  %(prog)s record --game-id 123 --action click --row 3 --col 4 --reason "Safe"
  %(prog)s status --game-id 123
  %(prog)s annotate /tmp/board.png /tmp/debug.png
        """)
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("new", help="Start a new game session")
    p.add_argument("--rows", type=int, default=8)
    p.add_argument("--cols", type=int, default=8)
    p.add_argument("--mines", type=int, help="Total mines (auto if omitted)")

    p = sub.add_parser("read", help="Read board from screenshot and solve")
    p.add_argument("image")
    p.add_argument("--game-id", dest="game_id")

    p = sub.add_parser("solve", help="Solve from board string")
    p.add_argument("board", help="Rows=';', cells=','")
    p.add_argument("--mines", type=int, required=True)
    p.add_argument("--game-id", dest="game_id")

    p = sub.add_parser("record", help="Record a move")
    p.add_argument("--game-id", dest="game_id", required=True)
    p.add_argument("--action", required=True, choices=["click", "flag", "unflag"])
    p.add_argument("--row", type=int, required=True)
    p.add_argument("--col", type=int, required=True)
    p.add_argument("--reason")
    p.add_argument("--confidence", type=float)
    p.add_argument("--result")

    p = sub.add_parser("status", help="View game state")
    p.add_argument("--game-id", dest="game_id", required=True)

    p = sub.add_parser("state", help="Detect game state from screenshot")
    p.add_argument("image")

    p = sub.add_parser("annotate", help="Debug: annotate screenshot with grid overlay")
    p.add_argument("image")
    p.add_argument("output")

    p = sub.add_parser("coords", help="Get screen coords for a cell")
    p.add_argument("image")
    p.add_argument("row", type=int)
    p.add_argument("col", type=int)

    args = parser.parse_args()
    commands = {
        "new": cmd_new, "read": cmd_read, "solve": cmd_solve,
        "record": cmd_record, "status": cmd_status, "state": cmd_state,
        "annotate": cmd_annotate, "coords": cmd_coords,
    }
    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
