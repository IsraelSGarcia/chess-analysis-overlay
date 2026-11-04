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
# Auto-Snapping: Chessboard outer boundary & internal grid line detection
# -------------------------------------------------------------------------

def refine_grid_box(
    gray_img: np.ndarray,
    init_x: int,
    init_y: int,
    init_w: int,
    init_h: int,
    search_radius: int = 14,
) -> Tuple[int, int, int, int]:
    """
    Sub-pixel/pixel grid alignment: Maximizes contrast along the 7 internal
    checkerboard square division lines to align perfectly with the 8x8 squares.
    """
    gh, gw = gray_img.shape
    if init_w < 40 or init_h < 40 or gray_img.std() < 5.0:
        return (init_x, init_y, init_w, init_h)

    pad = search_radius + 4
    x0 = max(0, init_x - pad)
    y0 = max(0, init_y - pad)
    x1 = min(gw, init_x + init_w + pad)
    y1 = min(gh, init_y + init_h + pad)

    sub = gray_img[y0:y1, x0:x1].astype(np.float32)
    if sub.shape[0] < 30 or sub.shape[1] < 30:
        return (init_x, init_y, init_w, init_h)

    dy = np.abs(sub[1:, :] - sub[:-1, :])
    dx = np.abs(sub[:, 1:] - sub[:, :-1])

    rel_x = init_x - x0
    rel_y = init_y - y0
    slice_dy = dy[:, max(0, rel_x) : min(sub.shape[1], rel_x + init_w)]
    row_means_y = np.mean(slice_dy, axis=1) if slice_dy.size > 0 else np.zeros(dy.shape[0])

    best_y, best_h, max_y = init_y, init_h, -1.0
    for dy_off in range(-search_radius, search_radius + 1):
        cy = rel_y + dy_off
        if cy < 0:
            continue
        for dh_off in range(-search_radius, search_radius + 1):
            ch = init_h + dh_off
            if ch < 40:
                continue
            max_line_y = cy + int(round(7 * ch / 8.0)) - 1
            if max_line_y >= len(row_means_y):
                continue
            idx = (cy + np.round(np.arange(1, 8) * (ch / 8.0)) - 1).astype(int)
            sc = float(np.sum(row_means_y[idx]))
            if sc > max_y:
                max_y = sc
                best_y = y0 + cy
                best_h = ch

    rel_y_best = best_y - y0
    slice_dx = dx[max(0, rel_y_best) : min(sub.shape[0], rel_y_best + best_h), :]
    col_means_x = np.mean(slice_dx, axis=0) if slice_dx.size > 0 else np.zeros(dx.shape[1])

    best_x, best_w, max_x = init_x, init_w, -1.0
    for dx_off in range(-search_radius, search_radius + 1):
        cx = rel_x + dx_off
        if cx < 0:
            continue
        for dw_off in range(-search_radius, search_radius + 1):
            cw = init_w + dw_off
            if cw < 40:
                continue
            max_line_x = cx + int(round(7 * cw / 8.0)) - 1
            if max_line_x >= len(col_means_x):
                continue
            idx = (cx + np.round(np.arange(1, 8) * (cw / 8.0)) - 1).astype(int)
            sc = float(np.sum(col_means_x[idx]))
            if sc > max_x:
                max_x = sc
                best_x = x0 + cx
                best_w = cw

    best_s = (best_w + best_h) // 2
    return (best_x, best_y, best_s, best_s)


def detect_chessboard_in_crop(
    crop_pil: Image.Image,
    rough_box_in_crop: Optional[Tuple[int, int, int, int]] = None,
) -> Optional[Tuple[int, int, int, int]]:
    """
    Detect the exact 8x8 chessboard outer boundary within an image crop.

    Uses chessvision.BoardDetector to identify the board and refines
    the boundaries against the internal 8x8 grid line transitions.
    Falls back to OpenCV contour detection if BoardDetector finds no candidate.

    Parameters
    ----------
    crop_pil : PIL.Image.Image
        The cropped image around the chessboard (in raw pixels).
    rough_box_in_crop : tuple of (x, y, w, h) or None
        Expected rough location of the board within the crop image.

    Returns
    -------
    (x, y, w, h) in crop pixel coordinates, or None if no board was detected.
    """
    crop_arr = np.array(crop_pil)
    gray = cv2.cvtColor(crop_arr, cv2.COLOR_RGB2GRAY) if crop_arr.ndim == 3 else crop_arr

    # 1. Primary: chessvision BoardDetector
    try:
        from chessvision import BoardDetector
        detector = BoardDetector()
        candidates = detector.detect(crop_pil)
        if candidates:
            if rough_box_in_crop is not None:
                rx, ry, rw, rh = rough_box_in_crop
                rcx, rcy = rx + rw / 2.0, ry + rh / 2.0
                candidates.sort(key=lambda c: (
                    (c.box[0] + c.box[2] / 2.0 - rcx) ** 2 +
                    (c.box[1] + c.box[3] / 2.0 - rcy) ** 2
                ))
            bx, by, bw, bh = candidates[0].box
            refined = refine_grid_box(gray, bx, by, bw, bh)
            return refined
    except Exception as exc:
        logger.debug("BoardDetector detection failed: %s", exc)

    # 2. Secondary fallback: OpenCV Canny edge + square contour
    gh, gw = gray.shape
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 30, 120)
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    cnt_candidates = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w < gw * 0.3 or h < gh * 0.3:
            continue
        aspect = w / float(h)
        if 0.82 <= aspect <= 1.18:
            hull = cv2.convexHull(cnt)
            if cv2.contourArea(hull) / (w * h) > 0.65:
                cnt_candidates.append((w * h, (x, y, w, h)))

    if cnt_candidates:
        cnt_candidates.sort(key=lambda c: c[0], reverse=True)
        cbx, cby, cbw, cbh = cnt_candidates[0][1]
        refined = refine_grid_box(gray, cbx, cby, cbw, cbh)
        return refined

    return None


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
