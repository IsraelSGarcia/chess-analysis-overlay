"""
blunders.py
===========
Detection of all possible tactical blunders for the active player.

Identifies:
1. Losing captures (SEE < -100 cp, e.g. capturing into a defended square losing material).
2. Hanging pieces on quiet moves (moving a piece to a square where it can be captured favorably).
3. Moves allowing immediate checkmate by the opponent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import chess

from chess_tactical.see import evaluate_exchange
from chess_tactical.values import get_piece_value


@dataclass(frozen=True)
class BlunderMove:
    """A move that results in severe tactical or material loss."""
    move: chess.Move
    score_loss: int                       # Centipawns lost (negative, e.g. -300)
    description: str                      # Human-readable explanation
    is_mate_allowed: bool = False

    @property
    def san(self) -> str:
        return str(self.move)


def find_all_blunders(
    board: chess.Board,
    color: Optional[chess.Color] = None,
    min_loss_cp: int = 100,
) -> List[BlunderMove]:
    """
    Find every single legal move that blunders material or allows immediate mate.

    Parameters
    ----------
    board : chess.Board
        The current chess position.
    color : Optional[chess.Color]
        The side to evaluate blunders for (defaults to board.turn).
    min_loss_cp : int
        Minimum centipawns lost to qualify as a blunder (default: 100 = 1 pawn).

    Returns
    -------
    List[BlunderMove]
        All blunder moves sorted by severity (worst blunders first).
    """
    turn_color = color if color is not None else board.turn
    opp_color = not turn_color

    test_board = board.copy()
    test_board.turn = turn_color

    candidate_moves = list(test_board.legal_moves)
    blunders: List[BlunderMove] = []

    for move in candidate_moves:
        san = test_board.san(move)
        is_cap = test_board.is_capture(move) or test_board.is_en_passant(move)

        # 1. Direct exchange evaluation on captured square (SEE)
        direct_ex_score = 0
        if is_cap:
            ex = evaluate_exchange(test_board, move)
            direct_ex_score = ex.score
            if ex.score <= -min_loss_cp or ex.is_dangerous:
                blunders.append(BlunderMove(
                    move=move,
                    score_loss=ex.score,
                    description=f"Losing capture: {san} ({ex.score/100:+.1f})",
                    is_mate_allowed=False,
                ))
                continue

        # 2. Simulate move to test opponent responses across the entire board
        test_board.push(move)

        # Check: Immediate mate in 1 reply
        has_mate_reply = False
        mate_san = ""
        for opp_m in test_board.legal_moves:
            test_board.push(opp_m)
            if test_board.is_checkmate():
                has_mate_reply = True
                test_board.pop()
                mate_san = test_board.san(opp_m)
                break
            test_board.pop()

        if has_mate_reply:
            test_board.pop()
            blunders.append(BlunderMove(
                move=move,
                score_loss=-99999,
                description=f"Allows mate in 1: {san} (allows #{mate_san})",
                is_mate_allowed=True,
            ))
            continue

        # Check: Opponent captures anywhere on the board
        # Evaluates: hanging moved piece, abandoning defenders of other pieces,
        # unmasking attacks on friendly pieces, or failing to address hanging material.
        best_opp_gain = 0
        worst_blunder_desc = ""

        for opp_m in list(test_board.legal_moves):
            if test_board.is_capture(opp_m) or test_board.is_en_passant(opp_m):
                opp_ex = evaluate_exchange(test_board, opp_m)
                if opp_ex.score > best_opp_gain:
                    best_opp_gain = opp_ex.score
                    opp_san = test_board.san(opp_m)
                    tgt_piece = test_board.piece_at(opp_m.to_square)
                    p_name = tgt_piece.symbol().upper() if tgt_piece else "piece"
                    tgt_name = chess.square_name(opp_m.to_square)
                    if opp_m.to_square == move.to_square:
                        worst_blunder_desc = f"Hangs piece: {san} on {tgt_name} (allows {opp_san} -{opp_ex.score/100:.1f})"
                    else:
                        worst_blunder_desc = f"Allows {opp_san} winning {p_name}@{tgt_name}: {san} (-{opp_ex.score/100:.1f})"

        test_board.pop()

        net_loss = best_opp_gain - direct_ex_score
        if net_loss >= min_loss_cp:
            blunders.append(BlunderMove(
                move=move,
                score_loss=-net_loss,
                description=worst_blunder_desc or f"Blunder: {san} (-{net_loss/100:.1f})",
                is_mate_allowed=False,
            ))

    # Sort blunders by severity (most damaging first)
    blunders.sort(key=lambda b: b.score_loss)
    return blunders
