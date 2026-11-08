"""
rules.py
========
0-ply geometric endgame principles:
- Rule of the Square (Runaway passed pawn races)
- King Opposition (Direct, Distant, Diagonal)
- Passed Pawn Classification (Protected, Outside, Connected)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import chess


@dataclass(frozen=True)
class RunawayPawnInfo:
    """Mathematical evaluation of a runaway passed pawn and its bounding square."""
    pawn_square: chess.Square
    color: chess.Color
    min_col: int
    min_row: int
    max_col: int
    max_row: int
    distance: int
    is_king_inside: bool
    can_promote_unstoppably: bool

    @property
    def pawn_name(self) -> str:
        return chess.square_name(self.pawn_square)

    @property
    def description(self) -> str:
        status = "King is inside square" if self.is_king_inside else "UNSTOPPABLE runaway pawn! Promotes to Queen"
        color_name = "White" if self.color == chess.WHITE else "Black"
        return f"{color_name} Passer on {self.pawn_name}: {status}"


@dataclass(frozen=True)
class OppositionInfo:
    """King opposition geometry in endgame positions."""
    kind: str                         # "direct", "distant", "diagonal"
    holder_color: chess.Color         # Player who holds the opposition
    white_king_sq: chess.Square
    black_king_sq: chess.Square

    @property
    def holder_name(self) -> str:
        return "White" if self.holder_color == chess.WHITE else "Black"

    @property
    def description(self) -> str:
        return f"{self.holder_name} holds {self.kind} opposition"


@dataclass(frozen=True)
class PassedPawnInfo:
    """Details of an established passed pawn."""
    square: chess.Square
    color: chess.Color
    category: str                     # "protected", "outside", "connected", "isolated"

    @property
    def square_name(self) -> str:
        return chess.square_name(self.square)


def is_endgame(board: chess.Board) -> bool:
    """
    Return True if the board state qualifies as an endgame.
    Criteria: Total piece count <= 12, or (no queens and piece count <= 16).
    """
    pieces = board.piece_map()
    if len(pieces) <= 12:
        return True
    has_queens = any(p.piece_type == chess.QUEEN for p in pieces.values())
    if not has_queens and len(pieces) <= 16:
        return True
    return False


def is_passed_pawn(board: chess.Board, sq: chess.Square, color: chess.Color) -> bool:
    """Check if the pawn on sq has no opposing pawns in front on its file or adjacent files."""
    file_idx = chess.square_file(sq)
    rank_idx = chess.square_rank(sq)
    opp_color = not color

    test_files = [f for f in (file_idx - 1, file_idx, file_idx + 1) if 0 <= f <= 7]

    if color == chess.WHITE:
        # Check ranks above
        for r in range(rank_idx + 1, 8):
            for f in test_files:
                p = board.piece_at(chess.square(f, r))
                if p and p.piece_type == chess.PAWN and p.color == opp_color:
                    return False
    else:
        # Check ranks below
        for r in range(0, rank_idx):
            for f in test_files:
                p = board.piece_at(chess.square(f, r))
                if p and p.piece_type == chess.PAWN and p.color == opp_color:
                    return False

    return True


def evaluate_runaway_passed_pawns(board: chess.Board) -> List[RunawayPawnInfo]:
    """
    Apply the Rule of the Square to all passed pawns.
    Returns geometric bounding boxes and whether the defending King can catch the pawn.
    """
    runaways: List[RunawayPawnInfo] = []

    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if not piece or piece.piece_type != chess.PAWN:
            continue

        color = piece.color
        opp_color = not color
        opp_king = board.king(opp_color)
        if opp_king is None:
            continue

        if not is_passed_pawn(board, sq, color):
            continue

        file_idx = chess.square_file(sq)
        rank_idx = chess.square_rank(sq)

        # Distance to promotion
        if color == chess.WHITE:
            effective_rank = max(rank_idx, 2)  # Pawns on rank 2 can jump to rank 4 (rank_idx 1 -> 2)
            promo_rank = 7
            dist = promo_rank - effective_rank
            if board.turn == chess.WHITE:
                dist = max(0, dist - 1)
        else:
            effective_rank = min(rank_idx, 5)  # Pawns on rank 7 can jump to rank 5 (rank_idx 6 -> 5)
            promo_rank = 0
            dist = effective_rank - promo_rank
            if board.turn == chess.BLACK:
                dist = max(0, dist - 1)

        # The square of the pawn:
        min_file = max(0, file_idx - dist)
        max_file = min(7, file_idx + dist)

        if color == chess.WHITE:
            min_rank = effective_rank
            max_rank = 7
        else:
            min_rank = 0
            max_rank = effective_rank

        k_file = chess.square_file(opp_king)
        k_rank = chess.square_rank(opp_king)

        is_inside = (min_file <= k_file <= max_file) and (min_rank <= k_rank <= max_rank)
        can_promote_unstoppably = not is_inside

        runaways.append(RunawayPawnInfo(
            pawn_square=sq,
            color=color,
            min_col=min_file,
            min_row=min_rank,
            max_col=max_file,
            max_row=max_rank,
            distance=dist,
            is_king_inside=is_inside,
            can_promote_unstoppably=can_promote_unstoppably,
        ))

    return runaways


def detect_king_opposition(board: chess.Board) -> Optional[OppositionInfo]:
    """
    Detect direct, distant, or diagonal King opposition in endgame positions.
    """
    wk = board.king(chess.WHITE)
    bk = board.king(chess.BLACK)
    if wk is None or bk is None:
        return None

    w_file, w_rank = chess.square_file(wk), chess.square_rank(wk)
    b_file, b_rank = chess.square_file(bk), chess.square_rank(bk)

    df = abs(w_file - b_file)
    dr = abs(w_rank - b_rank)

    # In opposition, the side NOT on move holds the opposition (the side to move must step aside)
    holder = not board.turn

    # Direct Opposition: 2 squares apart along file or rank (1 square between them)
    if (df == 0 and dr == 2) or (dr == 0 and df == 2):
        return OppositionInfo(
            kind="direct",
            holder_color=holder,
            white_king_sq=wk,
            black_king_sq=bk,
        )

    # Distant Opposition: 4 or 6 squares apart along file or rank
    if (df == 0 and dr in (4, 6)) or (dr == 0 and df in (4, 6)):
        return OppositionInfo(
            kind="distant",
            holder_color=holder,
            white_king_sq=wk,
            black_king_sq=bk,
        )

    # Diagonal Opposition: 2 squares diagonally
    if df == 2 and dr == 2:
        return OppositionInfo(
            kind="diagonal",
            holder_color=holder,
            white_king_sq=wk,
            black_king_sq=bk,
        )

    return None


def classify_passed_pawns(board: chess.Board) -> List[PassedPawnInfo]:
    """Find and categorize all passed pawns (protected, outside, connected)."""
    passers: List[PassedPawnInfo] = []

    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if not p or p.piece_type != chess.PAWN:
            continue

        if not is_passed_pawn(board, sq, p.color):
            continue

        file_idx = chess.square_file(sq)
        rank_idx = chess.square_rank(sq)

        # Check for friendly pawns protecting it
        is_protected = False
        is_connected = False

        adj_files = [f for f in (file_idx - 1, file_idx + 1) if 0 <= f <= 7]
        support_rank = rank_idx - 1 if p.color == chess.WHITE else rank_idx + 1

        for f in adj_files:
            # Protecting pawn
            p_sup = board.piece_at(chess.square(f, support_rank)) if 0 <= support_rank <= 7 else None
            if p_sup and p_sup.piece_type == chess.PAWN and p_sup.color == p.color:
                is_protected = True
            # Connected pawn on same rank
            p_adj = board.piece_at(chess.square(f, rank_idx))
            if p_adj and p_adj.piece_type == chess.PAWN and p_adj.color == p.color:
                is_connected = True

        category = "protected" if is_protected else ("connected" if is_connected else "isolated")

        # Outside passer check: furthest from file center
        if file_idx in (0, 7) or (file_idx in (1, 6) and category == "isolated"):
            category = "outside"

        passers.append(PassedPawnInfo(
            square=sq,
            color=p.color,
            category=category,
        ))

    return passers
