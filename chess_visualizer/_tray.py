"""
_tray.py
========
Windows System Tray Icon and status manager for Chess Analysis Overlay.

Ensures the application is always visible, accessible, and manageable from
the Windows notification area (near the clock), even when the overlay is
hidden or tracking a board.
"""

from __future__ import annotations

from typing import Callable, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PySide6.QtWidgets import QSystemTrayIcon, QMenu


def create_app_icon(size: int = 64) -> QIcon:
    """Generate a clean dark-mode chess knight icon programmatically."""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    # Dark rounded background with emerald border
    painter.setBrush(QColor(20, 24, 30))
    painter.setPen(QColor(0, 230, 118))
    radius = int(size * 0.2)
    painter.drawRoundedRect(2, 2, size - 4, size - 4, radius, radius)

    # White Knight glyph
    font = QFont("Segoe UI Symbol", int(size * 0.55))
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor(255, 255, 255))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "♞")
    painter.end()

    return QIcon(pixmap)


class AppTrayIcon(QSystemTrayIcon):
    """System tray integration providing presence and controls in the Windows Taskbar."""

    def __init__(
        self,
        on_toggle_master: Callable[[], None],
        on_toggle_mode: Callable[[], None],
        on_toggle_hud: Callable[[], None],
        on_toggle_auto: Callable[[], None],
        on_recalibrate: Callable[[], None],
        on_exit: Callable[[], None],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.on_toggle_master = on_toggle_master
        self.on_toggle_mode = on_toggle_mode
        self.on_toggle_hud = on_toggle_hud
        self.on_toggle_auto = on_toggle_auto
        self.on_recalibrate = on_recalibrate
        self.on_exit = on_exit

        self.setIcon(create_app_icon())
        self.setToolTip("Chess Analysis Overlay")

        self._setup_menu()
        self.activated.connect(self._handle_activation)

    def _setup_menu(self) -> None:
        self.menu = QMenu()
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #16191f;
                color: #e6edf3;
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 6px;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 6px 20px;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 25);
            }
        """)

        self.act_master = self.menu.addAction("Show Overlay")
        self.act_master.setCheckable(True)
        self.act_master.setChecked(True)
        self.act_master.triggered.connect(self.on_toggle_master)

        self.act_mode = self.menu.addAction("Mode: Tactical Analysis")
        self.act_mode.triggered.connect(self.on_toggle_mode)

        self.act_hud = self.menu.addAction("Show Tactical HUD")
        self.act_hud.setCheckable(True)
        self.act_hud.setChecked(True)
        self.act_hud.triggered.connect(self.on_toggle_hud)

        self.act_auto = self.menu.addAction("Auto-Track Board")
        self.act_auto.setCheckable(True)
        self.act_auto.setChecked(True)
        self.act_auto.triggered.connect(self.on_toggle_auto)

        self.menu.addSeparator()

        self.act_cal = self.menu.addAction("Calibrate Manually (Fallback)")
        self.act_cal.triggered.connect(self.on_recalibrate)

        self.menu.addSeparator()

        self.act_exit = self.menu.addAction("Exit Application")
        self.act_exit.triggered.connect(self.on_exit)

        self.setContextMenu(self.menu)

    def update_states(self, overlay_visible: bool, mode: str, hud_visible: bool, auto_track: bool) -> None:
        """Keep tray menu checkmarks in sync with active application settings."""
        self.act_master.setChecked(overlay_visible)
        if mode == "tactics":
            self.act_mode.setText("Mode: Tactical Analysis (Switch to Captures)")
        else:
            self.act_mode.setText("Mode: Legal Captures (Switch to Tactics)")
        self.act_hud.setChecked(hud_visible)
        self.act_auto.setChecked(auto_track)

    def set_status_text(self, status: str) -> None:
        self.setToolTip(f"Chess Analysis Overlay: {status}")

    def _handle_activation(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            # Left-click on tray icon toggles master overlay
            self.on_toggle_master()
