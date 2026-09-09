import math
import random

import pygame

from enemy import Ninja
from game_testing_environment_module import GameTestingEnvironment
from items import draw_item_icon
from player import Player
from settings import Settings
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


class Game:
    def __init__(self, settings=None, character=None):
        self.settings = settings if settings is not None else Settings()
        self.character = character or "knight"
        # Overworld also supports hold-to-shoot.
        self.mouse_held = False
        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        pygame.display.set_caption("ROTGM-Style Bullet Hell Test")
        self.clock = pygame.time.Clock()
        self.player_dead = False
        self.auto_shoot = False
        self.shoot_timer = 0
        self.drop_font = pygame.font.Font(None, 15)
        self._ability_hint = 0
        self._ability_msg = ""
        self._reset_world()

    def _reset_world(self):
        self.player = Player(self.screen, self.settings, self.character)
        self.ninja = Ninja((self.settings.world_width // 2, self.settings.world_height // 2 - 160))
        self.projectiles = []
        self.enemy_projectiles = []
        self.drops = []
        self.camera = pygame.Vector2()
        self.particles = []
        self.player_dead = False
        self.ui = UI(self.screen, self.settings)
        self.view_width = self.settings.screen_width - self.ui.panel.width
        # Always start with a weapon + ability equipped.
        self.ui.equipment["weapon"] = STARTER_WEAPON
        self.ui.equipment["ability"] = STARTER_ABILITY

    def run(self):
        """Main game loop. Returns True when the app should shut down (window closed)."""
        running = True
        exits = False
        shield_key = self.settings.keybinds.get("shield", pygame.K_SPACE)
        auto_shoot_key = self.settings.keybinds.get("auto_shoot", pygame.K_x)
        ability_key = self.settings.keybinds.get("ability", pygame.K_SPACE)
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exits = True
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == ability_key:
                        # SPACE = cast equipped ability (starter = 5s bubble).
                        mouse = pygame.mouse.get_pos()
                        world_mouse = (mouse[0] + self.camera.x, mouse[1] + self.camera.y)
                        self._cast_ability(world_mouse)
                    elif event.key == shield_key and shield_key != ability_key:
                        self.player.bubble_shield()
                    elif event.key == auto_shoot_key:
                        self.auto_shoot = not self.auto_shoot
                    else:
                        self.ui.handle_key(event, self.player)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.ui.panel.collidepoint(event.pos):
                        self.ui.handle_click(event.pos)
                    elif not self.ui.handle_world_click(event.pos):
                        self.mouse_held = True
                        mouse = pygame.mouse.get_pos()
                        world_mouse = (mouse[0] + self.camera.x, mouse[1] + self.camera.y)
                        # Rate-limited: fast clicking can't spam past attack speed.
                        self.projectiles.extend(self.player.try_attack(world_mouse, self.ui))
                elif event.type == pygame.MOUSEMOTION:
                    self.ui.handle_drag(event.pos)
                    self.ui.handle_hover(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.mouse_held = False
                    self.ui.handle_release(event.pos)

            if self.player_dead:
                action = self._run_death_screen()
                if action == "respawn":
                    self._reset_world()
                elif action == "menu":
                    running = False
                else:  # quit
                    exits = True
                    running = False
                continue

            self.player.update(pygame.key.get_pressed(), self.settings.keybinds)
            mouse = pygame.mouse.get_pos()
            world_mouse = (mouse[0] + self.camera.x, mouse[1] + self.camera.y)
            self.player.aim_at(world_mouse)
            # Hold-to-shoot at the weapon's attack speed.
            if self.mouse_held and not self.ui.panel.collidepoint(mouse):
                self.projectiles.extend(self.player.try_attack(world_mouse, self.ui))
            self._update_camera()
            if self.ninja.alive:
                self.ninja.update(self.player, self.enemy_projectiles)

            self.shoot_timer -= 1
            if self.auto_shoot and self.ninja.alive and self.shoot_timer <= 0:
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
                elif self.ninja.alive and proj.rect.colliderect(self.ninja.rect):
                    self.ninja.take_damage(proj.damage)
                    self.projectiles.remove(proj)
                    if not self.ninja.alive:
                        self._spawn_death_burst(
                            self.ninja.rect.center,
                            [(188, 205, 222), (118, 35, 49), (221, 215, 184), (26, 30, 34)],
                        )
                        self._maybe_drop_loot(self.ninja.rect.center)

            for star in self.enemy_projectiles[:]:
                star.update()
                if not self._in_world(star.rect):
                    self.enemy_projectiles.remove(star)
                elif star.rect.colliderect(self.player.rect):
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

            self._pickup_drops()

            self._draw_world()
            self.ui.draw_hud(self.player, self.auto_shoot)
            if self._ability_hint > 0:
                self._ability_hint -= 1
                hint = self.drop_font.render(getattr(self, "_ability_msg", "ABILITY ON COOLDOWN"), True, (255, 220, 120))
                self.ui.screen.blit(hint, (24, self.settings.screen_height - 190))
            self.ui.draw_inventory(self.player, self.camera, [self.ninja], self.drops, [self._building_landmark()])
            pygame.display.flip()
            self.clock.tick(60)
        return exits

    def _run_death_screen(self):
        big = pygame.font.Font(None, 88)
        sub = pygame.font.Font(None, 28)
        btn = pygame.font.Font(None, 34)
        cx = self.screen.get_width() // 2
        cy = self.screen.get_height() // 2
        title = big.render("YOU DIED", True, (228, 62, 62))
        title_rect = title.get_rect(center=(cx, cy - 130))
        flavor = sub.render("Your soul drifts back to the Nexus...", True, (170, 168, 160))
        flavor_rect = flavor.get_rect(center=(cx, cy - 55))
        respawn = btn.render("Respawn", True, (235, 232, 218))
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

    def _update_camera(self):
        target_x = self.player.rect.centerx - self.view_width // 2
        target_y = self.player.rect.centery - self.settings.screen_height // 2
        max_x = self.settings.world_width - self.view_width
        max_y = self.settings.world_height - self.settings.screen_height
        target_x = max(0, min(target_x, max_x))
        target_y = max(0, min(target_y, max_y))
        self.camera.x += (target_x - self.camera.x) * self.settings.camera_lerp
        self.camera.y += (target_y - self.camera.y) * self.settings.camera_lerp

    def _building_landmark(self):
        """World-space building rect + color for the minimap."""
        return (
            pygame.Rect(
                self.settings.world_width // 2 - 260,
                self.settings.world_height // 2 - 290,
                520,
                230,
            ),
            (90, 74, 62),
        )

    def _in_world(self, rect):
        return rect.right > 0 and rect.left < self.settings.world_width and rect.bottom > 0 and rect.top < self.settings.world_height

    def _cast_ability(self, world_mouse):
        try:
            ok, reason, payload = self.player.try_ability(world_mouse, self.ui)
        except Exception:
            return
        if not ok:
            # No ability equipped -> tell the player instead of crashing.
            if reason == "empty":
                self._ability_hint = 90
                self._ability_msg = "NO ABILITY EQUIPPED"
            elif reason == "mana":
                self._ability_hint = 45
                self._ability_msg = "NOT ENOUGH MANA"
            elif self.player.ability_cd > 0:
                self._ability_hint = 45
                self._ability_msg = "ABILITY ON COOLDOWN"
            return
        self._ability_hint = 0
        self._ability_msg = ""
        kind = reason
        try:
            if kind == "shots" and payload:
                self.projectiles.extend(payload)
            elif kind == "pulse" and isinstance(payload, dict):
                cx, cy = self.player.rect.center
                if self.ninja.alive:
                    nx, ny = self.ninja.rect.center
                    if math.hypot(nx - cx, ny - cy) <= payload.get("radius", 190):
                        self.ninja.take_damage(payload.get("damage", 30))
                self._spawn_death_burst((cx, cy), [(140, 240, 255), (90, 220, 255), (255, 255, 255)])
        except Exception:
            pass

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

        building = pygame.Rect(self.settings.world_width // 2 - 260, self.settings.world_height // 2 - 290, 520, 230)
        building_screen = building.move(-round(self.camera.x), -round(self.camera.y))
        pygame.draw.rect(self.screen, (77, 62, 58), building_screen)
        pygame.draw.rect(self.screen, (123, 93, 69), building_screen, 8)
        pygame.draw.rect(self.screen, (26, 29, 34), (building_screen.x + 190, building_screen.bottom - 12, 140, 22))
        pygame.draw.rect(self.screen, (54, 43, 42), (building_screen.x + 24, building_screen.y + 32, 78, 58))
        pygame.draw.rect(self.screen, (54, 43, 42), (building_screen.right - 102, building_screen.y + 32, 78, 58))
        self._draw_label("NINJA HIDEOUT", (building_screen.x + 168, building_screen.y + 14), (248, 214, 137))

        for drop in self.drops:
            self._draw_drop(drop)
        for star in self.enemy_projectiles:
            star.draw(self.screen, (round(self.camera.x), round(self.camera.y)))
        if self.ninja.alive:
            self.ninja.draw(self.screen, (round(self.camera.x), round(self.camera.y)))
        for proj in self.projectiles:
            proj.draw(self.screen, (round(self.camera.x), round(self.camera.y)))
        self.player.draw(self.screen, (round(self.camera.x), round(self.camera.y)))

        for burst in self.particles:
            px = round(burst["pos"].x - self.camera.x)
            py = round(burst["pos"].y - self.camera.y)
            self.screen.fill(burst["color"], (px, py, 4, 4))

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