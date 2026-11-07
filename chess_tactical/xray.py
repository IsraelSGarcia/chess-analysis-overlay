"""
xray.py
=======
Detection of slider X-Ray rays (indirect lines of sight through intervening pieces).

Identifies Bishop, Rook, and Queen lines extending through exactly one intervening
piece to a high-value enemy target (King, Queen, Rook) or equal-value piece.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple
import chess

from chess_tactical.values import get_piece_value


@dataclass(frozen=True)
class XRayRay:
    """A slider line of force passing through an obstacle to an enemy target."""
    slider_square: chess.Square
    intervening_square: chess.Square
    target_square: chess.Square
    slider_type: chess.PieceType
    intervening_type: chess.PieceType
    target_type: chess.PieceType
    slider_color: chess.Color
    intervening_color: chess.Color
    target_color: chess.Color

    @property
    def slider_name(self) -> str:
        return chess.square_name(self.slider_square)

    @property
    def intervening_name(self) -> str:
        return chess.square_name(self.intervening_square)

    @property
    def target_name(self) -> str:
        return chess.square_name(self.target_square)

    @property
    def description(self) -> str:
        s_sym = chess.piece_symbol(self.slider_type).upper() if self.slider_color == chess.WHITE else chess.piece_symbol(self.slider_type).lower()
        i_sym = chess.piece_symbol(self.intervening_type).upper() if self.intervening_color == chess.WHITE else chess.piece_symbol(self.intervening_type).lower()
        t_sym = chess.piece_symbol(self.target_type).upper() if self.target_color == chess.WHITE else chess.piece_symbol(self.target_type).lower()
        return f"{s_sym}@{self.slider_name} X-rays {t_sym}@{self.target_name} through {i_sym}@{self.intervening_name}"


def find_xray_rays(board: chess.Board) -> List[XRayRay]:
    """
    Find all active slider X-ray rays across the board.
    """
    xrays: List[XRayRay] = []

    for s_sq in chess.SQUARES:
        slider = board.piece_at(s_sq)
        if not slider or slider.piece_type not in (chess.BISHOP, chess.ROOK, chess.QUEEN):
            continue

        color = slider.color
        enemy_color = not color
        s_file, s_rank = chess.square_file(s_sq), chess.square_rank(s_sq)

        directions: List[Tuple[int, int]] = []
        if slider.piece_type in (chess.ROOK, chess.QUEEN):
            directions.extend([(0, 1), (0, -1), (1, 0), (-1, 0)])
        if slider.piece_type in (chess.BISHOP, chess.QUEEN):
            directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])

        for df, dr in directions:
            cur_f, cur_r = s_file + df, s_rank + dr
            first_sq: chess.Square | None = None
            second_sq: chess.Square | None = None

            while 0 <= cur_f <= 7 and 0 <= cur_r <= 7:
                sq = chess.square(cur_f, cur_r)
                occ = board.piece_at(sq)
                if occ:
                    if first_sq is None:
                        first_sq = sq
                    elif second_sq is None:
                        second_sq = sq
                        break
                cur_f += df
                cur_r += dr

            if first_sq is not None and second_sq is not None:
                p_first = board.piece_at(first_sq)
                p_second = board.piece_at(second_sq)

                if p_first and p_second and p_second.color == enemy_color:
                    # Target must be King, Queen, Rook, or of value >= slider
                    if (
                        p_second.piece_type in (chess.KING, chess.QUEEN, chess.ROOK)
                        or get_piece_value(p_second.piece_type) >= get_piece_value(slider.piece_type)
                    ):
                        xrays.append(XRayRay(
                            slider_square=s_sq,
                            intervening_square=first_sq,
                            target_square=second_sq,
                            slider_type=slider.piece_type,
                            intervening_type=p_first.piece_type,
                            target_type=p_second.piece_type,
                            slider_color=color,
                            intervening_color=p_first.color,
                            target_color=p_second.color,
                        ))

    return xrays
