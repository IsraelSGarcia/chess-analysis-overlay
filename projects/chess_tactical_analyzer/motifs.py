"""
motifs.py
=========
Detection of tactical patterns:
- Forks and Double Attacks
- Absolute and Relative Pins
- Skewers
- Discovered Attacks and Discovered Checks
- Overloaded Defenders
- Back-Rank Weaknesses
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set, Tuple
import chess

from core.shared_analysis.values import get_piece_value, PIECE_VALUES
from core.shared_analysis.attack_defense import AttackDefenseMap, PinInfo, DiscoveredAttackInfo, OverloadedPieceInfo


class MotifType(Enum):
    FORK = "fork"
    ABSOLUTE_PIN = "absolute_pin"
    RELATIVE_PIN = "relative_pin"
    SKEWER = "skewer"
    DISCOVERED_ATTACK = "discovered_attack"
    DISCOVERED_CHECK = "discovered_check"
    OVERLOADED_DEFENDER = "overloaded_defender"
    BACK_RANK_WEAKNESS = "back_rank_weakness"
    MATING_THREAT = "mating_threat"
    REMOVING_DEFENDER = "removing_defender"
    DEFLECTION = "deflection"
    DECOY = "decoy"


@dataclass(frozen=True)
class TacticalMotif:
    """A detected tactical motif with affected squares and explanation."""
    motif_type: MotifType
    color: chess.Color               # Initiator / attacking color
    source_square: chess.Square      # Piece delivering the motif (or pinner/attacker)
    target_squares: Tuple[chess.Square, ...]  # Affected target squares
    description: str

    @property
    def source_name(self) -> str:
        return chess.square_name(self.source_square)

    @property
    def target_names(self) -> List[str]:
        return [chess.square_name(s) for s in self.target_squares]

    @property
    def color_name(self) -> str:
        return "White" if self.color == chess.WHITE else "Black"

    def __str__(self) -> str:
        targets_str = ", ".join(self.target_names)
        return f"[{self.color_name} {self.motif_type.value}] {self.source_name} -> {targets_str}: {self.description}"


def find_forks(board: chess.Board, attack_map: AttackDefenseMap) -> List[TacticalMotif]:
    """
    Find pieces currently delivering a fork / double attack against 2+ high-value
    or undefended enemy targets.
    """
    forks: List[TacticalMotif] = []

    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if not piece:
            continue

        color = piece.color
        enemy_color = not color
        piece_val = get_piece_value(piece.piece_type)

        # Candidate targets attacked by this piece
        attacked_squares = board.attacks(sq)
        valuable_targets: List[chess.Square] = []

        for tgt_sq in attacked_squares:
            tgt_piece = board.piece_at(tgt_sq)
            if not tgt_piece or tgt_piece.color != enemy_color:
                continue

            tgt_val = get_piece_value(tgt_piece.piece_type)
            is_tgt_defended = attack_map.is_defended(tgt_sq)

            # A target is tactically meaningful if:
            # 1. It is the King (check)
            # 2. It is worth more than the attacker
            # 3. It is undefended
            if (
                tgt_piece.piece_type == chess.KING
                or tgt_val > piece_val
                or not is_tgt_defended
            ):
                valuable_targets.append(tgt_sq)

        if len(valuable_targets) >= 2:
            target_desc = ", ".join(
                f"{board.piece_at(t).symbol()}@{chess.square_name(t)}" for t in valuable_targets
            )
            forks.append(TacticalMotif(
                motif_type=MotifType.FORK,
                color=color,
                source_square=sq,
                target_squares=tuple(valuable_targets),
                description=f"{piece.symbol()} forks {target_desc}",
            ))

    return forks


def find_skewers(board: chess.Board) -> List[TacticalMotif]:
    """
    Find skewers: an enemy slider attacking a high-value piece in front,
    which shields an undefended or lower-value piece behind it.
    """
    skewers: List[TacticalMotif] = []

    for slider_sq in chess.SQUARES:
        slider = board.piece_at(slider_sq)
        if not slider:
            continue
        if slider.piece_type not in (chess.BISHOP, chess.ROOK, chess.QUEEN):
            continue

        color = slider.color
        enemy_color = not color

        s_file, s_rank = chess.square_file(slider_sq), chess.square_rank(slider_sq)
        directions: List[Tuple[int, int]] = []
        if slider.piece_type in (chess.ROOK, chess.QUEEN):
            directions.extend([(0, 1), (0, -1), (1, 0), (-1, 0)])
        if slider.piece_type in (chess.BISHOP, chess.QUEEN):
            directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])

        for df, dr in directions:
            cur_f, cur_r = s_file + df, s_rank + dr
            front_sq: Optional[chess.Square] = None
            back_sq: Optional[chess.Square] = None

            while 0 <= cur_f <= 7 and 0 <= cur_r <= 7:
                cur_sq = chess.square(cur_f, cur_r)
                occ = board.piece_at(cur_sq)

                if occ:
                    if occ.color == color:
                        break  # Blocked by friendly piece
                    if front_sq is None:
                        front_sq = cur_sq
                    elif back_sq is None:
                        back_sq = cur_sq
                        break
                cur_f += df
                cur_r += dr

            if front_sq is not None and back_sq is not None:
                p_front = board.piece_at(front_sq)
                p_back = board.piece_at(back_sq)

                if p_front and p_back and p_front.color == enemy_color and p_back.color == enemy_color:
                    val_front = get_piece_value(p_front.piece_type)
                    val_back = get_piece_value(p_back.piece_type)

                    # Skewer condition: Front piece is more valuable than back piece,
                    # or front is King (compelled to move).
                    if p_front.piece_type == chess.KING or val_front > val_back:
                        skewers.append(TacticalMotif(
                            motif_type=MotifType.SKEWER,
                            color=color,
                            source_square=slider_sq,
                            target_squares=(front_sq, back_sq),
                            description=(
                                f"{slider.symbol()} skewers {p_front.symbol()}@{chess.square_name(front_sq)} "
                                f"in front of {p_back.symbol()}@{chess.square_name(back_sq)}"
                            ),
                        ))

    return skewers


def find_back_rank_weaknesses(board: chess.Board) -> List[TacticalMotif]:
    """
    Detect back-rank weakness: King castled on the back rank with no escape squares (luft),
    where an enemy heavy piece is infiltrating or threatening the back rank.
    """
    weaknesses: List[TacticalMotif] = []

    for color in (chess.WHITE, chess.BLACK):
        enemy_color = not color
        king_sq = board.king(color)
        if king_sq is None:
            continue

        king_rank = chess.square_rank(king_sq)
        expected_back_rank = 0 if color == chess.WHITE else 7
        if king_rank != expected_back_rank:
            continue

        king_file = chess.square_file(king_sq)
        pawn_rank = 1 if color == chess.WHITE else 6

        # Check pawns in front of castled king (e.g. files f, g, h or a, b, c)
        adjacent_files = [f for f in (king_file - 1, king_file, king_file + 1) if 0 <= f <= 7]
        blocked_files = 0
        for f in adjacent_files:
            sq_in_front = chess.square(f, pawn_rank)
            p = board.piece_at(sq_in_front)
            if p and p.color == color and p.piece_type == chess.PAWN:
                blocked_files += 1

        # If 2 or 3 of the files in front of King are blocked by friendly pawns:
        if blocked_files >= 2:
            # Check if King has flight squares (luft)
            flight_squares = 0
            for move in board.legal_moves:
                if move.from_square == king_sq:
                    dest_rank = chess.square_rank(move.to_square)
                    if dest_rank != expected_back_rank:
                        flight_squares += 1

            if flight_squares == 0:
                # King has no luft! Check if enemy rooks/queens control or can infiltrate the back rank
                enemy_heavy_pieces = [
                    sq for sq in chess.SQUARES
                    if board.piece_at(sq)
                    and board.piece_at(sq).color == enemy_color
                    and board.piece_at(sq).piece_type in (chess.ROOK, chess.QUEEN)
                ]

                # Check if any enemy heavy piece attacks the back rank
                infiltrating = [
                    sq for sq in enemy_heavy_pieces
                    if any(chess.square_rank(atk_sq) == expected_back_rank for atk_sq in board.attacks(sq))
                ]

                if infiltrating:
                    weaknesses.append(TacticalMotif(
                        motif_type=MotifType.BACK_RANK_WEAKNESS,
                        color=enemy_color,
                        source_square=infiltrating[0],
                        target_squares=(king_sq,),
                        description=f"Back-rank vulnerability for {('White' if color == chess.WHITE else 'Black')} King on {chess.square_name(king_sq)} (no luft)",
                    ))

    return weaknesses



def find_mating_threats(board: chess.Board) -> List[TacticalMotif]:
    """Detect immediate mating threats: legal moves delivering checkmate."""
    threats: List[TacticalMotif] = []
    for move in board.legal_moves:
        board.push(move)
        is_mate = board.is_checkmate()
        board.pop()
        if is_mate:
            piece = board.piece_at(move.from_square)
            p_sym = piece.symbol() if piece else "?"
            threats.append(TacticalMotif(
                motif_type=MotifType.MATING_THREAT,
                color=board.turn,
                source_square=move.from_square,
                target_squares=(move.to_square,),
                description=f"{p_sym} delivers immediate checkmate on {chess.square_name(move.to_square)}",
            ))
    return threats


def find_removing_the_defender(board: chess.Board, attack_map: AttackDefenseMap) -> List[TacticalMotif]:
    """Detect undermining/removing the defender: attacking the sole protector of a piece."""
    motifs: List[TacticalMotif] = []
    for target_sq in chess.SQUARES:
        target_piece = board.piece_at(target_sq)
        if not target_piece:
            continue
        color = target_piece.color
        enemy_color = not color
        target_val = get_piece_value(target_piece.piece_type)
        if target_val < 3:
            continue
        ctrl = attack_map.squares[target_sq]
        defenders = ctrl.defenders_for(color)
        attackers = ctrl.attackers_for(enemy_color)
        if len(defenders) == 1 and len(attackers) >= 1:
            sole_def_sq = defenders[0]
            sole_def_piece = board.piece_at(sole_def_sq)
            if not sole_def_piece:
                continue
            sole_ctrl = attack_map.squares[sole_def_sq]
            def_attackers = sole_ctrl.attackers_for(enemy_color)
            for att_sq in def_attackers:
                att_piece = board.piece_at(att_sq)
                if att_piece and att_piece.color == enemy_color:
                    motifs.append(TacticalMotif(
                        motif_type=MotifType.REMOVING_DEFENDER,
                        color=enemy_color,
                        source_square=att_sq,
                        target_squares=(sole_def_sq, target_sq),
                        description=(
                            f"{att_piece.symbol()} undermines sole defender {sole_def_piece.symbol()}@{chess.square_name(sole_def_sq)} "
                            f"protecting {target_piece.symbol()}@{chess.square_name(target_sq)}"
                        ),
                    ))
                    break
    return motifs


def find_deflection_tactics(board: chess.Board, attack_map: AttackDefenseMap) -> List[TacticalMotif]:
    """Detect deflection opportunities: driving away a key protector from another piece."""
    deflections: List[TacticalMotif] = []
    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if not p:
            continue
        color = p.color
        enemy_color = not color
        ctrl = attack_map.squares[sq]
        defenders = ctrl.defenders_for(color)
        attackers = ctrl.attackers_for(enemy_color)
        if len(attackers) >= 1 and len(defenders) >= 1:
            for att_sq in attackers:
                att_p = board.piece_at(att_sq)
                if att_p and get_piece_value(att_p.piece_type) <= get_piece_value(p.piece_type):
                    for other_sq in chess.SQUARES:
                        if other_sq == sq:
                            continue
                        other_p = board.piece_at(other_sq)
                        if other_p and other_p.color == color and sq in attack_map.squares[other_sq].defenders_for(color):
                            deflections.append(TacticalMotif(
                                motif_type=MotifType.DEFLECTION,
                                color=enemy_color,
                                source_square=att_sq,
                                target_squares=(sq, other_sq),
                                description=f"{att_p.symbol()} deflecting {p.symbol()}@{chess.square_name(sq)} away from {other_p.symbol()}@{chess.square_name(other_sq)}",
                            ))
                            break
    return deflections

def scan_all_motifs(
    board: chess.Board,
    attack_map: Optional[AttackDefenseMap] = None,
) -> List[TacticalMotif]:
    """
    Run all tactical motif scanners on the board and return consolidated motifs.
    """
    if attack_map is None:
        attack_map = AttackDefenseMap(board)

    motifs: List[TacticalMotif] = []

    # 1. Forks
    motifs.extend(find_forks(board, attack_map))

    # 2. Skewers
    motifs.extend(find_skewers(board))

    # 3. Absolute & Relative Pins
    for pin in attack_map.pins:
        p_pinner = board.piece_at(pin.pinner_square)
        p_pinned = board.piece_at(pin.pinned_square)
        p_shielded = board.piece_at(pin.shielded_square)
        pinner_sym = p_pinner.symbol() if p_pinner else "?"
        pinned_sym = p_pinned.symbol() if p_pinned else "?"
        shielded_sym = p_shielded.symbol() if p_shielded else "?"

        motif_type = MotifType.ABSOLUTE_PIN if pin.is_absolute else MotifType.RELATIVE_PIN
        kind_str = "absolute" if pin.is_absolute else "relative"
        desc = f"{pinner_sym} pins {pinned_sym}@{pin.pinned_name} to {shielded_sym}@{pin.shielded_name} ({kind_str})"

        motifs.append(TacticalMotif(
            motif_type=motif_type,
            color=not pin.color,  # Pinner's color
            source_square=pin.pinner_square,
            target_squares=(pin.pinned_square, pin.shielded_square),
            description=desc,
        ))

    # 4. Discovered Attacks
    for disc in attack_map.discovered_attacks:
        slider = board.piece_at(disc.slider_square)
        mask = board.piece_at(disc.masking_square)
        tgt = board.piece_at(disc.target_square)
        slider_sym = slider.symbol() if slider else "?"
        mask_sym = mask.symbol() if mask else "?"
        tgt_sym = tgt.symbol() if tgt else "?"

        motif_type = MotifType.DISCOVERED_CHECK if disc.is_discovered_check else MotifType.DISCOVERED_ATTACK
        desc = (
            f"Moving {mask_sym}@{disc.masking_name} uncovers {slider_sym} "
            f"attack against {tgt_sym}@{disc.target_name}"
            + (" (CHECK!)" if disc.is_discovered_check else "")
        )

        motifs.append(TacticalMotif(
            motif_type=motif_type,
            color=disc.color,
            source_square=disc.masking_square,
            target_squares=(disc.slider_square, disc.target_square),
            description=desc,
        ))

    # 5. Overloaded Defenders
    for over in attack_map.overloaded_pieces:
        p = board.piece_at(over.piece_square)
        p_sym = p.symbol() if p else "?"
        targets_str = ", ".join(chess.square_name(s) for s in over.defended_targets)
        desc = f"{p_sym}@{over.piece_name} is overloaded defending {targets_str}"

        motifs.append(TacticalMotif(
            motif_type=MotifType.OVERLOADED_DEFENDER,
            color=not over.color,  # Exploitable by enemy
            source_square=over.piece_square,
            target_squares=over.defended_targets,
            description=desc,
        ))

    # 6. Back-rank weaknesses
    motifs.extend(find_back_rank_weaknesses(board))

    # 7. Mating threats
    motifs.extend(find_mating_threats(board))

    # 8. Removing the defender
    motifs.extend(find_removing_the_defender(board, attack_map))

    # 9. Deflection
    motifs.extend(find_deflection_tactics(board, attack_map))

    return motifs
