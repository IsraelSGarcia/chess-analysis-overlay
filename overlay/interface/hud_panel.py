"""
_hud_panel.py
=============
Compact floating Analysis HUD for real-time tactical intelligence.

Designed for instant glanceability:
- 🔴 Checks & Blunders (Crimson Red #FF1744)
- 🟢 Winning Trades (Vivid Emerald Green #00E676: SEE > 0)
- 🟣 Tactical Motifs (Electric Purple #D500F9: Forks, Pins, Skewers)
- 🟠 Hanging Pieces (Radiant Bright Orange #FF6D00)
- 🔵 Defended Pieces (Sky Blue #00B0FF)
Every element visible on the chessboard has a direct 1-line plain-English explanation.
"""

from __future__ import annotations

from typing import Optional, List
import chess
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
)

from projects.chess_tactical_analyzer.report import TacticalReport
from core.board_recognition.capture import set_window_capture_exclusion
from overlay.configuration.theme import THEME


class HUDPanel(QWidget):
    """
    Sleek, draggable floating HUD panel displaying live tactical analytics.
    Matches the colors, alerts, and arrows rendered directly on the board.
    """

    def __init__(self, on_close: Optional[callable] = None, on_toggle_turn: Optional[callable] = None) -> None:
        super().__init__(None)
        self.on_close_callback = on_close
        self.on_toggle_turn = on_toggle_turn or (lambda: None)
        self._drag_pos = QPoint()
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(310)
        set_window_capture_exclusion(self)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main Card container
        self.card = QFrame()
        self.card.setObjectName("hud_card")
        self.card.setStyleSheet("""
            QFrame#hud_card {
                background-color: rgba(16, 18, 22, 245);
                border: 1px solid rgba(255, 255, 255, 28);
                border-radius: 8px;
            }
        """)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(5)

        # -----------------------------------------------------------------
        # Header (Drag handle + Title + Close)
        # -----------------------------------------------------------------
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.grip = QLabel("::")
        self.grip.setStyleSheet("color: #4f5765; font-size: 13px; font-weight: bold; margin-right: 2px;")
        self.grip.setCursor(Qt.CursorShape.SizeAllCursor)
        header_layout.addWidget(self.grip)

        self.lbl_title = QLabel("Tactical Intelligence")
        self.lbl_title.setStyleSheet("color: #e6edf3; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()

        self.btn_turn_hud = QPushButton("White to Move")
        self.btn_turn_hud.setToolTip("Click to toggle active turn (White / Black)")
        self.btn_turn_hud.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 20);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 60);
                border-radius: 3px;
                font-size: 10px;
                font-weight: 600;
                padding: 1px 6px;
                margin-right: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 38);
                border-color: #ffffff;
            }
        """)
        self.btn_turn_hud.clicked.connect(self.on_toggle_turn)
        header_layout.addWidget(self.btn_turn_hud)

        self.btn_close = QPushButton("×")
        self.btn_close.setFixedSize(18, 18)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #7d8590;
                border: none;
                font-size: 14px;
                font-weight: bold;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                color: #ffffff;
                background-color: rgba(255, 255, 255, 20);
                border-radius: 9px;
            }
        """)
        self.btn_close.clicked.connect(self._handle_close)
        header_layout.addWidget(self.btn_close)

        card_layout.addLayout(header_layout)

        # -----------------------------------------------------------------
        # Glanceable Badges Grid (1:1 color matched to board annotations)
        # -----------------------------------------------------------------
        # Urgent Check / Mate Alert (Pure Crimson Red)
        self.lbl_alert = QLabel("")
        self.lbl_alert.setWordWrap(True)
        self.lbl_alert.setStyleSheet(THEME.get_badge_css(THEME.BLUNDER_HEX, bg_alpha=0.22, border_alpha=0.85))
        self.lbl_alert.setVisible(False)
        card_layout.addWidget(self.lbl_alert)

        # Winning Trades Pill (Vivid Emerald Green)
        self.lbl_trades = QLabel("")
        self.lbl_trades.setWordWrap(True)
        self.lbl_trades.setStyleSheet(THEME.get_badge_css(THEME.WINNING_TRADE_HEX))
        self.lbl_trades.setVisible(False)
        card_layout.addWidget(self.lbl_trades)

        # Tactical Motifs Pill (Electric Purple: Forks, Pins, Skewers)
        self.lbl_motifs = QLabel("")
        self.lbl_motifs.setWordWrap(True)
        self.lbl_motifs.setStyleSheet(THEME.get_badge_css(THEME.MOTIF_HEX))
        self.lbl_motifs.setVisible(False)
        card_layout.addWidget(self.lbl_motifs)

        # Hanging Pieces Pill (Radiant Bright Orange)
        self.lbl_hanging = QLabel("")
        self.lbl_hanging.setWordWrap(True)
        self.lbl_hanging.setStyleSheet(THEME.get_badge_css(THEME.HANGING_HEX))
        self.lbl_hanging.setVisible(False)
        card_layout.addWidget(self.lbl_hanging)

        # Trapped Pieces Pill (Ice Cyan)
        self.lbl_trapped = QLabel("")
        self.lbl_trapped.setWordWrap(True)
        self.lbl_trapped.setStyleSheet(THEME.get_badge_css(THEME.TRAPPED_HEX))
        self.lbl_trapped.setVisible(False)
        card_layout.addWidget(self.lbl_trapped)

        # Defended Pieces Pill (Sky Blue)
        self.lbl_defended = QLabel("")
        self.lbl_defended.setWordWrap(True)
        self.lbl_defended.setStyleSheet(THEME.get_badge_css(THEME.DEFENSE_HEX, bg_alpha=0.16, border_alpha=0.60))
        self.lbl_defended.setVisible(False)
        card_layout.addWidget(self.lbl_defended)

        # -----------------------------------------------------------------
        # 3. Compact Footer (Material balance + Turn)
        # -----------------------------------------------------------------
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(2, 2, 2, 0)

        self.lbl_material = QLabel("Material: Equal")
        self.lbl_material.setStyleSheet("color: #8b949e; font-size: 10px; font-weight: 600;")
        footer_layout.addWidget(self.lbl_material)
        footer_layout.addStretch()

        self.lbl_turn = QLabel("White to move")
        self.lbl_turn.setStyleSheet("color: #8b949e; font-size: 10px; font-weight: 500;")
        footer_layout.addWidget(self.lbl_turn)

        card_layout.addLayout(footer_layout)

        main_layout.addWidget(self.card)
        self.adjustSize()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        set_window_capture_exclusion(self)

    # -------------------------------------------------------------------------
    # Update from TacticalReport
    # -------------------------------------------------------------------------

    def update_report(self, report: Optional[TacticalReport]) -> None:
        """Update HUD UI elements from a TacticalReport."""
        if report is None:
            self.lbl_alert.setVisible(False)
            self.lbl_trades.setVisible(False)
            self.lbl_motifs.setVisible(False)
            self.lbl_hanging.setVisible(False)
            self.lbl_trapped.setVisible(False)
            self.lbl_defended.setVisible(False)
            self.lbl_material.setText("Waiting for board position...")
            self.adjustSize()
            return

        turn_color = report.board.turn
        turn_name = "White" if turn_color == chess.WHITE else "Black"
        self.btn_turn_hud.setText(f"{turn_name} to Move")

        # 1. Check / Mate Alert & Blunders (Red #FF1744)
        all_blunders = report.blunders.get(turn_color, []) if hasattr(report, 'blunders') else []
        blunder_summary = ""
        if all_blunders:
            blunder_sans = []
            for b in all_blunders:
                try:
                    blunder_sans.append(report.board.san(b.move))
                except Exception:
                    blunder_sans.append(str(b.move))
            blunder_summary = f"🔴 Blunder Alerts ({len(all_blunders)}): Avoid {', '.join(blunder_sans[:3])}"

        if report.board.is_checkmate():
            winner = "Black" if turn_color == chess.WHITE else "White"
            loser = "White" if turn_color == chess.WHITE else "Black"
            self.lbl_alert.setText(f"🔴 CHECKMATE — {winner} wins! ({loser} mated)")
            self.lbl_alert.setVisible(True)
        elif report.board.is_check():
            checkers = list(report.board.checkers())
            check_sources = []
            for chk_sq in checkers:
                p = report.board.piece_at(chk_sq)
                sym = p.symbol() if p else "?"
                check_sources.append(f"{sym}@{chess.square_name(chk_sq)}")
            src_str = f" from {', '.join(check_sources)}" if check_sources else ""
            msg = f"🔴 CHECK! {turn_name} King under attack{src_str}"
            if blunder_summary:
                msg += f" | {blunder_summary.replace('🔴 ', '')}"
            self.lbl_alert.setText(msg)
            self.lbl_alert.setVisible(True)
        elif report.board.is_stalemate():
            self.lbl_alert.setText("⚖️ STALEMATE — Draw by stalemate (no legal moves)")
            self.lbl_alert.setVisible(True)
        elif blunder_summary:
            self.lbl_alert.setText(blunder_summary)
            self.lbl_alert.setVisible(True)
        else:
            self.lbl_alert.setVisible(False)

        # 2. Winning Trades for Active Turn (SEE > 0, Emerald Green #00E676)
        fav_list = report.favorable_captures(turn_color)
        if fav_list:
            trades_desc = []
            for f in fav_list[:2]:
                trades_desc.append(f"{f.sequence[0]} (+{f.score/100:.1f})")
            self.lbl_trades.setText(f"🟢 Winning Trade: {', '.join(trades_desc)} — net material exchange")
            self.lbl_trades.setVisible(True)
        else:
            self.lbl_trades.setVisible(False)

        # 4. Tactical Motifs (Electric Purple #D500F9: Forks, Pins, Skewers)
        if report.motifs:
            motif_items = []
            for m in report.motifs[:2]:
                motif_items.append(m.description)
            more_count = len(report.motifs) - 2
            extra = f" (+{more_count} more)" if more_count > 0 else ""
            self.lbl_motifs.setText(f"🟣 Tactical Motif: {' | '.join(motif_items)}{extra}")
            self.lbl_motifs.setVisible(True)
        else:
            self.lbl_motifs.setVisible(False)

        # 5. Hanging Pieces (Radiant Bright Orange #FF6D00)
        hanging_own = report.hanging.get(turn_color, [])
        hanging_enemy = report.hanging.get(not turn_color, [])
        hanging_parts = []
        if hanging_own:
            extra = f" (+{len(hanging_own)-2} more)" if len(hanging_own) > 2 else ""
            hanging_parts.append(f"Friendly {', '.join(f'{h.piece_symbol}@{h.square_name}' for h in hanging_own[:2])}{extra} undefended")
        if hanging_enemy:
            extra = f" (+{len(hanging_enemy)-2} more)" if len(hanging_enemy) > 2 else ""
            hanging_parts.append(f"Enemy {', '.join(f'{h.piece_symbol}@{h.square_name}' for h in hanging_enemy[:2])}{extra} vulnerable")
        if hanging_parts:
            self.lbl_hanging.setText(f"🟠 Hanging: {' | '.join(hanging_parts)}")
            self.lbl_hanging.setVisible(True)
        else:
            self.lbl_hanging.setVisible(False)

        # 5b. Trapped Pieces (Ice Cyan #00E5FF)
        trapped_map = getattr(report, 'trapped_pieces', {})
        trapped_own = trapped_map.get(turn_color, [])
        trapped_enemy = trapped_map.get(not turn_color, [])
        trapped_parts = []
        if trapped_own:
            trapped_parts.append(f"Friendly {', '.join(f'{t.piece_symbol}@{t.square_name}' for t in trapped_own[:2])} trapped")
        if trapped_enemy:
            trapped_parts.append(f"Enemy {', '.join(f'{t.piece_symbol}@{t.square_name}' for t in trapped_enemy[:2])} trapped")
        if trapped_parts:
            self.lbl_trapped.setText(f"🧊 Trapped: {' | '.join(trapped_parts)}")
            self.lbl_trapped.setVisible(True)
        else:
            self.lbl_trapped.setVisible(False)

        # 6. Defended Pieces (Sky Blue #00B0FF)
        def_pieces = getattr(report.attack_map, 'defended_pieces', set())
        own_def_count = sum(1 for sq in def_pieces if report.board.piece_at(sq) and report.board.piece_at(sq).color == turn_color)
        if own_def_count > 0:
            self.lbl_defended.setText(f"🔵 Defense: {own_def_count} friendly pieces protected")
            self.lbl_defended.setVisible(True)
        else:
            self.lbl_defended.setVisible(False)

        # 7. Material Balance & Turn
        lead = report.white_material_lead
        if lead > 0:
            self.lbl_material.setText(f"Material: White +{lead:.1f}")
            self.lbl_material.setStyleSheet("color: #58a6ff; font-size: 10px; font-weight: 600;")
        elif lead < 0:
            self.lbl_material.setText(f"Material: Black +{abs(lead):.1f}")
            self.lbl_material.setStyleSheet("color: #ff7b72; font-size: 10px; font-weight: 600;")
        else:
            self.lbl_material.setText("Material: Equal")
            self.lbl_material.setStyleSheet("color: #8b949e; font-size: 10px; font-weight: 600;")

        turn_icon = "⚪" if turn_color == chess.WHITE else "⚫"
        self.lbl_turn.setText(f"{turn_name} to move {turn_icon}")

        self.adjustSize()

    def position_beside_board(self, left: int, top: int, width: int, height: int) -> None:
        """Position HUD panel neatly to the right of the board."""
        hud_x = left + width + 10
        hud_y = top
        self.move(hud_x, hud_y)

    def _handle_close(self) -> None:
        self.hide()
        if self.on_close_callback:
            self.on_close_callback()

    # -------------------------------------------------------------------------
    # Drag Handling
    # -------------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self._drag_pos = QPoint()
        event.accept()
