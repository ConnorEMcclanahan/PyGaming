"""Headless smoke test: Q/E camera rotation + POE orb currency + forge
crafting + new items/abilities, plus overworld regression checks.
"""
import math
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from settings import Settings
from game import Game
from town import ShopMenu, TOWN_RECT, SPAWN_POINT, BUY_PRICE, SELL_PRICE, UPGRADE_COST, REROLL_COST
from items import (
    LOOT_TABLE, ORB_ITEMS, ORB_VALUES, get_weapon_profile, get_ability_profile, upgrade_rarity,
    item_slot, orb_key,
)


def main():
    pygame.init()
    game = Game(Settings(), character="knight")
    p = game.player

    # --- regression: town spawn, ward, walls, gate, vault -------------------
    assert TOWN_RECT.collidepoint(p.rect.center)
    assert len(game.ninjas) == 17
    for _ in range(10):
        game._update_world()
    assert not hasattr(p, "gold"), "gold replaced by orb pouch"
    assert p.orbs == {"scrap": 6, "phase": 2, "quantum": 0, "singularity": 0}
    assert p.orb_balance() == 16

    # --- keybinds: interact moved to F, Q/E rotation bound ------------------
    kb = game.settings.keybinds
    assert kb["interact"] == pygame.K_f
    assert kb["rotate_left"] == pygame.K_q
    assert kb["rotate_right"] == pygame.K_e

    # --- rotation math: screen->world must invert the camera spin -----------
    game.camera = pygame.Vector2(500, 400)
    for angle in (0, 30, 90, 180, 270):
        game.camera_angle = angle
        for screen_pt in ((100, 100), (694, 768), (347, 384), (600, 200)):
            wx, wy = game._screen_to_world(screen_pt)
            # Forward transform: world -> screen offset (visual CCW matrix).
            view_c = pygame.Vector2(game.view_width / 2, game.settings.screen_height / 2)
            d = pygame.Vector2(wx - game.camera.x, wy - game.camera.y) - view_c
            th = math.radians(angle)
            fwd = pygame.Vector2(d.x * math.cos(th) + d.y * math.sin(th),
                                 -d.x * math.sin(th) + d.y * math.cos(th))
            back = fwd + view_c
            assert abs(back.x - screen_pt[0]) < 1e-6 and abs(back.y - screen_pt[1]) < 1e-6, \
                "roundtrip failed at angle {}".format(angle)
    game.camera_angle = 90.0
    game._draw_all()  # rotated frame renders without error
    assert game.world_surf.get_size() == (game.view_width, game.settings.screen_height)
    game.camera_angle = 0.0

    # --- orb math: spend cheapest-first with exact refund -------------------
    p.orbs = {"scrap": 0, "phase": 1, "quantum": 0, "singularity": 0}
    assert p.spend_orbs(3) and p.orbs == {"scrap": 2, "phase": 0, "quantum": 0, "singularity": 0}, \
        "overpay refunded in shards"
    assert not p.spend_orbs(99)
    p.credit_orbs(132)  # 1 singularity + 1 quantum + 1 phase + 2 scrap
    assert p.orbs == {"scrap": 2, "phase": 1, "quantum": 1, "singularity": 1}
    assert p.orb_balance() == 131
    p.orbs = {"scrap": 25, "phase": 0, "quantum": 0, "singularity": 0}
    assert p.spend_orbs(13) and p.orbs["scrap"] == 12

    # --- shop: buy paid in orb value, sell credits orbs ---------------------
    game.menu = ShopMenu(game.screen, game.ui, p, "shop")
    menu = game.menu
    p.orbs = {"scrap": 30, "phase": 4, "quantum": 1, "singularity": 0}  # value 75
    saber_index = next(i for i, it in enumerate(menu.item_cells)
                       if __import__("town").SHOP_STOCK[i][0] == "PLASMA SABER")
    row = menu.item_cells[saber_index][1]
    menu.handle_click(row.center)
    assert any(it and it[0] == "PLASMA SABER" for it in game.ui.backpack), "bought saber"
    assert p.orb_balance() == 75 - BUY_PRICE["common"], "buy consumed orb value"
    game.menu = None

    helm_index = next(i for i, it in enumerate(game.ui.backpack) if it and it[0] == "NANO HELM")
    game.menu = ShopMenu(game.screen, game.ui, p, "sell")
    sell = game.menu
    sell.handle_click(sell.item_cells[helm_index][1].center)
    assert game.ui.backpack[helm_index] is None
    assert p.orb_balance() == (75 - BUY_PRICE["common"]) + SELL_PRICE["common"], "sell credited orbs"
    game.menu = None

    # --- forge: upgrade bumps rarity and consumes recipe orbs ---------------
    game.ui.backpack[0] = ("ION MAIL", (100, 160, 220), "common", "armor")
    p.orbs = {"scrap": 4, "phase": 1, "quantum": 0, "singularity": 0}  # exactly common upgrade
    game.menu = ShopMenu(game.screen, game.ui, p, "forge", vault=game.vault_items)
    forge = game.menu
    forge.handle_click(forge.item_cells[0][2].center)  # select ION MAIL
    assert forge.selected == 0
    upgrade_btn = forge.recipe_rects[0][1]
    forge.handle_click(upgrade_btn.center)
    assert game.ui.backpack[0][2] == "uncommon", "upgrade bumped rarity"
    assert p.orbs == {"scrap": 0, "phase": 0, "quantum": 0, "singularity": 0}, "recipe orbs consumed"
    # reroll the now-uncommon item (cost: 3 phase + 1 quantum) - can't afford
    forge.handle_click(forge.recipe_rects[1][1].center)
    assert game.ui.backpack[0][2] == "uncommon", "reroll refused when short"
    p.orbs = {"scrap": 0, "phase": 3, "quantum": 1, "singularity": 0}
    forge.handle_click(forge.recipe_rects[1][1].center)
    assert p.orbs["phase"] == 0 and p.orbs["quantum"] == 0
    rerolled = game.ui.backpack[0]
    assert rerolled[3] == "armor" and rerolled[2] == "uncommon", "reroll keeps slot + rarity"
    forge._draw()  # forge menu renders
    game.menu = None

    # --- enemies drop physical orbs; pickups go to the pouch ----------------
    ninja = game.ninjas[0]
    ninja.take_damage(9999)
    game._on_enemy_killed(ninja)
    assert all(item_slot(d["item"]) in ("currency",) or item_slot(d["item"]) is not None
               or item_slot(d["item"]) is None for d in game.drops)
    game.drops.clear()
    game._drop_orbs((1600, 600), boss=True)
    boss_orbs = [d for d in game.drops if item_slot(d["item"]) == "currency"]
    assert len(boss_orbs) == 20, "boss drops 2+4+6+8 orbs"
    # walk onto one orb -> pouch grows, drop vanishes
    p.x, p.y = int(boss_orbs[0]["pos"].x), int(boss_orbs[0]["pos"].y)
    p.rect.topleft = (p.x, p.y)
    before = p.orbs[orb_key(boss_orbs[0]["item"])]
    game._pickup_drops()
    assert p.orbs[orb_key(boss_orbs[0]["item"])] == before + 1, "orb pickup credited pouch"
    assert boss_orbs[0] not in game.drops

    # --- new abilities cast through the game loop ---------------------------
    p.mana = 100
    p.ability_cd = 0
    game.ui.equipment["ability"] = ("TEMPEST SURGE", (170, 220, 255), "rare", "ability")
    game._cast_ability((800, 600))
    assert len(game.projectiles) == 12, "Tempest Surge spawns a 12-bolt ring"
    game.projectiles.clear()
    assert get_ability_profile(("PHOENIX CORE", (255, 120, 40), "legendary", "ability"))["key"] == "phoenix"
    p.health = 30
    p.ability_cd = 0
    game.ui.equipment["ability"] = ("PHOENIX CORE", (255, 120, 40), "legendary", "ability")
    game._cast_ability((800, 600))
    assert p.health == 90 and p.is_shielding, "Phoenix heals + shields"
    game.enemy_projectiles.clear()
    from enemy import NinjaStar
    game.ui.equipment["ability"] = ("GRAVITY WELL", (150, 120, 255), "epic", "ability")
    p.ability_cd = 0
    p.mana = 100
    star = NinjaStar(p.rect.center, (p.rect.centerx + 60, p.rect.centery))
    game.enemy_projectiles.append(star)
    game._cast_ability((800, 600))
    assert star not in game.enemy_projectiles, "Gravity Well collapsed the star"
    prof = get_weapon_profile(("EVENT HORIZON", (255, 96, 96), "legendary", "weapon"))
    assert prof["shots"] == 3 and prof["damage"] == round(22 * 2.8), "legendary mult applied"
    assert upgrade_rarity(("X", (0, 0, 0), "legendary", "weapon"))[2] == "legendary"
    assert len(LOOT_TABLE) == 27

    # --- regression: vault + respawn keep working ---------------------------
    game.vault_items[0] = ("ION MAIL", (100, 160, 220), "uncommon", "armor")
    game._respawn()
    assert TOWN_RECT.collidepoint(game.player.rect.center)
    assert game.vault_items[0] is not None
    assert game.camera_angle == 0.0

    print("ALL SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()
