"""
core.shared_analysis
====================
Shared chess analysis infrastructure:
- Static Exchange Evaluation (SEE)
- Attack and defense maps
- Standard piece valuations
"""

from .values import PIECE_VALUES, PIECE_NAMES, get_piece_value, ExchangeCategory
from .see import evaluate_exchange, evaluate_all_captures, ExchangeResult
from .attack_defense import (
    AttackDefenseMap,
    SquareControl,
    PinInfo,
    DiscoveredAttackInfo,
    OverloadedPieceInfo,
)

__all__ = [
    "PIECE_VALUES",
    "PIECE_NAMES",
    "get_piece_value",
    "ExchangeCategory",
    "evaluate_exchange",
    "evaluate_all_captures",
    "ExchangeResult",
    "AttackDefenseMap",
    "SquareControl",
    "PinInfo",
    "DiscoveredAttackInfo",
    "OverloadedPieceInfo",
]
