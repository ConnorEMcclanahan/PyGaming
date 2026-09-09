import math
import random

import pygame

from enemy import Ninja, NinjaBoss
from game_testing_environment_module import GameTestingEnvironment
from items import draw_item_icon
from player import Player
from settings import Settings
from town import (
    BUILDINGS,
    GATE_RECT,
    HIDEOUT_CENTER,
    HIDEOUT_RECT,
    VAULT_SIZE,
    ShopMenu,
    SPAWN_POINT,
    TOWN_RECT,
    WALL_RECTS,
    draw_town,
    make_npcs,
)
from ui import RARITY_BORDER, UI

STARTER_WEAPON = ("PULSE BLADE", (120, 220, 255), "common", "weapon")
STARTER_ABILITY = ("HOLO SCROLL", (188, 205, 222), "common", "ability")
LOOT_TABLE = [
    ("PLASMA SABER", (90, 220, 255), "common", "weapon"),
    ("PULSE BLADE", (200, 200, 215), "common", "weapon"),
    ("NANO HELM", (150, 160, 175), "common", "helmet"),
    ("ION MAIL", (100, 160, 220), "uncommon", "armor"),
    ("ENERGY CELL", (78, 200, 255), "uncommon", None),
    ("REPAIR CELL", (220, 70, 70), "common", None),
    ("NOVA SCROLL", (255, 190, 110), "rare", "ability"),
    ("BLINK DRIVE", (140, 240, 255), "rare", "ability"),
    ("SENTRY DRONE", (150, 255, 170), "epic", "ability"),
    ("OVERDRIVE CORE", (255, 120, 120), "epic", "ability"),
    ("AEGIS PROTOCOL", (170, 220, 255), "rare", "ability"),
    ("VOID CLOAK", (150, 90, 220), "rare", "armor"),
    ("NOVA SABER", (255, 190, 90), "rare", "weapon"),
    ("PLASMA RIFLE", (140, 255, 170), "epic", "weapon"),
    ("SCATTER CANNON", (220, 150, 255), "epic", "weapon"),
]

# Wilderness layout: ninjas scattered across the plains east of town, plus a
# patrol ring surrounding the boss hideout on the far side of the map.
WILDERNESS_NINJAS = [
    (1500, 620), (1450, 1500), (1750, 1000), (1800, 1900),
    (2050, 700), (2150, 1600), (1900, 1300), (2050, 2150),
]
RING_NINJAS = [
    (3060, 1120), (2925, 1445), (2600, 1580), (2275, 1445),
    (2140, 1120), (2275, 795), (2600, 660), (2925, 795),
]
BOSS_POS = (2600, 1380)   # in front of the hideout doors
INTERACT_RANGE = 95

NINJA_DEATH_PALETTE = [(188, 205, 222), (118, 35, 49), (221, 215, 184), (26, 30, 34)]


