"""
test_control_bar.py
===================
Unit tests verifying ControlBar functionality, mode switching, and status pills.
"""

import os
import sys
import unittest
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from overlay.interface.control_bar import ControlBar

app = QApplication.instance() or QApplication(sys.argv)


class TestControlBar(unittest.TestCase):

    def setUp(self):
        self.mode_toggled = False
        self.master_toggled = False
        self.turn_toggled = False
        self.cb = ControlBar(
            on_toggle_master=self._toggle_master,
            on_toggle_mode=self._toggle_mode,
            on_toggle_white=lambda: None,
            on_toggle_black=lambda: None,
            on_toggle_defense=lambda: None,
            on_flip=lambda: None,
            on_toggle_highlights=lambda: None,
            on_toggle_hud=lambda: None,
            on_toggle_auto=lambda: None,
            on_recalibrate=lambda: None,
            on_close=lambda: None,
            on_toggle_turn=self._toggle_turn,
        )

    def _toggle_master(self):
        self.master_toggled = True

    def _toggle_mode(self):
        self.mode_toggled = True

    def _toggle_turn(self):
        self.turn_toggled = True

    def tearDown(self):
        self.cb.close()

    def test_mode_button_click(self):
        self.cb.btn_mode.click()
        self.assertTrue(self.mode_toggled)

    def test_update_states_tactics_mode(self):
        self.cb.show()
        self.cb.update_states(
            overlay_visible=True,
            mode="tactics",
            show_player=True,
            show_enemy=True,
            show_defense=True,
            show_highlights=True,
            show_hud=True,
            auto_track=True,
            flipped=False,
        )
        self.assertEqual(self.cb.btn_mode.text(), "Tactics")
        self.assertTrue(self.cb.btn_master.isChecked())
        # STRICT FEATURE SEPARATION: Player, Enemy, Defense, Flip, Highlights hidden; HUD visible
        self.assertFalse(self.cb.btn_player.isVisible())
        self.assertFalse(self.cb.btn_enemy.isVisible())
        self.assertFalse(self.cb.btn_defense.isVisible())
        self.assertFalse(self.cb.btn_flip.isVisible())
        self.assertFalse(self.cb.btn_hl.isVisible())
        self.assertTrue(self.cb.btn_hud.isVisible())

    def test_update_states_captures_mode(self):
        self.cb.show()
        self.cb.update_states(
            overlay_visible=True,
            mode="captures",
            show_player=True,
            show_enemy=True,
            show_defense=True,
            show_highlights=True,
            show_hud=True,
            auto_track=True,
            flipped=False,
        )
        self.assertEqual(self.cb.btn_mode.text(), "Captures")
        # STRICT FEATURE SEPARATION: Player, Enemy, Defense, Flip, Highlights visible; HUD hidden
        self.assertTrue(self.cb.btn_player.isVisible())
        self.assertTrue(self.cb.btn_enemy.isVisible())
        self.assertTrue(self.cb.btn_defense.isVisible())
        self.assertTrue(self.cb.btn_flip.isVisible())
        self.assertTrue(self.cb.btn_hl.isVisible())
        self.assertFalse(self.cb.btn_hud.isVisible())

    def test_status_pill(self):
        self.cb.set_status("Searching...", mode="searching")
        self.assertIn("Searching...", self.cb.lbl_status.text())

        self.cb.set_status("Locked", mode="locked")
        self.assertIn("Locked", self.cb.lbl_status.text())

    def test_turn_button_click_and_state(self):
        self.cb.btn_turn.click()
        self.assertTrue(self.turn_toggled)

        self.cb.update_states(
            overlay_visible=True,
            mode="tactics",
            show_player=True,
            show_enemy=True,
            show_defense=True,
            show_highlights=True,
            show_hud=True,
            auto_track=True,
            flipped=False,
            active_turn=False,
        )
        self.assertEqual(self.cb.btn_turn.text(), "Turn: Black")


if __name__ == "__main__":
    unittest.main()
