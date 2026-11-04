"""
_overlay_widget.py
==================
PySide6 rendering overlay for chess capture visualization.

Features:
- Highlights every square a piece can capture or defend.
- Master toggle awareness: when hidden, renders nothing with zero overhead.
- Perspective aware: Player is ALWAYS Blue, Enemy is ALWAYS Red.
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

logger = logging.getLogger(__name__)

WDA_EXCLUDEFROMCAPTURE = 0x00000011


class OverlayWidget(QWidget):
    """
    Transparent, click-through, always-on-top window drawing capture
    arrows and square highlights on top of the chessboard.
    """

    def __init__(self, config) -> None:
        super().__init__(None)
        self._config = config
        self._white_captures: list = []
        self._black_captures: list = []
        self._status: str = ""
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

        try:
            hwnd = int(self.winId())
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        except Exception as exc:
            logger.debug("SetWindowDisplayAffinity failed: %s", exc)

    def set_captures(self, white: list, black: list, status: str = "") -> None:
        self._white_captures = white
        self._black_captures = black
        self._status = status
        self.update()

    def set_config(self, config) -> None:
        self._config = config
        left, top, w, h = config.board_region
        self.setGeometry(left, top, w, h)
        self.setWindowOpacity(config.opacity)
        self.update()

    # -------------------------------------------------------------------------
    # Paint
    # -------------------------------------------------------------------------

    def paintEvent(self, _) -> None:
        cfg = self._config

        # Master toggle: if hidden, render nothing
        if not cfg.overlay_visible:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Perspective awareness:
        # If not flipped (White view): Player = White (Blue), Enemy = Black (Red)
        # If flipped (Black view):     Player = Black (Blue), Enemy = White (Red)
        raw_player = self._white_captures if not cfg.flipped else self._black_captures
        raw_enemy  = self._black_captures if not cfg.flipped else self._white_captures

        # Filter out defense moves if defense toggle is disabled
        if cfg.show_defense:
            player_moves = raw_player
            enemy_moves  = raw_enemy
        else:
            player_moves = [m for m in raw_player if not getattr(m, 'is_defense', False)]
            enemy_moves  = [m for m in raw_enemy if not getattr(m, 'is_defense', False)]

        # 1. Draw square highlights
        if cfg.show_highlights:
            self._draw_square_highlights(p, player_moves, enemy_moves)

        # 2. Draw arrows (Blue for Player, Red for Enemy)
        if cfg.show_white:  # Player toggle
            self._draw_arrows(p, player_moves, QColor(*cfg.white_color))

        if cfg.show_black:  # Enemy toggle
            self._draw_arrows(p, enemy_moves, QColor(*cfg.black_color))

        # 3. HUD status text (optional)
        if cfg.show_hud:
            self._draw_hud(p, len(player_moves), len(enemy_moves))

        p.end()

    # -------------------------------------------------------------------------
    # Square Highlights
    # -------------------------------------------------------------------------

    def _draw_square_highlights(self, p: QPainter, player_caps: list, enemy_caps: list) -> None:
        cfg = self._config
        sq = cfg.square_size

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
            x, y = self._sq_topleft(sq_idx)
            rect = QRectF(x + 1, y + 1, sq - 2, sq - 2)

            if is_player and is_enemy:
                # Contested square (both sides can capture/defend here)
                fill_color = QColor(180, 75, 240, 80)     # rich violet
                border_color = QColor(210, 100, 255, 210)
            elif is_player:
                # Player capture/defense square (Blue)
                fill_color = QColor(45, 145, 255, 75)     # rich blue
                border_color = QColor(60, 160, 255, 200)
            else:
                # Enemy capture/defense square (Red)
                fill_color = QColor(245, 55, 55, 75)      # rich red
                border_color = QColor(255, 75, 75, 200)

            p.fillRect(rect, fill_color)
            pen = QPen(border_color, 2.0)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(rect)

    # -------------------------------------------------------------------------
    # Arrows
    # -------------------------------------------------------------------------

    def _draw_arrows(self, p: QPainter, captures: list, color: QColor) -> None:
        targets_count: Dict[int, int] = {}
        targets_index: Dict[int, int] = {}
        for c in captures:
            targets_count[c.to_sq] = targets_count.get(c.to_sq, 0) + 1

        for c in captures:
            idx = targets_index.get(c.to_sq, 0)
            targets_index[c.to_sq] = idx + 1
            total = targets_count[c.to_sq]

            fx, fy = self._sq_centre(c.from_sq)
            tx, ty = self._sq_centre(c.to_sq)

            # If multiple arrows point to same square, slightly fan out
            if total > 1:
                fan_offset = (idx - (total - 1) / 2.0) * (self._config.square_size * 0.15)
                dx, dy = tx - fx, ty - fy
                dist = math.hypot(dx, dy)
                if dist > 1:
                    tx += (-dy / dist) * fan_offset
                    ty += (dx / dist) * fan_offset

            self._draw_single_arrow(p, fx, fy, tx, ty, color, getattr(c, 'is_defense', False))

    def _draw_single_arrow(
        self,
        p: QPainter,
        x1: float, y1: float,
        x2: float, y2: float,
        color: QColor,
        is_defense: bool,
    ) -> None:
        cfg = self._config
        sq = cfg.square_size

        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length < 4:
            return

        ux, uy = dx / length, dy / length
        px, py = -uy, ux

        shaft_half = max(1.5, sq * cfg.shaft_width_ratio / 2.0)
        head_len = max(6.0, sq * cfg.head_length_ratio)
        head_half = max(4.0, sq * cfg.head_width_ratio / 2.0)

        # Start arrow away from piece center
        start_offset = sq * 0.20
        sx, sy = x1 + ux * start_offset, y1 + uy * start_offset

        # End arrow near square center
        end_offset = sq * 0.12
        target_x, target_y = x2 - ux * end_offset, y2 - uy * end_offset

        shaft_end_x = target_x - ux * head_len
        shaft_end_y = target_y - uy * head_len

        # Shaft polygon
        shaft_poly = QPolygonF([
            QPointF(sx + px * shaft_half, sy + py * shaft_half),
            QPointF(shaft_end_x + px * shaft_half, shaft_end_y + py * shaft_half),
            QPointF(shaft_end_x - px * shaft_half, shaft_end_y - py * shaft_half),
            QPointF(sx - px * shaft_half, sy - py * shaft_half),
        ])

        # Arrowhead polygon
        head_poly = QPolygonF([
            QPointF(target_x, target_y),
            QPointF(shaft_end_x + px * head_half, shaft_end_y + py * head_half),
            QPointF(shaft_end_x - px * head_half, shaft_end_y - py * head_half),
        ])

        # Small origin dot
        origin_radius = max(2.5, sq * 0.05)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(color))
        p.drawEllipse(QPointF(sx, sy), origin_radius, origin_radius)

        p.drawPolygon(shaft_poly)
        p.drawPolygon(head_poly)

    # -------------------------------------------------------------------------
    # HUD
    # -------------------------------------------------------------------------

    def _draw_hud(self, p: QPainter, player_count: int, enemy_count: int) -> None:
        cfg = self._config
        lines = [
            f"You: {player_count} arrows",
            f"Enemy: {enemy_count} arrows",
        ]
        if self._status:
            lines.append(self._status)

        font = QFont("Consolas", 8)
        font.setBold(True)
        p.setFont(font)

        line_h = 13
        pad = 4
        box_w = 140
        box_h = len(lines) * line_h + pad * 2

        p.fillRect(QRectF(0, 0, box_w, box_h), QColor(10, 14, 20, 180))

        for i, line in enumerate(lines):
            if i == 0:
                p.setPen(QColor(*cfg.white_color[:3]))
            elif i == 1:
                p.setPen(QColor(*cfg.black_color[:3]))
            else:
                p.setPen(QColor(180, 190, 205))
            p.drawText(pad + 2, pad + (i + 1) * line_h - 2, line)

    # -------------------------------------------------------------------------
    # Coordinates
    # -------------------------------------------------------------------------

    def _sq_topleft(self, sq_idx: int) -> Tuple[float, float]:
        cfg = self._config
        sq = cfg.square_size
        file_ = chess.square_file(sq_idx)
        rank_ = chess.square_rank(sq_idx)

        if not cfg.flipped:
            col = file_
            row = 7 - rank_
        else:
            col = 7 - file_
            row = rank_

        return float(col * sq), float(row * sq)

    def _sq_centre(self, sq_idx: int) -> Tuple[float, float]:
        x, y = self._sq_topleft(sq_idx)
        half = self._config.square_size / 2.0
        return x + half, y + half
