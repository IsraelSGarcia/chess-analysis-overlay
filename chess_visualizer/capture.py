"""
capture.py
==========
Robust screen capture for Windows with High-DPI scaling and black-frame detection.

SCREEN CAPTURE ISOLATION INVARIANT:
----------------------------------
Under no circumstances may any visualizer overlay, HUD, toolbar, or annotation
appear in captured screen frames.
All UI widgets rendered on top of the desktop MUST have WDA_EXCLUDEFROMCAPTURE
set on their native Windows handles so the Windows Desktop Window Manager (DWM)
compositor removes them from all capture pipelines (PIL ImageGrab, mss, DirectX).
If the overlay were captured, the neural-network piece classifier and highlight
detector would see the visualizer's own drawn arrows, brackets, and colors, causing
fatal self-detection feedback loops (flickering, turn toggling, evaluation cycling).

Backends:
1. PIL.ImageGrab.grab(bbox) - standard, captures DirectX/hardware accelerated browsers.
2. mss - fast DirectX/GDI capture.
3. Qt QScreen.grabWindow - native Qt fallback.
"""

from __future__ import annotations

import ctypes
import logging
import sys
from typing import Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Windows DWM Window Display Affinity Constants
WDA_NONE = 0x00000000
WDA_MONITOR = 0x00000001
WDA_EXCLUDEFROMCAPTURE = 0x00000011


def set_window_capture_exclusion(window) -> bool:
    """
    Exclude a window from all screen captures using the Windows DWM API.

    Guarantees that screen capture backends (PIL ImageGrab, mss, DirectX)
    read only the authentic underlying desktop and chessboard, completely
    ignoring overlay annotations, arrows, and highlights.

    Parameters
    ----------
    window : QWidget or int
        The PySide6 QWidget or native HWND to exclude from capture.

    Returns
    -------
    bool
        True if WDA_EXCLUDEFROMCAPTURE was successfully applied, False otherwise.
    """
    if sys.platform != "win32":
        return False

    try:
        if hasattr(window, "winId"):
            hwnd = int(window.winId())
        else:
            hwnd = int(window)

        if not hwnd:
            return False

        res = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        if res != 0:
            logger.debug("Successfully applied WDA_EXCLUDEFROMCAPTURE to HWND %s", hwnd)
            return True
        else:
            err = ctypes.GetLastError()
            logger.warning("SetWindowDisplayAffinity returned 0 (GetLastError: %s) for HWND %s", err, hwnd)
            return False
    except Exception as exc:
        logger.warning("Failed to apply capture exclusion to window: %s", exc)
        return False


def is_black_image(img: Optional[Image.Image]) -> bool:
    """Check if an image is completely black / blank."""
    if img is None:
        return True
    try:
        arr = np.array(img)
        # If max brightness is very low, it's black
        return float(arr.max()) < 8.0 and float(np.std(arr)) < 2.0
    except Exception:
        return True


class ScreenCapture:
    """Multi-backend screen capture with black-frame validation."""

    def __init__(self) -> None:
        self._dpr: float = 1.0
        self._init_dpr()

    def _init_dpr(self) -> None:
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                screen = app.primaryScreen()
                if screen:
                    self._dpr = float(screen.devicePixelRatio())
        except Exception:
            self._dpr = 1.0

    @property
    def available(self) -> bool:
        return True

    def grab_region(self, left: int, top: int, width: int, height: int) -> Optional[Image.Image]:
        """
        Capture a rectangular region of the screen (in logical coordinates).

        Returns
        -------
        PIL.Image.Image (RGB) or None on failure.
        """
        # Physical coordinates for backends that operate in raw pixels
        phys_l = int(round(left * self._dpr))
        phys_t = int(round(top * self._dpr))
        phys_r = int(round((left + width) * self._dpr))
        phys_b = int(round((top + height) * self._dpr))
        phys_w = phys_r - phys_l
        phys_h = phys_b - phys_t

        # 1. Try PIL ImageGrab (standard on Windows, captures hardware-accelerated desktop)
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab(bbox=(phys_l, phys_t, phys_r, phys_b), all_screens=True)
            if img and not is_black_image(img):
                return img.convert("RGB")
        except Exception as exc:
            logger.debug("ImageGrab failed: %s", exc)

        # 2. Try mss
        try:
            import mss
            with mss.mss() as sct:
                monitor = {
                    "left": phys_l,
                    "top": phys_t,
                    "width": phys_w,
                    "height": phys_h,
                }
                raw = sct.grab(monitor)
                arr = np.frombuffer(raw.bgra, dtype=np.uint8).reshape(raw.height, raw.width, 4)
                # BGRA to RGB
                rgb = arr[:, :, [2, 1, 0]]
                img = Image.fromarray(rgb)
                if not is_black_image(img):
                    return img
        except Exception as exc:
            logger.debug("mss failed: %s", exc)

        # 3. Try Qt QScreen.grabWindow (uses logical coordinates)
        try:
            from PySide6.QtWidgets import QApplication
            from PIL import ImageQt

            app = QApplication.instance()
            if app:
                screen = app.primaryScreen()
                if screen:
                    pixmap = screen.grabWindow(0, left, top, width, height)
                    if not pixmap.isNull():
                        img = ImageQt.fromqpixmap(pixmap).convert("RGB")
                        if not is_black_image(img):
                            return img
        except Exception as exc:
            logger.debug("Qt grabWindow failed: %s", exc)

        logger.warning("All capture backends returned None or black frames.")
        return None

    def release(self) -> None:
        pass

    def grab_fullscreen(self) -> Optional[Tuple[Image.Image, int, int]]:
        """
        Capture the entire primary display.
        Returns (PIL.Image.Image in RGB, geo_left, geo_top) or None.
        """
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                screen = app.primaryScreen()
                if screen:
                    geo = screen.geometry()
                    img = self.grab_region(geo.x(), geo.y(), geo.width(), geo.height())
                    if img:
                        return img, geo.x(), geo.y()
        except Exception as exc:
            logger.debug("grab_fullscreen Qt failed: %s", exc)

        try:
            from PIL import ImageGrab
            img = ImageGrab.grab(all_screens=False)
            if img and not is_black_image(img):
                return img.convert("RGB"), 0, 0
        except Exception as exc:
            logger.debug("grab_fullscreen ImageGrab failed: %s", exc)

        return None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.release()
