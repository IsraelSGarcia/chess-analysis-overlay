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
from .openings import (
    OpeningInfo,
    OpeningTrap,
    identify_opening_from_moves,
    detect_opening_traps,
    is_opening_phase,
)
from .endgames import (
    RunawayPawnInfo,
    OppositionInfo,
    PassedPawnInfo,
    is_endgame,
    is_passed_pawn,
    evaluate_runaway_passed_pawns,
    detect_king_opposition,
    classify_passed_pawns,
)
from .positional import (
    OutpostInfo,
    PawnStructureAnalysis,
    OpenFileControl,
    BishopQuality,
    PositionalReport,
    find_outposts,
    analyze_pawn_structure,
    analyze_open_files,
    evaluate_bishops,
    evaluate_space,
    generate_positional_report,
)
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
    "OpeningInfo",
    "OpeningTrap",
    "identify_opening_from_moves",
    "detect_opening_traps",
    "is_opening_phase",
    "RunawayPawnInfo",
    "OppositionInfo",
    "PassedPawnInfo",
    "is_endgame",
    "is_passed_pawn",
    "evaluate_runaway_passed_pawns",
    "detect_king_opposition",
    "classify_passed_pawns",
    "OutpostInfo",
    "PawnStructureAnalysis",
    "OpenFileControl",
    "BishopQuality",
    "PositionalReport",
    "find_outposts",
    "analyze_pawn_structure",
    "analyze_open_files",
    "evaluate_bishops",
    "evaluate_space",
    "generate_positional_report",
]
