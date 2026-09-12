"""Backward-compatible facade: imports moved to items_pkg/. (no logic here)."""
from items_pkg.kinds import get_item_kind, item_slot, is_consumable, can_equip_in, can_place_in_belt
from items_pkg.profiles import get_ability_profile, get_item_blurb, get_item_stats, get_weapon_profile
from items_pkg.icons import draw_item_icon
from items_pkg.currency import (ORB_ITEMS, ORB_NAMES, ORB_ORDER, ORB_VALUES, orb_key)
from items_pkg.loot import LOOT_TABLE, RARITY_ORDER, upgrade_rarity


__all__ = [
    "get_item_kind", "item_slot", "is_consumable", "can_equip_in", "can_place_in_belt",
    "get_ability_profile", "get_item_blurb", "get_item_stats", "get_weapon_profile",
    "draw_item_icon",
    "ORB_ITEMS", "ORB_NAMES", "ORB_ORDER", "ORB_VALUES", "orb_key",
    "LOOT_TABLE", "RARITY_ORDER", "upgrade_rarity",
]
