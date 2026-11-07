"""
chess_tactical
==============
Standalone tactical intelligence engine for chess-analysis-overlay.

Provides:
- Static Exchange Evaluation (SEE)
- Attack and defense square maps
- Multi-attacker/defender and overload analysis
- Absolute and relative pin detection
- Discovered attack and skewer detection
- Fork and double attack recognition
- Hanging piece identification
- Forcing sequence calculation (checks, captures, promotions)
"""

from chess_tactical.values import (
    PIECE_VALUES,
    PIECE_NAMES,
    ExchangeCategory,
    get_piece_value,
)
from chess_tactical.attack_defense import (
    AttackDefenseMap,
    SquareControl,
    PinInfo,
    DiscoveredAttackInfo,
    OverloadedPieceInfo,
)
from chess_tactical.see import (
    ExchangeResult,
    evaluate_exchange,
    evaluate_all_captures,
)
from chess_tactical.hanging import (
    HangingPiece,
    find_hanging_pieces,
)
from chess_tactical.motifs import (
    TacticalMotif,
    MotifType,
    scan_all_motifs,
    find_forks,
    find_skewers,
    find_back_rank_weaknesses,
)
from chess_tactical.forcing_search import (
    TacticalSequence,
    calculate_tactical_sequences,
)
from chess_tactical.blunders import (
    BlunderMove,
    find_all_blunders,
)
from chess_tactical.trapped import (
    TrappedPiece,
    find_trapped_pieces,
)
from chess_tactical.xray import (
    XRayRay,
    find_xray_rays,
)
from chess_tactical.report import (
    TacticalReport,
    generate_tactical_report,
)

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
    "ExchangeResult",
    "evaluate_exchange",
    "evaluate_all_captures",
    "HangingPiece",
    "find_hanging_pieces",
    "TacticalMotif",
    "MotifType",
    "scan_all_motifs",
    "find_forks",
    "find_skewers",
    "find_back_rank_weaknesses",
    "TacticalSequence",
    "calculate_tactical_sequences",
    "BlunderMove",
    "find_all_blunders",
    "TrappedPiece",
    "find_trapped_pieces",
    "XRayRay",
    "find_xray_rays",
    "TacticalReport",
    "generate_tactical_report",
]
