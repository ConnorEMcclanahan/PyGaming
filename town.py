"""Backward-compatible facade: imports moved to town_pkg/. (no logic here)."""
from town_pkg.layout import (
    BUILDINGS, FOUNTAIN, GATE_BOTTOM, GATE_RECT, GATE_TOP, HIDEOUT_CENTER,
    VAULT_SIZE,
    HIDEOUT_RECT, SPAWN_POINT, TOWN_RECT, WALL, WALL_RECTS,
)
from town_pkg.prices import BUY_PRICE, REROLL_COST, SELL_PRICE, SHOP_STOCK, UPGRADE_COST
from town_pkg.npcs import NPC, make_npcs
from town_pkg.draw import _draw_building, _label, draw_town
from town_pkg.shop import ShopMenu, _reroll_item, fmt_cost


__all__ = [
    "TOWN_RECT", "WALL", "GATE_TOP", "GATE_BOTTOM", "WALL_RECTS",
    "GATE_RECT", "SPAWN_POINT", "FOUNTAIN", "BUILDINGS",
    "HIDEOUT_RECT", "HIDEOUT_CENTER",
    "VAULT_SIZE",
    "BUY_PRICE", "SELL_PRICE", "UPGRADE_COST", "REROLL_COST", "SHOP_STOCK",
    "NPC", "make_npcs", "_label", "_draw_building", "draw_town",
    "fmt_cost", "_reroll_item", "ShopMenu",
]
