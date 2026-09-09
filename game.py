import math
import random

import pygame

from enemy import Ninja, NinjaBoss, Slime, SlimeBoss
from game_testing_environment_module import GameTestingEnvironment
from items import LOOT_TABLE, ORB_ITEMS, ORB_ORDER, draw_item_icon, item_slot, orb_key
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

# Wilderness layout:
# - Beach in the south (town side) with water, ocean going further south
# - Slime Ruins: east of town - beginner area with lots of slimes
# - Ninja Hideout: far south of town - advanced area
# Town gate is at x=1250, y=2420-2660. Town spans y=1800 to y=3280.

# Beach & Water (south, on town side)
BEACH_TOP = 3400       # Sandy beach starts just below town
BEACH_BOTTOM = 3700    # Beach ends, shallow water begins
SHALLOW_TOP = 3700
SHALLOW_BOTTOM = 4000  # Shallow water (walkable)
DEEP_WATER_TOP = 4000  # Deep water (blocked)
DEEP_WATER_BOTTOM = 4500  # Deep water ends here

# Slime Ruins - east of town (beginner area) - more slimes, moved east
STARTER_SLIMES = [
    (1900, 2000, "green"), (2100, 2100, "green"), (2000, 2300, "green"),
    (2200, 2000, "blue"), (2300, 2200, "green"), (2100, 2500, "green"),
    (2400, 2100, "blue"), (2200, 2400, "green"), (2500, 2300, "blue"),
    (2000, 2600, "green"), (2300, 2500, "green"), (2600, 2200, "blue"),
]
SLIME_BOSS_POS = (2200, 2200)  # Slime boss in the ruins
SLIME_RUIN_RECT = pygame.Rect(1800, 1900, 900, 800)  # Ruin structure area

# Ninja Hideout - far south of town (advanced area)
WILDERNESS_NINJAS = [
    (1500, 5500), (1700, 5700), (1400, 5900), (1800, 6100),
    (2000, 5600), (2100, 5800), (1900, 6200), (2200, 6000),
]
RING_NINJAS = [
    (2400, 5600), (2300, 5800), (2100, 5900), (1900, 5800),
    (1800, 5600), (1900, 5400), (2100, 5300), (2300, 5400),
]
BOSS_POS = (2100, 5700)   # Ninja boss hideout - far south of town
NINJA_HIDEOUT_RECT = pygame.Rect(1700, 5200, 900, 900)  # Southern hideout area

INTERACT_RANGE = 95

NINJA_DEATH_PALETTE = [(188, 205, 222), (118, 35, 49), (221, 215, 184), (26, 30, 34)]
SLIME_DEATH_PALETTE = [(80, 180, 80), (120, 220, 120), (60, 140, 60), (100, 200, 100)]

