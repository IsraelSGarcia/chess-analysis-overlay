"""
_overlay_widget.py
==================
PySide6 rendering overlay for chess capture visualization.

Features:
- Highlights every square a piece can capture or defend.
- Exact sub-pixel square alignment: eliminates integer division drift across the 8x8 grid.
- Independent physical orientation vs player perspective:
  Physical board orientation controls where squares sit on screen;
  Player perspective controls who gets Blue (Player) vs Red (Enemy).
- Master toggle awareness: when hidden, renders nothing with zero overhead.
- Small / Medium arrow size modes.
- Defending arrows pointing to friendly protected pieces.
- Click-through: completely transparent to mouse events.
- Excluded from screen capture via SetWindowDisplayAffinity.
"""

from __future__ import annotations

import ctypes
import math
import logging
from typing import List, Tuple, Set, Dict

import chess

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QColor, QPainter, QBrush, QPen, QPolygonF, QFont,
)
from PySide6.QtWidgets import QWidget

from projects.chess_tactical_analyzer.motifs import MotifType
from core.board_recognition.capture import set_window_capture_exclusion
from overlay.configuration.theme import THEME

logger = logging.getLogger(__name__)

class OverlayWidget(QWidget):
    """
    Transparent, click-through, always-on-top window drawing capture
    arrows and square highlights on top of the chessboard.

    SCREEN CAPTURE ISOLATION INVARIANT:
    ----------------------------------
    This widget MUST maintain WDA_EXCLUDEFROMCAPTURE at all times so that
    screen capture reads clean desktop pixels beneath it without any overlay
    annotations, arrows, or brackets.
    """

    def __init__(self, config) -> None:
        super().__init__(None)
        self._config = config
        self._white_captures: list = []
        self._black_captures: list = []
        self._tactical_report = None
        self._board_flipped: bool = False
        self._status: str = ""
        self._capture_excluded: bool = False
        self._setup_window()

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setWindowOpacity(self._config.opacity)

        left, top, w, h = self._config.board_region
        self.setGeometry(left, top, w, h)
        self._apply_capture_exclusion()

    def _apply_capture_exclusion(self) -> None:
        """Enforce OS-level DWM exclusion so the overlay never contaminates screen captures."""
        self._capture_excluded = set_window_capture_exclusion(self)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._apply_capture_exclusion()

    @property
    def is_capture_excluded(self) -> bool:
        """True if the window is verified excluded from screen captures by Windows DWM."""
        return self._capture_excluded

    def clear(self) -> None:
        """Clear all cached captures, tactical reports, and reset display."""
        self._white_captures = []
        self._black_captures = []
        self._tactical_report = None
        self._status = ""
        self.update()

    def set_captures(self, white: list, black: list, board_flipped: bool | None = None, status: str = "") -> None:
        self._white_captures = white
        self._black_captures = black
        if board_flipped is not None:
            self._board_flipped = board_flipped
        self._status = status
        self.update()

    def set_tactical_report(self, report) -> None:
        self._tactical_report = report
        self.update()

    def set_board_flipped(self, board_flipped: bool) -> None:
        self._board_flipped = board_flipped
        self.update()

    def set_config(self, config) -> None:
        self._config = config
        left, top, w, h = config.board_region
        self.setGeometry(left, top, w, h)
        self.setWindowOpacity(config.opacity)
        self.update()

    # -------------------------------------------------------------------------
    # Paint (Distinct branches for Captures vs Tactics modes)
    # -------------------------------------------------------------------------

    def paintEvent(self, _) -> None:
        cfg = self._config

        # Master toggle: if hidden, render nothing
        if not cfg.overlay_visible:
            return

        try:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

            if cfg.mode == "tactics":
                self._paint_tactics_mode(p)
            elif cfg.mode == "positional":
                self._paint_positional_mode(p)
            else:
                self._paint_captures_mode(p)

            p.end()
        except Exception as exc:
            logger.error("Overlay paintEvent error: %s", exc)

    def _paint_captures_mode(self, p: QPainter) -> None:
        """The original Capture Visualizer: legal captures, defenses, and control highlights."""
        cfg = self._config

        if not cfg.flipped:
            raw_player = self._white_captures
            raw_enemy  = self._black_captures
        else:
            raw_player = self._black_captures
            raw_enemy  = self._white_captures

        if cfg.show_defense:
            player_moves = raw_player
            enemy_moves  = raw_enemy
        else:
            player_moves = [m for m in raw_player if not getattr(m, 'is_defense', False)]
            enemy_moves  = [m for m in raw_enemy if not getattr(m, 'is_defense', False)]

        # 1. Square highlights
        if cfg.show_highlights:
            self._draw_square_highlights(p, player_moves, enemy_moves)

        # 2. Arrows (Blue for Player, Red for Enemy)
        if cfg.show_white:
            self._draw_arrows(p, player_moves, THEME.PLAYER_CAPTURE)

        if cfg.show_black:
            self._draw_arrows(p, enemy_moves, THEME.ENEMY_CAPTURE)

    def _draw_corner_brackets(
        self,
        p: QPainter,
        rect: QRectF,
        color: QColor,
        bracket_len: float = 12.0,
        pen_width: float = 2.5,
    ) -> None:
        """Draw tactical corner brackets [ ] around a square without occluding the piece center."""
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        blen = min(bracket_len, w * 0.32)
        pen = QPen(color, pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap)
        p.setPen(pen)

        # Top-Left
        p.drawLine(QPointF(x, y + blen), QPointF(x, y))
        p.drawLine(QPointF(x, y), QPointF(x + blen, y))

        # Top-Right
        p.drawLine(QPointF(x + w - blen, y), QPointF(x + w, y))
        p.drawLine(QPointF(x + w, y), QPointF(x + w, y + blen))

        # Bottom-Left
        p.drawLine(QPointF(x, y + h - blen), QPointF(x, y + h))
        p.drawLine(QPointF(x, y + h), QPointF(x + blen, y + h))

        # Bottom-Right
        p.drawLine(QPointF(x + w - blen, y + h), QPointF(x + w, y + h))
        p.drawLine(QPointF(x + w, y + h), QPointF(x + w, y + h - blen))

    def _paint_tactics_mode(self, p: QPainter) -> None:
        """The Tactical Intelligence Overlay: Fork/Pin/Skewer arrows, Winning trades, Blunder alerts, Hanging pieces."""
        cfg = self._config
        rep = self._tactical_report

        if not rep:
            return

        turn_color = rep.board.turn
        enemy_color = chess.BLACK if turn_color == chess.WHITE else chess.WHITE

        # ---------------------------------------------------------------------
        # 1. Clean Tactical Accents (Hanging pieces, Motifs, Trapped pieces)
        # ---------------------------------------------------------------------
        try:
            # Hanging pieces (Radiant Bright Orange: thin dashed perimeter & corner brackets)
            for color_key in (chess.WHITE, chess.BLACK):
                for h in rep.hanging.get(color_key, []):
                    h_rect = self._get_square_rect(h.square)
                    p.setPen(QPen(THEME.HANGING_OUTLINE, 1.8, Qt.PenStyle.DashLine))
                    p.drawRect(h_rect)
                    self._draw_corner_brackets(p, h_rect, THEME.HANGING, bracket_len=THEME.BRACKET_LEN, pen_width=THEME.BRACKET_PEN_WIDTH)

            # Tactical Motifs (Electric Purple corner brackets on target squares)
            for m in rep.motifs:
                for tgt_sq in m.target_squares:
                    tgt_rect = self._get_square_rect(tgt_sq)
                    self._draw_corner_brackets(p, tgt_rect, THEME.MOTIF_DASHED, bracket_len=9.0, pen_width=1.8)

            # Trapped Pieces (Ice Cyan: thin dashed perimeter & corner brackets)
            trapped_map = getattr(rep, 'trapped_pieces', {})
            for color_key in (chess.WHITE, chess.BLACK):
                for tp in trapped_map.get(color_key, []):
                    tp_rect = self._get_square_rect(tp.square)
                    p.setPen(QPen(THEME.TRAPPED_OUTLINE, 1.5, Qt.PenStyle.DashLine))
                    p.drawRect(tp_rect)
                    self._draw_corner_brackets(p, tp_rect, THEME.TRAPPED, bracket_len=THEME.BRACKET_LEN, pen_width=THEME.BRACKET_PEN_WIDTH)
        except Exception as exc:
            logger.debug("Tactical accents paint error: %s", exc)

        # ---------------------------------------------------------------------
        # 2. Every Single Blunder Move for Active Turn (Crimson Red - Subtle & Thin)
        # ---------------------------------------------------------------------
        try:
            all_blunders = rep.blunders.get(turn_color, []) if hasattr(rep, 'blunders') else []
            for b in all_blunders:
                fx, fy = self._get_square_centre(b.move.from_square)
                tx, ty = self._get_square_centre(b.move.to_square)
                self._draw_single_arrow(p, fx, fy, tx, ty, THEME.BLUNDER, False, width_mult=THEME.WIDTH_BLUNDER)
        except Exception as exc:
            logger.debug("Blunders paint error: %s", exc)

        # ---------------------------------------------------------------------
        # 3. Direct Threat & Attack Arrows on Hanging Pieces (Radiant Orange)
        # ---------------------------------------------------------------------
        try:
            # Undefended friendly pieces: arrows from enemy attackers
            for h in rep.hanging.get(turn_color, []):
                att_list = getattr(h, 'attackers', getattr(h, 'attacker_squares', []))
                for att_sq in att_list:
                    fx, fy = self._get_square_centre(att_sq)
                    tx, ty = self._get_square_centre(h.square)
                    self._draw_single_arrow(p, fx, fy, tx, ty, THEME.HANGING, False, width_mult=THEME.WIDTH_HANGING)

            # Undefended enemy pieces: arrows from friendly attackers
            for eh in rep.hanging.get(enemy_color, []):
                att_list = getattr(eh, 'attackers', getattr(eh, 'attacker_squares', []))
                for att_sq in att_list:
                    piece = rep.board.piece_at(att_sq)
                    if piece and piece.color == turn_color:
                        fx, fy = self._get_square_centre(att_sq)
                        tx, ty = self._get_square_centre(eh.square)
                        self._draw_single_arrow(p, fx, fy, tx, ty, THEME.HANGING_OUTLINE, False, width_mult=THEME.WIDTH_STANDARD)
        except Exception as exc:
            logger.debug("Hanging pieces paint error: %s", exc)

        # ---------------------------------------------------------------------
        # 4. Tactical Motif Arrows (Forks, Pins, Skewers, Discovered Attacks, Overloaded Defenders)
        # ---------------------------------------------------------------------
        try:
            for m in rep.motifs:
                fx, fy = self._get_square_centre(m.source_square)
                if m.motif_type == MotifType.FORK:
                    for tgt_sq in m.target_squares:
                        tx, ty = self._get_square_centre(tgt_sq)
                        self._draw_single_arrow(p, fx, fy, tx, ty, THEME.MOTIF, False, width_mult=THEME.WIDTH_FORK)

                elif m.motif_type in (MotifType.ABSOLUTE_PIN, MotifType.RELATIVE_PIN):
                    # Pinner attacks pinned piece (solid), continuing through to shielded King/Queen (dashed line of fire)
                    if len(m.target_squares) >= 2:
                        pinned_sq, shielded_sq = m.target_squares[0], m.target_squares[1]
                        px, py = self._get_square_centre(pinned_sq)
                        sx, sy = self._get_square_centre(shielded_sq)
                        self._draw_single_arrow(p, fx, fy, px, py, THEME.MOTIF, False, width_mult=THEME.WIDTH_MOTIF)
                        self._draw_single_arrow(p, px, py, sx, sy, THEME.MOTIF_DASHED, False, width_mult=THEME.WIDTH_XRAY, is_dashed=True)
                    elif m.target_squares:
                        tx, ty = self._get_square_centre(m.target_squares[0])
                        self._draw_single_arrow(p, fx, fy, tx, ty, THEME.MOTIF, False, width_mult=THEME.WIDTH_MOTIF)

                elif m.motif_type == MotifType.SKEWER:
                    # Skewer attacks front piece (solid), continuing through to rear piece (dashed)
                    if len(m.target_squares) >= 2:
                        front_sq, back_sq = m.target_squares[0], m.target_squares[1]
                        fx_front, fy_front = self._get_square_centre(front_sq)
                        bx_back, by_back = self._get_square_centre(back_sq)
                        self._draw_single_arrow(p, fx, fy, fx_front, fy_front, THEME.MOTIF, False, width_mult=THEME.WIDTH_MOTIF)
                        self._draw_single_arrow(p, fx_front, fy_front, bx_back, by_back, THEME.MOTIF_DASHED, False, width_mult=THEME.WIDTH_XRAY, is_dashed=True)
                    elif m.target_squares:
                        tx, ty = self._get_square_centre(m.target_squares[0])
                        self._draw_single_arrow(p, fx, fy, tx, ty, THEME.MOTIF, False, width_mult=THEME.WIDTH_MOTIF)

                elif m.motif_type in (MotifType.DISCOVERED_ATTACK, MotifType.DISCOVERED_CHECK):
                    # In discovered attacks: target_squares=(slider_square, target_square), source_square=masking_square
                    if len(m.target_squares) >= 2:
                        slider_sq, tgt_sq = m.target_squares[0], m.target_squares[1]
                        sx, sy = self._get_square_centre(slider_sq)
                        tx, ty = self._get_square_centre(tgt_sq)
                        # Dashed unveiled ray from slider to target
                        self._draw_single_arrow(p, sx, sy, tx, ty, THEME.MOTIF, False, width_mult=THEME.WIDTH_MOTIF, is_dashed=True)
                        # Corner brackets highlighting the masking piece that should step away
                        mask_rect = self._get_square_rect(m.source_square)
                        self._draw_corner_brackets(p, mask_rect, THEME.MOTIF, bracket_len=THEME.BRACKET_LEN, pen_width=THEME.BRACKET_PEN_WIDTH)

                elif m.motif_type == MotifType.OVERLOADED_DEFENDER:
                    # Overloaded piece is source_square; draw dashed defense connections to its defended pieces
                    for tgt_sq in m.target_squares:
                        tx, ty = self._get_square_centre(tgt_sq)
                        self._draw_single_arrow(p, fx, fy, tx, ty, THEME.DEFENSE, True, width_mult=THEME.WIDTH_XRAY, is_dashed=True)
                    ov_rect = self._get_square_rect(m.source_square)
                    self._draw_corner_brackets(p, ov_rect, THEME.DEFENSE, bracket_len=10.0, pen_width=2.0)

                elif m.motif_type == MotifType.BACK_RANK_WEAKNESS:
                    # Infiltrating piece attacking the back rank towards the King
                    for tgt_sq in m.target_squares:
                        tx, ty = self._get_square_centre(tgt_sq)
                        self._draw_single_arrow(p, fx, fy, tx, ty, THEME.BACK_RANK, False, width_mult=THEME.WIDTH_MOTIF)

                elif m.motif_type == MotifType.MATING_THREAT:
                    # Immediate checkmate threat move
                    tx, ty = self._get_square_centre(m.target_squares[0])
                    self._draw_single_arrow(p, fx, fy, tx, ty, THEME.MOTIF, False, width_mult=THEME.WIDTH_FORK)
                    tgt_rect = self._get_square_rect(m.target_squares[0])
                    self._draw_corner_brackets(p, tgt_rect, THEME.MOTIF, bracket_len=12.0, pen_width=2.5)

                elif m.motif_type in (MotifType.REMOVING_DEFENDER, MotifType.DEFLECTION):
                    if len(m.target_squares) >= 2:
                        def_x, def_y = self._get_square_centre(m.target_squares[0])
                        prize_x, prize_y = self._get_square_centre(m.target_squares[1])
                        # Solid attack arrow to defender
                        self._draw_single_arrow(p, fx, fy, def_x, def_y, THEME.MOTIF, False, width_mult=THEME.WIDTH_MOTIF)
                        # Dashed line from defender to prize
                        self._draw_single_arrow(p, def_x, def_y, prize_x, prize_y, THEME.DEFENSE, True, width_mult=THEME.WIDTH_XRAY, is_dashed=True)
                        # Corner brackets on sole defender square
                        self._draw_corner_brackets(p, self._get_square_rect(m.target_squares[0]), THEME.MOTIF, bracket_len=9.0, pen_width=1.8)
        except Exception as exc:
            logger.debug("Motifs paint error: %s", exc)

        # ---------------------------------------------------------------------
        # 5. Slider X-Ray Rays (Ice Cyan: Dashed Lines of Force through Obstacles)
        # ---------------------------------------------------------------------
        try:
            # Prevent duplicate rays where pins, skewers, or discovered attacks are already drawn
            existing_motif_rays = set()
            for m in rep.motifs:
                if m.motif_type in (MotifType.ABSOLUTE_PIN, MotifType.RELATIVE_PIN, MotifType.SKEWER) and len(m.target_squares) >= 2:
                    existing_motif_rays.add((m.source_square, m.target_squares[1]))
                    existing_motif_rays.add((m.target_squares[0], m.target_squares[1]))
                elif m.motif_type in (MotifType.DISCOVERED_ATTACK, MotifType.DISCOVERED_CHECK) and len(m.target_squares) >= 2:
                    existing_motif_rays.add((m.target_squares[0], m.target_squares[1]))

            for xr in getattr(rep, 'xray_rays', []):
                # Avoid overlapping existing pin/skewer/discovered attack lines
                if (xr.slider_square, xr.target_square) in existing_motif_rays:
                    continue
                if (xr.intervening_square, xr.target_square) in existing_motif_rays:
                    continue

                sx, sy = self._get_square_centre(xr.slider_square)
                tx, ty = self._get_square_centre(xr.target_square)
                # Thin, elegant dashed laser ray from slider piercing through obstacle to target
                self._draw_single_arrow(
                    p, sx, sy, tx, ty,
                    THEME.XRAY,
                    False,
                    width_mult=THEME.WIDTH_XRAY,
                    is_dashed=True,
                )
        except Exception as exc:
            logger.debug("X-Ray rays paint error: %s", exc)

        # ---------------------------------------------------------------------
        # 6. Winning Trades for Active Turn (Vivid Emerald Green: SEE > 0)
        # ---------------------------------------------------------------------
        try:
            fav_captures = rep.favorable_captures(turn_color)
            for ex in fav_captures:
                fx, fy = self._get_square_centre(ex.move.from_square)
                tx, ty = self._get_square_centre(ex.move.to_square)
                self._draw_single_arrow(p, fx, fy, tx, ty, THEME.WINNING_TRADE, False, width_mult=THEME.WIDTH_WINNING)
        except Exception as exc:
            logger.debug("Winning trades paint error: %s", exc)

        # ---------------------------------------------------------------------
        # 7. Endgame Rule of the Square (Ice Cyan Dashed Bounding Box)
        # ---------------------------------------------------------------------
        try:
            for rw in getattr(rep, 'runaway_pawns', []):
                if rw.can_promote_unstoppably:
                    top_left_sq = chess.square(rw.min_col, rw.max_row if not cfg.flipped else rw.min_row)
                    bot_right_sq = chess.square(rw.max_col, rw.min_row if not cfg.flipped else rw.max_row)
                    tl_rect = self._get_square_rect(top_left_sq)
                    br_rect = self._get_square_rect(bot_right_sq)
                    box_rect = QRectF(
                        min(tl_rect.left(), br_rect.left()),
                        min(tl_rect.top(), br_rect.top()),
                        abs(br_rect.right() - tl_rect.left()),
                        abs(br_rect.bottom() - tl_rect.top()),
                    )
                    p.setPen(QPen(THEME.RUNAWAY_BOX, 2.0, Qt.PenStyle.DashLine))
                    p.drawRect(box_rect)
        except Exception as exc:
            logger.debug("Runaway pawn paint error: %s", exc)

    def _paint_positional_mode(self, p: QPainter) -> None:
        """Positional analysis: Outposts, pawn structure weaknesses, open files."""
        cfg = self._config
        rep = self._tactical_report
        if not rep or not rep.positional:
            return

        pos = rep.positional

        try:
            # 1. Controlled Open and Semi-Open Files (Faint Sky Blue vertical band)
            for of in pos.open_files:
                col = of.file_idx if not cfg.flipped else 7 - of.file_idx
                file_rect = QRectF(col * self._sq_size, 0, self._sq_size, 8 * self._sq_size)
                p.fillRect(file_rect, THEME.OPEN_FILE)
                p.setPen(QPen(THEME.OPEN_FILE_BORDER, 1.0, Qt.PenStyle.DotLine))
                p.drawRect(file_rect)

            # 2. Outpost Squares (Gentle Mint Green fill + Corner Brackets)
            for out in pos.outposts:
                rect = self._get_square_rect(out.square)
                p.fillRect(rect, THEME.OUTPOST)
                self._draw_corner_brackets(p, rect, THEME.OUTPOST_BORDER, bracket_len=THEME.BRACKET_LEN, pen_width=THEME.BRACKET_PEN_WIDTH)

            # 3. Pawn Structure Weaknesses (Amber corner brackets on isolated/backward/doubled)
            weak_pawns = set()
            for color_key in (chess.WHITE, chess.BLACK):
                weak_pawns.update(pos.pawn_structure.isolated.get(color_key, []))
                weak_pawns.update(pos.pawn_structure.backward.get(color_key, []))
                weak_pawns.update(pos.pawn_structure.doubled.get(color_key, []))

            for sq in weak_pawns:
                rect = self._get_square_rect(sq)
                self._draw_corner_brackets(p, rect, THEME.PAWN_WEAKNESS, bracket_len=8.0, pen_width=1.8)

            # 4. Bad Bishops
            for b in pos.bishops:
                if b.is_bad:
                    rect = self._get_square_rect(b.square)
                    p.setPen(QPen(THEME.BAD_BISHOP, 1.8, Qt.PenStyle.DashDotLine))
                    p.drawRect(rect)

        except Exception as exc:
            logger.debug("Positional paint error: %s", exc)

    # -------------------------------------------------------------------------
    # Square Highlights
    # -------------------------------------------------------------------------

    def _draw_square_highlights(self, p: QPainter, player_caps: list, enemy_caps: list) -> None:
        cfg = self._config

        player_targets: Set[int] = set()
        enemy_targets: Set[int] = set()

        if cfg.show_white:
            for c in player_caps:
                player_targets.add(c.to_sq)

        if cfg.show_black:
            for c in enemy_caps:
                enemy_targets.add(c.to_sq)

        all_targets = player_targets | enemy_targets

        for sq_idx in all_targets:
            is_player = sq_idx in player_targets
            is_enemy = sq_idx in enemy_targets
            rect = self._get_square_rect(sq_idx)

            if is_player and is_enemy:
                fill_color = THEME.SQUARE_CONTESTED
                border_color = THEME.SQUARE_CONTESTED_BORDER
            elif is_player:
                fill_color = THEME.SQUARE_PLAYER
                border_color = THEME.SQUARE_PLAYER_BORDER
            else:
                fill_color = THEME.SQUARE_ENEMY
                border_color = THEME.SQUARE_ENEMY_BORDER

            p.fillRect(rect, fill_color)
            pen = QPen(border_color, 1.5)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(rect)

    # -------------------------------------------------------------------------
    # Arrows (Legal Captures Mode)
    # -------------------------------------------------------------------------

    def _draw_arrows(self, p: QPainter, captures: list, color: QColor) -> None:
        cfg = self._config
        targets_count: Dict[int, int] = {}
        targets_index: Dict[int, int] = {}
        for c in captures:
            targets_count[c.to_sq] = targets_count.get(c.to_sq, 0) + 1

        sq_dim = min(self.width(), self.height()) / 8.0

        for c in captures:
            idx = targets_index.get(c.to_sq, 0)
            targets_index[c.to_sq] = idx + 1
            total = targets_count[c.to_sq]

            fx, fy = self._get_square_centre(c.from_sq)
            tx, ty = self._get_square_centre(c.to_sq)

            # If multiple arrows point to same square, slightly fan out
            if total > 1:
                fan_offset = (idx - (total - 1) / 2.0) * (sq_dim * 0.15)
                dx, dy = tx - fx, ty - fy
                dist = math.hypot(dx, dy)
                if dist > 1:
                    tx += (-dy / dist) * fan_offset
                    ty += (dx / dist) * fan_offset

            is_def = getattr(c, 'is_defense', False)
            arrow_color = THEME.DEFENSE if is_def else color

            self._draw_single_arrow(p, fx, fy, tx, ty, arrow_color, is_def)

    def _draw_single_arrow(
        self,
        p: QPainter,
        x1: float, y1: float,
        x2: float, y2: float,
        color: QColor,
        is_defense: bool,
        width_mult: float = 1.0,
        is_dashed: bool = False,
    ) -> None:
        cfg = self._config
        sq = min(self.width(), self.height()) / 8.0

        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length < 4:
            return

        ux, uy = dx / length, dy / length
        px, py = -uy, ux

        shaft_half = max(1.5, sq * cfg.shaft_width_ratio / 2.0 * width_mult)
        head_len = max(6.0, sq * cfg.head_length_ratio * width_mult)
        head_half = max(4.0, sq * cfg.head_width_ratio / 2.0 * width_mult)

        # Start arrow away from piece center so piece remains visible
        start_offset = sq * THEME.START_OFFSET_RATIO
        sx, sy = x1 + ux * start_offset, y1 + uy * start_offset

        # End arrow before target center so target piece glyph remains visible
        end_offset = sq * THEME.END_OFFSET_RATIO
        target_x, target_y = x2 - ux * end_offset, y2 - uy * end_offset

        shaft_end_x = target_x - ux * head_len
        shaft_end_y = target_y - uy * head_len

        # Arrowhead polygon
        head_poly = QPolygonF([
            QPointF(target_x, target_y),
            QPointF(shaft_end_x + px * head_half, shaft_end_y + py * head_half),
            QPointF(shaft_end_x - px * head_half, shaft_end_y - py * head_half),
        ])

        if is_dashed:
            # Dashed X-Ray line of fire for pins & skewers
            dash_pen = QPen(color, max(2.0, shaft_half * 1.8), Qt.PenStyle.DashLine, Qt.PenCapStyle.RoundCap)
            p.setPen(dash_pen)
            p.drawLine(QPointF(sx, sy), QPointF(shaft_end_x, shaft_end_y))

            # Arrowhead with dark border
            outline_pen = QPen(THEME.ARROW_OUTLINE, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            p.setPen(outline_pen)
            p.setBrush(QBrush(color))
            p.drawPolygon(head_poly)
        else:
            # Shaft polygon
            shaft_poly = QPolygonF([
                QPointF(sx + px * shaft_half, sy + py * shaft_half),
                QPointF(shaft_end_x + px * shaft_half, shaft_end_y + py * shaft_half),
                QPointF(shaft_end_x - px * shaft_half, shaft_end_y - py * shaft_half),
                QPointF(sx - px * shaft_half, sy - py * shaft_half),
            ])

            # Origin dot
            origin_radius = max(2.5, sq * 0.05 * width_mult)
            p.setPen(QPen(THEME.ARROW_ORIGIN_PEN, 1.0))
            p.setBrush(QBrush(color))
            p.drawEllipse(QPointF(sx, sy), origin_radius, origin_radius)

            # High-contrast dark outline around the arrow
            outline_pen = QPen(THEME.ARROW_OUTLINE, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            p.setPen(outline_pen)
            p.setBrush(QBrush(color))
            p.drawPolygon(shaft_poly)
            p.drawPolygon(head_poly)

    # -------------------------------------------------------------------------
    # Exact Sub-Pixel Coordinates & Centering
    # -------------------------------------------------------------------------

    def _get_square_rect(self, sq_idx: int) -> QRectF:
        """
        Return the exact QRectF for square sq_idx within the overlay window.
        Uses exact floating-point divisions to eliminate integer rounding drift.
        Physical orientation on screen determines square placement.
        """
        w = float(self.width())
        h = float(self.height())
        sq_w = w / 8.0
        sq_h = h / 8.0

        file_ = chess.square_file(sq_idx)
        rank_ = chess.square_rank(sq_idx)

        # Physical board layout on screen:
        # If not board_flipped (White at bottom): rank 8 is top row 0, file a is left col 0.
        # If board_flipped (Black at bottom):     rank 1 is top row 0, file h is left col 0.
        if not self._board_flipped:
            col = file_
            row = 7 - rank_
        else:
            col = 7 - file_
            row = rank_

        x1 = col * sq_w
        y1 = row * sq_h
        x2 = (col + 1) * sq_w
        y2 = (row + 1) * sq_h

        # Inset by 1px so the square border doesn't collide with neighboring squares
        return QRectF(x1 + 1.0, y1 + 1.0, max(1.0, (x2 - x1) - 2.0), max(1.0, (y2 - y1) - 2.0))

    def _get_square_centre(self, sq_idx: int) -> Tuple[float, float]:
        """Return the exact center (x, y) for square sq_idx within the overlay window."""
        c = self._get_square_rect(sq_idx).center()
        return c.x(), c.y()
