"""
structure.py
============
Positional structure, pawn integrity, outposts, file control, and bishop quality.

Analyzes:
- Permanent Knight Outposts (holes in opponent camp immune to pawn attack)
- Pawn Structure Weaknesses (Isolated, Backward, Doubled pawns, Pawn Islands)
- Open & Semi-Open Files for heavy pieces
- Bad Bishops (restricted by own fixed pawns)
- Space Advantage (controlled squares past rank 4)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import chess

from core.shared_analysis.attack_defense import AttackDefenseMap


@dataclass(frozen=True)
class OutpostInfo:
    """An advanced square immune to enemy pawn attack, protected by friendly pawns."""
    square: chess.Square
    color: chess.Color
    is_occupied: bool
    occupant_piece_type: Optional[chess.PieceType] = None

    @property
    def square_name(self) -> str:
        return chess.square_name(self.square)

    @property
    def description(self) -> str:
        c_name = "White" if self.color == chess.WHITE else "Black"
        occ = f" occupied by {chess.piece_symbol(self.occupant_piece_type).upper()}" if self.occupant_piece_type else ""
        return f"{c_name} Outpost on {self.square_name}{occ}"


@dataclass(frozen=True)
class PawnStructureAnalysis:
    """Consolidated pawn structure metrics."""
    isolated: Dict[chess.Color, List[chess.Square]] = field(default_factory=lambda: {chess.WHITE: [], chess.BLACK: []})
    backward: Dict[chess.Color, List[chess.Square]] = field(default_factory=lambda: {chess.WHITE: [], chess.BLACK: []})
    doubled: Dict[chess.Color, List[chess.Square]] = field(default_factory=lambda: {chess.WHITE: [], chess.BLACK: []})
    pawn_islands: Dict[chess.Color, int] = field(default_factory=lambda: {chess.WHITE: 0, chess.BLACK: 0})


@dataclass(frozen=True)
class OpenFileControl:
    """Open and semi-open file metrics and heavy piece occupancy."""
    file_idx: int
    is_completely_open: bool
    is_semi_open_for: Optional[chess.Color]
    rooks_controlling: Dict[chess.Color, List[chess.Square]]

    @property
    def file_letter(self) -> str:
        return chr(ord('a') + self.file_idx)


@dataclass(frozen=True)
class BishopQuality:
    """Evaluation of bishop mobility vs. friendly pawns on same square color."""
    square: chess.Square
    color: chess.Color
    is_light_squared: bool
    is_bad: bool
    friendly_pawns_on_same_color: int

    @property
    def square_name(self) -> str:
        return chess.square_name(self.square)

    @property
    def description(self) -> str:
        c_name = "White" if self.color == chess.WHITE else "Black"
        b_type = "Bad Bishop (blocked by pawns)" if self.is_bad else "Active Bishop"
        return f"{c_name} Bishop on {self.square_name}: {b_type} ({self.friendly_pawns_on_same_color} pawns on color)"


@dataclass(frozen=True)
class PositionalReport:
    """Full positional analysis payload."""
    outposts: List[OutpostInfo]
    pawn_structure: PawnStructureAnalysis
    open_files: List[OpenFileControl]
    bishops: List[BishopQuality]
    space_control: Dict[chess.Color, int]  # Number of squares controlled in enemy territory


def find_outposts(board: chess.Board, attack_map: AttackDefenseMap) -> List[OutpostInfo]:
    """
    Find permanent outposts: squares on ranks 4-6 (for White) or 3-5 (for Black)
    that can NEVER be attacked by enemy pawns and are protected by at least 1 friendly pawn.
    """
    outposts: List[OutpostInfo] = []

    for color in (chess.WHITE, chess.BLACK):
        opp_color = not color
        eligible_ranks = (3, 4, 5) if color == chess.WHITE else (2, 3, 4)  # 0-indexed ranks (4,5,6 or 3,4,5)

        for sq in chess.SQUARES:
            r = chess.square_rank(sq)
            if r not in eligible_ranks:
                continue

            f = chess.square_file(sq)

            # 1. Must be protected by at least 1 friendly pawn
            ctrl = attack_map.squares[sq]
            defenders = ctrl.defenders_for(color)
            has_pawn_support = any(
                board.piece_at(d) and board.piece_at(d).piece_type == chess.PAWN
                for d in defenders
            )
            if not has_pawn_support:
                continue

            # 2. Can enemy pawns ever attack this square?
            # Check adjacent files for enemy pawns that are behind or on the rank
            can_be_attacked_by_pawn = False
            adj_files = [af for af in (f - 1, f + 1) if 0 <= af <= 7]

            for af in adj_files:
                for opp_r in range(8):
                    p = board.piece_at(chess.square(af, opp_r))
                    if p and p.piece_type == chess.PAWN and p.color == opp_color:
                        if color == chess.WHITE and opp_r > r:
                            # Black pawn in front of White outpost can advance to attack
                            can_be_attacked_by_pawn = True
                        elif color == chess.BLACK and opp_r < r:
                            # White pawn in front of Black outpost can advance to attack
                            can_be_attacked_by_pawn = True

            if not can_be_attacked_by_pawn:
                occupant = board.piece_at(sq)
                is_occ = occupant is not None and occupant.color == color
                p_type = occupant.piece_type if is_occ else None
                outposts.append(OutpostInfo(
                    square=sq,
                    color=color,
                    is_occupied=is_occ,
                    occupant_piece_type=p_type,
                ))

    return outposts


def analyze_pawn_structure(board: chess.Board) -> PawnStructureAnalysis:
    """Analyze pawn islands, isolated pawns, doubled pawns, and backward pawns."""
    isolated: Dict[chess.Color, List[chess.Square]] = {chess.WHITE: [], chess.BLACK: []}
    backward: Dict[chess.Color, List[chess.Square]] = {chess.WHITE: [], chess.BLACK: []}
    doubled: Dict[chess.Color, List[chess.Square]] = {chess.WHITE: [], chess.BLACK: []}
    pawn_islands: Dict[chess.Color, int] = {chess.WHITE: 0, chess.BLACK: 0}

    for color in (chess.WHITE, chess.BLACK):
        file_pawns: Dict[int, List[chess.Square]] = {f: [] for f in range(8)}
        for sq in chess.SQUARES:
            p = board.piece_at(sq)
            if p and p.piece_type == chess.PAWN and p.color == color:
                file_pawns[chess.square_file(sq)].append(sq)

        # 1. Doubled pawns
        for f, sqs in file_pawns.items():
            if len(sqs) >= 2:
                doubled[color].extend(sqs)

        # 2. Isolated pawns & Pawn Islands
        occupied_files = [f for f, sqs in file_pawns.items() if len(sqs) > 0]
        # Count islands (contiguous blocks of files with pawns)
        islands = 0
        in_island = False
        for f in range(8):
            if len(file_pawns[f]) > 0:
                if not in_island:
                    islands += 1
                    in_island = True
            else:
                in_island = False
        pawn_islands[color] = islands

        # Isolated: no pawns on adjacent files
        for f in occupied_files:
            has_left = (f > 0 and len(file_pawns[f - 1]) > 0)
            has_right = (f < 7 and len(file_pawns[f + 1]) > 0)
            if not has_left and not has_right:
                isolated[color].extend(file_pawns[f])

        # 3. Backward pawns: pawn lagged behind neighbors that cannot advance safely
        for f in occupied_files:
            sqs = file_pawns[f]
            if not sqs:
                continue
            trailing_sq = min(sqs, key=chess.square_rank) if color == chess.WHITE else max(sqs, key=chess.square_rank)
            r = chess.square_rank(trailing_sq)
            # Check adjacent friendly pawns
            adj_files = [af for af in (f - 1, f + 1) if 0 <= af <= 7]
            has_advanced_neighbors = False
            for af in adj_files:
                for n_sq in file_pawns[af]:
                    n_r = chess.square_rank(n_sq)
                    if (color == chess.WHITE and n_r > r) or (color == chess.BLACK and n_r < r):
                        has_advanced_neighbors = True

            # If neighbors are more advanced, check if the square in front is controlled by enemy pawns
            if has_advanced_neighbors and trailing_sq not in isolated[color]:
                stop_rank = r + 1 if color == chess.WHITE else r - 1
                if 0 <= stop_rank <= 7:
                    stop_sq = chess.square(f, stop_rank)
                    opp_color = not color
                    # Check if stop square is attacked by an enemy pawn
                    for af in adj_files:
                        opp_pawn_r = stop_rank + 1 if color == chess.WHITE else stop_rank - 1
                        if 0 <= opp_pawn_r <= 7:
                            opp_p = board.piece_at(chess.square(af, opp_pawn_r))
                            if opp_p and opp_p.piece_type == chess.PAWN and opp_p.color == opp_color:
                                backward[color].append(trailing_sq)
                                break

    return PawnStructureAnalysis(
        isolated=isolated,
        backward=backward,
        doubled=doubled,
        pawn_islands=pawn_islands,
    )


def analyze_open_files(board: chess.Board) -> List[OpenFileControl]:
    """Find open and semi-open files and heavy pieces controlling them."""
    open_files: List[OpenFileControl] = []

    for f in range(8):
        white_pawns = 0
        black_pawns = 0
        for r in range(8):
            p = board.piece_at(chess.square(f, r))
            if p and p.piece_type == chess.PAWN:
                if p.color == chess.WHITE:
                    white_pawns += 1
                else:
                    black_pawns += 1

        is_open = (white_pawns == 0 and black_pawns == 0)
        semi_for = None
        if not is_open:
            if white_pawns == 0 and black_pawns > 0:
                semi_for = chess.WHITE
            elif black_pawns == 0 and white_pawns > 0:
                semi_for = chess.BLACK

        if is_open or semi_for is not None:
            rooks: Dict[chess.Color, List[chess.Square]] = {chess.WHITE: [], chess.BLACK: []}
            for r in range(8):
                p = board.piece_at(chess.square(f, r))
                if p and p.piece_type in (chess.ROOK, chess.QUEEN):
                    rooks[p.color].append(chess.square(f, r))

            open_files.append(OpenFileControl(
                file_idx=f,
                is_completely_open=is_open,
                is_semi_open_for=semi_for,
                rooks_controlling=rooks,
            ))

    return open_files


def evaluate_bishops(board: chess.Board) -> List[BishopQuality]:
    """Evaluate bishop mobility against friendly fixed pawns on the same color."""
    bishops: List[BishopQuality] = []

    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if not p or p.piece_type != chess.BISHOP:
            continue

        color = p.color
        is_light = bool((chess.square_file(sq) + chess.square_rank(sq)) % 2 == 1)

        # Count friendly pawns on the same square color
        pawns_on_same = 0
        for p_sq in chess.SQUARES:
            pawn = board.piece_at(p_sq)
            if pawn and pawn.piece_type == chess.PAWN and pawn.color == color:
                pawn_is_light = bool((chess.square_file(p_sq) + chess.square_rank(p_sq)) % 2 == 1)
                if pawn_is_light == is_light:
                    pawns_on_same += 1

        # A bishop with 4+ pawns locked on its own color is a bad bishop
        is_bad = pawns_on_same >= 4

        bishops.append(BishopQuality(
            square=sq,
            color=color,
            is_light_squared=is_light,
            is_bad=is_bad,
            friendly_pawns_on_same_color=pawns_on_same,
        ))

    return bishops


def evaluate_space(board: chess.Board, attack_map: AttackDefenseMap) -> Dict[chess.Color, int]:
    """Count controlled squares past the 4th rank (ranks 5-8 for White, ranks 1-4 for Black)."""
    space: Dict[chess.Color, int] = {chess.WHITE: 0, chess.BLACK: 0}

    for sq in chess.SQUARES:
        r = chess.square_rank(sq)
        ctrl = attack_map.squares[sq]

        # White territory: ranks 0..3. White space = control on ranks 4..7
        if r >= 4 and ctrl.white_count > 0:
            space[chess.WHITE] += 1

        # Black territory: ranks 4..7. Black space = control on ranks 0..3
        if r <= 3 and ctrl.black_count > 0:
            space[chess.BLACK] += 1

    return space


def generate_positional_report(board: chess.Board, attack_map: AttackDefenseMap) -> PositionalReport:
    """Consolidate all positional metrics into a single report."""
    return PositionalReport(
        outposts=find_outposts(board, attack_map),
        pawn_structure=analyze_pawn_structure(board),
        open_files=analyze_open_files(board),
        bishops=evaluate_bishops(board),
        space_control=evaluate_space(board, attack_map),
    )
