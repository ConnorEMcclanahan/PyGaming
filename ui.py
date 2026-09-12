"""Backward-compatible facade: imports moved to ui_pkg/. (no logic here)."""
from ui_pkg.theme import (
    BAD_RED, EQUIP_ORDER, GOLD, GOLD_DIM, PANEL_BG, PANEL_EDGE,
    RARITY_BORDER, RARITY_COLORS, RARITY_TEXT, SLOT_BG, SLOT_BORDER,
    SLOT_LABEL, SLOT_TITLES, TEXT_DIM, TEXT_LIGHT,
)
from ui_pkg.ui import UI


__all__ = [
    "BAD_RED", "EQUIP_ORDER", "GOLD", "GOLD_DIM", "PANEL_BG", "PANEL_EDGE",
    "RARITY_BORDER", "RARITY_COLORS", "RARITY_TEXT", "SLOT_BG", "SLOT_BORDER",
    "SLOT_LABEL", "SLOT_TITLES", "TEXT_DIM", "TEXT_LIGHT", "UI",
]
