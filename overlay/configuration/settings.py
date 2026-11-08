"""
settings.py
===========
Persistent user configuration.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

SETTINGS_PATH = Path(__file__).parent / "settings.json"


@dataclass
class Settings:
    board_region: Optional[Tuple[int, int, int, int]] = None
    flipped: bool = False
    opacity: float = 1.0
    active_mode: str = "tactics"  # "tactics" or "captures"
    show_white: bool = True
    show_black: bool = True
    show_highlights: bool = True
    show_defense: bool = True
    overlay_visible: bool = True
    show_hud: bool = True
    show_tactical_arrows: bool = True
    auto_track: bool = True
    manual_locked: bool = False
    control_bar_pos: Optional[Tuple[int, int]] = None
    hud_pos: Optional[Tuple[int, int]] = None
    update_interval: float = 0.5

    @classmethod
    def load(cls) -> "Settings":
        if SETTINGS_PATH.exists():
            try:
                with SETTINGS_PATH.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("board_region") is not None:
                    data["board_region"] = tuple(data["board_region"])
                if data.get("control_bar_pos") is not None:
                    data["control_bar_pos"] = tuple(data["control_bar_pos"])
                if data.get("hud_pos") is not None:
                    data["hud_pos"] = tuple(data["hud_pos"])
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception as exc:
                logger.warning("Could not load settings: %s", exc)
        return cls()

    def save(self) -> None:
        try:
            d = asdict(self)
            if d.get("board_region") is not None:
                d["board_region"] = list(d["board_region"])
            if d.get("control_bar_pos") is not None:
                d["control_bar_pos"] = list(d["control_bar_pos"])
            if d.get("hud_pos") is not None:
                d["hud_pos"] = list(d["hud_pos"])
            with SETTINGS_PATH.open("w", encoding="utf-8") as f:
                json.dump(d, f, indent=2)
            logger.debug("Settings saved to %s", SETTINGS_PATH)
        except Exception as exc:
            logger.warning("Could not save settings: %s", exc)
