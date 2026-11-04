# Chess Capture Visualizer

A Windows desktop overlay that reads any chessboard visible on your screen and draws **live legal capture, attack, and defense arrows and highlights** on top of it.

---

## 🎨 Visualization Rules

- 🔵 **Blue Highlights & Arrows**: Your pieces' influence (captures onto enemy pieces, defense of your own pieces, and attacks onto empty squares).
- 🔴 **Red Highlights & Arrows**: Opponent pieces' influence (attacks on your pieces, defense of enemy pieces, and attacks onto empty squares).
- 🟣 **Violet Highlights**: Contested squares where **both** White and Black have influence.
- 🛡️ **Defending Pieces Included**: Arrows point to friendly pieces that are protected/defended by other pieces of the same color (can be toggled on/off with **F5** or button).
- 🎯 **Sleek Arrow Visualization**: Thin shafts with crisp arrowheads pointing from the attacking/defending pieces to target squares. Toggle between **Small** and **Medium** with **F8**.
- 🛡️ **Pinned Piece Filtering**: Pinned pieces that cannot legally move because doing so exposes their King are strictly excluded from illegal moves.
- 🧹 **Anti-Artifact Filter**: Grey move dots and click highlights on Chess.com / Lichess are automatically filtered out so arrows stay rock-solid.

---

## 🕹️ Shortcuts & Button System

Every shortcut has its own dedicated button on the floating Control Panel:

| Button on Panel | Shortcut Key | Description |
|:---|:---:|:---|
| `👁️ Overlay: ON / OFF` | **Ctrl + Space** *(or **F1**)* | **Master Toggle**: Show or hide all arrows & highlights instantly |
| `🔵 You (White/Black)` | **F3** | Toggle your influence arrows & highlights on/off |
| `🔴 Enemy (Black/White)` | **F4** | Toggle opponent influence arrows & highlights on/off |
| `🛡️ Defend: ON / OFF` | **F5** | Toggle arrows pointing to defended friendly pieces |
| `🔄 Playing: White / Black` | **F6** | Flip perspective (swaps You ↔ Enemy and White ↔ Black) |
| `🎨 Highlights: ON / OFF` | **F7** | Toggle square background tints on/off |
| `↕ Arrows: Small / Med` | **F8** | Toggle arrow size mode between Small and Medium |
| `🎯 Calibrate` | **F2** | Redraw the 8×8 board alignment box |
| `◀ ▲ ▼ ▶` (Nudge) | *Click on panel* | Nudge board region by 2px in any direction |
| `✖ Close` | **Esc** *(or **F9**)* | Exit the visualizer |

*All hotkeys are global and work even while your browser or chess game has focus!*

---

## 🚀 Moving & Repositioning the Window

The floating Control Panel has a **spacious top drag header**:
- Simply click and drag anywhere across the top bar (`::: Drag anywhere here to move window :::`) to effortlessly move it anywhere on your screen.
- Plenty of empty padding ensures you will never accidentally click a button while dragging.
- The control panel remembers where you placed it across sessions.

---

## 🚀 How to Launch

- **First Run (Calibration)**: Double-click **`launch_calibrate.bat`**
  - A live transparent window opens with an 8×8 dashed alignment grid.
  - Drag over your chessboard, align the grid, and press **Enter**!
- **Regular Runs**: Double-click **`launch.bat`** (launches silently in the background).

---

## 🧪 Running Tests

```bash
python tests/test_chess_logic.py
python tests/test_integration.py
```
*(All 15 unit and integration tests passing)*
