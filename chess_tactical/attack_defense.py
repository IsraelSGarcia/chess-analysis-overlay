"""
attack_defense.py
=================
Comprehensive attack, defense, square control, pin, discovered attack,
and overloaded piece analysis for both colors simultaneously.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import chess

from chess_tactical.values import get_piece_value, PIECE_VALUES


# Rays for each slider type:
# Orthogonal: N, S, E, W
ORTHOGONAL_DELTAS = [8, -8, 1, -1]
# Diagonal: NE, NW, SE, SW
DIAGONAL_DELTAS = [9, 7, -7, -9]


@dataclass
class SquareControl:
    """Detailed control metrics for a single board square."""
    square: chess.Square
    # Attacking square indices sorted from least valuable piece to most valuable
    white_attackers: List[chess.Square] = field(default_factory=list)
    black_attackers: List[chess.Square] = field(default_factory=list)

    @property
    def white_count(self) -> int:
        return len(self.white_attackers)

    @property
    def black_count(self) -> int:
        return len(self.black_attackers)

    @property
    def net_control(self) -> int:
        """Positive = White controlled, Negative = Black controlled."""
        return self.white_count - self.black_count

    def attackers_for(self, color: chess.Color) -> List[chess.Square]:
        return self.white_attackers if color == chess.WHITE else self.black_attackers

    def defenders_for(self, color: chess.Color) -> List[chess.Square]:
        """Friendly pieces guarding this square."""
        return self.white_attackers if color == chess.WHITE else self.black_attackers


@dataclass(frozen=True)
class PinInfo:
    """Information about an absolute or relative pin."""
    pinner_square: chess.Square      # Enemy slider pinning the piece
    pinned_square: chess.Square      # Piece that is pinned
    shielded_square: chess.Square    # King or high-value piece behind
    is_absolute: bool                # True = pinned to King (illegal to move off ray)
    pin_ray: Set[chess.Square]       # Squares along ray between pinner and shielded piece
    color: chess.Color               # Color of the pinned piece

    @property
    def pinner_name(self) -> str:
        return chess.square_name(self.pinner_square)

    @property
    def pinned_name(self) -> str:
        return chess.square_name(self.pinned_square)

    @property
    def shielded_name(self) -> str:
        return chess.square_name(self.shielded_square)


@dataclass(frozen=True)
class DiscoveredAttackInfo:
    """Information about a potential discovered attack."""
    masking_square: chess.Square     # Piece that if moved uncovers attack
    slider_square: chess.Square      # Slider piece that will attack
    target_square: chess.Square      # Enemy target piece
    is_discovered_check: bool        # True if target is the enemy King
    color: chess.Color               # Color of the attacking side

    @property
    def masking_name(self) -> str:
        return chess.square_name(self.masking_square)

    @property
    def slider_name(self) -> str:
        return chess.square_name(self.slider_square)

    @property
    def target_name(self) -> str:
        return chess.square_name(self.target_square)


@dataclass(frozen=True)
class OverloadedPieceInfo:
    """Information about a piece defending multiple attacked friendly pieces."""
    piece_square: chess.Square
    color: chess.Color
    defended_targets: Tuple[chess.Square, ...]  # Friendly squares currently attacked by enemy

    @property
    def piece_name(self) -> str:
        return chess.square_name(self.piece_square)


class AttackDefenseMap:
    """
    Computes and holds the attack, defense, square control, pin, discovered attack,
    and overload state for a board position.
    """

    def __init__(self, board: chess.Board) -> None:
        self.board = board
        self.squares: Dict[chess.Square, SquareControl] = {}
        self.pins: List[PinInfo] = []
        self.discovered_attacks: List[DiscoveredAttackInfo] = []
        self.overloaded_pieces: List[OverloadedPieceInfo] = []

        self._compute_square_controls()
        self._compute_pins()
        self._compute_discovered_attacks()
        self._compute_overloaded_pieces()

    def _sort_attackers_by_value(self, attacker_squares: List[chess.Square]) -> List[chess.Square]:
        """Sort attacker squares by piece value ascending (Pawn first, King last)."""
        def sort_key(sq: chess.Square) -> int:
            p = self.board.piece_at(sq)
            return get_piece_value(p.piece_type) if p else 99999
        return sorted(attacker_squares, key=sort_key)

    def _compute_square_controls(self) -> None:
        """Calculate White and Black attackers for every square on the board."""
        for sq in chess.SQUARES:
            w_attackers = list(self.board.attackers(chess.WHITE, sq))
            b_attackers = list(self.board.attackers(chess.BLACK, sq))

            self.squares[sq] = SquareControl(
                square=sq,
                white_attackers=self._sort_attackers_by_value(w_attackers),
                black_attackers=self._sort_attackers_by_value(b_attackers),
            )

    def _ray_between_inclusive(self, s1: chess.Square, s2: chess.Square) -> Set[chess.Square]:
        """Return squares strictly between s1 and s2, plus s1 and s2."""
        between = chess.SquareSet(chess.between(s1, s2))
        between.add(s1)
        between.add(s2)
        return set(between)

    def _compute_pins(self) -> None:
        """
        Detect absolute pins (pinned to King) and relative pins (pinned to Queen/Rook).
        """
        # 1. Absolute pins via python-chess
        for color in (chess.WHITE, chess.BLACK):
            king_sq = self.board.king(color)
            if king_sq is None:
                continue

            for sq in chess.SQUARES:
                piece = self.board.piece_at(sq)
                if piece and piece.color == color and sq != king_sq:
                    if self.board.is_pinned(color, sq):
                        # Find the enemy pinner slider
                        enemy_color = not color
                        pin_ray = set(self.board.pin(color, sq))
                        # Identify the attacker along this ray
                        pinner_sq = None
                        for ray_sq in pin_ray:
                            p = self.board.piece_at(ray_sq)
                            if p and p.color == enemy_color and p.piece_type in (chess.BISHOP, chess.ROOK, chess.QUEEN):
                                pinner_sq = ray_sq
                                break

                        if pinner_sq is not None:
                            self.pins.append(PinInfo(
                                pinner_square=pinner_sq,
                                pinned_square=sq,
                                shielded_square=king_sq,
                                is_absolute=True,
                                pin_ray=pin_ray,
                                color=color,
                            ))

        # 2. Relative pins (shielding Queen or Rook)
        for enemy_color in (chess.WHITE, chess.BLACK):
            friendly_color = not enemy_color
            for pinner_sq in chess.SQUARES:
                slider = self.board.piece_at(pinner_sq)
                if not slider or slider.color != enemy_color:
                    continue
                if slider.piece_type not in (chess.BISHOP, chess.ROOK, chess.QUEEN):
                    continue

                # Explore all ray directions from pinner_sq
                p_file, p_rank = chess.square_file(pinner_sq), chess.square_rank(pinner_sq)

                directions: List[Tuple[int, int]] = []
                if slider.piece_type in (chess.ROOK, chess.QUEEN):
                    directions.extend([(0, 1), (0, -1), (1, 0), (-1, 0)])
                if slider.piece_type in (chess.BISHOP, chess.QUEEN):
                    directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])

                for df, dr in directions:
                    cur_f, cur_r = p_file + df, p_rank + dr
                    first_piece_sq = None
                    second_piece_sq = None
                    ray_squares = {pinner_sq}

                    while 0 <= cur_f <= 7 and 0 <= cur_r <= 7:
                        cur_sq = chess.square(cur_f, cur_r)
                        ray_squares.add(cur_sq)
                        occ = self.board.piece_at(cur_sq)

                        if occ:
                            if occ.color == enemy_color:
                                # Blocked by friendly piece
                                break
                            # Friendly piece of shielded side
                            if first_piece_sq is None:
                                first_piece_sq = cur_sq
                            elif second_piece_sq is None:
                                second_piece_sq = cur_sq
                                break
                        cur_f += df
                        cur_r += dr

                    if first_piece_sq is not None and second_piece_sq is not None:
                        p1 = self.board.piece_at(first_piece_sq)
                        p2 = self.board.piece_at(second_piece_sq)
                        if p1 and p2 and p1.color == friendly_color and p2.color == friendly_color:
                            # If p2 is King, it's already an absolute pin
                            if p2.piece_type != chess.KING:
                                # Relative pin: p2 is worth more than p1 (e.g. Queen behind Knight/Bishop/Rook, or Rook behind Minor/Pawn)
                                if get_piece_value(p2.piece_type) > get_piece_value(p1.piece_type):
                                    pin_set = self._ray_between_inclusive(pinner_sq, second_piece_sq)
                                    self.pins.append(PinInfo(
                                        pinner_square=pinner_sq,
                                        pinned_square=first_piece_sq,
                                        shielded_square=second_piece_sq,
                                        is_absolute=False,
                                        pin_ray=pin_set,
                                        color=friendly_color,
                                    ))

    def _compute_discovered_attacks(self) -> None:
        """
        Detect sliding attacks that are currently masked by a friendly piece,
        which would uncover an attack if the friendly piece moves.
        """
        for color in (chess.WHITE, chess.BLACK):
            enemy_color = not color
            enemy_king = self.board.king(enemy_color)

            for slider_sq in chess.SQUARES:
                slider = self.board.piece_at(slider_sq)
                if not slider or slider.color != color:
                    continue
                if slider.piece_type not in (chess.BISHOP, chess.ROOK, chess.QUEEN):
                    continue

                s_file, s_rank = chess.square_file(slider_sq), chess.square_rank(slider_sq)
                directions: List[Tuple[int, int]] = []
                if slider.piece_type in (chess.ROOK, chess.QUEEN):
                    directions.extend([(0, 1), (0, -1), (1, 0), (-1, 0)])
                if slider.piece_type in (chess.BISHOP, chess.QUEEN):
                    directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])

                for df, dr in directions:
                    cur_f, cur_r = s_file + df, s_rank + dr
                    masking_sq = None
                    target_sq = None

                    while 0 <= cur_f <= 7 and 0 <= cur_r <= 7:
                        cur_sq = chess.square(cur_f, cur_r)
                        occ = self.board.piece_at(cur_sq)

                        if occ:
                            if occ.color == color:
                                if masking_sq is None:
                                    masking_sq = cur_sq
                                else:
                                    # Two friendly pieces in line, too deep
                                    break
                            else:
                                # Enemy piece encountered
                                if masking_sq is not None:
                                    target_sq = cur_sq
                                break
                        cur_f += df
                        cur_r += dr

                    if masking_sq is not None and target_sq is not None:
                        is_disc_check = (target_sq == enemy_king)
                        tgt_piece = self.board.piece_at(target_sq)

                        # Filter for tactically meaningful discovered attacks:
                        # 1. Target is King (check), Queen, Rook, or an undefended piece
                        tgt_val = get_piece_value(tgt_piece.piece_type) if tgt_piece else 0
                        is_tgt_meaningful = (
                            is_disc_check
                            or tgt_val >= get_piece_value(chess.ROOK)
                            or not self.is_defended(target_sq)
                        )

                        if is_tgt_meaningful:
                            # 2. Verify masking piece has at least one legal move off the ray
                            ray_set = self._ray_between_inclusive(slider_sq, target_sq)
                            has_vacating_move = False
                            test_board = self.board.copy()
                            test_board.turn = color

                            for m in test_board.legal_moves:
                                if m.from_square == masking_sq and m.to_square not in ray_set:
                                    has_vacating_move = True
                                    break

                            if has_vacating_move:
                                self.discovered_attacks.append(DiscoveredAttackInfo(
                                    masking_square=masking_sq,
                                    slider_square=slider_sq,
                                    target_square=target_sq,
                                    is_discovered_check=is_disc_check,
                                    color=color,
                                ))

    def _compute_overloaded_pieces(self) -> None:
        """
        Detect friendly pieces that are defending two or more friendly pieces
        that are under attack by the enemy.
        """
        for color in (chess.WHITE, chess.BLACK):
            enemy_color = not color

            # Map: friendly_sq -> set of attacked targets it defends
            defends_attacked: Dict[chess.Square, List[chess.Square]] = {}

            for sq in chess.SQUARES:
                piece = self.board.piece_at(sq)
                if not piece or piece.color != color:
                    continue

                # Is this piece under attack?
                enemy_attackers = self.squares[sq].attackers_for(enemy_color)
                if not enemy_attackers:
                    continue

                # Who defends this attacked piece? (Exclude Kings from overloaded status)
                friendly_defenders = self.squares[sq].defenders_for(color)
                for def_sq in friendly_defenders:
                    def_piece = self.board.piece_at(def_sq)
                    if def_piece and def_piece.piece_type != chess.KING:
                        if def_sq not in defends_attacked:
                            defends_attacked[def_sq] = []
                        defends_attacked[def_sq].append(sq)

            for def_sq, targets in defends_attacked.items():
                if len(targets) >= 2:
                    self.overloaded_pieces.append(OverloadedPieceInfo(
                        piece_square=def_sq,
                        color=color,
                        defended_targets=tuple(targets),
                    ))

    def get_attackers(self, sq: chess.Square, color: chess.Color) -> List[chess.Square]:
        """Return attacking squares for the specified color sorted by piece value."""
        return self.squares[sq].attackers_for(color)

    def is_defended(self, sq: chess.Square) -> bool:
        """Return True if the piece on sq is defended by at least one friendly piece."""
        piece = self.board.piece_at(sq)
        if not piece:
            return False
        return len(self.squares[sq].defenders_for(piece.color)) > 0

    def is_pinned(self, sq: chess.Square) -> Optional[PinInfo]:
        """Return PinInfo if sq is currently pinned (absolute or relative), else None."""
        for pin in self.pins:
            if pin.pinned_square == sq:
                return pin
        return None
