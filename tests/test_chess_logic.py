"""
tests/test_chess_logic.py
=========================
Unit tests for the chess_logic module.
Tests both occupied-only captures and capture squares including empty squares.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import chess
from chess_visualizer.chess_logic import (
    get_all_captures,
    get_all_captures_dict,
    get_legal_captures,
    CaptureMove,
)


def capture_pairs(captures):
    """Return a set of (from_name, to_name) tuples."""
    return {(c.from_name, c.to_name) for c in captures}


# ---------------------------------------------------------------------------
# Occupied-only captures (include_empty=False)
# ---------------------------------------------------------------------------

def test_starting_position_no_occupied_captures():
    result = get_all_captures_dict(chess.STARTING_FEN, include_empty=False)
    assert result["white"] == [], "White should have no occupied captures from starting position"
    assert result["black"] == [], "Black should have no occupied captures from starting position"


def test_one_white_capture():
    # White pawn on e4, Black pawn on d5
    board = chess.Board("8/8/8/3p4/4P3/8/8/4K1k1 w - - 0 1")
    result = get_all_captures_dict(board, include_empty=False)
    assert ("e4", "d5") in capture_pairs(result["white"]), "White pawn e4->d5 not found"
    assert ("d5", "e4") in capture_pairs(result["black"]), "Black pawn d5->e4 not found"


# ---------------------------------------------------------------------------
# Pin: pinned piece may NOT capture off its pin ray
# ---------------------------------------------------------------------------

def test_pinned_piece_excluded():
    # White King on e1, White Queen on e3, Black Rook on e8.
    # Queen is pinned along the e-file.
    # Queen cannot capture off the e-file (e.g. d4, f4, c5 are illegal).
    # Queen can capture on the e-file (e2..e8).
    board = chess.Board("4r3/8/8/8/8/4Q3/8/4K3 w - - 0 1")
    white_caps = get_legal_captures(board, chess.WHITE, include_empty=True)

    # Any capture starting from e3 MUST have to_sq on the e-file (file index 4)
    for c in white_caps:
        if c.from_name == "e3":
            assert c.to_name.startswith("e"), f"Pinned queen made off-axis move to {c.to_name}"


# ---------------------------------------------------------------------------
# En passant
# ---------------------------------------------------------------------------

def test_en_passant_white():
    board = chess.Board("8/8/8/3pP3/8/8/8/4K1k1 w - d6 0 1")
    white_caps = get_legal_captures(board, chess.WHITE, include_empty=False)
    ep_caps = [c for c in white_caps if c.is_en_passant]
    assert len(ep_caps) == 1
    assert ep_caps[0].from_name == "e5"
    assert ep_caps[0].to_name == "d6"


def test_en_passant_black():
    board = chess.Board("4k3/8/8/8/3pP3/8/8/4K3 b - e3 0 1")
    black_caps = get_legal_captures(board, chess.BLACK, include_empty=False)
    ep_caps = [c for c in black_caps if c.is_en_passant]
    assert len(ep_caps) == 1
    assert ep_caps[0].from_name == "d4"
    assert ep_caps[0].to_name == "e3"


def test_no_en_passant_when_unavailable():
    board = chess.Board("8/8/8/3pP3/8/8/8/4K1k1 w - - 0 1")
    white_caps = get_legal_captures(board, chess.WHITE, include_empty=False)
    ep_caps = [c for c in white_caps if c.is_en_passant]
    assert len(ep_caps) == 0


# ---------------------------------------------------------------------------
# Multiple attackers on same target
# ---------------------------------------------------------------------------

def test_multiple_attackers_same_target():
    # Bishop on b1 and Knight on f2 both attack e4
    board = chess.Board("8/8/8/8/4p3/8/5N2/1B2K1k1 w - - 0 1")
    white_caps = get_legal_captures(board, chess.WHITE, include_empty=False)
    targets_on_e4 = [c for c in white_caps if c.to_name == "e4"]
    assert len(targets_on_e4) >= 2


# ---------------------------------------------------------------------------
# Capture squares including empty squares (Rule #5)
# ---------------------------------------------------------------------------

def test_empty_capture_squares():
    # White pawn on e4: can capture diagonally onto d5 and f5 even if empty
    # Pawn cannot capture onto e5 (forward push is not a capture)
    board = chess.Board("8/8/8/8/4P3/8/8/4K1k1 w - - 0 1")
    caps = get_legal_captures(board, chess.WHITE, include_empty=True)
    targets = {c.to_name for c in caps if c.from_name == "e4"}
    assert "d5" in targets, "e4 pawn must be able to capture on d5"
    assert "f5" in targets, "e4 pawn must be able to capture on f5"
    assert "e5" not in targets, "e4 pawn cannot capture forward onto e5"


def test_color_separation():
    board = chess.Board("8/8/8/3p4/4P3/8/8/4K1k1 w - - 0 1")
    result = get_all_captures_dict(board)
    for c in result["white"]:
        assert c.color == chess.WHITE
    for c in result["black"]:
        assert c.color == chess.BLACK


def test_capture_move_names():
    cm = CaptureMove(color=chess.WHITE, from_sq=chess.E4, to_sq=chess.D5, is_occupied=True)
    assert cm.from_name == "e4"
    assert cm.to_name == "d5"
    assert cm.color_name == "White"
    assert "[x]" in str(cm)


if __name__ == "__main__":
    tests = [
        test_starting_position_no_occupied_captures,
        test_one_white_capture,
        test_pinned_piece_excluded,
        test_en_passant_white,
        test_en_passant_black,
        test_no_en_passant_when_unavailable,
        test_multiple_attackers_same_target,
        test_empty_capture_squares,
        test_color_separation,
        test_capture_move_names,
    ]

    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL {t.__name__}: {e}")
            failed += 1

    print(f"\n{passed}/{passed + failed} tests passed.")
    sys.exit(0 if failed == 0 else 1)
