"""
_hud_panel.py
=============
Compact floating Analysis HUD for real-time tactical and positional intelligence.

Designed for instant glanceability:
- In Tactical Mode:
  - 🔴 Checks & Blunders (Crimson Red #FF1744)
  - 🟢 Winning Trades (Vivid Emerald Green #00E676: SEE > 0)
  - 🟣 Tactical Motifs (Electric Purple #D500F9: Forks, Pins, Skewers)
  - 🟠 Hanging Pieces (Radiant Bright Orange #FF6D00)
  - 🧊 Trapped Pieces (Ice Cyan #00E5FF)
  - 🔵 Defended Pieces (Sky Blue #00B0FF)
  - 👑 Endgame Principles (Rule of the Square & Opposition)

- In Positional Mode:
  - 🟢 Outposts (Mint Green #00E676: holes in enemy camp immune to pawn attack)
  - 🔵 Open & Semi-Open Files (Sky Blue #00B0FF: heavy piece file control)
  - 🟠 Pawn Structure Weaknesses (Amber #FFAB00: isolated, backward, doubled, islands)
  - 🟠 Bishop Quality (Radiant Orange #FF6D00: bad vs. active bishops)
  - 🏛️ Space & Territory Control (Warm Gold #D29922: advanced square dominance)
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
    Sleek, draggable floating HUD panel displaying live tactical or positional analytics.
    Matches 1:1 with the colors, alerts, and annotations rendered directly on the board.
    """

    def __init__(self, on_close: Optional[callable] = None, on_toggle_turn: Optional[callable] = None) -> None:
        super().__init__(None)
        self.on_close_callback = on_close
        self.on_toggle_turn = on_toggle_turn or (lambda: None)
        self._drag_pos = QPoint()
        self._mode: str = "tactics"
        self._last_report: Optional[TacticalReport] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(320)
        set_window_capture_exclusion(self)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main Card container
        self.card = QFrame()
        self.card.setObjectName("hud_card")
        self.card.setStyleSheet("""
            QFrame#hud_card {
                background-color: rgba(16, 18, 22, 248);
                border: 1px solid rgba(255, 255, 255, 28);
                border-radius: 8px;
            }
        """)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(5)

        # -----------------------------------------------------------------
        # Header (Drag handle + Title + Turn override + Close)
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
        # Common Top Badge: Opening Classification & Trap Alerts (Soft Blue)
        # -----------------------------------------------------------------
        self.lbl_opening = QLabel("")
        self.lbl_opening.setWordWrap(True)
        self.lbl_opening.setStyleSheet(THEME.get_badge_css(THEME.OPENING_HEX, bg_alpha=0.18, border_alpha=0.65))
        self.lbl_opening.setVisible(False)
        card_layout.addWidget(self.lbl_opening)

        # -----------------------------------------------------------------
        # Tactical Mode Badges (1:1 color matched to board annotations)
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

        # Endgame Principles (Ice Cyan: Rule of the Square & Opposition)
        self.lbl_endgame = QLabel("")
        self.lbl_endgame.setWordWrap(True)
        self.lbl_endgame.setStyleSheet(THEME.get_badge_css(THEME.ENDGAME_HEX, bg_alpha=0.18, border_alpha=0.65))
        self.lbl_endgame.setVisible(False)
        card_layout.addWidget(self.lbl_endgame)

        # -----------------------------------------------------------------
        # Positional Mode Badges (1:1 matched to positional board highlights)
        # -----------------------------------------------------------------
        # 1. Outposts (Mint Green)
        self.lbl_pos_outposts = QLabel("")
        self.lbl_pos_outposts.setWordWrap(True)
        self.lbl_pos_outposts.setStyleSheet(THEME.get_badge_css(THEME.OUTPOST_HEX, bg_alpha=0.20, border_alpha=0.75))
        self.lbl_pos_outposts.setVisible(False)
        card_layout.addWidget(self.lbl_pos_outposts)

        # 2. Open & Semi-Open Files (Sky Blue)
        self.lbl_pos_files = QLabel("")
        self.lbl_pos_files.setWordWrap(True)
        self.lbl_pos_files.setStyleSheet(THEME.get_badge_css(THEME.OPEN_FILE_HEX, bg_alpha=0.20, border_alpha=0.75))
        self.lbl_pos_files.setVisible(False)
        card_layout.addWidget(self.lbl_pos_files)

        # 3. Pawn Structure Weaknesses (Amber)
        self.lbl_pos_pawns = QLabel("")
        self.lbl_pos_pawns.setWordWrap(True)
        self.lbl_pos_pawns.setStyleSheet(THEME.get_badge_css(THEME.PAWN_WEAKNESS_HEX, bg_alpha=0.20, border_alpha=0.75))
        self.lbl_pos_pawns.setVisible(False)
        card_layout.addWidget(self.lbl_pos_pawns)

        # 4. Bishop Quality (Radiant Orange)
        self.lbl_pos_bishops = QLabel("")
        self.lbl_pos_bishops.setWordWrap(True)
        self.lbl_pos_bishops.setStyleSheet(THEME.get_badge_css(THEME.BAD_BISHOP_HEX, bg_alpha=0.20, border_alpha=0.75))
        self.lbl_pos_bishops.setVisible(False)
        card_layout.addWidget(self.lbl_pos_bishops)

        # 5. Space & Territory Advantage (Warm Gold)
        self.lbl_pos_space = QLabel("")
        self.lbl_pos_space.setWordWrap(True)
        self.lbl_pos_space.setStyleSheet(THEME.get_badge_css(THEME.POSITIONAL_HEX, bg_alpha=0.20, border_alpha=0.75))
        self.lbl_pos_space.setVisible(False)
        card_layout.addWidget(self.lbl_pos_space)

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
    # Mode Switching: Strictly separates Tactical vs Positional Intelligence
    # -------------------------------------------------------------------------

    def set_mode(self, mode: str) -> None:
        """Update header title and context depending on active analysis mode."""
        self._mode = mode.lower()
        if self._mode == "positional":
            self.lbl_title.setText("Positional Intelligence")
        else:
            self.lbl_title.setText("Tactical Intelligence")

        if self._last_report:
            self.update_report(self._last_report)

    # -------------------------------------------------------------------------
    # Update from TacticalReport
    # -------------------------------------------------------------------------

    def update_report(self, report: Optional[TacticalReport]) -> None:
        """Update HUD UI elements from a TacticalReport."""
        self._last_report = report

        if report is None:
            self._hide_all_badges()
            self.lbl_material.setText("Waiting for board position...")
            self.adjustSize()
            return

        turn_color = report.board.turn
        turn_name = "White" if turn_color == chess.WHITE else "Black"
        self.btn_turn_hud.setText(f"{turn_name} to Move")

        # ---------------------------------------------------------------------
        # Branch 1: POSITIONAL INTELLIGENCE MODE
        # (Strictly hides tactical pills; displays outposts, files, pawns, bishops, space)
        # ---------------------------------------------------------------------
        if self._mode == "positional":
            self._hide_tactical_badges()
            self._update_positional_badges(report, turn_color)
        # ---------------------------------------------------------------------
        # Branch 2: TACTICAL INTELLIGENCE MODE
        # (Strictly hides positional pills; displays winning trades, motifs, blunders, hanging)
        # ---------------------------------------------------------------------
        else:
            self._hide_positional_badges()
            self._update_tactical_badges(report, turn_color)

        # Common Footer: Material Balance & Turn
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

    def _hide_all_badges(self) -> None:
        self._hide_tactical_badges()
        self._hide_positional_badges()
        self.lbl_opening.setVisible(False)

    def _hide_tactical_badges(self) -> None:
        self.lbl_alert.setVisible(False)
        self.lbl_trades.setVisible(False)
        self.lbl_motifs.setVisible(False)
        self.lbl_hanging.setVisible(False)
        self.lbl_trapped.setVisible(False)
        self.lbl_defended.setVisible(False)
        self.lbl_endgame.setVisible(False)

    def _hide_positional_badges(self) -> None:
        self.lbl_pos_outposts.setVisible(False)
        self.lbl_pos_files.setVisible(False)
        self.lbl_pos_pawns.setVisible(False)
        self.lbl_pos_bishops.setVisible(False)
        self.lbl_pos_space.setVisible(False)

    def _update_positional_badges(self, report: TacticalReport, turn_color: chess.Color) -> None:
        """Render dedicated positional analysis corresponding 1:1 with board highlights."""
        pos = getattr(report, "positional", None)
        if not pos:
            self._hide_positional_badges()
            return

        # 0. Opening classification if in opening
        if getattr(report, "opening", None):
            self.lbl_opening.setText(f"📖 {report.opening.display_str}")
            self.lbl_opening.setVisible(True)
        else:
            self.lbl_opening.setVisible(False)

        # 1. Outposts (Mint Green)
        if pos.outposts:
            out_parts = []
            for o in pos.outposts[:3]:
                side = "White" if o.color == chess.WHITE else "Black"
                occ = f" ({chess.piece_symbol(o.occupant_piece_type).upper()})" if o.occupant_piece_type else " (unoccupied)"
                out_parts.append(f"{side} {o.square_name}{occ}")
            self.lbl_pos_outposts.setText(f"🟢 Outposts: {', '.join(out_parts)} — immune to pawns")
            self.lbl_pos_outposts.setVisible(True)
        else:
            self.lbl_pos_outposts.setText("🟢 Outposts: None established yet")
            self.lbl_pos_outposts.setVisible(True)

        # 2. Open & Semi-Open Files (Sky Blue)
        if pos.open_files:
            file_descs = []
            for of in pos.open_files[:2]:
                f_name = of.file_letter + "-file"
                if of.is_completely_open:
                    r_w = [chess.square_name(s) for s in of.rooks_controlling.get(chess.WHITE, [])]
                    r_b = [chess.square_name(s) for s in of.rooks_controlling.get(chess.BLACK, [])]
                    ctrls = []
                    if r_w: ctrls.append(f"W R@{','.join(r_w)}")
                    if r_b: ctrls.append(f"B R@{','.join(r_b)}")
                    ctrl_str = f" ({', '.join(ctrls)})" if ctrls else ""
                    file_descs.append(f"Open {f_name}{ctrl_str}")
                elif of.is_semi_open_for is not None:
                    side = "White" if of.is_semi_open_for == chess.WHITE else "Black"
                    file_descs.append(f"Semi-open {f_name} ({side})")
            if file_descs:
                self.lbl_pos_files.setText(f"🔵 Files: {' | '.join(file_descs)}")
                self.lbl_pos_files.setVisible(True)
            else:
                self.lbl_pos_files.setVisible(False)
        else:
            self.lbl_pos_files.setText("🔵 Files: Closed board (all 8 files contested)")
            self.lbl_pos_files.setVisible(True)

        # 3. Pawn Structure Weaknesses (Amber)
        iso_w = [chess.square_name(s) for s in pos.pawn_structure.isolated.get(chess.WHITE, [])]
        iso_b = [chess.square_name(s) for s in pos.pawn_structure.isolated.get(chess.BLACK, [])]
        dbl_w = [chess.square_name(s) for s in pos.pawn_structure.doubled.get(chess.WHITE, [])]
        dbl_b = [chess.square_name(s) for s in pos.pawn_structure.doubled.get(chess.BLACK, [])]
        bkw_w = [chess.square_name(s) for s in pos.pawn_structure.backward.get(chess.WHITE, [])]
        bkw_b = [chess.square_name(s) for s in pos.pawn_structure.backward.get(chess.BLACK, [])]

        pawn_items = []
        all_iso = iso_w + iso_b
        all_dbl = dbl_w + dbl_b
        all_bkw = bkw_w + bkw_b
        if all_iso: pawn_items.append(f"Isolated {', '.join(all_iso[:2])}")
        if all_dbl: pawn_items.append(f"Doubled {', '.join(all_dbl[:2])}")
        if all_bkw: pawn_items.append(f"Backward {', '.join(all_bkw[:2])}")

        isl_str = f"Islands: W{pos.pawn_structure.pawn_islands[chess.WHITE]}/B{pos.pawn_structure.pawn_islands[chess.BLACK]}"
        if pawn_items:
            self.lbl_pos_pawns.setText(f"🟠 Pawns: {' | '.join(pawn_items)} ({isl_str})")
        else:
            self.lbl_pos_pawns.setText(f"🟠 Pawns: Healthy structure ({isl_str})")
        self.lbl_pos_pawns.setVisible(True)

        # 4. Bishop Quality (Radiant Orange)
        bad_bishops = [b for b in pos.bishops if b.is_bad]
        if bad_bishops:
            b_descs = [f"{'White' if b.color == chess.WHITE else 'Black'} B@{b.square_name} ({b.friendly_pawns_on_same_color} pawns on color)" for b in bad_bishops]
            self.lbl_pos_bishops.setText(f"🟠 Bad Bishop: {', '.join(b_descs)}")
            self.lbl_pos_bishops.setVisible(True)
        else:
            self.lbl_pos_bishops.setText("Active Bishops: Both sides hold open bishop diagonals")
            self.lbl_pos_bishops.setVisible(True)

        # 5. Space & Territory Control (Warm Gold)
        w_space = pos.space_control.get(chess.WHITE, 0)
        b_space = pos.space_control.get(chess.BLACK, 0)
        diff = w_space - b_space
        lead_str = f" (+{diff} White advantage)" if diff > 0 else (f" (+{abs(diff)} Black advantage)" if diff < 0 else " (Equal territory)")
        self.lbl_pos_space.setText(f"🏛️ Space: White {w_space} vs Black {b_space} squares{lead_str}")
        self.lbl_pos_space.setVisible(True)

    def _update_tactical_badges(self, report: TacticalReport, turn_color: chess.Color) -> None:
        """Render tactical motifs, winning trades, and blunders in Tactics Mode."""
        # 1. Opening Book & Traps
        if getattr(report, "opening", None):
            trap_str = f" | ⚠️ {report.opening_traps[0].name}" if report.opening_traps else ""
            self.lbl_opening.setText(f"📖 {report.opening.display_str}{trap_str}")
            self.lbl_opening.setVisible(True)
        elif getattr(report, "opening_traps", None):
            self.lbl_opening.setText(f"⚠️ {report.opening_traps[0].description}")
            self.lbl_opening.setVisible(True)
        else:
            self.lbl_opening.setVisible(False)

        # 2. Check / Mate Alert & Blunders (Red #FF1744)
        all_blunders = report.blunders.get(turn_color, []) if hasattr(report, "blunders") else []
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
        elif blunder_summary:
            self.lbl_alert.setText(blunder_summary)
            self.lbl_alert.setVisible(True)
        else:
            self.lbl_alert.setVisible(False)

        # 3. Winning Trades for Active Turn (SEE > 0, Emerald Green #00E676)
        fav_list = report.favorable_captures(turn_color)
        if fav_list:
            trades_desc = []
            for f in fav_list[:2]:
                trades_desc.append(f"{f.sequence[0]} (+{f.score/100:.1f})")
            self.lbl_trades.setText(f"🟢 Winning Trade: {', '.join(trades_desc)} — net material gain")
            self.lbl_trades.setVisible(True)
        else:
            self.lbl_trades.setVisible(False)

        # 4. Tactical Motifs (Electric Purple #D500F9: Forks, Pins, Skewers)
        if report.motifs:
            motif_items = [m.description for m in report.motifs[:2]]
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

        # 6. Trapped Pieces (Ice Cyan #00E5FF)
        trapped_map = getattr(report, "trapped_pieces", {})
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

        # 7. Defended Pieces (Sky Blue #00B0FF)
        def_pieces = getattr(report.attack_map, "defended_pieces", set())
        own_def_count = sum(1 for sq in def_pieces if report.board.piece_at(sq) and report.board.piece_at(sq).color == turn_color)
        if own_def_count > 0:
            self.lbl_defended.setText(f"🔵 Defense: {own_def_count} friendly pieces protected")
            self.lbl_defended.setVisible(True)
        else:
            self.lbl_defended.setVisible(False)

        # 8. Endgame Principles (Rule of the Square & Opposition)
        endgame_parts = []
        for rw in getattr(report, "runaway_pawns", []):
            if rw.can_promote_unstoppably:
                endgame_parts.append(f"Passer on {rw.pawn_name} unstoppably promotes!")
        if getattr(report, "opposition", None):
            endgame_parts.append(report.opposition.description)
        if endgame_parts:
            self.lbl_endgame.setText(f"👑 Endgame: {' | '.join(endgame_parts)}")
            self.lbl_endgame.setVisible(True)
        else:
            self.lbl_endgame.setVisible(False)

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
    # Draggable Window Mechanics
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
