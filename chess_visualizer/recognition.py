"""
recognition.py
==============
Board and piece recognition pipeline using chessvision.

Includes:
- Direct board recognition on cropped board images (no double-cropping).
- Move-indicator dot filtering on empty squares.
- Automatic or manual board orientation detection.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Tuple, List

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class RecognitionResult:
    """Output of a single recognition pass."""
    fen: Optional[str] = None
    board_box: Optional[Tuple[int, int, int, int]] = None
    flipped: bool = False
    confidence: float = 0.0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.fen is not None and self.error is None


# -------------------------------------------------------------------------
# Square preprocessing: Filter out move indicator dots & click artifacts
# -------------------------------------------------------------------------

def is_move_dot(sq_img: np.ndarray) -> bool:
    """
    Check if a square image contains a move indicator dot.

    On Chess.com / Lichess, empty squares that are legal destinations
    get a grey / translucent circle drawn in the exact center.
    This function uses edge detection: a move dot has a small circle of
    edges confined strictly to the center, while the outer 60% of the square
    has zero edges. Real chess pieces have edges spanning top to bottom.
    """
    h, w = sq_img.shape[:2]
    if min(h, w) < 16:
        return False

    gray = cv2.cvtColor(sq_img, cv2.COLOR_RGB2GRAY) if sq_img.ndim == 3 else sq_img
    edges = cv2.Canny(gray, 30, 90)

    cy, cx = h // 2, w // 2
    r = int(min(h, w) * 0.25)

    mask = np.ones_like(edges, dtype=bool)
    mask[cy - r : cy + r, cx - r : cx + r] = False

    outer_edges = np.count_nonzero(edges[mask])
    total_edges = np.count_nonzero(edges)

    return outer_edges < 15 and 20 <= total_edges < 150


def clean_square_image(sq_img: np.ndarray) -> Image.Image:
    """
    If a square has a move indicator dot, fill the center with the square's
    background color so the ONNX classifier sees a clean empty square.
    """
    if is_move_dot(sq_img):
        h, w = sq_img.shape[:2]
        corners = [
            sq_img[:max(2, h // 8), :max(2, w // 8)],
            sq_img[:max(2, h // 8), -max(2, w // 8):],
            sq_img[-max(2, h // 8):, :max(2, w // 8)],
            sq_img[-max(2, h // 8):, -max(2, w // 8):],
        ]
        bg_color = np.median(np.concatenate([c.reshape(-1, 3) for c in corners]), axis=0)

        cleaned = sq_img.copy()
        cy, cx = h // 2, w // 2
        cv2.circle(cleaned, (cx, cy), int(min(h, w) * 0.35), bg_color.tolist(), -1)
        return Image.fromarray(cleaned)

    return Image.fromarray(sq_img)


# -------------------------------------------------------------------------
# Recognizer
# -------------------------------------------------------------------------

class Recognizer:
    """Board and piece recognizer powered by chessvision."""

    def __init__(self) -> None:
        self._predictor = None
        self._classifier = None
        self._init()

    def _init(self) -> None:
        try:
            import chessvision
            from chessvision import PieceClassifier, BoardPredictor

            self._classifier = PieceClassifier()
            self._predictor = BoardPredictor(classifier=self._classifier)
            logger.info("chessvision loaded successfully.")
        except Exception as exc:
            logger.error("chessvision init failed: %s", exc)
            self._predictor = None
            self._classifier = None

    @property
    def available(self) -> bool:
        return self._predictor is not None

    def recognize_board(
        self,
        board_image: "np.ndarray | Image.Image",
        flipped: Optional[bool] = None,
    ) -> RecognitionResult:
        """
        Classify all 64 squares of an already-cropped chessboard image.

        Parameters
        ----------
        board_image : np.ndarray or PIL Image
            The cropped image containing the entire 8x8 chessboard.
        flipped : bool or None
            If None, orientation is automatically detected from piece positions.
            If True/False, forces Black/White perspective.
        """
        if self._predictor is None:
            return RecognitionResult(error="chessvision is not initialized")

        try:
            pil_board = _to_pil(board_image)
            bw, bh = pil_board.size

            if bw < 40 or bh < 40:
                return RecognitionResult(error=f"Image too small: {bw}x{bh}")

            import chessvision
            from chessvision import Orientation

            sq_w = bw / 8.0
            sq_h = bh / 8.0

            square_images: List[Image.Image] = []
            for row in range(8):
                for col in range(8):
                    crop_box = (
                        int(round(col * sq_w)),
                        int(round(row * sq_h)),
                        int(round((col + 1) * sq_w)),
                        int(round((row + 1) * sq_h)),
                    )
                    sq_pil = pil_board.crop(crop_box)
                    sq_np = np.array(sq_pil)

                    # Clean move dots and click artifacts
                    cleaned_sq = clean_square_image(sq_np)
                    square_images.append(cleaned_sq)

            # Classify all 64 squares
            predictions = self._classifier.predict_squares(square_images)
            avg_confidence = float(np.mean([p.confidence for p in predictions]))

            # Orientation
            if flipped is None:
                orientation = self._predictor._infer_orientation(predictions)
            else:
                orientation = Orientation.BLACK if flipped else Orientation.WHITE

            is_flipped = (orientation is Orientation.BLACK)

            # Map predictions to square coordinates
            square_map = dict(zip(orientation.grid_coordinates, predictions, strict=True))

            # Build FEN
            fen = self._predictor.fen(square_map=square_map, active_color=chessvision.Turn.AUTO)

            return RecognitionResult(
                fen=fen,
                board_box=(0, 0, bw, bh),
                flipped=is_flipped,
                confidence=avg_confidence,
            )

        except Exception as exc:
            logger.error("Recognition exception: %s", exc)
            return RecognitionResult(error=str(exc))

    # Backward compatibility
    def recognize_region(
        self,
        image: "np.ndarray | Image.Image",
        left: int = 0,
        top: int = 0,
        width: int = 0,
        height: int = 0,
        flipped: Optional[bool] = None,
    ) -> RecognitionResult:
        pil = _to_pil(image)
        # Only crop if caller passed a full screenshot where image is larger than region
        if width > 0 and height > 0 and (pil.width > width + 10 or pil.height > height + 10):
            pil = pil.crop((left, top, left + width, top + height))
        return self.recognize_board(pil, flipped=flipped)


def _to_pil(image: "np.ndarray | Image.Image") -> Image.Image:
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    if isinstance(image, np.ndarray):
        if image.ndim == 3 and image.shape[2] == 4:
            return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGRA2RGB))
        elif image.ndim == 3 and image.shape[2] == 3:
            return Image.fromarray(image)
        elif image.ndim == 2:
            return Image.fromarray(image).convert("RGB")
    raise TypeError(f"Unsupported image type: {type(image)}")