# Water rectangles for collision
DEEP_WATER_RECTS = [
    pygame.Rect(0, DEEP_WATER_TOP, 8000, DEEP_WATER_BOTTOM - DEEP_WATER_TOP),
]


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
        self.camera_angle = 0.0     # Q/E spin the whole view around you
        self.wave_time = 0.0        # animated wave timer
        self.drop_font = pygame.font.Font(None, 15)
        self.world_font = pygame.font.Font(None, 17)
        self._ability_hint = 0
        self._ability_msg = ""
        self.menu = None            # open ShopMenu (pauses the world)
        self.dialogue = None        # villager chatter: {name, line, life}
        self.float_texts = []       # floating "+GOLD" style labels
        self.vault_items = [None] * VAULT_SIZE
        # Level-up system
        self.level_up_choices = []  # 3 skill choices for level up
        self.show_level_up = False  # Whether to show level-up UI
        self.skill_tree_open = False  # Whether skill tree is open
        self._reset_world()

    # ------------------------------------------------------------ world setup
    def _reset_world(self):
        """Full reset (fresh session): new UI, empty vault, town spawn."""
        self.ui = UI(self.screen, self.settings)
        self.view_width = self.settings.screen_width - self.ui.panel.width
        # Offscreen surface the world renders onto (rotated for Q/E camera).
        self.world_surf = pygame.Surface((self.view_width, self.settings.screen_height), pygame.SRCALPHA)
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
        """Spawn slimes (starter area) and ninjas (advanced area)."""
        self.ninjas = []
        self.slimes = []
        
        # Slimes near town - beginner area
        for x, y, variant in STARTER_SLIMES:
            self.slimes.append(Slime((x, y), variant, self._patrol_bounds(x, y, 150, 100)))
        
        # Slime boss near starter area
        self.slime_boss = SlimeBoss(SLIME_BOSS_POS, self._patrol_bounds(SLIME_BOSS_POS[0], SLIME_BOSS_POS[1], 200, 150))
        self.slimes.append(self.slime_boss)
        
        # Ninjas - advanced area far from town
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
        interact_key = self.settings.keybinds.get("interact", pygame.K_f)
        rotate_left_key = self.settings.keybinds.get("rotate_left", pygame.K_q)
        rotate_right_key = self.settings.keybinds.get("rotate_right", pygame.K_e)
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exits = True
                    running = False
                elif event.type == pygame.KEYDOWN:
                    # Respec confirmation
                    if getattr(self, '_show_respec_confirm', False):
                        if event.key == pygame.K_y:
                            if self._do_respec():
                                self.float_texts.append(
                                    {
                                        "text": "Skills reset!",
                                        "pos": pygame.Vector2(self.player.rect.centerx, self.player.rect.top - 40),
                                        "life": 90,
                                        "color": (255, 215, 0),
                                    }
                                )
                            else:
                                self.float_texts.append(
                                    {
                                        "text": "Not enough orbs!",
                                        "pos": pygame.Vector2(self.player.rect.centerx, self.player.rect.top - 40),
                                        "life": 90,
                                        "color": (255, 100, 100),
                                    }
                                )
                        elif event.key == pygame.K_n:
                            self._show_respec_confirm = False
                        continue
                    
                    # Level-up skill selection
                    if self.show_level_up and self.level_up_choices:
                        if event.key == pygame.K_1 and len(self.level_up_choices) >= 1:
                            self._select_skill(self.level_up_choices[0])
                        elif event.key == pygame.K_2 and len(self.level_up_choices) >= 2:
                            self._select_skill(self.level_up_choices[1])
                        elif event.key == pygame.K_3 and len(self.level_up_choices) >= 3:
                            self._select_skill(self.level_up_choices[2])
                        continue
                    
                    # Skill tree toggle
                    if event.key == pygame.K_t:
                        self.skill_tree_open = not self.skill_tree_open
                        continue
                    
                    if self.menu is not None:
                        # Modal menu: ESC or the interact key closes it.
                        if event.key in (pygame.K_ESCAPE, interact_key):
                            self.menu = None
                        continue
                    if event.key == ability_key:
                        # SPACE = cast equipped ability (starter = 5s bubble).
                        mouse = pygame.mouse.get_pos()
                        world_mouse = self._screen_to_world(mouse)
                        self._cast_ability(world_mouse)
                    elif event.key == shield_key and shield_key != ability_key:
                        self.player.bubble_shield()
                    elif event.key == auto_shoot_key:
                        self.auto_shoot = not self.auto_shoot
                    elif event.key == interact_key:
                        self._try_interact()
                    elif event.key == rotate_left_key:
                        self.camera_angle = (self.camera_angle + 15) % 360
                    elif event.key == rotate_right_key:
                        self.camera_angle = (self.camera_angle - 15) % 360
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
                        world_mouse = self._screen_to_world(mouse)
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
            self.wave_time += 0.05
        return exits

    # ------------------------------------------------------------------ update
    def _update_world(self):
        prev_x, prev_y = self.player.x, self.player.y
        self.player.update(pygame.key.get_pressed(), self.settings.keybinds)
        # Hold Q / E to keep spinning the camera.
        keys = pygame.key.get_pressed()
        binds = self.settings.keybinds
        if keys[binds.get("rotate_left", pygame.K_q)]:
            self.camera_angle = (self.camera_angle + 2.5) % 360
        if keys[binds.get("rotate_right", pygame.K_e)]:
            self.camera_angle = (self.camera_angle - 2.5) % 360
        self._resolve_town_collision(prev_x, prev_y)
        mouse = pygame.mouse.get_pos()
        world_mouse = self._screen_to_world(mouse)
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
            for slime in self.slimes:
                if slime.alive:
                    slime.update(self.player, self.enemy_projectiles)

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
            # Check ninja hits
            for ninja in self.ninjas:
                if ninja.alive and proj.rect.colliderect(ninja.rect):
                    ninja.take_damage(proj.damage)
                    self.projectiles.remove(proj)
                    if not ninja.alive:
                        self._on_enemy_killed(ninja)
                    break
            # Check slime hits
            for slime in self.slimes:
                if slime.alive and proj.rect.colliderect(slime.rect):
                    slime.take_damage(proj.damage)
                    self.projectiles.remove(proj)
                    if not slime.alive:
                        self._on_enemy_killed(slime)
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
        """Axis-separated collision against town walls, buildings, the
        hideout, and deep water. The gate gap in the east wall is the only way in/out."""
        solids = self._solid_rects()
        # Add deep water as solid (shallow water is walkable)
        solids = solids + DEEP_WATER_RECTS
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
        """Death burst + item loot + orb currency drops (POE-style)."""
        # Use correct death palette
        if isinstance(enemy, (Slime, SlimeBoss)):
            palette = SLIME_DEATH_PALETTE
        else:
            palette = NINJA_DEATH_PALETTE
        
        self._spawn_death_burst(enemy.rect.center, palette)
        self._maybe_drop_loot(enemy.rect.center)
        
        boss = enemy is self.boss or enemy is self.slime_boss
        self._drop_orbs(enemy.rect.center, boss)
        
        # Give EXP and check for level up
        exp_reward = getattr(enemy, 'exp_reward', 10)
        leveled_up = self.player.gain_exp(exp_reward)
        
        # Show EXP gain
        self.float_texts.append(
            {
                "text": f"+{exp_reward} EXP",
                "pos": pygame.Vector2(enemy.rect.centerx, enemy.rect.top - 50),
                "life": 60,
                "color": (100, 200, 255),
            }
        )
        
        if boss:
            if enemy is self.slime_boss:
                boss_name = "KING SLIME"
                color = (100, 255, 100)
            else:
                boss_name = "THE WARLORD"
                color = (255, 130, 50)
            self.float_texts.append(
                {
                    "text": f"{boss_name} FALLS!",
                    "pos": pygame.Vector2(enemy.rect.centerx, enemy.rect.top - 34),
                    "life": 90,
                    "color": color,
                }
            )
        
        if leveled_up:
            self._on_level_up()
    
    def _on_level_up(self):
        """Handle level up - show skill choices."""
        self.player.apply_skill_effects()
        self.level_up_choices = self.player.skill_tree.get_random_choices(3)
        self.show_level_up = True

    def _drop_orbs(self, position, boss=False):
        """Scatter physical orb pickups around the corpse."""
        if boss:
            plan = [("singularity", 2), ("quantum", 4), ("phase", 6), ("scrap", 8)]
        else:
            plan = []
            if random.random() < 0.45:
                plan.append(("scrap", random.randint(1, 2)))
            if random.random() < 0.15:
                plan.append(("phase", 1))
            if random.random() < 0.05:
                plan.append(("quantum", 1))
        for key, count in plan:
            for _ in range(count):
                offset = pygame.Vector2(random.uniform(-36, 36), random.uniform(-26, 26))
                self.drops.append(
                    {
                        "item": ORB_ITEMS[key],
                        "pos": pygame.Vector2(position) + offset,
                        "phase": random.uniform(0, math.tau),
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
                if item_slot(drop["item"]) == "currency":
                    # Orbs go straight to the pouch, they never fill the pack.
                    key = orb_key(drop["item"])
                    self.player.add_orb(key)
                    self.drops.remove(drop)
                    self._spawn_pickup_burst(drop_rect.center, drop["item"][1])
                    self.float_texts.append(
                        {
                            "text": "+1 {}".format(drop["item"][0]),
                            "pos": pygame.Vector2(drop_rect.centerx, drop_rect.top - 14),
                            "life": 55,
                            "color": drop["item"][1],
                        }
                    )
                elif self._add_to_backpack(drop["item"]):
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
    def _screen_to_world(self, screen_pos):
        """Map a screen position to world coordinates, inverting the camera
        rotation so aiming stays accurate at any Q/E angle."""
        view_c = pygame.Vector2(self.view_width / 2, self.settings.screen_height / 2)
        offset = pygame.Vector2(screen_pos) - view_c
        if self.camera_angle % 360 != 0:
            offset = offset.rotate(self.camera_angle)
        p = offset + view_c
        return (p.x + self.camera.x, p.y + self.camera.y)

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
            if npc.role == "respec":
                self._open_respec_menu()
            else:
                self.menu = ShopMenu(self.screen, self.ui, self.player, npc.role, vault=self.vault_items)
        else:
            self.dialogue = {"name": npc.name, "line": npc.line, "life": 300}
    
    def _open_respec_menu(self):
        """Open the respec confirmation dialog."""
        self._show_respec_confirm = True
    
    def _draw_respec_confirm(self):
        """Draw the respec confirmation overlay."""
        if not getattr(self, '_show_respec_confirm', False):
            return
        
        overlay = pygame.Surface((self.settings.screen_width, self.settings.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        font_title = pygame.font.Font(None, 36)
        title = font_title.render("RESET SKILLS?", True, (255, 215, 0))
        self.screen.blit(title, (self.settings.screen_width//2 - title.get_width()//2, 200))
        
        font_text = pygame.font.Font(None, 24)
        text = font_text.render("This will refund all skill points.", True, (200, 200, 200))
        self.screen.blit(text, (self.settings.screen_width//2 - text.get_width()//2, 260))
        
        cost_text = font_text.render("Cost: 5 Phase Orbs", True, (100, 200, 255))
        self.screen.blit(cost_text, (self.settings.screen_width//2 - cost_text.get_width()//2, 300))
        
        font_key = pygame.font.Font(None, 22)
        yes = font_key.render("Press Y to confirm", True, (100, 255, 100))
        self.screen.blit(yes, (self.settings.screen_width//2 - yes.get_width()//2, 360))
        
        no = font_key.render("Press N to cancel", True, (255, 100, 100))
        self.screen.blit(no, (self.settings.screen_width//2 - no.get_width()//2, 400))
    
    def _do_respec(self):
        """Reset all skills and refund points."""
        if self.player.orbs.get("phase", 0) >= 5:
            self.player.orbs["phase"] -= 5
            points = self.player.skill_tree.total_points_spent
            self.player.skill_tree.reset()
            self.player.skill_points = points
            self.player.bonus_health = 0
            self.player.apply_skill_effects()
            self._show_respec_confirm = False
            return True
        return False

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
            elif kind in ("pulse", "well", "phoenix", "cryo") and isinstance(payload, dict):
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
                if kind == "well":
                    # Gravity Well also collapses incoming shots near you.
                    for star in self.enemy_projectiles[:]:
                        sx, sy = star.rect.center
                        if math.hypot(sx - cx, sy - cy) <= radius:
                            self.enemy_projectiles.remove(star)
                            self._spawn_death_burst(star.rect.center, [(150, 120, 255), (200, 180, 255)])
                self._spawn_death_burst((cx, cy), [(140, 240, 255), (90, 220, 255), (255, 255, 255)])
        except Exception:
            pass

    def _landmarks(self):
        """World-space rects + colors for the minimap."""
        landmarks = [
            (TOWN_RECT, (52, 74, 52)),
            (GATE_RECT, (200, 168, 80)),
        ]
        for spec in BUILDINGS:
            landmarks.append((spec["rect"], (150, 110, 70)))
        # Beach (sandy south, town side)
        landmarks.append((pygame.Rect(0, BEACH_TOP, 8000, BEACH_BOTTOM - BEACH_TOP), (214, 198, 146)))
        # Shallow water (walkable)
        landmarks.append((pygame.Rect(0, SHALLOW_TOP, 8000, SHALLOW_BOTTOM - SHALLOW_TOP), (80, 160, 200)))
        # Deep water (blocked)
        landmarks.append((pygame.Rect(0, DEEP_WATER_TOP, 8000, DEEP_WATER_BOTTOM - DEEP_WATER_TOP), (40, 100, 160)))
        # Slime Ruins (east of town)
        landmarks.append((SLIME_RUIN_RECT, (100, 120, 60)))
        landmarks.append((pygame.Rect(SLIME_BOSS_POS[0] - 40, SLIME_BOSS_POS[1] - 40, 80, 80), (100, 200, 100)))
        # Ninja Hideout (south)
        landmarks.append((NINJA_HIDEOUT_RECT, (120, 44, 44)))
        landmarks.append((pygame.Rect(BOSS_POS[0] - 55, BOSS_POS[1] - 55, 110, 110), (214, 60, 62)))
        return landmarks

    # ------------------------------------------------------------------ draw
    def _draw_all(self):
        self._draw_world()
        # Spin the rendered world around the view center (Q/E camera) so
        # things hidden under the inventory panel can be brought into view.
        self.screen.fill((8, 10, 14))
        if self.camera_angle % 360 == 0:
            self.screen.blit(self.world_surf, (0, 0))
        else:
            rotated = pygame.transform.rotate(self.world_surf, self.camera_angle)
            rect = rotated.get_rect(center=(self.view_width // 2, self.settings.screen_height // 2))
            self.screen.blit(rotated, rect)
        # Out of the tutorial: no more hand-holding text, just your orbs.
        self.ui.draw_hud(self.player, self.auto_shoot, show_auto_shoot=False, show_orbs=True)
        if self._ability_hint > 0:
            self._ability_hint -= 1
            hint = self.drop_font.render(getattr(self, "_ability_msg", "ABILITY ON COOLDOWN"), True, (255, 220, 120))
            self.ui.screen.blit(hint, (24, self.settings.screen_height - 190))
        self.ui.draw_inventory(self.player, self.camera, [n for n in self.ninjas if n.alive], self.drops, self._landmarks())
        self._draw_compass()
        self._draw_dialogue()
        self._draw_level_up_ui()
        self._draw_skill_tree_ui()
        self._draw_respec_confirm()

    def _draw_compass(self):
        """Tiny arrow on the minimap showing which world way is screen-up."""
        rect = self.ui.minimap_rect
        ws, hs = self.settings.world_width, self.settings.world_height
        px = rect.x + self.player.rect.centerx / ws * rect.width
        py = rect.y + self.player.rect.centery / hs * rect.height
        ang = math.radians(self.camera_angle)
        dx, dy = math.sin(ang), -math.cos(ang)
        pygame.draw.line(self.screen, (120, 220, 255), (px, py), (px + dx * 14, py + dy * 14), 2)
        pygame.draw.circle(self.screen, (120, 220, 255), (round(px + dx * 16), round(py + dy * 16)), 2)

    def _draw_world(self):
        surf = self.world_surf
        surf.fill(self.settings.background_color)
        arena = pygame.Rect(0, 0, self.view_width, self.settings.screen_height)
        pygame.draw.rect(surf, (34, 45, 53), arena)
        tile = 48
        start_x = int(self.camera.x // tile) * tile
        start_y = int(self.camera.y // tile) * tile
        for x in range(start_x, int(self.camera.x) + self.view_width + tile, tile):
            screen_x = x - round(self.camera.x)
            pygame.draw.line(surf, (38, 50, 59), (screen_x, 0), (screen_x, self.settings.screen_height))
        for y in range(start_y, int(self.camera.y) + self.settings.screen_height + tile, tile):
            screen_y = y - round(self.camera.y)
            pygame.draw.line(surf, (38, 50, 59), (0, screen_y), (self.view_width, screen_y))

        # Beach (sandy area in south, town side)
        beach_rect = pygame.Rect(0, BEACH_TOP, 8000, BEACH_BOTTOM - BEACH_TOP)
        screen_beach = beach_rect.move(-round(self.camera.x), -round(self.camera.y))
        pygame.draw.rect(surf, (214, 198, 146), screen_beach)
        # Sand texture dots
        for sx in range(0, 8000, 60):
            for sy in range(BEACH_TOP, BEACH_BOTTOM, 60):
                pygame.draw.circle(surf, (196, 180, 130), (sx - round(self.camera.x), sy - round(self.camera.y)), 2)

        # Shallow water (walkable) with animated waves
        shallow_rect = pygame.Rect(0, SHALLOW_TOP, 8000, SHALLOW_BOTTOM - SHALLOW_TOP)
        screen_shallow = shallow_rect.move(-round(self.camera.x), -round(self.camera.y))
        pygame.draw.rect(surf, (80, 160, 200), screen_shallow)
        # Animated wave lines in shallow water
        for sy in range(SHALLOW_TOP, SHALLOW_BOTTOM, 25):
            for sx in range(0, 8000, 60):
                wave_offset = math.sin(self.wave_time + sx * 0.02 + sy * 0.01) * 4
                pygame.draw.arc(surf, (100, 180, 220),
                    (sx - round(self.camera.x), sy - round(self.camera.y) + wave_offset, 35, 12), 0, 3.14, 2)

        # Deep water (blocked - darker) with animated waves
        deep_rect = pygame.Rect(0, DEEP_WATER_TOP, 8000, DEEP_WATER_BOTTOM - DEEP_WATER_TOP)
        screen_deep = deep_rect.move(-round(self.camera.x), -round(self.camera.y))
        pygame.draw.rect(surf, (40, 100, 160), screen_deep)
        # Animated deep water waves
        for sy in range(DEEP_WATER_TOP, DEEP_WATER_BOTTOM, 40):
            for sx in range(0, 8000, 80):
                wave_offset = math.sin(self.wave_time * 1.3 + sx * 0.015 + sy * 0.02) * 6
                pygame.draw.arc(surf, (60, 120, 180),
                    (sx - round(self.camera.x), sy - round(self.camera.y) + wave_offset, 45, 18), 0, 3.14, 2)

        # Slime Ruins (east of town)
        ruin = SLIME_RUIN_RECT.move(-round(self.camera.x), -round(self.camera.y))
        # Crumbled stone floor
        pygame.draw.rect(surf, (80, 75, 65), ruin)
        pygame.draw.rect(surf, (60, 55, 45), ruin, 4)
        # Broken pillars
        for px in [ruin.x + 30, ruin.x + 150, ruin.x + 300, ruin.x + 400]:
            pygame.draw.rect(surf, (100, 90, 75), (px, ruin.y + 20, 20, 80))
            pygame.draw.rect(surf, (80, 70, 55), (px - 5, ruin.y + 10, 30, 15))
        # Moss patches
        for mx in range(ruin.x + 20, ruin.right - 20, 80):
            for my in range(ruin.y + 30, ruin.bottom - 30, 60):
                pygame.draw.ellipse(surf, (60, 90, 50), (mx, my, 25, 15))
        self._draw_label("SLIME RUINS", (ruin.centerx, ruin.y - 10), (180, 220, 120))

        # Ninja Hideout (south of town)
        hideout = NINJA_HIDEOUT_RECT.move(-round(self.camera.x), -round(self.camera.y))
        pygame.draw.rect(surf, (60, 50, 55), hideout)
        pygame.draw.rect(surf, (100, 80, 70), hideout, 6)
        # Hideout building
        building_rect = pygame.Rect(hideout.centerx - 150, hideout.centery - 100, 300, 200)
        pygame.draw.rect(surf, (45, 40, 45), building_rect)
        pygame.draw.rect(surf, (80, 65, 55), building_rect, 6)
        pygame.draw.rect(surf, (26, 29, 34), (building_rect.x + 100, building_rect.bottom - 15, 100, 15))
        # Guard towers
        for tx in [hideout.x + 50, hideout.right - 70]:
            pygame.draw.rect(surf, (55, 50, 50), (tx, hideout.y + 30, 20, 60))
            pygame.draw.rect(surf, (75, 60, 50), (tx - 5, hideout.y + 20, 30, 15))
        self._draw_label("NINJA HIDEOUT", (hideout.centerx, hideout.y - 10), (248, 214, 137))

        # Safe town + wilderness hideout.
        draw_town(surf, (self.camera.x, self.camera.y))

        for drop in self.drops:
            self._draw_drop(drop)
        for star in self.enemy_projectiles:
            star.draw(surf, (round(self.camera.x), round(self.camera.y)))
        for ninja in self.ninjas:
            if ninja.alive:
                ninja.draw(surf, (round(self.camera.x), round(self.camera.y)))
        for slime in self.slimes:
            if slime.alive:
                slime.draw(surf, (round(self.camera.x), round(self.camera.y)))
        for npc in self.npcs:
            npc.draw(surf, (round(self.camera.x), round(self.camera.y)))
        for proj in self.projectiles:
            proj.draw(surf, (round(self.camera.x), round(self.camera.y)))
        self.player.draw(surf, (round(self.camera.x), round(self.camera.y)))

        for burst in self.particles:
            px = round(burst["pos"].x - self.camera.x)
            py = round(burst["pos"].y - self.camera.y)
            surf.fill(burst["color"], (px, py, 4, 4))

        self._draw_interact_prompt()

        for text in self.float_texts:
            label = self.world_font.render(text["text"], True, text["color"])
            surf.blit(label, (round(text["pos"].x - self.camera.x), round(text["pos"].y - self.camera.y)))

    def _draw_interact_prompt(self):
        npc = self._near_npc()
        if npc is None:
            return
        x = npc.rect.centerx - round(self.camera.x)
        y = npc.rect.centery - round(self.camera.y) - 44
        key = self.settings.keybinds.get("interact", pygame.K_f)
        label = self.world_font.render("[{}] {}".format(pygame.key.name(key).upper(), npc.prompt_label()), True, (255, 255, 255))
        self.world_surf.blit(label, label.get_rect(midbottom=(x, y)))

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
        item = drop["item"]
        name, color, rarity = item[0], item[1], item[2]
        x = round(drop["pos"].x - self.camera.x)
        y = round(drop["pos"].y - self.camera.y) + int(math.sin(drop["phase"]) * 3)
        box = pygame.Rect(x - 13, y - 13, 26, 26)
        pygame.draw.rect(self.world_surf, (22, 26, 34), box)
        draw_item_icon(self.world_surf, drop["item"], box.inflate(-4, -4))
        pygame.draw.rect(self.world_surf, RARITY_BORDER.get(rarity, (140, 142, 148)), box, 2)
        label = self.drop_font.render(name, True, (205, 200, 190))
        self.world_surf.blit(label, (x - label.get_width() // 2, y - 28))

    def _draw_label(self, text, position, color):
        font = pygame.font.Font(None, 22)
        self.world_surf.blit(font.render(text, True, color), position)


    def _draw_level_up_ui(self):
        """Draw the level-up skill selection overlay."""
        if not self.show_level_up or not self.level_up_choices:
            return
        
        overlay = pygame.Surface((self.settings.screen_width, self.settings.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        font_title = pygame.font.Font(None, 48)
        title = font_title.render(f"LEVEL UP! Level {self.player.level}", True, (255, 215, 0))
        self.screen.blit(title, (self.settings.screen_width//2 - title.get_width()//2, 80))
        
        font_sub = pygame.font.Font(None, 24)
        subtitle = font_sub.render("Choose a skill to upgrade:", True, (200, 200, 200))
        self.screen.blit(subtitle, (self.settings.screen_width//2 - subtitle.get_width()//2, 130))
        
        from skills import ALL_SKILLS
        card_width = 250
        card_height = 180
        gap = 30
        total_width = card_width * 3 + gap * 2
        start_x = self.settings.screen_width//2 - total_width//2
        y = 200
        
        self._skill_rects = []
        for i, skill_id in enumerate(self.level_up_choices):
            skill = ALL_SKILLS[skill_id]
            x = start_x + i * (card_width + gap)
            rect = pygame.Rect(x, y, card_width, card_height)
            self._skill_rects.append((rect, skill_id))
            
            pygame.draw.rect(self.screen, (40, 45, 55), rect)
            pygame.draw.rect(self.screen, (100, 150, 200), rect, 3)
            
            font_name = pygame.font.Font(None, 28)
            name = font_name.render(skill["name"], True, (255, 255, 255))
            self.screen.blit(name, (x + card_width//2 - name.get_width()//2, y + 15))
            
            font_cat = pygame.font.Font(None, 18)
            cat_color = {"combat": (255, 100, 100), "defense": (100, 200, 255), "utility": (100, 255, 100)}
            cat = font_cat.render(skill["category"].upper(), True, cat_color.get(skill["category"], (200, 200, 200)))
            self.screen.blit(cat, (x + card_width//2 - cat.get_width()//2, y + 50))
            
            font_desc = pygame.font.Font(None, 20)
            desc = font_desc.render(skill["description"], True, (180, 180, 180))
            self.screen.blit(desc, (x + card_width//2 - desc.get_width()//2, y + 85))
            
            rank = self.player.skill_tree.get_rank(skill_id)
            max_rank = skill["max_rank"]
            font_rank = pygame.font.Font(None, 22)
            rank_text = font_rank.render(f"Rank: {rank}/{max_rank}", True, (255, 215, 0) if rank > 0 else (150, 150, 150))
            self.screen.blit(rank_text, (x + card_width//2 - rank_text.get_width()//2, y + 125))
            
            font_key = pygame.font.Font(None, 18)
            key = font_key.render(f"Press {i+1} to select", True, (120, 220, 120))
            self.screen.blit(key, (x + card_width//2 - key.get_width()//2, y + card_height - 30))





    def _draw_skill_tree_ui(self):
        """Draw the full skill tree overlay."""
        if not self.skill_tree_open:
            return
        
        overlay = pygame.Surface((self.settings.screen_width, self.settings.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        font_title = pygame.font.Font(None, 36)
        title = font_title.render("SKILL TREE", True, (255, 215, 0))
        self.screen.blit(title, (self.settings.screen_width//2 - title.get_width()//2, 30))
        
        font_stats = pygame.font.Font(None, 20)
        stats = font_stats.render(f"Level: {self.player.level}  |  Points: {self.player.skill_points}  |  T to close", True, (200, 200, 200))
        self.screen.blit(stats, (self.settings.screen_width//2 - stats.get_width()//2, 70))
        
        from skills import ALL_SKILLS
        categories = {"combat": (100, 120), "defense": (380, 120), "utility": (660, 120)}
        cat_colors = {"combat": (255, 100, 100), "defense": (100, 200, 255), "utility": (100, 255, 100)}
        
        for cat, (cx, cy) in categories.items():
            font_cat = pygame.font.Font(None, 24)
            header = font_cat.render(cat.upper(), True, cat_colors[cat])
            self.screen.blit(header, (cx + 60, cy))
            
            y_offset = 35
            for skill_id, skill in ALL_SKILLS.items():
                if skill["category"] == cat:
                    rank = self.player.skill_tree.get_rank(skill_id)
                    max_rank = skill["max_rank"]
                    
                    box = pygame.Rect(cx, cy + y_offset, 180, 45)
                    color = cat_colors[cat] if rank > 0 else (80, 80, 80)
                    pygame.draw.rect(self.screen, (40, 45, 55), box)
                    pygame.draw.rect(self.screen, color, box, 2)
                    
                    font_skill = pygame.font.Font(None, 16)
                    name = font_skill.render(skill["name"], True, color)
                    self.screen.blit(name, (cx + 8, cy + y_offset + 5))
                    
                    desc = font_skill.render(skill["description"], True, (150, 150, 150))
                    self.screen.blit(desc, (cx + 8, cy + y_offset + 24))
                    
                    rank_text = font_skill.render(f"{rank}/{max_rank}", True, (255, 215, 0) if rank > 0 else (100, 100, 100))
                    self.screen.blit(rank_text, (cx + 145, cy + y_offset + 5))
                    
                    y_offset += 55
    
    def _select_skill(self, skill_id):
        """Select a skill to upgrade."""
        if self.player.skill_points > 0 and self.player.skill_tree.upgrade_skill(skill_id):
            self.player.skill_points -= 1
            self.player.apply_skill_effects()
            
            from skills import ALL_SKILLS
            skill = ALL_SKILLS[skill_id]
            self.float_texts.append(
                {
                    "text": f"Learned: {skill['name']}!",
                    "pos": pygame.Vector2(self.player.rect.centerx, self.player.rect.top - 40),
                    "life": 90,
                    "color": (255, 215, 0),
                }
            )
        
        if self.player.skill_points <= 0:
            self.show_level_up = False
            self.level_up_choices = []
        else:
            self.level_up_choices = self.player.skill_tree.get_random_choices(3)
