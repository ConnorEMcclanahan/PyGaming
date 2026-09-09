import math

import pygame

from items import get_ability_profile, get_weapon_profile


def _white(core):
    return (min(255, core[0] + 90), min(255, core[1] + 90), min(255, core[2] + 90))


class Projectile:
    """Player shot. Color/shape/damage come from the equipped weapon so
    different weapons leave different colored / shaped attacks."""

    def __init__(self, start_pos, target_pos, weapon=None, speed=10, damage=18):
        try:
            prof = get_weapon_profile(weapon)
        except Exception:
            prof = None
        if not isinstance(prof, dict):
            prof = {"damage": damage, "speed": speed, "color": (200, 200, 210), "shape": "bolt", "shots": 1, "spread": 0.0}
        self.weapon = weapon
        self.damage = prof.get("damage", damage)
        spd = prof.get("speed", speed)
        self.color = prof.get("color", (200, 200, 210))
        self.shape = prof.get("shape", "bolt")
        self.position = pygame.Vector2(start_pos)
        direction = pygame.Vector2(target_pos) - self.position
        self.velocity = direction.normalize() * spd if direction.length() else pygame.Vector2(1, 0)
        self.angle = math.atan2(self.velocity.y, self.velocity.x)
        self.rect = pygame.Rect(0, 0, 26, 26)
        self.rect.center = (round(self.position.x), round(self.position.y))

    def update(self):
        self.position += self.velocity
        self.rect.center = (round(self.position.x), round(self.position.y))

    def draw(self, screen, camera=(0, 0)):
        cx = self.rect.centerx - camera[0]
        cy = self.rect.centery - camera[1]
        dx, dy = math.cos(self.angle), math.sin(self.angle)
        px, py = -dy, dx
        tip = (cx + dx * 14, cy + dy * 14)
        tail = (cx - dx * 10, cy - dy * 10)
        core = self.color
        hot = _white(core)
        if self.shape == "pellet":
            pygame.draw.circle(screen, core, (int(cx), int(cy)), 7)
            pygame.draw.circle(screen, hot, (int(cx), int(cy)), 4)
            pygame.draw.line(screen, hot, tail, tip, 2)
        elif self.shape == "arc":
            half = 9
            pygame.draw.line(screen, core, (cx + px * half, cy + py * half), (cx - px * half, cy - py * half), 5)
            pygame.draw.line(screen, hot, (cx + px * half, cy + py * half), (cx - px * half, cy - py * half), 2)
            pygame.draw.circle(screen, core, (int(tip[0]), int(tip[1])), 3)
        elif self.shape == "comet":
            pygame.draw.line(screen, core, tail, tip, 8)
            pygame.draw.line(screen, hot, tail, tip, 4)
            pygame.draw.circle(screen, hot, (int(tip[0]), int(tip[1])), 5)
            pygame.draw.circle(screen, (255, 255, 255), (int(tip[0]), int(tip[1])), 2)
        elif self.shape == "shard":
            pts = [tip, (cx - dx * 8 + px * 6, cy - dy * 8 + py * 6), (cx - dx * 8 - px * 6, cy - dy * 8 - py * 6)]
            pygame.draw.polygon(screen, core, pts)
            pygame.draw.polygon(screen, hot, pts, 1)
        else:  # bolt
            pygame.draw.line(screen, (18, 22, 30), tail, tip, 7)
            pygame.draw.line(screen, core, tail, tip, 4)
            pygame.draw.line(screen, hot, tail, tip, 2)

