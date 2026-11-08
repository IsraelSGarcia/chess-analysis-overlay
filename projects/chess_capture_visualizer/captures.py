"""
chess_logic.py
==============
Legal capture, attack, and defense square calculation for both colors simultaneously.

For every piece on the board, calculates:
1. Capture opportunities (opponent pieces that can be captured).
2. Defending opportunities (friendly pieces protected/defended by this piece).
3. Attack/influence squares (empty squares the piece controls).

Rules:
- Pawns: attack/defend diagonally (d5, f5 from e4), NOT forward.
- En passant: counts as a capture onto the landing square.
- Defending: friendly pieces directly in the attack ray of friendly pieces.
- Pinned pieces: strictly excluded from illegal moves that would expose the King.
- Checked King: only moves that resolve the check are permitted.
"""

from __future__ import annotations

import chess
from dataclasses import dataclass
from typing import List, Dict


@dataclass(frozen=True)
class CaptureMove:
    """A move/influence from from_sq to to_sq."""
    color: int                   # chess.WHITE or chess.BLACK
    from_sq: int                 # piece's square (chess.A1 … chess.H8)
    to_sq: int                   # target square
    is_occupied: bool = False   # True if a piece is on to_sq
    is_en_passant: bool = False
    is_defense: bool = False    # True if target is a friendly piece (defending)

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
        if self.is_defense:
            kind = " [defense]"
        elif self.is_en_passant:
            kind = " [EP]"
        elif self.is_occupied:
            kind = " [capture]"
        else:
            kind = " [empty]"
        return f"{self.color_name}: {self.from_name} -> {self.to_name}{kind}"


# Backward compatibility alias
MoveArrow = CaptureMove


# -------------------------------------------------------------------------
# Core calculation
# -------------------------------------------------------------------------

def get_legal_captures(
    board: chess.Board,
    color: int,
    include_empty: bool = True,
    include_defense: bool = True,
) -> List[CaptureMove]:
    """
    Return all capture, defense, and influence moves for *color*.

    Parameters
    ----------
    board : chess.Board
        The current position.
    color : int
        chess.WHITE or chess.BLACK
    include_empty : bool
        If True (default), include empty squares that pieces can capture onto.
    include_defense : bool
        If True (default), include arrows pointing to friendly pieces that are
        defended/protected by this piece.

    Returns
    -------
    List[CaptureMove]
    """
    hyp = board.copy(stack=False)
    hyp.turn = color
    enemy_color = not color

    moves: List[CaptureMove] = []
    seen = set()

    # 1. Normal legal moves on current board (captures and en-passant)
    for move in hyp.legal_moves:
        is_ep = hyp.is_en_passant(move)
        if hyp.is_capture(move) or is_ep:
            cm = CaptureMove(
                color=color,
                from_sq=move.from_square,
                to_sq=move.to_square,
                is_occupied=(not is_ep),
                is_en_passant=is_ep,
                is_defense=False,
            )
            key = (cm.from_sq, cm.to_sq)
            if key not in seen:
                seen.add(key)
                moves.append(cm)

    # 2. Defending friendly pieces & attacking empty squares
    for from_sq in chess.SQUARES:
        piece = hyp.piece_at(from_sq)
        if piece is None or piece.color != color:
            continue

        # Squares attacked/defended by this piece
        attacked = hyp.attacks(from_sq)
        for to_sq in attacked:
            key = (from_sq, to_sq)
            if key in seen:
                continue

            target_piece = hyp.piece_at(to_sq)

            # Friendly piece -> Defending!
            if target_piece is not None and target_piece.color == color:
                if include_defense:
                    seen.add(key)
                    moves.append(CaptureMove(
                        color=color,
                        from_sq=from_sq,
                        to_sq=to_sq,
                        is_occupied=True,
                        is_en_passant=False,
                        is_defense=True,
                    ))
                continue

            # Empty square -> Potential capture if enemy moves there
            if include_empty and target_piece is None:
                test_board = hyp.copy(stack=False)
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
                    moves.append(CaptureMove(
                        color=color,
                        from_sq=from_sq,
                        to_sq=to_sq,
                        is_occupied=False,
                        is_en_passant=False,
                        is_defense=False,
                    ))

    return moves


def get_all_captures(
    fen_or_board: "str | chess.Board",
    include_empty: bool = True,
    include_defense: bool = True,
) -> List[CaptureMove]:
    """Return all capture and defense moves for both colors."""
    board = chess.Board(fen_or_board) if isinstance(fen_or_board, str) else fen_or_board
    return (
        get_legal_captures(board, chess.WHITE, include_empty=include_empty, include_defense=include_defense) +
        get_legal_captures(board, chess.BLACK, include_empty=include_empty, include_defense=include_defense)
    )


def get_all_captures_dict(
    fen_or_board: "str | chess.Board",
    include_empty: bool = True,
    include_defense: bool = True,
) -> Dict[str, List[CaptureMove]]:
    """Return captures/defenses split by color: {'white': [...], 'black': [...]}."""
    board = chess.Board(fen_or_board) if isinstance(fen_or_board, str) else fen_or_board
    return {
        "white": get_legal_captures(board, chess.WHITE, include_empty=include_empty, include_defense=include_defense),
        "black": get_legal_captures(board, chess.BLACK, include_empty=include_empty, include_defense=include_defense),
    }


# Backward compatibility aliases
get_all_moves = get_all_captures_dict
get_legal_moves = get_legal_captures


if __name__ == "__main__":
    import sys

    fen = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else chess.STARTING_FEN
    print(f"FEN: {fen}\n")
    board = chess.Board(fen)

    result = get_all_captures_dict(fen, include_empty=True, include_defense=True)

    for color_name, moves in [("White", result["white"]), ("Black", result["black"])]:
        captures = [m for m in moves if m.is_occupied and not m.is_defense]
        defenses = [m for m in moves if m.is_defense]
        empty = [m for m in moves if not m.is_occupied]
        print(f"{color_name} moves ({len(moves)} total: {len(captures)} captures, {len(defenses)} defending, {len(empty)} empty squares):")
        for m in sorted(moves, key=lambda m: (m.from_name, m.to_name)):
            print(f"  {m}")
        print()
