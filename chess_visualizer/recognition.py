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

import chess
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
    active_turn: Optional[bool] = None

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
    receive a translucent circle in the exact geometric center.
    This function analyzes radial symmetry, edge distribution, and color
    contrast. For an empty square with a move dot, features are strictly
    confined to the center (radius < 0.25), while the outer margin and corners
    are uniform board background without piece bases or contours.
    """
    h, w = sq_img.shape[:2]
    min_dim = min(h, w)
    if min_dim < 16:
        return False

    # 1. Background color and variance from 4 corners
    cw = max(3, int(w * 0.12))
    ch = max(3, int(h * 0.12))
    corners = np.concatenate([
        sq_img[:ch, :cw].reshape(-1, 3),
        sq_img[:ch, -cw:].reshape(-1, 3),
        sq_img[-ch:, :cw].reshape(-1, 3),
        sq_img[-ch:, -cw:].reshape(-1, 3),
    ])
    bg_color = np.median(corners, axis=0)

    # 2. Radial distance from geometric center
    y, x = np.ogrid[:h, :w]
    cy, cx = h / 2.0, w / 2.0
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)

    center_mask = dist <= (min_dim * 0.22)
    outer_mask = dist >= (min_dim * 0.32)

    # Color difference from background
    diff = np.linalg.norm(sq_img.astype(float) - bg_color.astype(float), axis=2)
    center_diff = float(np.mean(diff[center_mask]))
    outer_diff = float(np.mean(diff[outer_mask]))
    bottom_diff = float(np.mean(diff[int(h * 0.78):int(h * 0.95), int(w * 0.20):int(w * 0.80)]))
    top_diff = float(np.mean(diff[int(h * 0.08):int(h * 0.25), int(w * 0.25):int(w * 0.75)]))

    # Real chess pieces possess wide bases at the bottom and significant outer contours
    if bottom_diff > 18.0 or outer_diff > 18.0:
        return False

    # Criterion A: Radial color contrast shift in center with pristine periphery
    if center_diff >= 6.0 and center_diff > 1.8 * outer_diff and bottom_diff < 12.0 and top_diff < 12.0:
        return True

    # Criterion B: Resolution-scaled edge concentration in center circle
    gray = cv2.cvtColor(sq_img, cv2.COLOR_RGB2GRAY) if sq_img.ndim == 3 else sq_img
    edges = cv2.Canny(gray, 25, 75)

    center_edges = np.count_nonzero(edges[center_mask])
    outer_edges = np.count_nonzero(edges[outer_mask])
    total_edges = np.count_nonzero(edges)

    if total_edges >= max(8, int(min_dim * 0.2)) and outer_edges <= max(15, int(0.015 * h * w)):
        if center_edges >= 0.55 * total_edges:
            return True

    return False


def strip_overlay_artifacts(img_rgb: np.ndarray) -> np.ndarray:
    """
    Remove visualizer overlay arrows before piece classification or turn detection.
    Overlay annotations use ultra-saturated neon colors (Gold #FFE600, Green #00E676,
    Purple #D500F9, Red #FF1744, Orange #FF6D00) with saturation >= 215.
    Authentic Chess.com / Lichess square highlights have saturation <= 165 and are strictly preserved.
    """
    if img_rgb.ndim != 3 or img_rgb.shape[2] != 3:
        return img_rgb
    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    overlay_mask = (sat >= 215) & (val >= 120)
    if np.any(overlay_mask):
        return cv2.inpaint(img_rgb, overlay_mask.astype(np.uint8), 3, cv2.INPAINT_TELEA)
    return img_rgb


def clean_square_image(sq_img: np.ndarray) -> Image.Image:
    """
    Strip visualizer overlay artifacts and move indicator dots so the ONNX
    classifier sees clean, unmodified chess pieces.
    """
    cleaned = strip_overlay_artifacts(sq_img)
    if is_move_dot(cleaned):
        cleaned = cleaned.copy()
        h, w = cleaned.shape[:2]
        corners = [
            cleaned[:max(2, h // 8), :max(2, w // 8)],
            cleaned[:max(2, h // 8), -max(2, w // 8):],
            cleaned[-max(2, h // 8):, :max(2, w // 8)],
            cleaned[-max(2, h // 8):, -max(2, w // 8):],
        ]
        bg_color = np.median(np.concatenate([c.reshape(-1, 3) for c in corners]), axis=0)

        cy, cx = h // 2, w // 2
        cv2.circle(cleaned, (cx, cy), int(min(h, w) * 0.35), bg_color.tolist(), -1)
    return Image.fromarray(cleaned)


# -------------------------------------------------------------------------
# Turn Detection: Last-Move Square Highlights Analysis
# -------------------------------------------------------------------------

def could_piece_reach_from(piece: chess.Piece, from_sq: chess.Square, to_sq: chess.Square) -> bool:
    """Return True if piece on to_sq could plausibly have moved from from_sq."""
    df = abs(chess.square_file(to_sq) - chess.square_file(from_sq))
    dr = abs(chess.square_rank(to_sq) - chess.square_rank(from_sq))
    if df == 0 and dr == 0:
        return False
    pt = piece.piece_type
    if pt == chess.PAWN:
        if piece.color == chess.WHITE:
            return df <= 1 and 1 <= (chess.square_rank(to_sq) - chess.square_rank(from_sq)) <= 2
        else:
            return df <= 1 and 1 <= (chess.square_rank(from_sq) - chess.square_rank(to_sq)) <= 2
    elif pt == chess.KNIGHT:
        return (df == 1 and dr == 2) or (df == 2 and dr == 1)
    elif pt == chess.BISHOP:
        return df == dr
    elif pt == chess.ROOK:
        return df == 0 or dr == 0
    elif pt == chess.QUEEN:
        return df == dr or df == 0 or dr == 0
    elif pt == chess.KING:
        return max(df, dr) == 1
    return False


def detect_active_turn(
    board_image: "np.ndarray | Image.Image",
    board: chess.Board,
    flipped: bool = False,
    threshold: float = 16.0,
    current_turn: Optional[bool] = None,
) -> bool:
    """
    Detect whose turn it is to move by analyzing the last-move square highlights
    (e.g., Chess.com olive/yellow tint or Lichess green/yellow tint).

    Identifies the from-square (now empty) and to-square (contains the piece that just moved),
    and determines that the player whose turn it is to move is the OPPOSITE color.

    Parameters
    ----------
    board_image : np.ndarray or PIL.Image
        The cropped image of the 8x8 chessboard.
    board : chess.Board
        The recognized chess position.
    flipped : bool
        True if Black is at the bottom.
    threshold : float
        Minimum color deviation threshold for highlight detection.
    current_turn : Optional[bool]
        Previously established turn to preserve when no move highlights are detected.

    Returns
    -------
    bool:
        chess.WHITE (True) or chess.BLACK (False).
    """
    try:
        # Fundamental Chess Invariant: A King in check MUST move.
        # In chess, a side can NEVER be to move if the opponent's king is under attack.
        # Checking this first guarantees that website check animations (pulsing red squares)
        # never corrupt or cycle active turn detection.
        wk = board.king(chess.WHITE)
        bk = board.king(chess.BLACK)
        w_in_check = bool(board.attackers(chess.BLACK, wk)) if wk is not None else False
        b_in_check = bool(board.attackers(chess.WHITE, bk)) if bk is not None else False

        if b_in_check and not w_in_check:
            return chess.BLACK
        if w_in_check and not b_in_check:
            return chess.WHITE

        pil_board = _to_pil(board_image)
        bw, bh = pil_board.size
        sq_w = bw / 8.0
        sq_h = bh / 8.0
        # Inpaint any overlay artifacts before measuring square colors
        arr = strip_overlay_artifacts(np.array(pil_board))

        square_samples = []

        for r in range(8):
            for c in range(8):
                x1 = int(round(c * sq_w))
                y1 = int(round(r * sq_h))
                x2 = int(round((c + 1) * sq_w))
                y2 = int(round((r + 1) * sq_h))
                sw = x2 - x1
                sh = y2 - y1

                # Sample an inner perimeter ring (10% to 22% from edge):
                # avoids the piece in center and avoids coordinate text in extreme corners
                in_1 = max(1, int(sw * 0.10))
                in_2 = max(2, int(sw * 0.22))

                top_strip = arr[y1 + in_1 : y1 + in_2, x1 + in_1 : x2 - in_1]
                bottom_strip = arr[y2 - in_2 : y2 - in_1, x1 + in_1 : x2 - in_1]
                left_strip = arr[y1 + in_1 : y2 - in_1, x1 + in_1 : x1 + in_2]
                right_strip = arr[y1 + in_1 : y2 - in_1, x2 - in_2 : x2 - in_1]

                pts = np.concatenate([
                    top_strip.reshape(-1, 3),
                    bottom_strip.reshape(-1, 3),
                    left_strip.reshape(-1, 3),
                    right_strip.reshape(-1, 3),
                ])
                med = np.median(pts, axis=0)

                # Map grid (r, c) to chess.Square taking orientation into account
                file_idx = (7 - c) if flipped else c
                rank_idx = r if flipped else (7 - r)
                sq = chess.square(file_idx, rank_idx)
                is_light = (file_idx + rank_idx) % 2 != 0

                square_samples.append((sq, is_light, med))

        # Baseline median colors for light and dark squares
        light_meds = np.array([col for _, is_l, col in square_samples if is_l])
        dark_meds = np.array([col for _, is_l, col in square_samples if not is_l])

        if light_meds.size == 0 or dark_meds.size == 0:
            return current_turn if current_turn is not None else chess.WHITE

        base_light = np.median(light_meds, axis=0)
        base_dark = np.median(dark_meds, axis=0)

        # Measure color deviation from baseline for every square
        deviations = []
        for sq, is_l, col in square_samples:
            base = base_light if is_l else base_dark
            delta = float(np.linalg.norm(col - base))
            deviations.append((delta, sq))

        deviations.sort(reverse=True, key=lambda x: x[0])
        sig_squares = [item for item in deviations if item[0] >= threshold]

        # 1. Clean Two-Square Move Highlight (from-square and to-square)
        if len(sig_squares) >= 2:
            third_delta = deviations[2][0] if len(deviations) > 2 else 0.0
            # Ensure top two are significantly higher than background / 3rd square
            if third_delta < 0.80 * deviations[1][0] or (deviations[1][0] - third_delta) >= 6.0:
                sq_a = deviations[0][1]
                sq_b = deviations[1][1]

                piece_a = board.piece_at(sq_a)
                piece_b = board.piece_at(sq_b)

                if piece_a is not None and piece_b is None:
                    # piece_a arrived at sq_a -> opposite color moves now
                    return not piece_a.color
                elif piece_b is not None and piece_a is None:
                    # piece_b arrived at sq_b -> opposite color moves now
                    return not piece_b.color
                elif piece_a is not None and piece_b is not None:
                    # Both occupied (e.g., castling)
                    if piece_a.color == piece_b.color:
                        return not piece_a.color

        # 2. Move Highlight + Clicked/Selected Piece (3 to 5 highlighted squares)
        # e.g., Origin empty square, destination moved piece, and player clicked a piece to move
        if 3 <= len(sig_squares) <= 5:
            empty_sqs = [item[1] for item in sig_squares if board.piece_at(item[1]) is None]
            occ_sqs = [item[1] for item in sig_squares if board.piece_at(item[1]) is not None]

            if len(empty_sqs) == 1 and len(occ_sqs) >= 1:
                from_sq = empty_sqs[0]
                for dest_sq in occ_sqs:
                    p = board.piece_at(dest_sq)
                    if p and could_piece_reach_from(p, from_sq, dest_sq):
                        # p arrived from from_sq; active turn is opposite of moved piece
                        return not p.color

        # 3. Single Selected Piece Highlight (e.g. user clicked piece at game start or idle board)
        if len(sig_squares) == 1:
            sq = sig_squares[0][1]
            p = board.piece_at(sq)
            if p is not None:
                # On Chess.com / Lichess a user can only select pieces of their own color on their turn
                return p.color

        # Fallback: preserve established active turn, or default to White
        if current_turn is not None:
            return current_turn

        return chess.WHITE
    except Exception as exc:
        logger.debug("Turn detection fallback: %s", exc)
        return current_turn if current_turn is not None else chess.WHITE


# -------------------------------------------------------------------------
# Auto-Snapping: Chessboard outer boundary & internal grid line detection
# -------------------------------------------------------------------------

def refine_grid_box(
    gray_img: np.ndarray,
    init_x: int,
    init_y: int,
    init_w: int,
    init_h: int,
    max_drift: int = 40,
) -> Tuple[int, int, int, int]:
    """
    Sub-pixel/pixel grid alignment: Maximizes contrast along the 7 internal
    checkerboard square division lines to align perfectly with the 8x8 squares.
    Searches up to max_drift pixels in x, y, and size s using vectorized 1D profiles,
    guaranteeing instant (sub-100ms) snapping that robustly recovers from chopped ranks,
    evaluation bars (Lichess/Chess.com), and exterior coordinate margins.
    """
    gh, gw = gray_img.shape[:2]
    init_s = (init_w + init_h) // 2
    if init_s < 40 or gray_img.std() < 5.0:
        return (init_x, init_y, init_s, init_s)

    dy = np.abs(gray_img[1:, :].astype(np.float32) - gray_img[:-1, :].astype(np.float32))
    dx = np.abs(gray_img[:, 1:].astype(np.float32) - gray_img[:, :-1].astype(np.float32))

    search_drift = min(max_drift, max(8, int(round(init_s * 0.08))))

    y_min = max(0, init_y - search_drift)
    y_max = min(gh, init_y + init_s + search_drift)
    x_min = max(0, init_x - search_drift)
    x_max = min(gw, init_x + init_s + search_drift)

    col_profile = np.mean(dx[y_min:y_max, :], axis=0)
    row_profile = np.mean(dy[:, x_min:x_max], axis=1)

    s_min = max(40, init_s - search_drift)
    s_max = min(min(gw, gh), init_s + search_drift)

    # Base score for initial box
    init_grid = (np.round(np.arange(1, 8) * (init_s / 8.0)) - 1).astype(int)
    init_x_lines = init_x + init_grid
    init_y_lines = init_y + init_grid
    v_base = float(np.mean(col_profile[init_x_lines])) if init_x_lines[-1] < len(col_profile) else 0.0
    h_base = float(np.mean(row_profile[init_y_lines])) if init_y_lines[-1] < len(row_profile) else 0.0
    best_score = v_base + h_base
    best_box = (init_x, init_y, init_s, init_s)

    for s in range(s_min, s_max + 1):
        grid_offsets = (np.round(np.arange(1, 8) * (s / 8.0)) - 1).astype(int)

        x_cands = np.arange(max(0, init_x - search_drift), min(gw - s, init_x + search_drift + 1))
        if len(x_cands) == 0:
            continue
        x_lines = x_cands[:, None] + grid_offsets[None, :]
        valid_x = (x_lines >= 0) & (x_lines < len(col_profile))
        x_scores = np.mean(np.where(valid_x, col_profile[np.clip(x_lines, 0, len(col_profile) - 1)], 0.0), axis=1)

        best_x_idx = np.argmax(x_scores)
        best_x = x_cands[best_x_idx]
        best_v = x_scores[best_x_idx]

        y_cands = np.arange(max(0, init_y - search_drift), min(gh - s, init_y + search_drift + 1))
        if len(y_cands) == 0:
            continue
        y_lines = y_cands[:, None] + grid_offsets[None, :]
        valid_y = (y_lines >= 0) & (y_lines < len(row_profile))
        y_scores = np.mean(np.where(valid_y, row_profile[np.clip(y_lines, 0, len(row_profile) - 1)], 0.0), axis=1)

        best_y_idx = np.argmax(y_scores)
        best_y = y_cands[best_y_idx]
        best_h = y_scores[best_y_idx]

        total_sc = best_v + best_h
        penalty = 0.03 * (abs(best_x - init_x) + abs(best_y - init_y) + abs(s - init_s))
        score = total_sc - penalty

        if score > best_score:
            best_score = score
            best_box = (int(best_x), int(best_y), int(s), int(s))

    return best_box


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

    # 2. Secondary fallback: OpenCV Canny edge + checkerboard pattern verification
    try:
        from chessvision.detector import BoardDetector
        det = BoardDetector()

        gh, gw = gray.shape
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 30, 120)
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        scored_candidates = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w < gw * 0.3 or h < gh * 0.3:
                continue
            aspect = w / float(h)
            if 0.82 <= aspect <= 1.18:
                hull = cv2.convexHull(cnt)
                if cv2.contourArea(hull) / (w * h) > 0.65:
                    sub = gray[y : y + h, x : x + w]
                    score = det._is_8x8_board(sub)
                    if score is not None and score >= 20.0:
                        scored_candidates.append((score, (x, y, w, h)))

        if scored_candidates:
            scored_candidates.sort(key=lambda c: c[0], reverse=True)
            cbx, cby, cbw, cbh = scored_candidates[0][1]
            return refine_grid_box(gray, cbx, cby, cbw, cbh)
    except Exception as exc:
        logger.debug("Secondary crop detection failed: %s", exc)

    return None


def detect_chessboard_fullscreen(
    screen_pil: Image.Image,
    min_size: int = 200,
    max_size: int = 1600,
) -> Optional[Tuple[int, int, int, int]]:
    """
    Scan a full-screen desktop screenshot to detect the location of a chessboard.

    Combines chessvision.BoardDetector with multi-contour checkerboard pattern
    verification and sub-pixel grid boundary refinement.
    Returns (phys_x, phys_y, phys_w, phys_h) in image pixels, or None if no board is found.
    """
    arr = np.array(screen_pil)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY) if arr.ndim == 3 else arr

    # 1. Primary: chessvision BoardDetector
    try:
        from chessvision import BoardDetector
        detector = BoardDetector()
        candidates = detector.detect(screen_pil)
        if candidates:
            valid = []
            for c in candidates:
                bx, by, bw, bh = c.box
                if min_size <= bw <= max_size and min_size <= bh <= max_size:
                    aspect = bw / float(bh)
                    if 0.85 <= aspect <= 1.15:
                        valid.append(c)
            if valid:
                valid.sort(key=lambda c: getattr(c, 'score', 0.0), reverse=True)
                best_box = valid[0].box
                return refine_grid_box(gray, best_box[0], best_box[1], best_box[2], best_box[3])
    except Exception as exc:
        logger.debug("Full-screen BoardDetector failed: %s", exc)

    # 2. Secondary: OpenCV Canny + Contour checkerboard pattern detection
    try:
        from chessvision.detector import BoardDetector
        det = BoardDetector()

        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 30, 120)
        dilated = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        scored_candidates = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if min_size <= w <= max_size and min_size <= h <= max_size:
                aspect = w / float(h)
                if 0.85 <= aspect <= 1.15:
                    sub = gray[y : y + h, x : x + w]
                    score = det._is_8x8_board(sub)
                    if score is not None and score >= 20.0:
                        scored_candidates.append((score, (x, y, w, h)))

        if scored_candidates:
            scored_candidates.sort(key=lambda item: item[0], reverse=True)
            best_box = scored_candidates[0][1]
            return refine_grid_box(gray, best_box[0], best_box[1], best_box[2], best_box[3])
    except Exception as exc:
        logger.debug("Secondary contour checkerboard search failed: %s", exc)

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
        current_turn: Optional[bool] = None,
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
        current_turn : bool or None
            Previously active turn to maintain if no new move highlights are observed.
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

            # Determine active turn from last-move square highlights
            active_turn = None
            if fen:
                try:
                    parsed_board = chess.Board(fen)
                    active_turn = detect_active_turn(pil_board, parsed_board, flipped=is_flipped, current_turn=current_turn)
                    parsed_board.turn = active_turn
                    # Reconstruct FEN with the accurate active turn
                    fen_parts = fen.split(" ")
                    if len(fen_parts) >= 2:
                        fen_parts[1] = "w" if active_turn == chess.WHITE else "b"
                        fen = " ".join(fen_parts)
                except Exception as t_err:
                    logger.debug("Active turn refinement error: %s", t_err)

            return RecognitionResult(
                fen=fen,
                board_box=(0, 0, bw, bh),
                flipped=is_flipped,
                confidence=avg_confidence,
                active_turn=active_turn,
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
