"""
settings.py
===========
Persistent settings — saved to a JSON file next to the package.

Usage
-----
    from chess_visualizer.settings import Settings

    s = Settings.load()
    s.board_region = (100, 200, 800, 800)
    s.save()
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

SETTINGS_PATH = Path(__file__).parent.parent / "settings.json"


@dataclass
class Settings:
    board_region: Optional[Tuple[int, int, int, int]] = None
    flipped: bool = False
    opacity: float = 1.0
    show_white: bool = True
    show_black: bool = True
    show_highlights: bool = True
    show_hud: bool = True
    arrow_width: int = 5
    update_interval: float = 1.0

    # ------------------------------------------------------------------ #

    @classmethod
    def load(cls) -> "Settings":
        if SETTINGS_PATH.exists():
            try:
                with SETTINGS_PATH.open() as f:
                    data = json.load(f)
                # board_region stored as list → convert to tuple
                if data.get("board_region") is not None:
                    data["board_region"] = tuple(data["board_region"])
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception as exc:
                logger.warning("Could not load settings: %s", exc)
        return cls()

    def save(self) -> None:
        try:
            d = asdict(self)
            if d.get("board_region") is not None:
                d["board_region"] = list(d["board_region"])
            with SETTINGS_PATH.open("w") as f:
                json.dump(d, f, indent=2)
            logger.debug("Settings saved to %s", SETTINGS_PATH)
        except Exception as exc:
            logger.warning("Could not save settings: %s", exc)
