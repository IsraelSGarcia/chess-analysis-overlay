"""
overlay.interface
=================
Floating user interface controls:
- Floating analysis HUD panel
- Draggable control bar
- System tray management
"""

from .hud_panel import HUDPanel
from .control_bar import ControlBar
from .tray import AppTrayIcon, create_app_icon

# Aliases
HudPanel = HUDPanel
TrayIcon = AppTrayIcon

__all__ = [
    "HUDPanel",
    "HudPanel",
    "ControlBar",
    "AppTrayIcon",
    "TrayIcon",
    "create_app_icon",
]
