"""
see.py
======
Static Exchange Evaluation (SEE) and Capture Evaluation.

Computes the exact net material balance of any capture sequence on a square,
accounting for:
- Multi-piece recaptures in ascending value order (least valuable attacker first).
- X-ray attacks revealed when pieces vacate squares along slider rays.
- Standing pat (minimax pruning where a player declines an unfavorable recapture).
- Illegal moves (absolute pins, king in check, king moving into attack).
- En passant captures and pawn promotions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import chess

from core.shared_analysis.values import (
    ExchangeCategory,
    PIECE_VALUES,
    get_piece_value,
)


@dataclass(frozen=True)
class ExchangeResult:
    """The result of Static Exchange Evaluation on a move."""
    move: chess.Move
    score: int                       # Net material gain for initiator in centipawns
    category: ExchangeCategory       # WINNING, EQUAL, LOSING, FREE_PIECE
    sequence: Tuple[str, ...]        # SAN or UCI string sequence of theoretical trades
    target_piece_type: chess.PieceType
    attacker_piece_type: chess.PieceType
    is_defended: bool                # True if target had any defenders

    @property
    def is_favorable(self) -> bool:
        """Net material win (> 50 cp) or free capture."""
        return self.score > 50 or self.category in (
            ExchangeCategory.WINNING,
            ExchangeCategory.FREE_PIECE,
        )

    @property
    def is_equal(self) -> bool:
        """Even trade (-50 to +50 cp)."""
        return -50 <= self.score <= 50 and self.category == ExchangeCategory.EQUAL

    @property
    def is_dangerous(self) -> bool:
        """Net loss (< -50 cp)."""
        return self.score < -50 or self.category == ExchangeCategory.LOSING


def _find_least_valuable_attacker(
    board: chess.Board,
    target_sq: chess.Square,
    color: chess.Color,
) -> Optional[chess.Move]:
    """
    Find the legal move for 'color' capturing on target_sq with the lowest piece value.
    Returns the legal Move, or None if no legal recapture exists.
    """
    candidates: List[Tuple[int, chess.Move]] = []

    # Check all pieces attacking target_sq
    for sq in board.attackers(color, target_sq):
        piece = board.piece_at(sq)
        if not piece:
            continue

        # Promotion handling for pawns reaching rank 1 or 8
        is_promo = (
            piece.piece_type == chess.PAWN
            and chess.square_rank(target_sq) in (0, 7)
        )
        promo_type = chess.QUEEN if is_promo else None

        move = chess.Move(sq, target_sq, promotion=promo_type)
        if board.is_legal(move):
            val = get_piece_value(piece.piece_type)
            candidates.append((val, move))

    if not candidates:
        return None

    # Sort by piece value ascending (least valuable piece recaptures first)
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def evaluate_exchange(
    board: chess.Board,
    move: chess.Move,
) -> ExchangeResult:
    """
    Perform Static Exchange Evaluation (SEE) on a capture move.

    Parameters
    ----------
    board : chess.Board
        The current position.
    move : chess.Move
        The initial capture move to evaluate.

    Returns
    -------
    ExchangeResult
        Evaluation metrics including score (centipawns), category, and sequence.
    """
    if not board.is_legal(move):
        raise ValueError(f"Move {move} is not legal in the given position.")

    attacker = board.piece_at(move.from_square)
    if attacker is None:
        raise ValueError(f"No piece on from_square {chess.square_name(move.from_square)}.")

    target_sq = move.to_square
    enemy_color = not attacker.color

    # Determine victim piece type and value
    is_ep = board.is_en_passant(move)
    if is_ep:
        victim_type = chess.PAWN
        victim_val = get_piece_value(chess.PAWN)
    else:
        target_piece = board.piece_at(target_sq)
        if target_piece is None:
            # Not a capture; SEE of a quiet move is 0
            return ExchangeResult(
                move=move,
                score=0,
                category=ExchangeCategory.EQUAL,
                sequence=(board.san(move),),
                target_piece_type=chess.PAWN,
                attacker_piece_type=attacker.piece_type,
                is_defended=False,
            )
        victim_type = target_piece.piece_type
        victim_val = get_piece_value(victim_type)

    # Check if target is defended before the capture
    is_defended = len(board.attackers(enemy_color, target_sq)) > 0

    # Extra value gained on promotion
    if move.promotion:
        victim_val += get_piece_value(move.promotion) - get_piece_value(chess.PAWN)

    # Simulate sequence on a working board copy
    sim_board = board.copy(stack=False)
    san_seq: List[str] = [sim_board.san(move)]
    sim_board.push(move)

    gains: List[int] = [victim_val]
    current_color = enemy_color

    # Simulate subsequent recaptures
    # A single square cannot have more than 32 pieces involved
    for _ in range(32):
        recapture = _find_least_valuable_attacker(sim_board, target_sq, current_color)
        if recapture is None:
            break

        # Victim is the piece currently sitting on target_sq
        curr_victim = sim_board.piece_at(target_sq)
        if curr_victim is None:
            break
        curr_val = get_piece_value(curr_victim.piece_type)

        if recapture.promotion:
            curr_val += get_piece_value(recapture.promotion) - get_piece_value(chess.PAWN)

        san_seq.append(sim_board.san(recapture))
        sim_board.push(recapture)
        gains.append(curr_val)
        current_color = not current_color

    # Minimax with standing pat (pass option) from leaf back to root
    # d[i] is the material gained by the side making recapture i.
    # At depth i >= 1, a player can decline to capture if it results in a net loss.
    n = len(gains)
    if n == 1:
        net_score = gains[0]
    else:
        gain_table = [0] * n
        gain_table[-1] = gains[-1]
        for i in range(n - 2, 0, -1):
            gain_table[i] = max(0, gains[i] - gain_table[i + 1])
        # Root move is committed
        net_score = gains[0] - gain_table[1]

    # Categorize the exchange
    if not is_defended and net_score > 0:
        category = ExchangeCategory.FREE_PIECE
    elif net_score > 50:
        category = ExchangeCategory.WINNING
    elif net_score < -50:
        category = ExchangeCategory.LOSING
    else:
        category = ExchangeCategory.EQUAL

    return ExchangeResult(
        move=move,
        score=net_score,
        category=category,
        sequence=tuple(san_seq),
        target_piece_type=victim_type,
        attacker_piece_type=attacker.piece_type,
        is_defended=is_defended,
    )


def evaluate_all_captures(board: chess.Board, color: Optional[chess.Color] = None) -> List[ExchangeResult]:
    """
    Evaluate all legal captures available for color (or both colors if None).
    """
    results: List[ExchangeResult] = []

    colors = [color] if color is not None else [chess.WHITE, chess.BLACK]
    for c in colors:
        test_board = board.copy()
        test_board.turn = c
        for move in test_board.legal_moves:
            if test_board.is_capture(move) or test_board.is_en_passant(move):
                results.append(evaluate_exchange(test_board, move))

    return results
