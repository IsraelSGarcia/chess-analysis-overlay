"""
chess_logic.py
==============
Legal capture square calculation for both colors simultaneously.

For every piece on the board:
Calculates EVERY square that the piece can legally capture onto,
INCLUDING empty squares (if an opponent piece were to move there).

Rules:
- Pawns: capture diagonally (d5, f5 from e4), NOT forward.
- En passant: counts as a capture onto the landing square.
- Pinned pieces: strictly excluded from captures that would leave the king in check.
- Checked king: only captures that resolve the check are permitted.
- Friendly pieces: cannot capture own pieces.
"""

from __future__ import annotations

import chess
from dataclasses import dataclass
from typing import List, Dict


@dataclass(frozen=True)
class CaptureMove:
    """A capture opportunity from from_sq to to_sq."""
    color: int           # chess.WHITE or chess.BLACK
    from_sq: int         # piece's current square (chess.A1 … chess.H8)
    to_sq: int           # target square it can capture onto
    is_occupied: bool = False   # True if an opponent piece is currently on to_sq
    is_en_passant: bool = False

    @property
    def from_name(self) -> str:
        return chess.square_name(self.from_sq)

    @property
    def to_name(self) -> str:
        return chess.square_name(self.to_sq)

    @property
    def color_name(self) -> str:
        return "White" if self.color == chess.WHITE else "Black"

    def __str__(self) -> str:
        ep = " [EP]" if self.is_en_passant else ""
        occ = " [x]" if self.is_occupied else " [empty]"
        return f"{self.color_name}: {self.from_name} -> {self.to_name}{occ}{ep}"


# Backward compatibility alias
MoveArrow = CaptureMove


# -------------------------------------------------------------------------
# Core calculation
# -------------------------------------------------------------------------

def get_legal_captures(board: chess.Board, color: int, include_empty: bool = True) -> List[CaptureMove]:
    """
    Return every legal square *color* can capture onto.

    Parameters
    ----------
    board : chess.Board
        The current position.
    color : int
        chess.WHITE or chess.BLACK
    include_empty : bool
        If True (default), include empty squares that pieces can capture onto
        (e.g., pawn diagonal attacks, knight forks on empty squares).
        If False, only return captures of pieces currently occupying squares.

    Returns
    -------
    List[CaptureMove]
    """
    hyp = board.copy()
    hyp.turn = color
    enemy_color = not color

    captures: List[CaptureMove] = []
    seen = set()

    # 1. First, check actual legal moves from the current position
    # (covers normal captures and active en-passant)
    for move in hyp.legal_moves:
        is_ep = hyp.is_en_passant(move)
        if hyp.is_capture(move) or is_ep:
            cm = CaptureMove(
                color=color,
                from_sq=move.from_square,
                to_sq=move.to_square,
                is_occupied=(not is_ep),
                is_en_passant=is_ep,
            )
            key = (cm.from_sq, cm.to_sq)
            if key not in seen:
                seen.add(key)
                captures.append(cm)

    # 2. If include_empty is True, test all attacked squares that are currently empty
    if include_empty:
        for from_sq in chess.SQUARES:
            piece = hyp.piece_at(from_sq)
            if piece is None or piece.color != color:
                continue

            # Squares attacked by this piece according to chess rules
            # (Pawns only attack diagonally!)
            attacked = hyp.attacks(from_sq)
            for to_sq in attacked:
                key = (from_sq, to_sq)
                if key in seen:
                    continue

                target_piece = hyp.piece_at(to_sq)
                if target_piece is not None:
                    # If target is own piece, cannot capture
                    continue

                # Target is empty. Test if piece can legally capture there
                # by placing a hypothetical enemy pawn on to_sq.
                test_board = hyp.copy()
                test_board.set_piece_at(to_sq, chess.Piece(chess.PAWN, enemy_color))

                promotion = chess.QUEEN if piece.piece_type == chess.PAWN and chess.square_rank(to_sq) in (0, 7) else None
                test_move = chess.Move(from_sq, to_sq, promotion=promotion)

                # Checking if move is in legal_moves enforces:
                # - Pinned pieces cannot expose king
                # - Checked king must be resolved
                # - Kings cannot move into attacked squares
                # - Pawns only capture diagonally
                if test_move in test_board.legal_moves:
                    seen.add(key)
                    captures.append(CaptureMove(
                        color=color,
                        from_sq=from_sq,
                        to_sq=to_sq,
                        is_occupied=False,
                        is_en_passant=False,
                    ))

    return captures


def get_all_captures(fen_or_board: "str | chess.Board", include_empty: bool = True) -> List[CaptureMove]:
    """Return all legal capture opportunities for both colors."""
    board = chess.Board(fen_or_board) if isinstance(fen_or_board, str) else fen_or_board
    return (
        get_legal_captures(board, chess.WHITE, include_empty=include_empty) +
        get_legal_captures(board, chess.BLACK, include_empty=include_empty)
    )


def get_all_captures_dict(fen_or_board: "str | chess.Board", include_empty: bool = True) -> Dict[str, List[CaptureMove]]:
    """Return captures split by color: {'white': [...], 'black': [...]}."""
    board = chess.Board(fen_or_board) if isinstance(fen_or_board, str) else fen_or_board
    return {
        "white": get_legal_captures(board, chess.WHITE, include_empty=include_empty),
        "black": get_legal_captures(board, chess.BLACK, include_empty=include_empty),
    }


# Aliases for backward compatibility
get_all_moves = get_all_captures_dict
get_legal_moves = get_legal_captures


if __name__ == "__main__":
    import sys

    fen = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else chess.STARTING_FEN
    print(f"FEN: {fen}\n")
    board = chess.Board(fen)

    result = get_all_captures_dict(fen, include_empty=True)

    for color_name, caps in [("White", result["white"]), ("Black", result["black"])]:
        occupied = [c for c in caps if c.is_occupied]
        empty = [c for c in caps if not c.is_occupied]
        print(f"{color_name} capture squares ({len(caps)} total: {len(occupied)} occupied, {len(empty)} empty):")
        for c in sorted(caps, key=lambda c: (c.from_name, c.to_name)):
            status = "OCCUPIED" if c.is_occupied else "empty"
            ep = " (en passant)" if c.is_en_passant else ""
            print(f"  {c.from_name} -> {c.to_name} [{status}]{ep}")
        print()
