"""
forcing_search.py
=================
Specialized forcing move search (checks, captures, promotions)
to calculate concrete tactical combinations without a general-purpose engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import chess

from chess_tactical.values import get_piece_value, PIECE_VALUES
from chess_tactical.see import evaluate_exchange


MATE_SCORE = 100000


@dataclass(frozen=True)
class TacticalSequence:
    """A calculated concrete tactical sequence."""
    root_move: chess.Move
    score: int                       # Centipawns from the perspective of the initiator
    pv: Tuple[str, ...]              # Line of play in SAN notation (e.g. ("Bxf7+", "Kxf7", "Ng5+"))
    initiator_color: chess.Color
    is_mate: bool = False
    motif_summary: str = ""

    @property
    def root_san(self) -> str:
        return self.pv[0] if self.pv else str(self.root_move)

    @property
    def is_favorable(self) -> bool:
        return self.is_mate or self.score >= 100

    def __str__(self) -> str:
        pv_str = " ".join(self.pv)
        score_str = f"#{'' if self.score > 0 else '-'}" if self.is_mate else f"{self.score:+d} cp"
        return f"[{'White' if self.initiator_color == chess.WHITE else 'Black'}] {pv_str} ({score_str})"


def _static_material_balance(board: chess.Board) -> int:
    """Return net material balance (White - Black) in centipawns."""
    balance = 0
    for sq, piece in board.piece_map().items():
        if piece.piece_type == chess.KING:
            continue
        val = get_piece_value(piece.piece_type)
        if piece.color == chess.WHITE:
            balance += val
        else:
            balance -= val
    return balance


def _get_forcing_moves(board: chess.Board) -> List[chess.Move]:
    """
    Generate only forcing moves:
    1. If in check: ALL legal moves are forcing evasion responses.
    2. If not in check: all captures, checks, and pawn promotions.
    """
    if board.is_check():
        # All legal evasions must be searched
        return list(board.legal_moves)

    forcing: List[chess.Move] = []
    for move in board.legal_moves:
        is_cap = board.is_capture(move) or board.is_en_passant(move)
        is_promo = move.promotion is not None
        gives_chk = board.gives_check(move)

        if is_cap or is_promo or gives_chk:
            forcing.append(move)

    # Order moves: checks first, then promotions, then captures
    def move_priority(m: chess.Move) -> int:
        score = 0
        if board.gives_check(m):
            score += 1000
        if m.promotion:
            score += 500
        if board.is_capture(m):
            captured = board.piece_at(m.to_square)
            if captured:
                score += get_piece_value(captured.piece_type)
            else:
                score += 100  # En passant
        return score

    forcing.sort(key=move_priority, reverse=True)
    return forcing


def _search_forcing_ply(
    board: chess.Board,
    depth: int,
    alpha: int,
    beta: int,
    max_depth: int,
    budget: List[int],
) -> Tuple[int, List[str]]:
    """
    Alpha-beta minimax on forcing moves with strict node budget.
    Returns (score_for_side_to_move, pv_moves_in_san).
    """
    if board.is_checkmate():
        return -MATE_SCORE, []

    if board.is_stalemate() or board.is_insufficient_material():
        return 0, []

    # Stand pat evaluation: evaluate quiet material balance
    mat = _static_material_balance(board)
    stand_pat = mat if board.turn == chess.WHITE else -mat

    # Check node budget or depth limit
    if budget[0] <= 0 or depth >= max_depth:
        return stand_pat, []
    budget[0] -= 1

    # Beta cut-off on stand-pat if not in check
    if not board.is_check():
        if stand_pat >= beta:
            return beta, []
        if stand_pat > alpha:
            alpha = stand_pat

    moves = _get_forcing_moves(board)
    if not moves:
        # No forcing moves left: return stand-pat
        return stand_pat, []

    # Limit branching factor to top 10 forcing moves to prevent combinatorial explosion
    moves = moves[:10]

    best_score = -MATE_SCORE if board.is_check() else stand_pat
    best_pv: List[str] = []

    for move in moves:
        san = board.san(move)
        test_m = move
        board.push(test_m)
        score, child_pv = _search_forcing_ply(board, depth + 1, -beta, -alpha, max_depth, budget)
        score = -score
        board.pop()

        if score > best_score:
            best_score = score
            best_pv = [san] + child_pv

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    return best_score, best_pv


def calculate_tactical_sequences(
    board: chess.Board,
    color: Optional[chess.Color] = None,
    max_depth: int = 3,
    min_gain_cp: int = 100,
) -> List[TacticalSequence]:
    """
    Search forcing tactical sequences for 'color' (or side to move if None).

    Parameters
    ----------
    board : chess.Board
        The current position.
    color : Optional[chess.Color]
        The side initiating the tactic. Defaults to side to move.
    max_depth : int
        Maximum ply search depth for forcing combinations (default: 3 plies).
    min_gain_cp : int
        Minimum centipawn gain required to report as a winning tactic.

    Returns
    -------
    List[TacticalSequence]
        Favorable tactical sequences sorted by net gain descending.
    """
    initiator = color if color is not None else board.turn
    test_board = board.copy()
    test_board.turn = initiator

    initial_mat = _static_material_balance(test_board)
    initial_initiator_mat = initial_mat if initiator == chess.WHITE else -initial_mat

    candidate_sequences: List[TacticalSequence] = []
    forcing_moves = _get_forcing_moves(test_board)[:12]

    # Global search budget across root moves
    budget = [1000]

    for move in forcing_moves:
        if budget[0] <= 0:
            break
        san = test_board.san(move)
        test_board.push(move)

        score, child_pv = _search_forcing_ply(
            test_board,
            depth=1,
            alpha=-MATE_SCORE,
            beta=MATE_SCORE,
            max_depth=min(3, max_depth),
            budget=budget,
        )
        # Score is from opponent's perspective, so negate for initiator
        initiator_score = -score
        test_board.pop()

        is_mate = abs(initiator_score) >= (MATE_SCORE - 100)
        net_gain = initiator_score - initial_initiator_mat

        if is_mate or net_gain >= min_gain_cp:
            full_pv = (san,) + tuple(child_pv)
            candidate_sequences.append(TacticalSequence(
                root_move=move,
                score=net_gain if not is_mate else initiator_score,
                pv=full_pv,
                initiator_color=initiator,
                is_mate=is_mate,
            ))

    # Sort sequences by net score descending
    candidate_sequences.sort(key=lambda s: s.score, reverse=True)
    return candidate_sequences
