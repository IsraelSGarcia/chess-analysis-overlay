"""
report.py
=========
Unified Tactical Analysis Report.

Aggregates:
- Attack and defense square maps
- Static Exchange Evaluations (SEE) for all captures
- Hanging and vulnerable pieces
- Tactical motifs (forks, pins, skewers, discovered attacks, back-rank threats)
- Calculated forcing sequences
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import chess

from core.shared_analysis.values import ExchangeCategory, PIECE_VALUES, get_piece_value
from core.shared_analysis.attack_defense import AttackDefenseMap
from core.shared_analysis.see import ExchangeResult, evaluate_all_captures
from projects.chess_tactical_analyzer.hanging import HangingPiece, find_hanging_pieces
from projects.chess_tactical_analyzer.motifs import TacticalMotif, scan_all_motifs, MotifType
from projects.chess_tactical_analyzer.forcing_search import TacticalSequence, calculate_tactical_sequences
from projects.chess_tactical_analyzer.blunders import BlunderMove, find_all_blunders
from projects.chess_tactical_analyzer.trapped import TrappedPiece, find_trapped_pieces
from projects.chess_tactical_analyzer.xray import XRayRay, find_xray_rays


@dataclass
class TacticalReport:
    """Consolidated tactical intelligence report for a board position."""
    board: chess.Board
    material_balance_cp: int
    attack_map: AttackDefenseMap
    captures: Dict[chess.Color, List[ExchangeResult]]
    hanging: Dict[chess.Color, List[HangingPiece]]
    motifs: List[TacticalMotif]
    forcing_sequences: Dict[chess.Color, List[TacticalSequence]]
    blunders: Dict[chess.Color, List[BlunderMove]] = field(default_factory=dict)
    trapped_pieces: Dict[chess.Color, List[TrappedPiece]] = field(default_factory=dict)
    xray_rays: List[XRayRay] = field(default_factory=list)

    @property
    def white_material_lead(self) -> float:
        """Net material balance in standard pawns from White's perspective."""
        return self.material_balance_cp / 100.0

    def favorable_captures(self, color: chess.Color) -> List[ExchangeResult]:
        return [c for c in self.captures.get(color, []) if c.is_favorable]

    def dangerous_captures(self, color: chess.Color) -> List[ExchangeResult]:
        return [c for c in self.captures.get(color, []) if c.is_dangerous]

    def equal_trades(self, color: chess.Color) -> List[ExchangeResult]:
        return [c for c in self.captures.get(color, []) if c.is_equal]

    def motifs_for(self, color: chess.Color) -> List[TacticalMotif]:
        return [m for m in self.motifs if m.color == color]

    def get_square_tactical_status(self, sq: chess.Square) -> Dict[str, bool]:
        """Return tactical flags for a square (for overlay highlighting)."""
        piece = self.board.piece_at(sq)
        is_hanging = any(h.square == sq for h_list in self.hanging.values() for h in h_list)
        is_motif_target = any(sq in m.target_squares for m in self.motifs)
        is_motif_source = any(m.source_square == sq for m in self.motifs)
        is_in_check = (piece is not None and piece.piece_type == chess.KING and self.board.is_check() and piece.color == self.board.turn)

        return {
            "hanging": is_hanging,
            "motif_target": is_motif_target,
            "motif_source": is_motif_source,
            "in_check": is_in_check,
        }

    def summary_lines(self) -> List[str]:
        """Compact text summary suitable for the floating HUD."""
        lines: List[str] = []

        # 1. Material
        lead = self.white_material_lead
        if lead > 0:
            mat_str = f"White +{lead:.1f}"
        elif lead < 0:
            mat_str = f"Black +{abs(lead):.1f}"
        else:
            mat_str = "Material Equal"
        lines.append(f"Balance: {mat_str}")

        # 2. Check / Mate
        if self.board.is_checkmate():
            winner = "Black" if self.board.turn == chess.WHITE else "White"
            lines.append(f"CHECKMATE! {winner} wins.")
        elif self.board.is_check():
            in_check = "White" if self.board.turn == chess.WHITE else "Black"
            lines.append(f"CHECK: {in_check} King under attack!")

        # 3. Hanging pieces
        for color, name in [(chess.WHITE, "White"), (chess.BLACK, "Black")]:
            hp_list = self.hanging.get(color, [])
            if hp_list:
                items = [f"{h.piece_symbol}@{h.square_name}" for h in hp_list[:3]]
                lines.append(f"Hanging {name}: {', '.join(items)}")

        # 4. Favorable captures
        for color, name in [(chess.WHITE, "White"), (chess.BLACK, "Black")]:
            fav = self.favorable_captures(color)
            if fav:
                caps = [f"{c.sequence[0]} (+{c.score/100:.1f})" for c in fav[:2]]
                lines.append(f"Favorable {name}: {', '.join(caps)}")

        # 5. Top Motifs
        for m in self.motifs[:3]:
            lines.append(f"Motif: {m.description}")

        # 6. Trapped pieces
        for color, name in [(chess.WHITE, "White"), (chess.BLACK, "Black")]:
            trapped_list = self.trapped_pieces.get(color, [])
            if trapped_list:
                items = [f"{t.piece_symbol}@{t.square_name}" for t in trapped_list]
                lines.append(f"Trapped {name}: {', '.join(items)}")

        # 7. Forcing sequence preview
        for color, name in [(chess.WHITE, "White"), (chess.BLACK, "Black")]:
            seqs = self.forcing_sequences.get(color, [])
            if seqs:
                top = seqs[0]
                lines.append(f"Tactic {name}: {' '.join(top.pv[:3])} ({'+' if top.score > 0 else ''}{top.score/100:.1f})")

        return lines


