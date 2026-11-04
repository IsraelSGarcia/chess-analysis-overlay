"""
capture.py
==========
Robust screen capture for Windows with High-DPI scaling and black-frame detection.

Backends:
1. PIL.ImageGrab.grab(bbox) - standard, captures DirectX/hardware accelerated browsers.
2. mss - fast DirectX/GDI capture.
3. Qt QScreen.grabWindow - native Qt fallback.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


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

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.release()
