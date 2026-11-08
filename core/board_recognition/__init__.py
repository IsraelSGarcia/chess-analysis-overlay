"""
core.board_recognition
======================
Computer vision infrastructure for screen capture, chessboard identification,
and piece classification.
"""

from .capture import ScreenCapture, set_window_capture_exclusion, is_black_image
from .recognition import (
    detect_chessboard_fullscreen,
    detect_chessboard_in_crop,
    RecognitionResult,
    Recognizer,
)
from .calibration import CalibrationWidget

find_chessboard = detect_chessboard_fullscreen
BoardDetectionResult = RecognitionResult
CalibrationDialog = CalibrationWidget

__all__ = [
    "ScreenCapture",
    "set_window_capture_exclusion",
    "is_black_image",
    "detect_chessboard_fullscreen",
    "detect_chessboard_in_crop",
    "find_chessboard",
    "RecognitionResult",
    "BoardDetectionResult",
    "Recognizer",
    "CalibrationWidget",
    "CalibrationDialog",
]
