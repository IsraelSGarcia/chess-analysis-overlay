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

### Step 3: Launch & Play (Zero Configuration)
1. Open your browser with a chessboard visible (e.g., [Chess.com](https://www.chess.com) or [Lichess](https://lichess.org)).
2. Double-click **`launch.bat`**.
3. **Auto-Detect & Auto-Disappearance**: The visualizer automatically detects the chessboard on your screen in milliseconds and snaps the overlay directly over it. If you switch tabs, minimize the browser, or close the game, **nothing is shown**—the overlay and HUD disappear automatically until a board returns.

---

## Daily Use

- **Fully Automatic**: Just launch **`launch.bat`**. When a chessboard is open, the overlay appears; when no board is visible, it stays completely invisible.
- **Window Movement / Scrolling**: If you move or resize your browser window, the auto-tracker immediately follows the board to its new location.
- **Manual Fallback**: If you ever want to manually lock a specific region (e.g. multi-monitor setups or studying two boards simultaneously), click **`Calibrate`** or press **`Ctrl + Alt + C`** to drag a manual selection box. Click **`Auto`** or press **`Ctrl + Alt + B`** to return to automatic mode at any time.

---

## Two Distinct Visualization Modes: Captures vs Tactics

The application provides clean separation between **Capture Visualization** and **Tactical Intelligence**. Switch between them at any time with the **`Tactics` / `Captures`** button on the toolbar or via **`Ctrl + Alt + M`**:

### 1. Tactics Mode (`Mode: Tactics`)
Specialized analytical mode focusing on concrete tactical threats, combinations, and advantages:
- **Winning Trade Arrows**: Vivid Emerald Green arrows (`#00E676`) on all favorable captures (Static Exchange Evaluation $> 0$) and free hanging pieces.
- **Multi-Target Fork Arrows**: Vivid purple arrows (`#D500F9`) radiating from attacking pieces directly to all forked victims.
- **Pin & Skewer Rays**: Directed lines highlighting absolute pins (to the King) and relative pins (to the Queen/Rook).
- **Blunder Warnings**: Crimson Red arrows (`#FF1744`) indicating all self-destructive moves and immediate mate allowances.
- **Hanging Piece Alerts**: Radiant Orange dashed boxes and threat arrows (`#FF6D00`) on undefended or tactically vulnerable pieces.
- **Check Alerts**: Urgent Red border and threat arrows on King in check.
- **Tactical Analysis HUD**: Draggable companion card showing live material balance, hanging piece summaries, and active motifs.

### 2. Captures Mode (`Mode: Captures`)
The classic capture visualizer displaying the complete legal influence and square control network:
- **Player Legal Captures**: Vibrant Blue arrows for all your available captures.
- **Enemy Legal Captures**: Vibrant Red arrows for all opponent captures.
- **Defending Arrows**: Royal Blue arrows showing which friendly pieces protect other friendly pieces.
- **Square Control Highlights**: Blue (friendly influence), Red (enemy influence), and Violet (contested squares).

---

## Minimalist Controls & Shortcuts

A sleek, monochromatic floating toolbar sits above your board, paired with a Windows System Tray icon (near the clock) and a first-class Windows Taskbar entry. Every button has dedicated, conflict-free global hotkeys using `Ctrl + Alt`:

| Toolbar Button | Global Shortcut | Description |
|:---|:---:|:---|
| `Overlay` | **Ctrl + Alt + X** | **Master Toggle**: Show or hide the entire overlay instantly |
| `Tactics` / `Captures` | **Ctrl + Alt + M** | **Mode Switch**: Toggle between Tactical Analysis and Legal Captures |
| `Player` | **Ctrl + Alt + A** | Toggle your influence arrows & highlights on/off |
| `Enemy` | **Ctrl + Alt + S** | Toggle opponent influence arrows & highlights on/off |
| `Defense` | **Ctrl + Alt + D** | Toggle arrows pointing to friendly defended pieces |
| `Flip` | **Ctrl + Alt + F** | Flip player color / perspective (swaps Blue ↔ Red assignment) |
| `Highlights` | **Ctrl + Alt + H** | Toggle square background tints on/off |
| `HUD` | **Ctrl + Alt + T** | Toggle the floating **Tactical Analysis HUD** panel |
| `Auto` | **Ctrl + Alt + B** | Toggle **Full-Screen Auto-Detect** mode |
| `Calibrate` | **Ctrl + Alt + C** | Launch manual calibration fallback |
| `Close` | **Ctrl + Alt + Q** | Exit the visualizer completely |

*All shortcuts use `Ctrl + Alt + [Key]`, meaning they will never interfere with normal typing, chat boxes, browser shortcuts, or games.*

### Windows Taskbar & System Tray Integration
- **Immediate Launch Feedback**: When launched, the sleek control bar appears immediately with live status (`● Searching...` while scanning, `● Locked` when tracking a board, `● Manual` when locked to a custom region).
- **Windows Taskbar**: The toolbar appears on your Windows Taskbar with a custom dark-mode chess knight icon.
- **System Tray Icon**: Right-click the chess knight icon in your Windows notification tray (near the clock) to toggle the Overlay, toggle the Tactical HUD, switch Auto-Track, recalibrate, or exit at any time.

### Moving the Toolbar & HUD
- Click and drag anywhere on the toolbar or HUD (or on the `::` grip on the left) to move them anywhere on your screen.
- Both positions are saved automatically across restarts.

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

## Architecture & Screen Capture Isolation Invariant

### The Anti-Self-Detection Standard
To prevent visual feedback loops (where the screen capture grabs the visualizer's own arrows, brackets, or highlights and feeds them back into the ML piece classifier or turn detector), the application enforces a strict **Three-Layer Capture Isolation Architecture**:

1. **Layer 1 — Hardware/OS DWM Window Exclusion (`WDA_EXCLUDEFROMCAPTURE`)**:
   Every overlay window (`OverlayWidget`, `HUDPanel`, `ControlBar`, `CalibrationWidget`) enforces `SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE = 0x11)` upon creation and in its `showEvent()`. Windows Desktop Window Manager (DWM) excludes these windows from the capture pipeline at the GPU compositor level with zero CPU overhead and zero visual flickering.
2. **Layer 2 — Defensive Fallback (`_grab_clean`)**:
   If running in an environment where OS-level DWM exclusion is unsupported or returns an error, the orchestration loop momentarily hides the overlay during frame acquisition (`overlay.hide()` $\to$ `grab()` $\to$ `overlay.show()`), mathematically guaranteeing clean input frames.
3. **Layer 3 — Visual Sanitization (`strip_overlay_artifacts`)**:
   An OpenCV image preprocessor scans crops for any high-saturation overlay colors ($\ge 215$) and inpaints them before piece classification or move highlight analysis.

**Rule for Future Code:**
> Any new window or widget rendered above the desktop must invoke `set_window_capture_exclusion(self)` in `_setup_ui()` and `showEvent()`. Under no circumstances may an overlay window be created without active capture exclusion.

---

## Running Automated Tests

To verify that the capture logic, tactical intelligence engine, recognition pipeline, and grid alignment are working on your system:

```bash
python -m unittest discover tests -v
```

*(All 72 unit and integration tests passing in under 3 seconds)*
