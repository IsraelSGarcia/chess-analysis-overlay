import sys
import unittest
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt

from chess_visualizer.capture import set_window_capture_exclusion, WDA_EXCLUDEFROMCAPTURE
from chess_visualizer.overlay import OverlayConfig
from chess_visualizer._overlay_widget import OverlayWidget
from chess_visualizer._control_bar import ControlBar
from chess_visualizer._hud_panel import HUDPanel


class TestCaptureExclusion(unittest.TestCase):
    """
    Verify the Screen Capture Isolation Invariant:
    Overlays, HUDs, and toolbars must never appear in screen capture buffers,
    preventing self-detection feedback loops (blinking, turn flipping, evaluation cycling).
    """

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_set_window_capture_exclusion_on_widget(self):
        w = QWidget()
        w.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        w.show()
        success = set_window_capture_exclusion(w)
        if sys.platform == "win32":
            self.assertTrue(success, "set_window_capture_exclusion should succeed on Windows")
        w.close()

    def test_overlay_widget_capture_excluded(self):
        cfg = OverlayConfig(board_region=(100, 100, 400, 400))
        overlay = OverlayWidget(cfg)
        overlay.show()
        if sys.platform == "win32":
            self.assertTrue(overlay.is_capture_excluded, "OverlayWidget must have capture exclusion active")
        overlay.close()

    def test_hud_and_control_bar_capture_excluded(self):
        cb = ControlBar(
            on_toggle_master=lambda: None,
            on_toggle_mode=lambda: None,
            on_toggle_white=lambda: None,
            on_toggle_black=lambda: None,
            on_toggle_defense=lambda: None,
            on_flip=lambda: None,
            on_toggle_highlights=lambda: None,
            on_toggle_hud=lambda: None,
            on_toggle_auto=lambda: None,
            on_recalibrate=lambda: None,
            on_close=lambda: None,
        )
        hud = HUDPanel()
        cb.show()
        hud.show()

        if sys.platform == "win32":
            self.assertTrue(set_window_capture_exclusion(cb))
            self.assertTrue(set_window_capture_exclusion(hud))

        cb.close()
        hud.close()


if __name__ == "__main__":
    unittest.main()
