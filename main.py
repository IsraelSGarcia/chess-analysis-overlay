"""
main.py
=======
Chess Analysis Overlay — Root Monorepo Entry Point.

Integrates:
- core (board recognition, chess rules, position representation, shared analysis)
- projects/chess-capture-visualizer (legal capture & defense visualization)
- projects/chess-tactical-analyzer (tactical motifs, hanging, trapped, X-rays, blunders, HUD)
- overlay (rendering, floating HUD, draggable control bar, theme system)
"""

import sys
from overlay.app import main

if __name__ == "__main__":
    main()
