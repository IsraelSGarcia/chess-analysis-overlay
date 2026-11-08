"""
trapped.py
==========
Detection of trapped and immobilized pieces.

A piece (Knight, Bishop, Rook, Queen) is considered trapped when:
1. It is not an undisturbed piece on its starting square behind friendly pawns.
2. It is not immobilized solely by an absolute pin to its King (which is a pin motif).
3. The player's King is not currently in check.
4. Every legal destination square results in immediate material loss (SEE < 0 or hangs to enemy recapture),
   leaving the piece with 0 safe moves.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
import chess

from core.shared_analysis.see import evaluate_exchange
from core.shared_analysis.values import get_piece_value


STARTING_SQUARES: Dict[chess.Color, Dict[chess.PieceType, Set[chess.Square]]] = {
    chess.WHITE: {
        chess.ROOK: {chess.A1, chess.H1},
        chess.KNIGHT: {chess.B1, chess.G1},
        chess.BISHOP: {chess.C1, chess.F1},
        chess.QUEEN: {chess.D1},
    },
    chess.BLACK: {
        chess.ROOK: {chess.A8, chess.H8},
        chess.KNIGHT: {chess.B8, chess.G8},
        chess.BISHOP: {chess.C8, chess.F8},
        chess.QUEEN: {chess.D8},
    },
}


@dataclass(frozen=True)
class TrappedPiece:
    """Represents a piece that has zero safe squares and cannot escape material loss."""
    square: chess.Square
    piece_type: chess.PieceType
    color: chess.Color
    attackers: Tuple[chess.Square, ...] = ()
    is_attacked: bool = False

    @property
    def square_name(self) -> str:
        return chess.square_name(self.square)

    @property
    def piece_symbol(self) -> str:
        sym = chess.piece_symbol(self.piece_type)
        return sym.upper() if self.color == chess.WHITE else sym.lower()

    @property
    def description(self) -> str:
        side = "White" if self.color == chess.WHITE else "Black"
        p_name = chess.piece_name(self.piece_type).capitalize()
        status = "under attack with no escape" if self.is_attacked else "completely trapped (0 safe moves)"
        return f"{side} {p_name} on {self.square_name} is {status}"


def find_trapped_pieces(
    board: chess.Board,
    color: chess.Color | None = None,
) -> Dict[chess.Color, List[TrappedPiece]]:
    """
    Find all trapped pieces on the board for the specified color or both colors.
    """
    colors_to_check = [color] if color is not None else [chess.WHITE, chess.BLACK]
    results: Dict[chess.Color, List[TrappedPiece]] = {chess.WHITE: [], chess.BLACK: []}

    for c in colors_to_check:
        enemy_c = not c

        # If King is in check for this color, pieces cannot move due to check evasion rules,
        # which is not piece trapping.
        test_board = board.copy()
        test_board.turn = c
        if test_board.is_check():
            continue

        for sq, piece in board.piece_map().items():
            if piece.color != c:
                continue
            if piece.piece_type in (chess.PAWN, chess.KING):
                continue

            # Skip undisturbed home pieces on starting squares that are not attacked
            start_sqs = STARTING_SQUARES[c].get(piece.piece_type, set())
            att_squares = tuple(board.attackers(enemy_c, sq))
            is_attacked = len(att_squares) > 0

            if sq in start_sqs and not is_attacked:
                continue

            # Skip pieces that are absolutely pinned to the King (handled by Pin motif)
            if board.is_pinned(c, sq):
                continue

            # Evaluate whether this piece has any safe destinations
            has_safe_move = False
            candidate_moves = [m for m in test_board.legal_moves if m.from_square == sq]
            for m in candidate_moves:
                to_sq = m.to_square

                # Case 1: Capture or en passant
                if test_board.is_capture(m) or test_board.is_en_passant(m):
                    ex = evaluate_exchange(test_board, m)
                    if ex.score >= 0 and not ex.is_dangerous:
                        has_safe_move = True
                        break
                else:
                    # Case 2: Quiet move -> test if destination can be captured profitably by enemy
                    test_board.push(m)
                    is_hung = False
                    for opp_m in test_board.legal_moves:
                        if opp_m.to_square == to_sq and test_board.is_capture(opp_m):
                            opp_ex = evaluate_exchange(test_board, opp_m)
                            if opp_ex.score > 0:
                                is_hung = True
                                break
                    test_board.pop()

                    if not is_hung:
                        has_safe_move = True
                        break

            if not has_safe_move:
                results[c].append(TrappedPiece(
                    square=sq,
                    piece_type=piece.piece_type,
                    color=c,
                    attackers=att_squares,
                    is_attacked=is_attacked,
                ))

    return results
