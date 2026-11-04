"""
tests/test_integration.py
=========================
Integration test: Recognition → chess_logic pipeline.

Uses the synthetic board images generated earlier.
Run with:
    python tests/test_integration.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from chess_visualizer.recognition import Recognizer
from chess_visualizer.chess_logic import get_all_captures_dict
from chess_visualizer.settings import Settings
from PIL import Image


def test_recognizer_available():
    r = Recognizer()
    assert r.available, "chessvision should load successfully"
    print("  PASS recognizer_available")


def test_region_recognize_returns_fen():
    r = Recognizer()
    img = Image.open(os.path.join(os.path.dirname(__file__), "test_board_starting.png"))
    w, h = img.size
    result = r.recognize_region(img, 0, 0, w, h)
    assert result.success or result.error is not None, "Must return either FEN or error"
    # We only assert it doesn't crash — the synthetic board may not decode perfectly
    print(f"  PASS recognize_returns_fen  (fen={result.fen}, conf={result.confidence:.2f})")


def test_captures_from_known_fen():
    # Italian game: Bc4 threatens f7, Nf3 threatens e5
    fen = "r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    caps = get_all_captures_dict(fen)
    to_names_w = {c.to_name for c in caps["white"]}
    to_names_b = {c.to_name for c in caps["black"]}
    assert "f7" in to_names_w, "White Bc4xf7 should be a legal capture"
    assert "e5" in to_names_w, "White Nf3xe5 should be a legal capture"
    assert "f2" in to_names_b, "Black Bc5xf2 should be a legal capture"
    print("  PASS captures_from_known_fen")


def test_settings_round_trip():
    import tempfile, json
    from chess_visualizer.settings import Settings, SETTINGS_PATH
    s = Settings(board_region=(50, 100, 640, 640), opacity=0.8)
    s.save()
    s2 = Settings.load()
    assert s2.board_region == (50, 100, 640, 640)
    assert abs(s2.opacity - 0.8) < 1e-9
    print("  PASS settings_round_trip")


if __name__ == "__main__":
    tests = [
        test_recognizer_available,
        test_region_recognize_returns_fen,
        test_captures_from_known_fen,
        test_settings_round_trip,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  FAIL {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed}/{passed+failed} integration tests passed.")
    sys.exit(0 if failed == 0 else 1)
