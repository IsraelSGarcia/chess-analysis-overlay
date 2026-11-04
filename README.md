# Chess Capture Visualizer

A lightweight Windows desktop overlay that reads any chessboard visible on your screen (Chess.com, Lichess, desktop engines, etc.) and draws **live legal capture, attack, and defense arrows and square highlights** directly over the board in real time.

---

## Quick Start (For Complete Beginners)

You do **not** need programming experience to use this app. Follow these 3 simple steps:

### Step 1: Install Python (If you don't already have it)
1. Download Python 3.10 or newer from [python.org](https://www.python.org/downloads/).
2. Run the installer.
3. **IMPORTANT**: On the first installer screen, check the box that says:
   > `[x] Add python.exe to PATH`
4. Click **Install Now**.

### Step 2: Install Dependencies (One-Click)
1. Download or clone this repository to your computer.
2. Open the folder and double-click **`install.bat`**.
3. A terminal window will open, automatically install all required packages, and notify you when complete.

### Step 3: Calibrate & Play
1. Open your browser with a chessboard visible (e.g., [Chess.com](https://www.chess.com) or [Lichess](https://lichess.org)).
2. Double-click **`launch_calibrate.bat`**.
3. A transparent calibration overlay will appear.
4. **Click and loosely drag a box over your chessboard.** You don't need to be precise—the app automatically detects the outer borders and snaps the 8×8 grid to the squares.
5. Press **Enter** (or click **Confirm**) on your screen.
6. The visualizer and floating toolbar will appear over your board!

---

## Daily Use

After your initial calibration, you don't need to recalibrate every time.

- **Standard Launch**: Double-click **`launch.bat`** (launches directly using your saved board position).
- **Recalibrate anytime**: If you moved or resized your browser window, simply click the **`Calibrate`** button on the toolbar or press **`Ctrl + Alt + C`**.

---

## Visualization Legend

- **Blue Highlights & Arrows**: Your pieces' legal captures, attacks onto empty squares, and defenses of friendly pieces.
- **Red Highlights & Arrows**: Opponent pieces' legal captures, attacks onto empty squares, and defenses of enemy pieces.
- **Violet Highlights**: Contested squares where both sides have influence.
- **Defending Arrows**: Shows which friendly pieces are protected by other friendly pieces.
- **Pinned Piece Protection**: Pieces pinned to their King cannot legally move off their pin line; illegal moves are excluded automatically.
- **Anti-Dot Filter**: Move-indicator dots and click circles (common on Chess.com and Lichess) are cleaned dynamically so arrows remain rock-solid.

---

## Minimalist Controls & Shortcuts

A sleek, monochromatic floating toolbar sits above your board. Every button has dedicated, conflict-free global hotkeys using `Ctrl + Alt`:

| Toolbar Button | Global Shortcut | Description |
|:---|:---:|:---|
| `Overlay` | **Ctrl + Alt + X** | **Master Toggle**: Show or hide the entire overlay instantly |
| `Player` | **Ctrl + Alt + A** | Toggle your influence arrows & highlights on/off |
| `Enemy` | **Ctrl + Alt + S** | Toggle opponent influence arrows & highlights on/off |
| `Defense` | **Ctrl + Alt + D** | Toggle arrows pointing to friendly defended pieces |
| `Flip` | **Ctrl + Alt + F** | Flip player color / perspective (swaps Blue ↔ Red assignment) |
| `Highlights` | **Ctrl + Alt + H** | Toggle square background tints on/off |
| `Calibrate` | **Ctrl + Alt + C** | Launch the auto-snapping board grid calibrator |
| `Close` | **Ctrl + Alt + Q** | Exit the visualizer completely |

*All shortcuts use `Ctrl + Alt + [Key]`, meaning they will never interfere with normal typing, chat boxes, browser shortcuts, or games.*

### Moving the Toolbar
- Click and drag anywhere on the toolbar (or on the `::` grip on the left) to move it anywhere on your screen.
- Its position is saved automatically across restarts.

---

## Manual / Command-Line Setup (For Developers)

If you prefer using the command line:

```bash
# 1. Clone repository
git clone https://github.com/IsraelSGarcia/chess-capture-visualizer.git
cd chess-capture-visualizer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch calibration mode
python -m chess_visualizer --calibrate

# 4. Standard launch
python -m chess_visualizer
```

---

## Troubleshooting & FAQ

#### Nothing happens when I double-click `launch.bat`
- Make sure you ran **`install.bat`** first.
- Ensure Python was added to your PATH. If unsure, open Command Prompt, type `python --version`, and press Enter. If it says command not found, reinstall Python and check `Add python.exe to PATH`.

#### Does the overlay capture itself or lag the screen?
- No. Both the overlay and calibration windows use Windows `SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)`. Windows excludes the overlay from screen captures, preventing feedback loops and screen lag.

#### The board was rotated / I am playing as Black
- The visualizer automatically detects whether White or Black is at the bottom directly from the piece layout. If you want your pieces to be Blue while playing as Black, click **`Flip`** (or press **`Ctrl + Alt + F`**).

---

## Running Automated Tests

To verify that the capture logic, recognition pipeline, and grid alignment are working on your system:

```bash
python tests/test_chess_logic.py
python tests/test_integration.py
python tests/test_grid_snapping.py
python tests/test_overlay_alignment.py
```

*(All 25 unit and integration tests passing)*
