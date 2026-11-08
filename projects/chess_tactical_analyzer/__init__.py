"""
projects.chess_tactical_analyzer
================================
Specialized analytical subproject responsible for 0-ply tactical awareness:
- Tactical pattern recognition (forks, pins, skewers, discovered attacks, overloaded defenders, back-rank, mating threats, removing defender)
- Hanging piece detection
- Trapped piece detection
- Slider X-ray ray detection
- Blunder candidate detection
- Consolidated tactical reporting
"""

from core.shared_analysis import (
    PIECE_VALUES,
    PIECE_NAMES,
    ExchangeCategory,
    get_piece_value,
    AttackDefenseMap,
    SquareControl,
    PinInfo,
    DiscoveredAttackInfo,
    OverloadedPieceInfo,
    evaluate_exchange,
    evaluate_all_captures,
    ExchangeResult,
)

from .motifs import (
    TacticalMotif,
    MotifType,
    find_forks,
    find_skewers,
    find_back_rank_weaknesses,
    find_mating_threats,
    find_removing_the_defender,
    find_deflection_tactics,
    scan_all_motifs,
)
from .hanging import HangingPiece, find_hanging_pieces
from .trapped import TrappedPiece, find_trapped_pieces
from .xray import XRayRay, find_xray_rays
from .blunders import BlunderMove, find_all_blunders
from .forcing_search import TacticalSequence, calculate_tactical_sequences
from .report import TacticalReport, generate_tactical_report

__all__ = [
    "PIECE_VALUES",
    "PIECE_NAMES",
    "ExchangeCategory",
    "get_piece_value",
    "AttackDefenseMap",
    "SquareControl",
    "PinInfo",
    "DiscoveredAttackInfo",
    "OverloadedPieceInfo",
    "evaluate_exchange",
    "evaluate_all_captures",
    "ExchangeResult",
    "TacticalMotif",
    "MotifType",
    "find_forks",
    "find_skewers",
    "find_back_rank_weaknesses",
    "find_mating_threats",
    "find_removing_the_defender",
    "find_deflection_tactics",
    "scan_all_motifs",
    "HangingPiece",
    "find_hanging_pieces",
    "TrappedPiece",
    "find_trapped_pieces",
    "XRayRay",
    "find_xray_rays",
    "TacticalSequence",
    "calculate_tactical_sequences",
    "BlunderMove",
    "find_all_blunders",
    "TacticalReport",
    "generate_tactical_report",
]
