"""
hanging.py
==========
Detection and evaluation of hanging (undefended and under-defended) pieces.

Distinguishes genuinely vulnerable pieces from tactically protected pieces
using Static Exchange Evaluation (SEE).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import chess

from core.shared_analysis.values import get_piece_value
from core.shared_analysis.attack_defense import AttackDefenseMap
from core.shared_analysis.see import evaluate_exchange


@dataclass(frozen=True)
class HangingPiece:
    """Details of a hanging or vulnerable piece."""
    square: chess.Square
    piece: chess.Piece
    color: chess.Color
    attacker_count: int
    defender_count: int
    is_undefended: bool              # 0 friendly defenders
    is_underdefended: bool            # Attacker count > Defender count
    is_tactically_vulnerable: bool    # Opponent has at least 1 legal capture with net gain > 0
    best_capture_gain: int           # Maximum centipawns opponent can win by taking it
    attacker_squares: List[chess.Square] = field(default_factory=list)
    defender_squares: List[chess.Square] = field(default_factory=list)

    @property
    def attackers(self) -> List[chess.Square]:
        """Convenience alias for attacker_squares."""
        return self.attacker_squares

    @property
    def defenders(self) -> List[chess.Square]:
        """Convenience alias for defender_squares."""
        return self.defender_squares

    @property
    def square_name(self) -> str:
        return chess.square_name(self.square)

    @property
    def piece_symbol(self) -> str:
        return self.piece.symbol()

    @property
    def piece_name(self) -> str:
        names = {
            chess.PAWN: "Pawn",
            chess.KNIGHT: "Knight",
            chess.BISHOP: "Bishop",
            chess.ROOK: "Rook",
            chess.QUEEN: "Queen",
            chess.KING: "King",
        }
        return names.get(self.piece.piece_type, "Piece")


def find_hanging_pieces(
    board: chess.Board,
    attack_map: Optional[AttackDefenseMap] = None,
    color: Optional[chess.Color] = None,
) -> List[HangingPiece]:
    """
    Find all hanging pieces for the specified color (or both if None).

    Parameters
    ----------
    board : chess.Board
        The current position.
    attack_map : Optional[AttackDefenseMap]
        Pre-computed attack/defense map, or computed on demand if None.
    color : Optional[chess.Color]
        Filter for a specific color (chess.WHITE or chess.BLACK), or both if None.

    Returns
    -------
    List[HangingPiece]
        Hanging pieces sorted by piece value descending (Queens/Rooks first).
    """
    if attack_map is None:
        attack_map = AttackDefenseMap(board)

    hanging: List[HangingPiece] = []
    colors = [color] if color is not None else [chess.WHITE, chess.BLACK]

    for c in colors:
        enemy_color = not c
        test_board = board.copy()
        test_board.turn = enemy_color

        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if not piece or piece.color != c:
                continue

            # King cannot be captured in legal chess, handled by check/mate detection
            if piece.piece_type == chess.KING:
                continue

            control = attack_map.squares[sq]
            attackers = control.attackers_for(enemy_color)
            defenders = control.defenders_for(c)

            # Piece is under attack if enemy attackers > 0
            if not attackers:
                continue

            is_undefended = (len(defenders) == 0)
            is_underdefended = (len(attackers) > len(defenders))

            # Test legal captures by the enemy to check concrete tactical vulnerability
            best_gain = -99999
            can_be_captured_legally = False

            for atk_sq in attackers:
                is_promo = (
                    board.piece_at(atk_sq).piece_type == chess.PAWN
                    and chess.square_rank(sq) in (0, 7)
                )
                move = chess.Move(atk_sq, sq, promotion=chess.QUEEN if is_promo else None)

                if test_board.is_legal(move):
                    can_be_captured_legally = True
                    see_res = evaluate_exchange(test_board, move)
                    if see_res.score > best_gain:
                        best_gain = see_res.score

            if not can_be_captured_legally:
                # E.g. attackers are all pinned or unable to legally move to sq
                continue

            # Tactically vulnerable if opponent can capture for net positive gain
            is_vulnerable = best_gain > 0

            # It qualifies as hanging if undefended, underdefended, or tactically vulnerable
            if is_undefended or is_underdefended or is_vulnerable:
                hanging.append(HangingPiece(
                    square=sq,
                    piece=piece,
                    color=c,
                    attacker_count=len(attackers),
                    defender_count=len(defenders),
                    is_undefended=is_undefended,
                    is_underdefended=is_underdefended,
                    is_tactically_vulnerable=is_vulnerable,
                    best_capture_gain=best_gain if best_gain != -99999 else 0,
                    attacker_squares=attackers,
                    defender_squares=defenders,
                ))

    # Sort hanging pieces by piece value descending
    hanging.sort(key=lambda h: get_piece_value(h.piece.piece_type), reverse=True)
    return hanging