def generate_tactical_report(
    board: chess.Board,
    search_depth: int = 4,
    active_turn: Optional[chess.Color] = None,
) -> TacticalReport:
    """
    Generate a complete TacticalReport for the given board position.
    """
    turn_color = active_turn if active_turn is not None else board.turn
    if board.turn != turn_color:
        board = board.copy(stack=False)
        board.turn = turn_color

    # 1. Material balance
    mat_balance = 0
    for sq, piece in board.piece_map().items():
        if piece.piece_type == chess.KING:
            continue
        val = get_piece_value(piece.piece_type)
        if piece.color == chess.WHITE:
            mat_balance += val
        else:
            mat_balance -= val

    # 2. Attack and defense map
    attack_map = AttackDefenseMap(board)

    # 3. Evaluated captures for both colors
    captures = {
        chess.WHITE: evaluate_all_captures(board, chess.WHITE),
        chess.BLACK: evaluate_all_captures(board, chess.BLACK),
    }

    # 4. Hanging pieces
    hanging = {
        chess.WHITE: find_hanging_pieces(board, attack_map, chess.WHITE),
        chess.BLACK: find_hanging_pieces(board, attack_map, chess.BLACK),
    }

    # 5. Motifs
    motifs = scan_all_motifs(board, attack_map)

    # 6. Forcing sequences (disabled multi-ply calculation per 0-ply pure non-engine geometric design)
    forcing_sequences = {
        chess.WHITE: [],
        chess.BLACK: [],
    }

    # 7. Comprehensive blunder analysis for active turn
    blunders = {
        turn_color: find_all_blunders(board, color=turn_color),
        not turn_color: [],
    }

    # 8. Trapped pieces detection
    trapped_pieces = find_trapped_pieces(board)

    # 9. Slider X-Ray rays
    xray_rays = find_xray_rays(board)

    return TacticalReport(
        board=board,
        material_balance_cp=mat_balance,
        attack_map=attack_map,
        captures=captures,
        hanging=hanging,
        motifs=motifs,
        forcing_sequences=forcing_sequences,
        blunders=blunders,
        trapped_pieces=trapped_pieces,
        xray_rays=xray_rays,
    )
