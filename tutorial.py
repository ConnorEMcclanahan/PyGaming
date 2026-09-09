import math
import random

import pygame

from enemy import Chicken, GiantChickenBoss
from player import Player
from ui import UI

WORLD_W = 3000
WORLD_H = 768
TUT_BG = (27, 35, 43)

# Boss room + meadow layout (all x coordinates are world-space).
BOSS_ROOM_X = 1900      # west/entry door of the boss room
BOSS_ROOM_X2 = 2400     # east/exit door of the boss room
GRASS_X = 2500          # meadow starts here; ship lands on the grass
SHIP_PAD_X = 2730       # landing pad center on the meadow

CHEST_GEAR = [
    {"x": 1420, "item": ("NANO HELM", (150, 170, 200), "common", "helmet"), "opened": False},
    {"x": 1580, "item": ("PULSE BLADE", (120, 220, 255), "common", "weapon"), "opened": False},
]
ARROW_XS = [720, 1180, 1620, 2050]
BOSS_ARROW_X = 1820  # single arrow pointing into the boss room door


class Tutorial:
    """A guided tutorial stage in the style of ROTMG's 'chicken level':

    * Arrows point the way along the route.
    * A small chicken teaches combat.
    * Gear chests teach looting + equipping (right-side panel).
    * A giant chicken boss blocks the route - defeat it to call down
      a spaceship, board it, and fly to the overworld.
    """

    def __init__(self, screen, settings, character="knight"):
        self.screen = screen
        self.settings = settings
        self.character = character
        self.clock = pygame.time.Clock()
        self.ui = UI(screen, settings)
        self.view_width = screen.get_width() - self.ui.panel.width
        self.ui.equipment["weapon"] = ("PULSE BLADE", (120, 220, 255), "common", "weapon")
        self.ui.equipment["ability"] = ("HOLO SCROLL", (188, 205, 222), "common", "ability")

        self.player = Player(screen, settings, character)
        self.player.x = 420
        self.player.y = WORLD_H // 2
        self.player.rect.topleft = (self.player.x, self.player.y)

        self.chicken = Chicken((1120, WORLD_H // 2), pygame.Rect(850, 0, 650, WORLD_H))
        # Boss lives INSIDE its room; the east half of it is closed until dead.
        self.boss = GiantChickenBoss((2150, WORLD_H // 2), pygame.Rect(BOSS_ROOM_X + 30, 0, 340, WORLD_H))
        self.boss_door_open = False
        self.in_boss_room = False
        self.boss_fight_on = False
        self.projectiles = []
        self.egg_projectiles = []
        self.particles = []
        self.camera = pygame.Vector2()
        self.shoot_timer = 0
        self.auto_shoot = False
        self.mouse_held = False
        self.chests = [dict(c) for c in CHEST_GEAR]
        self.ship = None
        self.ship_beam = 0
        self.ship_msg = 0
        self.font_title = pygame.font.Font(None, 30)
        self.font_med = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 17)

    def run(self):
        auto_shoot_key = self.settings.keybinds.get("auto_shoot", pygame.K_x)
        ability_key = self.settings.keybinds.get("ability", pygame.K_SPACE)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "skipped"
                    if event.key == ability_key:
                        mouse = pygame.mouse.get_pos()
                        world_mouse = (mouse[0] + self.camera.x, mouse[1] + self.camera.y)
                        self._cast_ability(world_mouse)
                    elif event.key == auto_shoot_key:
                        self.auto_shoot = not self.auto_shoot
                    else:
                        self.ui.handle_key(event, self.player)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.ui.panel.collidepoint(event.pos):
                        self.ui.handle_click(event.pos)
                    elif not self.ui.handle_world_click(event.pos):
                        self.mouse_held = True
                        mouse = pygame.mouse.get_pos()
                        world_mouse = (mouse[0] + self.camera.x, mouse[1] + self.camera.y)
                        self.projectiles.extend(self.player.try_attack(world_mouse, self.ui))
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.mouse_held = False
                if event.type == pygame.MOUSEMOTION:
                    self.ui.handle_drag(event.pos)
                    self.ui.handle_hover(event.pos)
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.ui.handle_release(event.pos)

            if not self.boss.alive and not self.boss_door_open:
                # Boss down -> east room door swings open, ship heads for grass.
                self.boss_door_open = True
                if self.ship is None:
                    self._start_ship()

            self.player.update(pygame.key.get_pressed(), self.settings.keybinds)
            mouse = pygame.mouse.get_pos()
            world_mouse = (mouse[0] + self.camera.x, mouse[1] + self.camera.y)
            self.player.aim_at(world_mouse)
            self.player.x = max(0, min(self.player.x, WORLD_W - self.player.width))
            self.player.y = max(0, min(self.player.y, WORLD_H - self.player.height))
            self.player.rect.topleft = (self.player.x, self.player.y)
            # Boss-room doors: west always open; east locked until boss dies.
            # Keep the player fully inside or outside (no standing in doorway).
            self.in_boss_room = self.player.rect.centerx > BOSS_ROOM_X + 8
            if not self.boss_door_open and self.player.rect.centerx > BOSS_ROOM_X2 - 10:
                self.player.x = BOSS_ROOM_X2 - 10 - self.player.width // 2
                self.player.rect.topleft = (self.player.x, self.player.y)
            if not self.boss_fight_on and self.boss.alive and self.player.rect.centerx > BOSS_ROOM_X + 60:
                self.boss_fight_on = True

            # Hold-to-shoot: keep firing at the cursor while LMB is held.
            # try_attack() rate-limits to the weapon's attack speed.
            if self.mouse_held and not self.ui.panel.collidepoint(pygame.mouse.get_pos()):
                mouse = pygame.mouse.get_pos()
                world_mouse = (mouse[0] + self.camera.x, mouse[1] + self.camera.y)
                self.projectiles.extend(self.player.try_attack(world_mouse, self.ui))

            self.chicken.update()
            # Boss idles until you step inside its room (no long-range eggs).
            if self.boss.alive and self.boss_fight_on:
                self.boss.update(self.player, self.egg_projectiles)
            self._update_camera()
            self._auto_fire()
            self._update_projectiles()
            if self.ship is not None:
                self._update_ship()
            self._check_chests()

            for burst in self.particles[:]:
                burst["pos"] += burst["vel"]
                burst["vel"] *= 0.92
                burst["life"] -= 1
                if burst["life"] <= 0:
                    self.particles.remove(burst)

            if self.ship is not None and self.ship["landed"]:
                ship_rect = pygame.Rect(self.ship["x"] - 55, self.ship["land_y"] - 40, 110, 90)
                if ship_rect.colliderect(self.player.rect):
                    return "done"

            self._draw()
            pygame.display.flip()
            self.clock.tick(60)

    # ------------------------------------------------------------------ logic
    def _start_ship(self):
        # Ship flies in from the right edge of the world, high up, then
        # descends straight onto the grass meadow pad.
        self.ship = {
            "x": WORLD_W + 160,
            "y": -260,
            "land_x": SHIP_PAD_X,
            "land_y": WORLD_H // 2 - 52,
            "landed": False,
            "trail": 0,
        }
        self.ship_msg = 150

    def _update_ship(self):
        ship = self.ship
        if not ship["landed"]:
            # Fly left first, then descend once above the pad.
            if ship["x"] > ship["land_x"]:
                ship["x"] -= 9
                if random.random() < 0.5:
                    self._spawn_burst(
                        (ship["x"] + 50, ship["y"] + 10),
                        [(150, 220, 255), (200, 240, 255), (255, 255, 255)],
                    )
            else:
                ship["x"] = ship["land_x"]
                ship["y"] += 7
                if ship["y"] >= ship["land_y"]:
                    ship["y"] = ship["land_y"]
                    ship["landed"] = True
        self.ship_beam += 0.25
        if self.ship_msg > 0:
            self.ship_msg -= 1
        if ship["landed"] and random.random() < 0.12:
            self._spawn_burst(
                (ship["x"] + random.randint(-40, 40), ship["land_y"] + 42),
                [(120, 220, 120), (90, 200, 90), (190, 255, 190)],
            )

    def _update_camera(self):
        target_x = self.player.rect.centerx - self.view_width // 2
        max_x = WORLD_W - self.view_width
        target_x = max(0, min(target_x, max_x))
        self.camera.x += (target_x - self.camera.x) * 0.14

    def _auto_fire(self):
        import math as _math
        self.shoot_timer -= 1
        if self.auto_shoot and self.shoot_timer <= 0:
            shots = self.player.try_attack(
                (self.player.rect.centerx + _math.cos(self.player.aim_angle) * 600,
                 self.player.rect.centery + _math.sin(self.player.aim_angle) * 600),
                self.ui,
            )
            if shots:
                self.projectiles.extend(shots)
                self.shoot_timer = self.player.weapon_cooldown(self.ui)
            else:
                self.shoot_timer = 4

    def _cast_ability(self, world_mouse):
        try:
            ok, reason, payload = self.player.try_ability(world_mouse, self.ui)
        except Exception:
            return
        if not ok:
            return
        kind = reason
        try:
            if kind == "shots" and payload:
                self.projectiles.extend(payload)
            elif kind == "pulse" and isinstance(payload, dict):
                cx, cy = self.player.rect.center
                for foe in (self.chicken, self.boss):
                    try:
                        if foe.alive and _math.hypot(foe.rect.centerx - cx, foe.rect.centery - cy) <= payload.get("radius", 190):
                            foe.take_damage(payload.get("damage", 30))
                    except Exception:
                        continue
                self._spawn_burst((cx, cy), [(140, 240, 255), (90, 220, 255), (255, 255, 255)])
        except Exception:
            pass

    def _update_projectiles(self):
        for proj in self.projectiles[:]:
            proj.update()
            if not (0 <= proj.rect.x <= WORLD_W) or not (0 <= proj.rect.y <= WORLD_H):
                self.projectiles.remove(proj)
            elif self.chicken.alive and proj.rect.colliderect(self.chicken.rect):
                self.chicken.take_damage(proj.damage)
                self.projectiles.remove(proj)
                if not self.chicken.alive:
                    self._spawn_burst(
                        self.chicken.rect.center,
                        [(240, 230, 150), (230, 180, 60), (255, 240, 200), (120, 80, 40)],
                    )
            elif self.boss.alive and proj.rect.colliderect(self.boss.rect):
                self.boss.take_damage(proj.damage)
                self.projectiles.remove(proj)
                if not self.boss.alive:
                    self._spawn_burst(
                        self.boss.rect.center,
                        [(240, 230, 150), (230, 180, 60), (200, 40, 40), (255, 240, 200)],
                    )
            elif self.ship is not None and self.ship["landed"]:
                ship_rect = pygame.Rect(self.ship["x"] - 55, self.ship["land_y"] - 40, 110, 90)
                if proj.rect.colliderect(ship_rect):
                    self.projectiles.remove(proj)

        for egg in self.egg_projectiles[:]:
            egg.update()
            if not (0 <= egg.rect.x <= WORLD_W) or not (0 <= egg.rect.y <= WORLD_H):
                self.egg_projectiles.remove(egg)
            elif egg.rect.colliderect(self.player.rect):
                self.egg_projectiles.remove(egg)
                self._spawn_burst(egg.rect.center, [(245, 240, 225), (230, 190, 90)])

    def _check_chests(self):
        for chest in self.chests:
            if chest["opened"]:
                continue
            rect = pygame.Rect(chest["x"] - 24, WORLD_H // 2 - 20, 48, 40)
            if rect.colliderect(self.player.rect):
                chest["opened"] = True
                item = chest["item"]
                self._add_to_backpack(item)
                self._spawn_burst((chest["x"], WORLD_H // 2), [item[1], (255, 215, 90), (200, 200, 210)])

    def _add_to_backpack(self, item):
        return self.ui.add_item(item)

    def _spawn_burst(self, center, palette):
        for _ in range(24):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(1.0, 6.0)
            self.particles.append(
                {
                    "pos": pygame.Vector2(center),
                    "vel": pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                    "life": random.randint(12, 26),
                    "color": random.choice(palette),
                }
            )

    # ------------------------------------------------------------------ draw
    def _draw(self):
        w = self.screen.get_width()
        self.screen.fill(TUT_BG)
        pygame.draw.rect(self.screen, (34, 45, 53), (0, 0, w, WORLD_H))
        tile = 48
        start_x = int(self.camera.x // tile) * tile
        for x in range(start_x, int(self.camera.x) + w + tile, tile):
            sx = x - round(self.camera.x)
            pygame.draw.line(self.screen, (38, 50, 59), (sx, 0), (sx, WORLD_H))
        # Grass meadow east of the boss room (where the ship lands).
        gx = GRASS_X - round(self.camera.x)
        pygame.draw.rect(self.screen, (46, 80, 52), (gx, 0, w - gx + 400, WORLD_H))
        for x in range(int(GRASS_X // tile) * tile, WORLD_W + tile, tile):
            sx = x - round(self.camera.x)
            if -tile < sx < w + tile:
                pygame.draw.line(self.screen, (56, 96, 62), (sx, 0), (sx, WORLD_H))
        pygame.draw.rect(self.screen, (40, 68, 46), (gx, WORLD_H - 46, w - gx + 400, 46))

        self._draw_arrows()
        self._draw_back_gate()
        self._draw_boss_room()
        self._draw_chests()
        if self.chicken.alive:
            self.chicken.draw(self.screen, (round(self.camera.x), 0))
        if self.boss.alive:
            self.boss.draw(self.screen, (round(self.camera.x), 0))
        for egg in self.egg_projectiles:
            egg.draw(self.screen, (round(self.camera.x), 0))
        for proj in self.projectiles:
            proj.draw(self.screen, (round(self.camera.x), 0))
        if self.ship is not None:
            self._draw_ship()
        self.player.draw(self.screen, (round(self.camera.x), 0))
        for burst in self.particles:
            px = round(burst["pos"].x - self.camera.x)
            py = round(burst["pos"].y)
            self.screen.fill(burst["color"], (px, py, 4, 4))

        self.ui.draw_hud(self.player, self.auto_shoot)
        self.ui.draw_inventory(self.player, self.camera, [self.chicken, self.boss], [], self._landmarks(), (WORLD_W, WORLD_H))
        self._draw_instructions()

    def _landmarks(self):
        """World-space rects + colors for the minimap: gate, wall, chests, ship."""
        landmarks = [(pygame.Rect(140, WORLD_H // 2 - 70, 90, 140), (90, 80, 60))]
        if not self.wall_open:
            landmarks.append((pygame.Rect(self.wall_x - 4, WORLD_H // 2 - 170, 12, 340), (95, 76, 58)))
        for chest in self.chests:
            if not chest["opened"]:
                landmarks.append((pygame.Rect(chest["x"] - 24, WORLD_H // 2 - 20, 48, 40), (200, 168, 80)))
        if self.ship is not None:
            landmarks.append((pygame.Rect(self.ship["x"] - 55, self.ship["land_y"] - 40, 110, 90), (120, 190, 130)))
        return landmarks

    def _draw_arrows(self):
        t = pygame.time.get_ticks() / 1000
        for ax in ARROW_XS:
            x = ax - round(self.camera.x)
            if x < -60 or x > self.screen.get_width() + 60:
                continue
            y = WORLD_H // 2 + 78 + int(math.sin(t * 3 + ax) * 7)
            pygame.draw.rect(self.screen, (255, 190, 40), (x, y - 3, 26, 6))
            pygame.draw.polygon(self.screen, (255, 190, 40), [(x + 26, y - 9), (x + 44, y), (x + 26, y + 9)])
            pygame.draw.rect(self.screen, (140, 100, 40), (x, y - 3, 44, 6), 1)
        first = ARROW_XS[0] - round(self.camera.x)
        self._label("FOLLOW THE ARROWS ->", (first + 40, WORLD_H // 2 + 48), (255, 224, 130))

    def _draw_back_gate(self):
        x = 140 - round(self.camera.x)
        if x < -120 or x > self.screen.get_width() + 120:
            return
        y = WORLD_H // 2 - 70
        pygame.draw.rect(self.screen, (90, 80, 60), (x, y, 90, 140))
        pygame.draw.rect(self.screen, (150, 130, 90), (x, y, 90, 140), 6)
        self._label("THE GATE", (x + 45, y - 12), (248, 214, 137))

    def _draw_wall(self):
        x = self.wall_x - round(self.camera.x)
        y = WORLD_H // 2 - 170
        if self.wall_open:
            pygame.draw.rect(self.screen, (110, 90, 70), (x + 6, y, 60, 90))
            pygame.draw.rect(self.screen, (90, 72, 58), (x - 6, y + 100, 44, 70))
            self._label("WAY CLEARED!", (x, y - 16), (120, 220, 120))
            return
        pygame.draw.rect(self.screen, (95, 76, 58), (x - 4, y, 12, 340))
        for i in range(11):
            pygame.draw.rect(self.screen, (110, 88, 66), (x - 20, y + i * 30 - 8, 16, 12))
        self._label("SHIP PAD AHEAD!", (x, y - 16), (248, 214, 137))

    def _draw_chests(self):
        for chest in self.chests:
            x = chest["x"] - round(self.camera.x)
            y = WORLD_H // 2 + 6
            if chest["opened"]:
                pygame.draw.rect(self.screen, (70, 54, 38), (x - 22, y - 8, 44, 32))
                pygame.draw.line(self.screen, (50, 40, 28), (x - 22, y - 8), (x + 22, y - 8), 4)
                self._label("OPENED", (x, y - 26), (130, 160, 130))
            else:
                pygame.draw.rect(self.screen, (120, 92, 56), (x - 24, y - 4, 48, 36))
                pygame.draw.rect(self.screen, (200, 168, 80), (x - 24, y - 4, 48, 36), 3)
                pygame.draw.rect(self.screen, (240, 205, 110), (x - 8, y - 4, 16, 10))
                self._label("GEAR", (x, y - 26), (255, 224, 130))

    def _draw_ship(self):
        ship = self.ship
        x = ship["x"] - round(self.camera.x)
        y = round(ship["y"])
        if x < -160 or x > self.screen.get_width() + 160:
            return
        # Thruster flames while flying in.
        if not ship["landed"]:
            for i, off in enumerate((-14, 0, 14)):
                fl = 14 + int(math.sin(self.ship_beam * 6 + i) * 5)
                pygame.draw.polygon(
                    self.screen,
                    (255, 190, 90),
                    [(x - 52 + off - 5, y + 2), (x - 52 + off + 5, y + 2), (x - 52 + off, y + 2 + fl + 14)],
                )
                pygame.draw.polygon(
                    self.screen,
                    (255, 240, 180),
                    [(x - 52 + off - 2, y + 2), (x - 52 + off + 2, y + 2), (x - 52 + off, y + 2 + fl)],
                )
            self._label("SHIP INCOMING!", (x, y - 44), (150, 220, 255))
        if ship["landed"]:
            beam_w = 20 + int(math.sin(self.ship_beam * 2) * 3)
            beam = pygame.Surface((beam_w, ship["land_y"] + 60 - y), pygame.SRCALPHA)
            beam.fill((90, 220, 110, 110))
            self.screen.blit(beam, (x - beam_w // 2, int(ship["land_y"])))
        pygame.draw.ellipse(self.screen, (120, 190, 130), (x - 46, y - 8, 92, 34))
        pygame.draw.ellipse(self.screen, (200, 240, 190), (x - 16, y - 24, 34, 20))
        pygame.draw.rect(self.screen, (150, 215, 155), (x - 18, y - 4, 36, 8))
        pygame.draw.circle(self.screen, (80, 170, 90), (x - 32, y + 2), 5)
        pygame.draw.circle(self.screen, (80, 170, 90), (x + 32, y + 2), 5)
        pygame.draw.ellipse(self.screen, (90, 200, 110), (x - 56, y - 14, 112, 46), 2)
        if ship["landed"]:
            self._label("ENTER THE SHIP!", (x, y - 44), (255, 210, 120))

    def _draw_instructions(self):
        panel = self.ui.panel
        cx = max(30, (panel.x - 560) // 2)
        box = pygame.Rect(cx, 10, 560, 118)
        pygame.draw.rect(self.screen, (20, 20, 24), box)
        pygame.draw.rect(self.screen, (110, 92, 58), box, 2)
        lines = self._instruction_lines()
        y = box.y + 10
        for i, line in enumerate(lines):
            font = self.font_title if i == 0 else self.font_small
            color = (235, 232, 218) if i == 0 else (180, 174, 162)
            surf = font.render(line, True, color)
            self.screen.blit(surf, (box.centerx - surf.get_width() // 2, y))
            y += 24

    def _instruction_lines(self):
        equip_count = sum(1 for v in self.ui.equipment.values() if v is not None)
        if self.chicken.alive:
            return [
                "WELCOME, KNIGHT!",
                "Move: WASD   |   Shoot: Left Click (auto shoot with X)",
                "Follow the arrows and defeat the CHICKEN ahead!",
            ]
        if self.boss.alive and equip_count == 0:
            return [
                "NICE SHOT!",
                "Grab the gear from the chests below, then drag items",
                "from your BACKPACK to a slot in the right panel!",
            ]
        if self.boss.alive:
            return [
                "YOU'RE EQUIPPED!",
                "The GIANT CHICKEN blocks the way - defeat it to call",
                "down the spaceship! X = auto shoot, LMB = manual slash.",
            ]
        return [
            "BOSS DOWN!",
            "The SPACESHIP is descending - wait for it to land, then",
            "walk into the beam to fly to the safe town in the overworld!",
        ]

    def _label(self, text, center, color):
        surf = self.font_small.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(center=(center[0], center[1])))