class Player:
    def __init__(self, screen, settings, character="knight"):
        self.screen = screen
        self.settings = settings
        self.character = character
        self.width = 32
        self.height = 32
        self.x = settings.world_width // 2
        self.y = settings.world_height // 2 + 170
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.speed = 4
        self.health = 100
        self.max_health = 100
        self.mana = 65
        self.level = 1
        self.is_moving = False
        self.is_shielding = False
        self.shield_timer = 0
        self.aim_angle = 0
        self.anim_timer = 0
        self.attack_cd = 0
        self.ability_cd = 0
        self.overdrive_timer = 0
        # Pocket gold for shopping / selling in town.
        self.gold = 30

    def equipped_weapon(self, ui=None):
        try:
            if ui is not None:
                w = ui.equipment.get("weapon")
                if w is not None and len(w) >= 4 and w[3] == "weapon":
                    return w
        except Exception:
            pass
        return ("PULSE BLADE", (120, 220, 255), "common", "weapon")

    def equipped_ability(self, ui=None):
        try:
            if ui is not None:
                a = ui.equipment.get("ability")
                # Empty slot OR something dragged into it that isn't an
                # ability (shouldn't happen, but never crash): no ability.
                if a is not None and len(a) >= 4 and a[3] == "ability":
                    return a
                if a is None:
                    return None
        except Exception:
            pass
        return ("HOLO SCROLL", (188, 205, 222), "common", "ability") if ui is None else None

    def weapon_cooldown(self, ui=None):
        try:
            prof = get_weapon_profile(self.equipped_weapon(ui))
            cd = int(prof.get("cooldown", 24))
        except Exception:
            cd = 24
        if self.overdrive_timer > 0:
            cd = max(4, cd // 2)
        return cd

    def try_attack(self, world_mouse_pos, ui=None):
        """Rate-limited attack: returns list of new Projectiles (may be empty
        if the weapon is still on cooldown). Handles multi-shot spread."""
        try:
            self.aim_at(world_mouse_pos)
        except Exception:
            pass
        if self.attack_cd > 0:
            return []
        weapon = self.equipped_weapon(ui)
        self._last_weapon = weapon
        try:
            prof = get_weapon_profile(weapon)
            shots_n = int(prof.get("shots", 1))
            spread = float(prof.get("spread", 0.0))
            cd = int(prof.get("cooldown", 24))
        except Exception:
            shots_n, spread, cd = 1, 0.0, 24
        shots = []
        try:
            base_ang = math.atan2(world_mouse_pos[1] - self.rect.centery, world_mouse_pos[0] - self.rect.centerx)
        except Exception:
            base_ang = 0.0
        for i in range(max(1, shots_n)):
            off = (i - (shots_n - 1) / 2) * spread
            ang = base_ang + off
            target = (self.rect.centerx + math.cos(ang) * 600, self.rect.centery + math.sin(ang) * 600)
            try:
                shots.append(Projectile(self.rect.center, target, weapon=weapon))
            except Exception:
                continue
        if self.overdrive_timer > 0:
            cd = max(4, cd // 2)
        self.attack_cd = cd
        return shots

    def try_ability(self, world_mouse_pos, ui=None):
        """Cast equipped ability. Returns (ok, kind, payload) for game loop.
        Never crashes: no ability / bad slot / no mana -> (False, ...)."""
        try:
            if self.ability_cd > 0:
                return (False, "cooldown", None)
            ability = self.equipped_ability(ui)
            if ability is None:
                return (False, "empty", None)
            try:
                prof = get_ability_profile(ability)
                mana_cost = int(prof.get("mana", 20))
                cd = int(prof.get("cooldown", 360))
                key = prof.get("key", "shield")
            except Exception:
                mana_cost, cd, key = 20, 360, "shield"
            if self.mana < mana_cost:
                return (False, "mana", None)
            self.mana -= mana_cost
            self.ability_cd = cd
            self.aim_at(world_mouse_pos)
        except Exception:
            return (False, "error", None)
        if key == "nova":
            bolts = []
            for i in range(8):
                try:
                    ang = i * math.tau / 8
                    target = (self.rect.centerx + math.cos(ang) * 600, self.rect.centery + math.sin(ang) * 600)
                    bolts.append(Projectile(self.rect.center, target, weapon=("NOVA SURGE", (255, 170, 60), "rare", "weapon")))
                except Exception:
                    continue
            for b in bolts:
                try:
                    b.damage = 22
                except Exception:
                    pass
            return (True, "shots", bolts)
        if key == "blink":
            try:
                dx = world_mouse_pos[0] - self.rect.centerx
                dy = world_mouse_pos[1] - self.rect.centery
            except Exception:
                dx, dy = 0, 0
            dist = math.hypot(dx, dy)
            if dist > 0:
                step = min(dist, 220)
                try:
                    self.x += dx / dist * step
                    self.y += dy / dist * step
                    self.x = max(0, min(self.x, self.settings.world_width - self.width))
                    self.y = max(0, min(self.y, self.settings.world_height - self.height))
                    self.rect.topleft = (self.x, self.y)
                except Exception:
                    pass
            try:
                self.bubble_shield(300)
            except Exception:
                self.shield_timer = 300
                self.is_shielding = True
            return (True, "blink", None)
        if key == "drone":
            bolts = []
            for i in range(6):
                try:
                    off = (i - 2.5) * 0.09
                    ang = self.aim_angle + off
                    target = (self.rect.centerx + math.cos(ang) * 700, self.rect.centery + math.sin(ang) * 700)
                    bolts.append(Projectile(self.rect.center, target, weapon=("SENTRY", (150, 255, 170), "rare", "weapon")))
                except Exception:
                    continue
            return (True, "shots", bolts)
        if key == "overdrive":
            self.overdrive_timer = 300
            return (True, "buff", None)
        if key == "repair":
            self.health = min(self.max_health, self.health + 50)
            self.bubble_shield(300)
            return (True, "buff", None)
        if key == "shield":
            # Default ability: 5-second damage-blocking bubble + cooldown.
            self.bubble_shield(300)
            return (True, "buff", None)
        # decoy fallback: damaging pulse around player
        return (True, "pulse", {"radius": 190, "damage": 30})

    def update(self, keys, keybinds=None):
        self.is_moving = False
        keys_pressed = keys
        binds = keybinds if keybinds is not None else {}
        left = binds.get("move_left", pygame.K_a)
        right = binds.get("move_right", pygame.K_d)
        up = binds.get("move_up", pygame.K_w)
        down = binds.get("move_down", pygame.K_s)
        if keys_pressed[pygame.K_LEFT] or keys_pressed[left]:
            self.x -= self.speed
            self.is_moving = True
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[right]:
            self.x += self.speed
            self.is_moving = True
        if keys_pressed[pygame.K_UP] or keys_pressed[up]:
            self.y -= self.speed
            self.is_moving = True
        if keys_pressed[pygame.K_DOWN] or keys_pressed[down]:
            self.y += self.speed
            self.is_moving = True
        if self.x < 0:
            self.x = 0
        if self.x + self.width > self.settings.world_width:
            self.x = self.settings.world_width - self.width
        if self.y < 0:
            self.y = 0
        if self.y + self.height > self.settings.world_height:
            self.y = self.settings.world_height - self.height
        self.rect.topleft = (self.x, self.y)
        if self.is_moving:
            self.anim_timer += 0.18
        if self.attack_cd > 0:
            self.attack_cd -= 1
        if self.ability_cd > 0:
            self.ability_cd -= 1
        if self.overdrive_timer > 0:
            self.overdrive_timer -= 1
        if self.shield_timer > 0:
            self.shield_timer -= 1
            self.is_shielding = True
        else:
            self.is_shielding = False

    def aim_at(self, world_pos):
        """Continuously point the character's sword at a world-space position
        (typically the mouse cursor). Does not fire anything."""
        self.aim_angle = math.atan2(world_pos[1] - self.rect.centery, world_pos[0] - self.rect.centerx)

    def attack(self, world_mouse_pos, ui=None):
        self.aim_at(world_mouse_pos)
        weapon = self.equipped_weapon(ui)
        return Projectile(self.rect.center, world_mouse_pos, weapon=weapon)

    def fire_at_angle(self, ui=None):
        """Fire a projectile in the current aim direction WITHOUT rotating the
        sword (so auto-shoot is just auto-shoot, not auto-aim)."""
        direction = pygame.Vector2(math.cos(self.aim_angle), math.sin(self.aim_angle))
        target = (self.rect.centerx + direction.x * 600, self.rect.centery + direction.y * 600)
        return Projectile(self.rect.center, target, weapon=self.equipped_weapon(ui))

    def bubble_shield(self, duration=300):
        """5-second (300 frame) damage bubble by default."""
        self.shield_timer = duration
        self.is_shielding = True

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)

    def draw(self, screen, camera=(0, 0)):
        bob = int(math.sin(self.anim_timer) * 2) if self.is_moving else 0
        center_x = self.rect.centerx - camera[0]
        center_y = self.rect.centery - camera[1] + bob
        pygame.draw.ellipse(screen, (12, 17, 22), (center_x - 16, center_y + 13, 32, 9))

        # Chunky, unscaled pixel-art knight assembled from hard-edged blocks.
        pygame.draw.rect(screen, (55, 62, 76), (center_x - 12, center_y - 5, 24, 21))
        pygame.draw.rect(screen, (177, 183, 192), (center_x - 10, center_y - 8, 20, 18))
        pygame.draw.rect(screen, (76, 84, 101), (center_x - 10, center_y + 7, 20, 6))
        pygame.draw.rect(screen, (211, 216, 215), (center_x - 8, center_y - 18, 16, 12))
        pygame.draw.rect(screen, (106, 116, 132), (center_x - 11, center_y - 13, 22, 5))
        pygame.draw.rect(screen, (34, 39, 50), (center_x - 6, center_y - 10, 12, 3))
        pygame.draw.rect(screen, (230, 63, 63), (center_x - 3, center_y - 10, 6, 2))
        pygame.draw.rect(screen, (68, 83, 104), (center_x - 16, center_y - 1, 6, 15))
        pygame.draw.rect(screen, (206, 214, 220), (center_x - 17, center_y + 2, 8, 4))

        sword_x = center_x + round(math.cos(self.aim_angle) * 22)
        sword_y = center_y + round(math.sin(self.aim_angle) * 22)
        # Held weapon glows in the equipped weapon's color.
        from items import get_weapon_profile as _gwp
        try:
            wcolor = _gwp(getattr(self, "_last_weapon", None))["color"]
        except Exception:
            wcolor = (90, 220, 255)
        pygame.draw.line(screen, (18, 22, 30), (center_x, center_y), (sword_x, sword_y), 6)
        pygame.draw.line(screen, wcolor, (center_x, center_y), (sword_x, sword_y), 3)
        pygame.draw.line(screen, (230, 250, 255), (center_x, center_y), (sword_x, sword_y), 1)
        hx = center_x - round(math.cos(self.aim_angle) * 5)
        hy = center_y - round(math.sin(self.aim_angle) * 5)
        pygame.draw.circle(screen, (60, 66, 80), (hx, hy), 4)
        pygame.draw.circle(screen, (140, 235, 255), (hx, hy), 2)
        if self.is_shielding:
            pygame.draw.circle(screen, (144, 226, 255), (center_x, center_y), 29, 3)
