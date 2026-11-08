# Chess Analysis Overlay

An advanced Windows desktop chess analysis overlay that uses computer vision to recognize chess positions on your screen (Chess.com, Lichess, desktop GUIs) and provides real-time tactical and capture intelligence through high-precision visual annotations.

**Non-Engine Philosophy**: Unlike conventional chess engines (Stockfish, LCZero, Komodo) that calculate deep search trees to recommend single "best" moves, this project is built upon **0-ply geometric awareness, concrete tactical pattern recognition, and simultaneous two-sided analysis**.

---

## Architecture: The Umbrella Monorepo

The codebase is organized as a modular monorepo structured strictly by domain responsibility:

```text
chess-analysis-overlay/
│
├── README.md
├── requirements.txt
├── install.bat / launch.bat
├── main.py                          # Root umbrella entry point
│
├── core/                            # Shared domain infrastructure
│   ├── board_recognition/           # Screen capture, grid snapping, piece classification
│   ├── chess_rules/                 # Move legality, board validation, transition continuity
│   ├── position_representation/     # Board models, geometric square-to-pixel coordinate transforms
│   └── shared_analysis/             # Static Exchange Evaluation (SEE), attack/defense maps, piece values
│
├── projects/                        # Specialized analytical subprojects
│   ├── chess-capture-visualizer/    # Legal capture & defense moves for both sides simultaneously
│   └── chess-tactical-analyzer/     # Tactical motifs, hanging pieces, trapped pieces, X-rays, blunders
│
├── overlay/                         # Unified presentation layer
│   ├── rendering/                   # Hardware-accelerated transparent canvas (arrows, brackets, rays)
│   ├── interface/                   # Draggable control bar, floating analysis HUD panel, system tray
│   └── configuration/               # Centralized VisualTheme design system, persistent settings
│
└── tests/                           # Complete test suite covering all modules (113 unit tests)
```

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

## Specialized Analytical Modes

Switch between analytical modes at any time with the **`Tactics` / `Captures`** button on the toolbar or via **`Ctrl + Alt + M`**:

### 1. Tactical Analyzer Mode (`Mode: Tactics`)
Specialized analytical mode focusing on concrete tactical motifs, vulnerabilities, and exchanges:
- **Winning Trade Arrows**: Emerald Green arrows (`#00E676`) on favorable captures (Static Exchange Evaluation $> 0$) and free hanging pieces.
- **Multi-Target Fork Arrows**: Vivid purple arrows (`#D500F9`) radiating from attacking pieces directly to forked victims.
- **Pins & Skewers**: Directed lines highlighting absolute pins (to the King) and relative pins (to the Queen/Rook).
- **Discovered Attacks & Checks**: Highlighting the masking piece and uncovering slider rays.
- **Trapped Pieces**: Ice Cyan corner bracket outlines (`#00E5FF`) on pieces with zero safe destination squares.
- **Slider X-Ray Rays**: Ice Cyan dashed arrows (`#00E5FF`) piercing through 1 obstacle directly threatening enemy heavy pieces.
- **Removing the Defender & Mating Threats**: Visualizing attacks on sole defenders and immediate checkmate opportunities.
- **Subtle Blunder Warnings**: Semi-transparent Crimson Red arrows (`#FF1744`, opacity 0.43, width mult 0.55) indicating candidate moves that immediately lose material or allow checkmate.
- **Hanging Piece Alerts**: Radiant Orange dashed boxes and threat arrows (`#FF6D00`) on undefended or tactically vulnerable pieces.
- **Analysis HUD Panel**: Floating, collapsible companion card showing material balance, hanging piece counts, and active motif badges with click-to-highlight filtering.

### 2. Capture Visualizer Mode (`Mode: Captures`)
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
| `Turn` (White/Black/Auto) | **Click Turn Badge** | Explicitly toggle or cycle active player turn |
| `Player` | **Ctrl + Alt + A** | Toggle your influence arrows & highlights on/off |
| `Enemy` | **Ctrl + Alt + S** | Toggle opponent influence arrows & highlights on/off |
| `Defense` | **Ctrl + Alt + D** | Toggle arrows pointing to friendly defended pieces |
| `Flip` | **Ctrl + Alt + F** | Flip player color / perspective (Captures mode) |
| `Highlights` | **Ctrl + Alt + H** | Toggle square background tints on/off (Captures mode) |
| `HUD` | **Ctrl + Alt + T** | Toggle the floating **Tactical Analysis HUD** panel |
| `Auto` | **Ctrl + Alt + B** | Toggle **Full-Screen Auto-Detect** mode |
| `Calibrate` | **Ctrl + Alt + C** | Launch manual calibration fallback |
| `Close` | **Ctrl + Alt + Q** | Exit the visualizer completely |

*All shortcuts use `Ctrl + Alt + [Key]`, meaning they will never interfere with normal typing, chat boxes, browser shortcuts, or games.*

---

## Screen Capture Isolation Invariant

### The Anti-Self-Detection Standard
To prevent visual feedback loops (where the screen capture grabs the visualizer's own arrows, brackets, or highlights and feeds them back into piece classification or turn detection), the application enforces a strict **Hardware/OS DWM Window Exclusion**:
- Every overlay window (`OverlayWidget`, `HUDPanel`, `ControlBar`, `CalibrationWidget`) enforces `SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE = 0x11)` upon creation and in its `showEvent()`. Windows Desktop Window Manager (DWM) excludes these windows from the capture pipeline at the GPU compositor level with zero CPU overhead and zero visual flickering.

---

## Running Automated Tests

To verify that the monorepo packages, core rules, tactical engines, and coordinate geometry are functioning correctly:

```bash
python -m unittest discover tests -v
```

*(All 113 unit and integration tests passing in ~2 seconds)*
