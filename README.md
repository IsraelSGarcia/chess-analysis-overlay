# Chess Capture Visualizer

A Windows desktop overlay that reads any chessboard visible on your screen and draws **live legal capture, attack, and defense arrows and highlights** on top of it.

---

## 🎨 Visualization Rules

- 🔵 **Blue Highlights & Arrows**: Your pieces' influence (captures onto enemy pieces, defense of friendly pieces, and attacks onto empty squares).
- 🔴 **Red Highlights & Arrows**: Opponent pieces' influence (attacks on your pieces, defense of enemy pieces, and attacks onto empty squares).
- 🟣 **Violet Highlights**: Contested squares where **both** White and Black have influence.
- 🛡️ **Defending Pieces Included**: Arrows point to friendly pieces protected by pieces of the same color (can be toggled on/off with the `[ 🛡 Defend ]` button or shortcut).
- 🛡️ **Pinned Piece Filtering**: Pinned pieces that cannot legally move because doing so exposes their King are strictly excluded from illegal moves.
- 🧹 **Anti-Artifact Filter**: Grey move dots and click highlights on Chess.com / Lichess are automatically filtered out so arrows stay rock-solid.

---

## 🕹️ Clean Controls & Conflict-Free Shortcuts

A compact, minimalist floating pill toolbar sits above your chessboard. Every button has tooltips and dedicated, conflict-free global shortcuts using `Ctrl + Alt`:

| Button on Toolbar | Global Shortcut | Description |
|:---|:---:|:---|
| `[ 👁 ON / OFF ]` | **Ctrl + Alt + X** | **Master Toggle**: Show or hide the entire overlay instantly |
| `[ 🔵 You ]` | **Ctrl + Alt + A** | Toggle your influence arrows & highlights on/off |
| `[ 🔴 Enemy ]` | **Ctrl + Alt + S** | Toggle opponent influence arrows & highlights on/off |
| `[ 🛡 Defend ]` | **Ctrl + Alt + D** | Toggle defending friendly pieces arrows |
| `[ 🔄 Flip ]` | **Ctrl + Alt + F** | Flip perspective (swaps You ↔ Enemy and White ↔ Black) |
| `[ 🎨 Grid ]` | **Ctrl + Alt + H** | Toggle square background tints on/off |
| `[ 🎯 Calibrate ]` | **Ctrl + Alt + C** | Redraw the 8×8 board alignment box |
| `[ ✕ ]` | **Ctrl + Alt + Q** | Exit the visualizer |

*The `Ctrl + Alt + [Key]` combinations are globally safe and will not conflict with typing, chat, IDEs, browser keys, or games.*

---

## 🚀 Moving the Toolbar

- The floating toolbar has comfortable drag space around the grip on the left (`♟`).
- Click and drag anywhere on the toolbar to reposition it anywhere on your screen.
- Remembers its position across sessions automatically.

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