def _wrap_text(text, width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        if len(current) + len(word) + 1 > width:
            lines.append(current)
            current = word
        else:
            current = current + " " + word if current else word
    if current:
        lines.append(current)
    return lines


class Game:
    def __init__(self, settings=None, character=None):
        self.settings = settings if settings is not None else Settings()
        self.character = character or "knight"
        # Overworld also supports hold-to-shoot.
        self.mouse_held = False
        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        pygame.display.set_caption("ROTGM-Style Bullet Hell Test")
        self.clock = pygame.time.Clock()
        self.auto_shoot = False
        self.shoot_timer = 0
        self.drop_font = pygame.font.Font(None, 15)
        self.world_font = pygame.font.Font(None, 17)
        self._ability_hint = 0
        self._ability_msg = ""
        self.menu = None            # open ShopMenu (pauses the world)
        self.dialogue = None        # villager chatter: {name, line, life}
        self.float_texts = []       # floating "+GOLD" style labels
        self.vault_items = [None] * VAULT_SIZE
        self._reset_world()

    # ------------------------------------------------------------ world setup
    def _reset_world(self):
        """Full reset (fresh session): new UI, empty vault, town spawn."""
        self.ui = UI(self.screen, self.settings)
        self.view_width = self.settings.screen_width - self.ui.panel.width
        # Always start with a weapon + ability equipped.
        self.ui.equipment["weapon"] = STARTER_WEAPON
        self.ui.equipment["ability"] = STARTER_ABILITY
        self.vault_items = [None] * VAULT_SIZE
        self._respawn()

    def _respawn(self):
        """(Re)spawn in the safe town. Keeps inventory, gold and vault, so
        dying only costs you the walk back out of town."""
        self.player = Player(self.screen, self.settings, self.character)
        self.player.x, self.player.y = SPAWN_POINT
        self.player.rect.topleft = (self.player.x, self.player.y)
        self.npcs = make_npcs()
        self._spawn_enemies()
        self.projectiles = []
        self.enemy_projectiles = []
        self.drops = []
        self.camera = pygame.Vector2()
        self.particles = []
        self.player_dead = False
        self.menu = None
        self.dialogue = None

    def _spawn_enemies(self):
        """Scattered wilderness ninjas + a ninja ring around the boss lair."""
        self.ninjas = []
        for x, y in WILDERNESS_NINJAS:
            self.ninjas.append(Ninja((x, y), self._patrol_bounds(x, y)))
        for x, y in RING_NINJAS:
            self.ninjas.append(Ninja((x, y), self._patrol_bounds(x, y)))
        self.boss = NinjaBoss(BOSS_POS, self._patrol_bounds(BOSS_POS[0], BOSS_POS[1], 120, 90))
        self.ninjas.append(self.boss)

    def _patrol_bounds(self, x, y, rx=170, ry=130):
        """Wander rectangle around a spawn point, clamped to the world and
        always clear of the town walls."""
        rect = pygame.Rect(max(0, x - rx), max(0, y - ry), rx * 2, ry * 2)
        rect.right = min(rect.right, self.settings.world_width)
        rect.bottom = min(rect.bottom, self.settings.world_height)
        return rect

    def _solid_rects(self):
        """Walls, town buildings and the hideout all block the player."""
        return WALL_RECTS + [b["rect"] for b in BUILDINGS] + [HIDEOUT_RECT]

    # ------------------------------------------------------------------ loop
    def run(self):
        """Main game loop. Returns True when the app should shut down (window closed)."""
        running = True
        exits = False
        shield_key = self.settings.keybinds.get("shield", pygame.K_SPACE)
        auto_shoot_key = self.settings.keybinds.get("auto_shoot", pygame.K_x)
        ability_key = self.settings.keybinds.get("ability", pygame.K_SPACE)
        interact_key = self.settings.keybinds.get("interact", pygame.K_e)
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exits = True
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if self.menu is not None:
                        # Modal menu: ESC or the interact key closes it.
                        if event.key in (pygame.K_ESCAPE, interact_key):
                            self.menu = None
                        continue
                    if event.key == ability_key:
                        # SPACE = cast equipped ability (starter = 5s bubble).
                        mouse = pygame.mouse.get_pos()
                        world_mouse = (mouse[0] + self.camera.x, mouse[1] + self.camera.y)
                        self._cast_ability(world_mouse)
                    elif event.key == shield_key and shield_key != ability_key:
                        self.player.bubble_shield()
                    elif event.key == auto_shoot_key:
                        self.auto_shoot = not self.auto_shoot
                    elif event.key == interact_key:
                        self._try_interact()
                    else:
                        self.ui.handle_key(event, self.player)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.menu is not None:
                        self.menu.handle_click(event.pos)
                        if self.menu.done:
                            self.menu = None
                        continue
                    if self.ui.panel.collidepoint(event.pos):
                        self.ui.handle_click(event.pos)
                    elif not self.ui.handle_world_click(event.pos):
                        self.mouse_held = True
                        mouse = pygame.mouse.get_pos()
                        world_mouse = (mouse[0] + self.camera.x, mouse[1] + self.camera.y)
                        # Rate-limited: fast clicking can't spam past attack speed.
                        self.projectiles.extend(self.player.try_attack(world_mouse, self.ui))
                elif event.type == pygame.MOUSEMOTION:
                    if self.menu is None:
                        self.ui.handle_drag(event.pos)
                        self.ui.handle_hover(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.mouse_held = False
                    if self.menu is None:
                        self.ui.handle_release(event.pos)

            if self.menu is not None:
                # Modal menu: freeze the world, keep drawing it behind the menu.
                self._draw_all()
                self.menu.draw()
                pygame.display.flip()
                self.clock.tick(60)
                continue

            if self.player_dead:
                action = self._run_death_screen()
                if action == "respawn":
                    self._respawn()
                elif action == "menu":
                    running = False
                else:  # quit
                    exits = True
                    running = False
                continue

            self._update_world()
            self._pickup_drops()

            self._draw_all()
            pygame.display.flip()
            self.clock.tick(60)
        return exits

    # ------------------------------------------------------------------ update
    def _update_world(self):
        prev_x, prev_y = self.player.x, self.player.y
        self.player.update(pygame.key.get_pressed(), self.settings.keybinds)
        self._resolve_town_collision(prev_x, prev_y)
        mouse = pygame.mouse.get_pos()
        world_mouse = (mouse[0] + self.camera.x, mouse[1] + self.camera.y)
        self.player.aim_at(world_mouse)
        # Hold-to-shoot at the weapon's attack speed.
        if self.mouse_held and not self.ui.panel.collidepoint(mouse):
            self.projectiles.extend(self.player.try_attack(world_mouse, self.ui))
        self._update_camera()

        in_town = TOWN_RECT.collidepoint(self.player.rect.center)
        if not in_town:
            # Safe town: enemies hold position and hold fire while you're
            # inside the walls.
            for ninja in self.ninjas:
                if ninja.alive:
                    ninja.update(self.player, self.enemy_projectiles)

        self.shoot_timer -= 1
        if self.auto_shoot and any(n.alive for n in self.ninjas) and self.shoot_timer <= 0:
            # Auto-shoot respects the equipped weapon's attack speed.
            shots = self.player.try_attack(
                (self.player.rect.centerx + math.cos(self.player.aim_angle) * 600,
                 self.player.rect.centery + math.sin(self.player.aim_angle) * 600),
                self.ui,
            )
            if shots:
                self.projectiles.extend(shots)
                self.shoot_timer = self.player.weapon_cooldown(self.ui)
            else:
                self.shoot_timer = 4

        for proj in self.projectiles[:]:
            proj.update()
            if not self._in_world(proj.rect):
                self.projectiles.remove(proj)
                continue
            for ninja in self.ninjas:
                if ninja.alive and proj.rect.colliderect(ninja.rect):
                    ninja.take_damage(proj.damage)
                    self.projectiles.remove(proj)
                    if not ninja.alive:
                        self._on_enemy_killed(ninja)
                    break

        for star in self.enemy_projectiles[:]:
            star.update()
            if not self._in_world(star.rect):
                self.enemy_projectiles.remove(star)
            elif star.rect.colliderect(self.player.rect):
                if in_town:
                    # Town wards: nothing can hurt you inside the walls.
                    self.enemy_projectiles.remove(star)
                    self._spawn_death_burst(star.rect.center, [(140, 235, 255), (90, 220, 255)])
                    continue
                if not self.player.is_shielding:
                    if not self.player_dead:
                        self.player.take_damage(8)
                        if self.player.health <= 0:
                            self.player_dead = True
                            self._spawn_death_burst(
                                self.player.rect.center,
                                [(55, 62, 76), (230, 63, 63), (211, 216, 215), (226, 226, 204)],
                            )
                self.enemy_projectiles.remove(star)

        for burst in self.particles[:]:
            burst["pos"] += burst["vel"]
            burst["vel"] *= 0.92
            burst["life"] -= 1
            if burst["life"] <= 0:
                self.particles.remove(burst)

        for npc in self.npcs:
            npc.update()
        for text in self.float_texts[:]:
            text["pos"].y -= 0.6
            text["life"] -= 1
            if text["life"] <= 0:
                self.float_texts.remove(text)
        if self.dialogue is not None:
            self.dialogue["life"] -= 1
            if self.dialogue["life"] <= 0:
                self.dialogue = None

    def _resolve_town_collision(self, prev_x, prev_y):
        """Axis-separated collision against town walls, buildings and the
        hideout. The gate gap in the east wall is the only way in/out."""
        solids = self._solid_rects()
        p = self.player
        if not any(p.rect.colliderect(s) for s in solids):
            return
        new_x, new_y = p.x, p.y
        p.x, p.y = prev_x, prev_y
        p.rect.topleft = (p.x, p.y)
        p.x = new_x
        p.rect.topleft = (p.x, p.y)
        if any(p.rect.colliderect(s) for s in solids):
            p.x = prev_x
            p.rect.topleft = (p.x, p.y)
        p.y = new_y
        p.rect.topleft = (p.x, p.y)
        if any(p.rect.colliderect(s) for s in solids):
            p.y = prev_y
            p.rect.topleft = (p.x, p.y)

    # ---------------------------------------------------------------- screens
    def _run_death_screen(self):
        big = pygame.font.Font(None, 88)
        sub = pygame.font.Font(None, 28)
        btn = pygame.font.Font(None, 34)
        cx = self.screen.get_width() // 2
        cy = self.screen.get_height() // 2
        title = big.render("YOU DIED", True, (228, 62, 62))
        title_rect = title.get_rect(center=(cx, cy - 130))
        flavor = sub.render("The town healers drag you back inside the walls...", True, (170, 168, 160))
        flavor_rect = flavor.get_rect(center=(cx, cy - 55))
        respawn = btn.render("Respawn in Town", True, (235, 232, 218))
        respawn_rect = respawn.get_rect(center=(cx - 90, cy + 120))
        main_menu = btn.render("Main Menu", True, (235, 232, 218))
        main_menu_rect = main_menu.get_rect(center=(cx + 90, cy + 120))

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if respawn_rect.collidepoint(event.pos):
                        return "respawn"
                    if main_menu_rect.collidepoint(event.pos):
                        return "menu"

            self.screen.fill((13, 10, 12))
            pygame.draw.circle(self.screen, (38, 30, 32), (cx, cy - 90), 150, 2)
            pygame.draw.circle(self.screen, (50, 40, 42), (cx, cy - 90), 120, 1)
            self.screen.blit(title, title_rect)
            self.screen.blit(flavor, flavor_rect)
            self._draw_button(respawn_rect, respawn, (200, 60, 60))
            self._draw_button(main_menu_rect, main_menu, (110, 92, 58))
            pygame.display.flip()
            self.clock.tick(60)

    def _draw_button(self, rect, label, edge):
        base = rect.inflate(26, 14)
        pygame.draw.rect(self.screen, (34, 30, 27), base)
        pygame.draw.rect(self.screen, edge, base, 3)
        self.screen.blit(label, rect)

    # ---------------------------------------------------------------- effects
    def _spawn_death_burst(self, center, palette):
        for _ in range(30):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(1.0, 7.5)
            self.particles.append(
                {
                    "pos": pygame.Vector2(center),
                    "vel": pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                    "life": random.randint(14, 32),
                    "color": random.choice(palette),
                }
            )

    def run_testing_environment(self):
        testing_environment = GameTestingEnvironment(self)
        testing_environment.run_testing_environment()

    # ------------------------------------------------------------------ loot
    def _on_enemy_killed(self, enemy):
        """Death burst + item loot + a little gold for the town shops."""
        self._spawn_death_burst(enemy.rect.center, NINJA_DEATH_PALETTE)
        self._maybe_drop_loot(enemy.rect.center)
        gold = getattr(enemy, "gold_reward", 6)
        self.player.gold += gold
        self.float_texts.append(
            {
                "text": "+{} GOLD".format(gold),
                "pos": pygame.Vector2(enemy.rect.centerx, enemy.rect.top - 20),
                "life": 70,
                "color": (240, 200, 90),
            }
        )

    def _maybe_drop_loot(self, position):
        if random.random() <= 0.4:
            self.drops.append(
                {
                    "item": random.choice(LOOT_TABLE),
                    "pos": pygame.Vector2(position),
                    "phase": random.uniform(0, math.tau),
                }
            )

    def _pickup_drops(self):
        for drop in self.drops[:]:
            drop_rect = pygame.Rect(0, 0, 36, 36)
            drop_rect.center = (round(drop["pos"].x), round(drop["pos"].y))
            if drop_rect.colliderect(self.player.rect):
                if self._add_to_backpack(drop["item"]):
                    self.drops.remove(drop)
                    self._spawn_pickup_burst(drop_rect.center, drop["item"][1])

    def _add_to_backpack(self, item):
        return self.ui.add_item(item)

    def _spawn_pickup_burst(self, center, color):
        for _ in range(12):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(1.0, 4.5)
            self.particles.append(
                {
                    "pos": pygame.Vector2(center),
                    "vel": pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                    "life": random.randint(10, 20),
                    "color": color,
                }
            )

    def _in_world(self, rect):
        return (
            rect.right > 0
            and rect.left < self.settings.world_width
            and rect.bottom > 0
            and rect.top < self.settings.world_height
        )

    def _update_camera(self):
        target_x = self.player.rect.centerx - self.view_width // 2
        target_y = self.player.rect.centery - self.settings.screen_height // 2
        max_x = self.settings.world_width - self.view_width
        max_y = self.settings.world_height - self.settings.screen_height
        target_x = max(0, min(target_x, max_x))
        target_y = max(0, min(target_y, max_y))
        self.camera.x += (target_x - self.camera.x) * self.settings.camera_lerp
        self.camera.y += (target_y - self.camera.y) * self.settings.camera_lerp

    # ------------------------------------------------------------ interaction
    def _near_npc(self):
        best, best_d = None, INTERACT_RANGE
        for npc in self.npcs:
            d = math.hypot(
                npc.rect.centerx - self.player.rect.centerx,
                npc.rect.centery - self.player.rect.centery,
            )
            if d <= best_d:
                best, best_d = npc, d
        return best

    def _try_interact(self):
        npc = self._near_npc()
        if npc is None:
            return
        if npc.is_keeper:
            self.menu = ShopMenu(self.screen, self.ui, self.player, npc.role, vault=self.vault_items)
        else:
            self.dialogue = {"name": npc.name, "line": npc.line, "life": 300}

    # ------------------------------------------------------------------ combat
    def _cast_ability(self, world_mouse):
        try:
            consumed, kind, payload = self.player.try_ability(world_mouse, self.ui)
        except Exception:
            return
        if not consumed:
            self._ability_hint = 90
            self._ability_msg = "ABILITY ON COOLDOWN"
            return
        try:
            if kind == "shots" and payload:
                self.projectiles.extend(payload)
            elif kind == "pulse" and isinstance(payload, dict):
                cx, cy = self.player.rect.center
                radius = payload.get("radius", 190)
                alive_before = [n for n in self.ninjas if n.alive]
                for ninja in alive_before:
                    nx, ny = ninja.rect.center
                    if math.hypot(nx - cx, ny - cy) <= radius:
                        ninja.take_damage(payload.get("damage", 30))
                for ninja in alive_before:
                    if not ninja.alive:
                        self._on_enemy_killed(ninja)
                self._spawn_death_burst((cx, cy), [(140, 240, 255), (90, 220, 255), (255, 255, 255)])
        except Exception:
            pass

    def _landmarks(self):
        """World-space rects + colors for the minimap."""
        return [
            (TOWN_RECT, (52, 74, 52)),
            (GATE_RECT, (200, 168, 80)),
            (BUILDINGS[0]["rect"], (150, 110, 70)),
            (BUILDINGS[1]["rect"], (150, 110, 70)),
            (BUILDINGS[2]["rect"], (150, 110, 70)),
            (HIDEOUT_RECT, (120, 44, 44)),
            (pygame.Rect(BOSS_POS[0] - 55, BOSS_POS[1] - 55, 110, 110), (214, 60, 62)),
        ]

    # ------------------------------------------------------------------ draw
    def _draw_all(self):
        self._draw_world()
        # Out of the tutorial: no more hand-holding text, just your gold.
        self.ui.draw_hud(self.player, self.auto_shoot, show_auto_shoot=False, show_gold=True)
        if self._ability_hint > 0:
            self._ability_hint -= 1
            hint = self.drop_font.render(getattr(self, "_ability_msg", "ABILITY ON COOLDOWN"), True, (255, 220, 120))
            self.ui.screen.blit(hint, (24, self.settings.screen_height - 190))
        self.ui.draw_inventory(self.player, self.camera, [n for n in self.ninjas if n.alive], self.drops, self._landmarks())
        self._draw_interact_prompt()
        self._draw_dialogue()

    def _draw_world(self):
        self.screen.fill(self.settings.background_color)
        arena = pygame.Rect(0, 0, self.view_width, self.settings.screen_height)
        pygame.draw.rect(self.screen, (34, 45, 53), arena)
        tile = 48
        start_x = int(self.camera.x // tile) * tile
        start_y = int(self.camera.y // tile) * tile
        for x in range(start_x, int(self.camera.x) + self.view_width + tile, tile):
            screen_x = x - round(self.camera.x)
            pygame.draw.line(self.screen, (38, 50, 59), (screen_x, 0), (screen_x, self.settings.screen_height))
        for y in range(start_y, int(self.camera.y) + self.settings.screen_height + tile, tile):
            screen_y = y - round(self.camera.y)
            pygame.draw.line(self.screen, (38, 50, 59), (0, screen_y), (self.view_width, screen_y))

        # Safe town + wilderness hideout.
        draw_town(self.screen, (self.camera.x, self.camera.y))
        building = HIDEOUT_RECT.move(-round(self.camera.x), -round(self.camera.y))
        pygame.draw.rect(self.screen, (77, 62, 58), building)
        pygame.draw.rect(self.screen, (123, 93, 69), building, 8)
        pygame.draw.rect(self.screen, (26, 29, 34), (building.x + 150, building.bottom - 12, 140, 22))
        pygame.draw.rect(self.screen, (54, 43, 42), (building.x + 24, building.y + 32, 78, 58))
        pygame.draw.rect(self.screen, (54, 43, 42), (building.right - 102, building.y + 32, 78, 58))
        self._draw_label("NINJA HIDEOUT", (building.x + 148, building.y + 14), (248, 214, 137))

        for drop in self.drops:
            self._draw_drop(drop)
        for star in self.enemy_projectiles:
            star.draw(self.screen, (round(self.camera.x), round(self.camera.y)))
        for ninja in self.ninjas:
            if ninja.alive:
                ninja.draw(self.screen, (round(self.camera.x), round(self.camera.y)))
        for npc in self.npcs:
            npc.draw(self.screen, (round(self.camera.x), round(self.camera.y)))
        for proj in self.projectiles:
            proj.draw(self.screen, (round(self.camera.x), round(self.camera.y)))
        self.player.draw(self.screen, (round(self.camera.x), round(self.camera.y)))

        for burst in self.particles:
            px = round(burst["pos"].x - self.camera.x)
            py = round(burst["pos"].y - self.camera.y)
            self.screen.fill(burst["color"], (px, py, 4, 4))

        for text in self.float_texts:
            label = self.world_font.render(text["text"], True, text["color"])
            self.screen.blit(label, (round(text["pos"].x - self.camera.x), round(text["pos"].y - self.camera.y)))

    def _draw_interact_prompt(self):
        npc = self._near_npc()
        if npc is None:
            return
        x = npc.rect.centerx - round(self.camera.x)
        y = npc.rect.centery - round(self.camera.y) - 44
        key = self.settings.keybinds.get("interact", pygame.K_e)
        label = self.world_font.render("[{}] {}".format(pygame.key.name(key).upper(), npc.prompt_label()), True, (255, 255, 255))
        self.screen.blit(label, label.get_rect(midbottom=(x, y)))

    def _draw_dialogue(self):
        if not self.dialogue:
            return
        box = pygame.Rect(18, self.settings.screen_height - 250, 520, 96)
        pygame.draw.rect(self.screen, (20, 17, 14), box)
        pygame.draw.rect(self.screen, (110, 92, 58), box, 2)
        name = self.world_font.render(self.dialogue["name"] + ":", True, (248, 214, 137))
        self.screen.blit(name, (box.x + 12, box.y + 10))
        y = box.y + 36
        for line in _wrap_text(self.dialogue["line"], 58):
            t = self.drop_font.render(line, True, (215, 210, 195))
            self.screen.blit(t, (box.x + 12, y))
            y += 18
        close = self.drop_font.render("press E to close", True, (140, 134, 124))
        self.screen.blit(close, (box.right - close.get_width() - 12, box.bottom - 20))

    def _draw_drop(self, drop):
        item, color, rarity = drop["item"]
        x = round(drop["pos"].x - self.camera.x)
        y = round(drop["pos"].y - self.camera.y) + int(math.sin(drop["phase"]) * 3)
        box = pygame.Rect(x - 13, y - 13, 26, 26)
        pygame.draw.rect(self.screen, (22, 26, 34), box)
        draw_item_icon(self.screen, drop["item"], box.inflate(-4, -4))
        pygame.draw.rect(self.screen, RARITY_BORDER.get(rarity, (140, 142, 148)), box, 2)
        label = self.drop_font.render(item, True, (205, 200, 190))
        self.screen.blit(label, (x - label.get_width() // 2, y - 28))

    def _draw_label(self, text, position, color):
        font = pygame.font.Font(None, 22)
        self.screen.blit(font.render(text, True, color), position)





