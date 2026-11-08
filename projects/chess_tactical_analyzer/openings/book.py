"""
book.py
=======
Opening book classification and ECO code detection.

Maps board positions in the opening phase (first 1–15 moves) to:
- ECO Code (A00–E99)
- Canonical Opening Name
- Specific Variation Name
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import chess


@dataclass(frozen=True)
class OpeningInfo:
    """Classified opening information for a board position."""
    eco: str
    name: str
    variation: str = ""
    ply: int = 0

    @property
    def full_name(self) -> str:
        if self.variation:
            return f"{self.name}, {self.variation}"
        return self.name

    @property
    def display_str(self) -> str:
        return f"{self.eco}: {self.full_name}"


# Canonical opening move signatures mapping (sequence of UCI moves -> (ECO, Name, Variation))
OPENING_SIGNATURES: List[Tuple[Tuple[str, ...], str, str, str]] = [
    # -------------------------------------------------------------------------
    # Ruy Lopez (Spanish)
    # -------------------------------------------------------------------------
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5a4", "g8f6", "e1g1", "f8e7", "f1e1", "b7b5", "a4b3", "d7d6", "c2c3", "e1g1"), "C92", "Ruy Lopez", "Closed, Zaitsev System"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5a4", "g8f6", "e1g1", "f8e7", "f1e1", "b7b5", "a4b3", "d7d6", "c2c3"), "C84", "Ruy Lopez", "Closed, Main Line"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5a4", "g8f6", "e1g1", "f8e7"), "C78", "Ruy Lopez", "Closed"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5a4", "g8f6", "e1g1", "f6e4"), "C80", "Ruy Lopez", "Open"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5c6"), "C68", "Ruy Lopez", "Exchange Variation"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5a4"), "C70", "Ruy Lopez", "Morphy Defense"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "g8f6"), "C65", "Ruy Lopez", "Berlin Defense"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "f7f5"), "C63", "Ruy Lopez", "Schliemann Defense"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "d7d6"), "C62", "Ruy Lopez", "Old Steinitz Defense"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1b5"), "C60", "Ruy Lopez", ""),

    # -------------------------------------------------------------------------
    # Italian Game
    # -------------------------------------------------------------------------
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5", "c2c3", "g8f6", "d2d3"), "C53", "Italian Game", "Giuoco Pianissimo"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5", "c2c3", "g8f6", "d2d4"), "C54", "Italian Game", "Giuoco Piano, Main Line"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5", "b2b4"), "C51", "Evans Gambit", ""),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5"), "C50", "Italian Game", "Giuoco Piano"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "d2d4"), "C55", "Italian Game", "Two Knights, Modern Bishop's Opening"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "f3g5"), "C57", "Italian Game", "Two Knights, Fried Liver Attack Tension"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6"), "C55", "Italian Game", "Two Knights Defense"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8e7"), "C50", "Italian Game", "Hungarian Defense"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1c4"), "C50", "Italian Game", ""),

    # -------------------------------------------------------------------------
    # Scotch Game & Other 1. e4 e5
    # -------------------------------------------------------------------------
    (("e2e4", "e7e5", "g1f3", "b8c6", "d2d4", "e5d4", "f3d4", "f8c5"), "C45", "Scotch Game", "Classical Defense"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "d2d4", "e5d4", "f3d4", "g8f6"), "C45", "Scotch Game", "Schmidt Variation"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "d2d4", "e5d4", "c2c3"), "C44", "Scotch Game", "Göring Gambit"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "d2d4"), "C45", "Scotch Game", ""),
    (("e2e4", "e7e5", "g1f3", "b8c6", "b1c3", "g8f6"), "C47", "Four Knights Game", ""),
    (("e2e4", "e7e5", "g1f3", "g8f6"), "C42", "Petrov's Defense", ""),
    (("e2e4", "e7e5", "g1f3", "d7d6"), "C41", "Philidor Defense", ""),
    (("e2e4", "e7e5", "f2f4", "e5f4"), "C33", "King's Gambit Accepted", ""),
    (("e2e4", "e7e5", "f2f4"), "C30", "King's Gambit", ""),
    (("e2e4", "e7e5", "b1c3"), "C25", "Vienna Game", ""),
    (("e2e4", "e7e5", "d2d4", "e5d4", "d1d4"), "C21", "Center Game", ""),
    (("e2e4", "e7e5"), "C20", "Open Game", "King's Pawn"),

    # -------------------------------------------------------------------------
    # Sicilian Defense
    # -------------------------------------------------------------------------
    (("e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "a7a6", "c1e3"), "B90", "Sicilian Defense", "Najdorf, English Attack"),
    (("e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "a7a6", "c1g5"), "B95", "Sicilian Defense", "Najdorf, Main Line"),
    (("e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "a7a6"), "B90", "Sicilian Defense", "Najdorf Variation"),
    (("e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "g7g6", "c1e3", "f8g7", "f2f3"), "B75", "Sicilian Defense", "Dragon, Yugoslav Attack"),
    (("e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "g7g6"), "B70", "Sicilian Defense", "Dragon Variation"),
    (("e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "e7e6"), "B80", "Sicilian Defense", "Scheveningen Variation"),
    (("e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "b8c6"), "B56", "Sicilian Defense", "Classical Variation"),
    (("e2e4", "c7c5", "g1f3", "d7d6", "f1b5"), "B51", "Sicilian Defense", "Canal-Sokolsky Attack"),
    (("e2e4", "c7c5", "g1f3", "e7e6", "d2d4", "c5d4", "f3d4", "a7a6"), "B41", "Sicilian Defense", "Kan Variation"),
    (("e2e4", "c7c5", "g1f3", "e7e6", "d2d4", "c5d4", "f3d4", "b8c6"), "B44", "Sicilian Defense", "Taimanov Variation"),
    (("e2e4", "c7c5", "g1f3", "b8c6", "d2d4", "c5d4", "f3d4"), "B32", "Sicilian Defense", "Open"),
    (("e2e4", "c7c5", "c2c3"), "B22", "Sicilian Defense", "Alapin Variation"),
    (("e2e4", "c7c5", "b1c3"), "B23", "Sicilian Defense", "Closed"),
    (("e2e4", "c7c5", "d2d4", "c5d4", "c2c3"), "B21", "Sicilian Defense", "Smith-Morra Gambit"),
    (("e2e4", "c7c5"), "B20", "Sicilian Defense", ""),

    # -------------------------------------------------------------------------
    # French Defense
    # -------------------------------------------------------------------------
    (("e2e4", "e7e6", "d2d4", "d7d5", "b1c3", "f8b4"), "C15", "French Defense", "Winawer Variation"),
    (("e2e4", "e7e6", "d2d4", "d7d5", "b1c3", "g8f6"), "C11", "French Defense", "Classical Variation"),
    (("e2e4", "e7e6", "d2d4", "d7d5", "b1d2"), "C03", "French Defense", "Tarrasch Variation"),
    (("e2e4", "e7e6", "d2d4", "d7d5", "e4e5"), "C02", "French Defense", "Advance Variation"),
    (("e2e4", "e7e6", "d2d4", "d7d5", "e4d5"), "C01", "French Defense", "Exchange Variation"),
    (("e2e4", "e7e6"), "C00", "French Defense", ""),

    # -------------------------------------------------------------------------
    # Caro-Kann Defense
    # -------------------------------------------------------------------------
    (("e2e4", "c7c6", "d2d4", "d7d5", "b1c3", "d5e4", "c3e4", "c8f5"), "B18", "Caro-Kann Defense", "Classical Variation"),
    (("e2e4", "c7c6", "d2d4", "d7d5", "b1c3", "d5e4", "c3e4", "g8f6"), "B17", "Caro-Kann Defense", "Steinitz Variation"),
    (("e2e4", "c7c6", "d2d4", "d7d5", "e4e5", "c8f5"), "B12", "Caro-Kann Defense", "Advance Variation"),
    (("e2e4", "c7c6", "d2d4", "d7d5"), "B12", "Caro-Kann Defense", "Main Line"),
    (("e2e4", "c7c6", "d2d4", "d7d5", "e4d5", "c6d5", "c2c4"), "B13", "Caro-Kann Defense", "Panov-Botvinnik Attack"),
    (("e2e4", "c7c6", "d2d4", "d7d5", "e4d5", "c6d5"), "B13", "Caro-Kann Defense", "Exchange Variation"),
    (("e2e4", "c7c6"), "B10", "Caro-Kann Defense", ""),

    # -------------------------------------------------------------------------
    # Other Semi-Open Games (1. e4 ...)
    # -------------------------------------------------------------------------
    (("e2e4", "d7d5", "e4d5", "d8d5", "b1c3", "d5a5"), "B01", "Scandinavian Defense", "Mieses-Kotroc Variation"),
    (("e2e4", "d7d5", "e4d5", "g8f6"), "B01", "Scandinavian Defense", "Modern Variation"),
    (("e2e4", "d7d5"), "B01", "Scandinavian Defense", ""),
    (("e2e4", "g8f6", "e4e5", "f6d5"), "B02", "Alekhine's Defense", ""),
    (("e2e4", "d7d6", "d2d4", "g8f6", "b1c3", "g7g6"), "B07", "Pirc Defense", ""),
    (("e2e4", "g7g6"), "B06", "Modern Defense", ""),

    # -------------------------------------------------------------------------
    # Queen's Gambit & Closed Games (1. d4 d5 ...)
    # -------------------------------------------------------------------------
    (("d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "g8f6", "c1g5", "f8e7", "e2e3", "e8g8", "g1f3", "h7h6", "g5h4"), "D55", "Queen's Gambit Declined", "Orthodox Defense"),
    (("d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "g8f6", "c4d5", "e6d5"), "D35", "Queen's Gambit Declined", "Exchange Variation"),
    (("d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "g8f6", "g1f3", "c7c5"), "D40", "Queen's Gambit Declined", "Semi-Tarrasch Defense"),
    (("d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "c7c5"), "D32", "Queen's Gambit Declined", "Tarrasch Defense"),
    (("d2d4", "d7d5", "c2c4", "e7e6"), "D30", "Queen's Gambit Declined", ""),
    (("d2d4", "d7d5", "c2c4", "c7c6", "g1f3", "g8f6", "b1c3", "e7e6"), "D45", "Semi-Slav Defense", ""),
    (("d2d4", "d7d5", "c2c4", "c7c6", "g1f3", "g8f6", "b1c3", "d5c4"), "D15", "Slav Defense", "Main Line"),
    (("d2d4", "d7d5", "c2c4", "c7c6"), "D10", "Slav Defense", ""),
    (("d2d4", "d7d5", "c2c4", "d5c4"), "D20", "Queen's Gambit Accepted", ""),
    (("d2d4", "d7d5", "c2c4"), "D06", "Queen's Gambit", ""),
    (("d2d4", "d7d5", "c1f4"), "D00", "London System", ""),
    (("d2d4", "d7d5", "g1f3", "g8f6", "e2e3"), "D05", "Colle System", ""),
    (("d2d4", "d7d5"), "D00", "Queen's Pawn Game", ""),

    # -------------------------------------------------------------------------
    # Indian Defenses (1. d4 Nf6 ...)
    # -------------------------------------------------------------------------
    (("d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "f8g7", "e2e4", "d7d6", "g1f3", "e8g8", "f1e2", "e7e5"), "E97", "King's Indian Defense", "Classical Variation"),
    (("d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "f8g7", "e2e4", "d7d6", "f2f3"), "E81", "King's Indian Defense", "Sämisch Variation"),
    (("d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "f8g7", "e2e4", "d7d6"), "E70", "King's Indian Defense", "Main Line"),
    (("d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "d7d5"), "D85", "Grünfeld Defense", "Exchange Variation"),
    (("d2d4", "g8f6", "c2c4", "g7g6", "g1f3", "f8g7", "g2g3", "d7d5"), "D90", "Grünfeld Defense", ""),
    (("d2d4", "g8f6", "c2c4", "e7e6", "b1c3", "f8b4", "e2e3"), "E40", "Nimzo-Indian Defense", "Rubinstein System"),
    (("d2d4", "g8f6", "c2c4", "e7e6", "b1c3", "f8b4", "d1c2"), "E32", "Nimzo-Indian Defense", "Classical Variation"),
    (("d2d4", "g8f6", "c2c4", "e7e6", "b1c3", "f8b4"), "E20", "Nimzo-Indian Defense", ""),
    (("d2d4", "g8f6", "c2c4", "e7e6", "g1f3", "b7b6"), "E12", "Queen's Indian Defense", ""),
    (("d2d4", "g8f6", "c2c4", "e7e6", "g1f3", "c7c5", "d4d5"), "A60", "Modern Benoni", ""),
    (("d2d4", "g8f6", "c2c4", "c7c5", "d4d5", "b7b5"), "A57", "Benko Gambit", ""),
    (("d2d4", "g8f6", "c2c4", "e7e5"), "A51", "Budapest Gambit", ""),
    (("d2d4", "g8f6", "c1g5"), "A45", "Trompowsky Attack", ""),
    (("d2d4", "g8f6"), "A45", "Indian Defense", ""),

    # -------------------------------------------------------------------------
    # Flank Openings (1. c4, 1. Nf3, 1. f4, etc.)
    # -------------------------------------------------------------------------
    (("c2c4", "e7e5", "b1c3", "g8f6"), "A22", "English Opening", "King's English"),
    (("c2c4", "c7c5"), "A30", "English Opening", "Symmetrical Variation"),
    (("c2c4", "e7e5"), "A20", "English Opening", "King's English Variation"),
    (("c2c4",), "A10", "English Opening", ""),
    (("g1f3", "d7d5", "g2g3"), "A07", "King's Indian Attack", ""),
    (("g1f3", "d7d5", "c2c4"), "A09", "Réti Opening", ""),
    (("g1f3",), "A04", "Réti Opening", ""),
    (("f2f4", "d7d5"), "A03", "Bird's Opening", ""),
    (("f2f4",), "A02", "Bird's Opening", ""),
    (("b2b3",), "A01", "Nimzo-Larsen Attack", ""),
    (("d2d4", "f7f5"), "A80", "Dutch Defense", ""),
]

# Sort signatures from longest sequence to shortest to match most specific variation first
OPENING_SIGNATURES.sort(key=lambda s: len(s[0]), reverse=True)


def identify_opening_from_moves(uci_moves: List[str]) -> Optional[OpeningInfo]:
    """Identify the most specific ECO opening from a list of UCI move strings."""
    if not uci_moves:
        return None

    moves_tuple = tuple(uci_moves)
    for sig_moves, eco, name, var in OPENING_SIGNATURES:
        sig_len = len(sig_moves)
        if len(moves_tuple) >= sig_len and moves_tuple[:sig_len] == sig_moves:
            return OpeningInfo(
                eco=eco,
                name=name,
                variation=var,
                ply=len(moves_tuple),
            )

    return None


def is_opening_phase(board: chess.Board) -> bool:
    """
    Return True if the board is still in the opening phase.
    Criteria: Move count <= 15 and both sides maintain major material.
    """
    if board.fullmove_number > 15:
        return False
    pieces = board.piece_map()
    if len(pieces) < 22:
        return False
    return True
