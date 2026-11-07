"""
test_tray.py
============
Unit tests verifying Windows system tray icon and menu integration.
"""

import os
import sys
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from chess_visualizer._tray import AppTrayIcon, create_app_icon

app = QApplication.instance() or QApplication(sys.argv)


class TestTrayIntegration(unittest.TestCase):

    def setUp(self):
        self.master_toggled = False
        self.mode_toggled = False
        self.hud_toggled = False
        self.auto_toggled = False
        self.recal_triggered = False
        self.exit_triggered = False

        self.tray = AppTrayIcon(
            on_toggle_master=self._toggle_master,
            on_toggle_mode=self._toggle_mode,
            on_toggle_hud=self._toggle_hud,
            on_toggle_auto=self._toggle_auto,
            on_recalibrate=self._recal,
            on_exit=self._exit,
        )

    def _toggle_master(self):
        self.master_toggled = True

    def _toggle_mode(self):
        self.mode_toggled = True

    def _toggle_hud(self):
        self.hud_toggled = True

    def _toggle_auto(self):
        self.auto_toggled = True

    def _recal(self):
        self.recal_triggered = True

    def _exit(self):
        self.exit_triggered = True

    def test_create_app_icon(self):
        icon = create_app_icon(64)
        self.assertIsInstance(icon, QIcon)
        self.assertFalse(icon.isNull())

    def test_tray_initial_state(self):
        self.assertIn("Chess Analysis Overlay", self.tray.toolTip())
        self.assertIsNotNone(self.tray.contextMenu())

    def test_tray_status_update(self):
        self.tray.set_status_text("Board Locked")
        self.assertIn("Board Locked", self.tray.toolTip())

    def test_tray_menu_actions(self):
        self.tray.act_master.trigger()
        self.assertTrue(self.master_toggled)

        self.tray.act_mode.trigger()
        self.assertTrue(self.mode_toggled)

        self.tray.act_hud.trigger()
        self.assertTrue(self.hud_toggled)

        self.tray.act_auto.trigger()
        self.assertTrue(self.auto_toggled)

        self.tray.act_cal.trigger()
        self.assertTrue(self.recal_triggered)

        self.tray.act_exit.trigger()
        self.assertTrue(self.exit_triggered)

    def test_update_states(self):
        self.tray.update_states(overlay_visible=False, mode="tactics", hud_visible=False, auto_track=True)
        self.assertFalse(self.tray.act_master.isChecked())
        self.assertIn("Tactical Analysis", self.tray.act_mode.text())
        self.assertFalse(self.tray.act_hud.isChecked())
        self.assertTrue(self.tray.act_auto.isChecked())


if __name__ == "__main__":
    unittest.main()
