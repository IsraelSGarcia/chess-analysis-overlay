# Chess Capture Visualizer

A Windows desktop overlay that reads any chessboard visible on your screen and draws **live legal capture arrows and square highlights** on top of it.

---

## 🎨 Visualization Rules

- 🔵 **Blue Highlights & Arrows**: Every square White can legally capture onto (including empty squares).
- 🔴 **Red Highlights & Arrows**: Every square Black can legally capture onto (including empty squares).
- 🟣 **Violet Highlights**: Contested squares where **both** White and Black can capture.
- 🎯 **Small, Sleek Arrows**: Slender shafts with crisp arrowheads pointing from the attacking pieces to the highlighted target squares.
- 🛡️ **Pinned Piece Filtering**: Pinned pieces that cannot legally move because doing so exposes their King are strictly excluded.
- ♟️ **Pawns**: Accurately shows diagonal capture squares (e.g. e4 pawn captures onto d5 and f5, not forward).
- 🧹 **Anti-Artifact Filter**: Clicking on pieces or hovering on Chess.com / Lichess (which displays grey move dots) is filtered out automatically so your arrows stay rock-solid.

---

## 🚀 How to Use

### First Run — Calibrate Your Board

Double-click:
```
launch_calibrate.bat
```
*(or run `python -m chess_visualizer --calibrate`)*

1. The screen will dim slightly into a **live transparent view** (you can see your real browser / chessboard live).
2. **Click and drag a box** over your chessboard.
3. An **8×8 dashed alignment grid** will appear inside your box — line it up with the 64 squares on screen!
4. *(Optional)* Use your **Arrow keys** to nudge position (Hold `Shift` for larger steps) or `+` / `-` to resize.
5. Press **ENTER** (or Space) to confirm!

### Regular Runs

Double-click:
```
launch.bat
```
The app launches silently in the background (no console window blocking your view) and remembers your saved board position.

---

## 🕹️ Controls (Floating Bar & Global Hotkeys)

A sleek floating Control Bar appears right above your chessboard:

| Button | Hotkey | Action |
|:---|:---:|:---|
| `🔵 Blue` | **F3** *(or Ctrl+Shift+W)* | Toggle Blue (White) captures on/off |
| `🔴 Red` | **F4** *(or Ctrl+Shift+B)* | Toggle Red (Black) captures on/off |
| `🔄 Flip` | **F6** | Flip perspective between White and Black at bottom |
| `🎯 Calibrate` | **F2** *(or Ctrl+Shift+C)* | Recalibrate board position anytime |
| `Highlights` | **F7** | Toggle square background tints |
| `✖ Close` | **F9** *(or Ctrl+Shift+Q)* | Exit the overlay |

*All hotkeys are global and work even while your browser or chess game has focus!*

---

## 📁 Project Structure

```
chess-capture-visualizer/
├── chess_visualizer/
│   ├── chess_logic.py       # Legal capture calculation (including empty squares)
│   ├── recognition.py       # chessvision neural net + move-dot artifact cleaner
│   ├── capture.py           # High-DPI aware screen capture
│   ├── _overlay_widget.py   # Small arrows & square highlight renderer (click-through)
│   ├── _control_bar.py      # Floating 1-click toolbar
│   ├── _calibration.py      # Live transparent 8x8 grid calibration tool
│   ├── settings.py          # Persistent JSON settings
│   └── main.py              # Main application orchestrator
├── tests/
│   ├── test_chess_logic.py  # 10 unit tests for chess capture rules
│   └── test_integration.py  # 4 integration tests
├── launch.bat               # Silent double-click launcher
├── launch_calibrate.bat     # Calibration double-click launcher
└── requirements.txt
```

---

## 🧪 Running Tests

```bash
python tests/test_chess_logic.py
python tests/test_integration.py
```
*(All 14 unit and integration tests passing)*
