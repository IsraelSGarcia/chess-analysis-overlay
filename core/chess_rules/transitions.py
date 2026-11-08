"""
transitions.py
==============
Physical board continuity, state transition sanitization, and turn determination.

Ensures that:
1. Piece movements between consecutive frames are validated against legal moves and reverse undos.
2. Transient move indicator dots (Chess.com / Lichess destination circles) are sanitized
   so phantom pieces never materialize on empty squares.
3. Turn state is deterministically inferred from verified physical transitions.
"""

from __future__ import annotations

import logging
from typing import Iterator, Optional
import chess

logger = logging.getLogger(__name__)


def generate_candidate_moves(board: chess.Board) -> Iterator[chess.Move]:
    """
    Generate all legal moves, explicitly considering potential en-passant opportunities.
    """
    yield from board.legal_moves

    rank = 4 if board.turn == chess.WHITE else 3
    ep_dest_rank = 5 if board.turn == chess.WHITE else 2

    for file in range(8):
        sq = chess.square(file, rank)
        p = board.piece_at(sq)
        if p and p.piece_type == chess.PAWN and p.color == board.turn:
            for adj_file in (file - 1, file + 1):
                if 0 <= adj_file <= 7:
                    adj_sq = chess.square(adj_file, rank)
                    adj_p = board.piece_at(adj_sq)
                    if adj_p and adj_p.piece_type == chess.PAWN and adj_p.color != board.turn:
                        b_ep = board.copy(stack=False)
                        b_ep.ep_square = chess.square(adj_file, ep_dest_rank)
                        for m in b_ep.legal_moves:
                            if m.from_square == sq and m.to_square == b_ep.ep_square:
                                yield m


# Backward-compatible internal alias
_generate_candidate_moves = generate_candidate_moves


def determine_turn_from_move(prev_board: chess.Board, new_board: chess.Board) -> Optional[chess.Color]:
    """
    Given consecutive board positions, determine whose turn it is now based on whether
    a forward move was played or a previous move was undone.

    Optimized using in-place push/pop to eliminate repeated heap copies.

    Returns
    -------
    chess.BLACK / chess.WHITE:
        - If a forward move was played by White, returns chess.BLACK (and vice versa).
        - If a previous move by White was undone/reversed, returns chess.WHITE (and vice versa).
    None:
        If no single legal transition was identified.
    """
    prev_map = prev_board.piece_map()
    new_map = new_board.piece_map()

    if prev_map == new_map:
        return None

    # 1. Check forward move from prev_board (using in-place push/pop)
    p_test = prev_board.copy(stack=False)
    p_test.turn = prev_board.turn
    for m in generate_candidate_moves(p_test):
        p_test.push(m)
        if p_test.piece_map() == new_map:
            p_test.pop()
            return not prev_board.turn
        p_test.pop()

    # 2. Check undo / reverse move from new_board to prev_board
    # In new_board, mover_turn played m to reach prev_board -> in new_board, it is mover_turn's turn!
    for mover_turn in (not prev_board.turn, prev_board.turn):
        n_test = new_board.copy(stack=False)
        n_test.turn = mover_turn
        for m in generate_candidate_moves(n_test):
            n_test.push(m)
            if n_test.piece_map() == prev_map:
                n_test.pop()
                return mover_turn
            n_test.pop()

    # 3. Fallback to piece difference heuristic if legal moves didn't match (e.g. crop drift)
    prev_w = {sq: p for sq, p in prev_map.items() if p.color == chess.WHITE}
    new_w = {sq: p for sq, p in new_map.items() if p.color == chess.WHITE}
    prev_b = {sq: p for sq, p in prev_map.items() if p.color == chess.BLACK}
    new_b = {sq: p for sq, p in new_map.items() if p.color == chess.BLACK}

    w_vacated = set(prev_w.keys()) - set(new_w.keys())
    b_vacated = set(prev_b.keys()) - set(new_b.keys())
    w_new_squares = set(new_w.keys()) - set(prev_w.keys())
    b_new_squares = set(new_b.keys()) - set(prev_b.keys())

    white_moved = bool(w_vacated) and bool(w_new_squares) and not b_new_squares
    black_moved = bool(b_vacated) and bool(b_new_squares) and not w_new_squares

    if white_moved and not black_moved:
        return chess.BLACK
    elif black_moved and not white_moved:
        return chess.WHITE

    return None


def sanitize_board_transition(prev_board: chess.Board, new_board: chess.Board) -> chess.Board:
    """
    Ensure physical board state continuity between consecutive frames.

    In chess, pieces NEVER spontaneously materialize on empty squares without
    a corresponding piece leaving an origin square. When a user clicks a piece
    on Chess.com / Lichess, move indicator dots on destination squares can occasionally
    be misclassified as pawns. If new pieces appear while every single established piece
    from prev_board remains on its exact square, those newly added pieces are identified
    as click/move dot artifacts and purged.
    """
    prev_map = prev_board.piece_map()
    new_map = new_board.piece_map()

    if prev_map == new_map:
        return new_board

    # Check for phantom move dot spawn:
    # All established pieces from prev_board are still present on their exact squares,
    # but 1 to 6 extra pieces appeared on previously empty squares (e.g. piece clicked).
    if all(new_map.get(sq) == p for sq, p in prev_map.items()):
        newly_added = set(new_map.keys()) - set(prev_map.keys())
        if 0 < len(newly_added) <= 6:
            clean_board = new_board.copy()
            for sq in newly_added:
                clean_board.remove_piece_at(sq)
            logger.debug(
                "Sanitized impossible piece spawn on empty squares %s (click/move dot artifacts)",
                [chess.square_name(s) for s in newly_added],
            )
            return clean_board

    # In all other cases (forward moves, capture undos, castling, promotions, navigation),
    # the new_board piece placements are authentic and must NEVER be deleted.
    return new_board
