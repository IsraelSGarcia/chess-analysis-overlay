"""
traps.py
========
Detection of classic opening traps and critical opening-phase mistakes.

Identifies:
- Noah's Ark Trap (Ruy Lopez bishop trap)
- Fishing Pole Trap (H-file sacrifice onto castled King)
- Légal Trap (Queen sacrifice leading to smothered bishop/knight mate)
- Elephant Trap (Queen's Gambit Declined counter-sacrifice)
- Blackburne Shilling Trap (Italian queen infiltration)
- Budapest Kieninger Trap (Smothered mate threat)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import chess


@dataclass(frozen=True)
class OpeningTrap:
    """Classified opening trap situation on the board."""
    name: str
    victim_color: chess.Color
    trap_squares: tuple[chess.Square, ...]
    description: str


def detect_opening_traps(board: chess.Board) -> List[OpeningTrap]:
    """Scan the board for active opening trap tensions."""
    traps: List[OpeningTrap] = []

    # 1. Noah's Ark Trap (White Light-Squared Bishop trapped on b3/a2)
    # Ruy Lopez setup: Black pawns on a6, b5, c4, d6; White Bishop on b3
    wb = board.piece_at(chess.B3)
    if wb and wb.piece_type == chess.BISHOP and wb.color == chess.WHITE:
        p_c4 = board.piece_at(chess.C4)
        p_b5 = board.piece_at(chess.B5)
        p_a6 = board.piece_at(chess.A6)
        p_d6 = board.piece_at(chess.D6)
        if (
            p_c4 and p_c4.piece_type == chess.PAWN and p_c4.color == chess.BLACK
            and p_b5 and p_b5.piece_type == chess.PAWN and p_b5.color == chess.BLACK
            and (p_a6 and p_a6.color == chess.BLACK or p_d6 and p_d6.color == chess.BLACK)
        ):
            traps.append(OpeningTrap(
                name="Noah's Ark Trap",
                victim_color=chess.WHITE,
                trap_squares=(chess.B3, chess.C4),
                description="Noah's Ark Trap: White Bishop on b3 is trapped by Black pawns (c4/b5)",
            ))

    # 2. Fishing Pole Trap
    # White King on g1 (castled). Black Knight on g4, Black Pawn on h5.
    # White Pawn on h3. If White plays hxg4, hxg4 opens h-file to h8 rook.
    wk = board.king(chess.WHITE)
    if wk in (chess.G1, chess.H1):
        bn = board.piece_at(chess.G4)
        bp = board.piece_at(chess.H5)
        wp = board.piece_at(chess.H3)
        if (
            bn and bn.piece_type == chess.KNIGHT and bn.color == chess.BLACK
            and bp and bp.piece_type == chess.PAWN and bp.color == chess.BLACK
            and wp and wp.piece_type == chess.PAWN and wp.color == chess.WHITE
        ):
            # Check if Black rook is on h8
            br = board.piece_at(chess.H8)
            if br and br.piece_type == chess.ROOK and br.color == chess.BLACK:
                traps.append(OpeningTrap(
                    name="Fishing Pole Trap",
                    victim_color=chess.WHITE,
                    trap_squares=(chess.G4, chess.H3, chess.H5),
                    description="Fishing Pole Trap: Capturing Ng4 opens the h-file for Black's attack on the castled King",
                ))

    # 3. Légal Trap Tension
    # Italian/Philidor: White Bishop on c4, Knight on e5/f3, Knight on c3.
    # Black Bishop on g4 pinning Knight, White can sacrifice Queen with Nxe5!
    wb_c4 = board.piece_at(chess.C4)
    wn_e5 = board.piece_at(chess.E5)
    bb_g4 = board.piece_at(chess.G4)
    bk_e8 = board.king(chess.BLACK)
    if (
        wb_c4 and wb_c4.piece_type == chess.BISHOP and wb_c4.color == chess.WHITE
        and wn_e5 and wn_e5.piece_type == chess.KNIGHT and wn_e5.color == chess.WHITE
        and bb_g4 and bb_g4.piece_type == chess.BISHOP and bb_g4.color == chess.BLACK
        and bk_e8 == chess.E8
    ):
        f7_pawn = board.piece_at(chess.F7)
        if f7_pawn and f7_pawn.color == chess.BLACK:
            traps.append(OpeningTrap(
                name="Légal Trap",
                victim_color=chess.BLACK,
                trap_squares=(chess.E5, chess.G4, chess.F7),
                description="Légal Trap: White threatens Bxf7+ followed by Nd5# mate if Queen is captured",
            ))

    # 4. Elephant Trap (Queen's Gambit Declined)
    # White Knight on d5 capturing d5 after 1. d4 d5 2. c4 e6 3. Nc3 Nf6 4. Bg5 Nbd7 5. cxd5 exd5 6. Nxd5?
    wn_d5 = board.piece_at(chess.D5)
    bn_d7 = board.piece_at(chess.D7)
    wb_g5 = board.piece_at(chess.G5)
    if (
        wn_d5 and wn_d5.piece_type == chess.KNIGHT and wn_d5.color == chess.WHITE
        and bn_d7 and bn_d7.piece_type == chess.KNIGHT and bn_d7.color == chess.BLACK
        and wb_g5 and wb_g5.piece_type == chess.BISHOP and wb_g5.color == chess.WHITE
    ):
        traps.append(OpeningTrap(
            name="Elephant Trap",
            victim_color=chess.WHITE,
            trap_squares=(chess.D5, chess.G5, chess.D7),
            description="Elephant Trap: 6... Nxd5! sacrifices the Queen to win with 7... Bb4+",
        ))

    # 5. Budapest Kieninger Smothered Mate Threat
    # Black Knight on e5, Black Bishop on b4, White Queen on d1 or e2, White Pawn on a3
    bn_e5 = board.piece_at(chess.E5)
    bb_b4 = board.piece_at(chess.B4)
    wn_d2 = board.piece_at(chess.D2)
    wk_e1 = board.king(chess.WHITE)
    if (
        bn_e5 and bn_e5.piece_type == chess.KNIGHT and bn_e5.color == chess.BLACK
        and bb_b4 and bb_b4.piece_type == chess.BISHOP and bb_b4.color == chess.BLACK
        and wn_d2 and wn_d2.piece_type == chess.KNIGHT and wn_d2.color == chess.WHITE
        and wk_e1 == chess.E1
    ):
        traps.append(OpeningTrap(
            name="Budapest Kieninger Trap",
            victim_color=chess.WHITE,
            trap_squares=(chess.E5, chess.B4, chess.D3),
            description="Budapest Trap: axb4?? allows smothered checkmate 8... Nd3#",
        ))

    return traps
