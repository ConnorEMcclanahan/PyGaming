"""Backward-compatible facade: imports moved to tutorial_pkg/. (no logic here)."""
from tutorial_pkg.config import (
    WORLD_W,
    WORLD_H,
    TUT_BG,
    BOSS_ROOM_X,
    BOSS_ROOM_X2,
    GRASS_X,
    SHIP_PAD_X,
    CHEST_GEAR,
    ARROW_XS,
    BOSS_ARROW_X,
)
from tutorial_pkg.tutorial import Tutorial


__all__ = [
    "WORLD_W",
    "WORLD_H",
    "TUT_BG",
    "BOSS_ROOM_X",
    "BOSS_ROOM_X2",
    "GRASS_X",
    "SHIP_PAD_X",
    "CHEST_GEAR",
    "ARROW_XS",
    "BOSS_ARROW_X",
    "Tutorial",
]
