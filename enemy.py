import math
import random

import pygame


class NinjaStar:
    def __init__(self, start_pos, target_pos):
        self.position = pygame.Vector2(start_pos)
        direction = pygame.Vector2(target_pos) - self.position
        self.velocity = direction.normalize() * 5 if direction.length() else pygame.Vector2(0, 1)
        self.rect = pygame.Rect(0, 0, 20, 20)
        self.rect.center = start_pos

    def update(self):
        self.position += self.velocity
        self.rect.center = (round(self.position.x), round(self.position.y))

    def draw(self, screen, camera):
        center = (self.rect.centerx - camera[0], self.rect.centery - camera[1])
        points = []
        for index in range(8):
            angle = index * math.pi / 4
            radius = 16 if index % 2 == 0 else 5
            points.append((center[0] + round(math.cos(angle) * radius), center[1] + round(math.sin(angle) * radius)))
        pygame.draw.polygon(screen, (188, 205, 222), points)
        pygame.draw.circle(screen, (54, 65, 80), center, 4)


class SlimeBall:
    """Slime projectile - a wobbly blob shot at the player."""
    def __init__(self, start_pos, target_pos, color=(100, 200, 100)):
        self.position = pygame.Vector2(start_pos)
        direction = pygame.Vector2(target_pos) - self.position
        self.velocity = direction.normalize() * 3.5 if direction.length() else pygame.Vector2(0, 1)
        self.rect = pygame.Rect(0, 0, 16, 16)
        self.rect.center = start_pos
        self.color = color
        self.wobble = random.uniform(0, math.tau)

    def update(self):
        self.position += self.velocity
        self.wobble += 0.1
        self.velocity.x += math.sin(self.wobble) * 0.05
        self.rect.center = (round(self.position.x), round(self.position.y))

    def draw(self, screen, camera):
        cx = self.rect.centerx - camera[0]
        cy = self.rect.centery - camera[1]
        pygame.draw.ellipse(screen, self.color, (cx - 8, cy - 6, 16, 12))
        pygame.draw.ellipse(screen, (255, 255, 255), (cx - 4, cy - 4, 4, 3))


class Slime:
    """A friendly-looking slime enemy. Hops toward the player and shoots slime balls."""
    
    VARIANTS = {
        "green":  {"name": "GREEN SLIME",  "color": (80, 180, 80),  "health": 40,  "damage": 8,  "speed": 1.2, "shoot_interval": 90, "exp": 10},
        "blue":   {"name": "BLUE SLIME",   "color": (80, 140, 220), "health": 60,  "damage": 12, "speed": 1.0, "shoot_interval": 80, "exp": 15},
        "red":    {"name": "RED SLIME",    "color": (220, 80, 80),  "health": 80,  "damage": 18, "speed": 1.5, "shoot_interval": 70, "exp": 20},
        "purple": {"name": "PURPLE SLIME", "color": (160, 80, 200), "health": 100, "damage": 22, "speed": 0.8, "shoot_interval": 60, "exp": 25},
    }
    
    def __init__(self, position, variant="green", bounds=None):
        self.variant = variant
        stats = self.VARIANTS[variant]
        self.name = stats["name"]
        self.color = stats["color"]
        self.max_health = stats["health"]
        self.health = self.max_health
        self.damage = stats["damage"]
        self.move_speed = stats["speed"]
        self.shoot_interval = stats["shoot_interval"]
        self.exp_reward = stats["exp"]
        
        self.position = pygame.Vector2(position)
        self.rect = pygame.Rect(0, 0, 36, 36)
        self.rect.center = position
        self.shoot_timer = random.randint(30, self.shoot_interval)
        self.anim_timer = random.uniform(0, math.tau)
        self.alive = True
        
        self.hop_timer = 0
        self.is_hopping = False
        self.hop_target = None
        self.bounds = bounds
        self.wander_timer = 0
        self.wander_dir = pygame.Vector2(0, 0)
        self.aggro_range = 400
        self.shoot_range = 350
        # Persistent aggro state: stay mad at the player briefly after they flee.
        self.is_aggro = False
        self.aggro_timer = 0
        self.prev_dist = float("inf")
        self.flee_cooldown = 0
        self.last_seen_pos = None
        self.last_seen_timer = 0

    def _dist_to_player(self, player):
        return (pygame.Vector2(player.rect.center) - self.position).length()

    def _wander(self):
        if self.bounds is None:
            return
        self.wander_timer -= 1
        if self.wander_timer <= 0:
            self.wander_timer = random.randint(60, 120)
            self.wander_dir = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
            if self.wander_dir.length_squared() == 0:
                self.wander_dir = pygame.Vector2(1, 0)
            self.wander_dir.scale_to_length(self.move_speed * 0.5)
        self.position += self.wander_dir
        self.position.x = max(self.bounds.x + 18, min(self.position.x, self.bounds.right - 18))
        self.position.y = max(self.bounds.y + 18, min(self.position.y, self.bounds.bottom - 18))
        self.rect.center = (round(self.position.x), round(self.position.y))

    def _hop_toward(self, target_pos):
        if not self.is_hopping:
            self.is_hopping = True
            self.hop_timer = 20
            direction = pygame.Vector2(target_pos) - self.position
            if direction.length() > 0:
                self.hop_target = self.position + direction.normalize() * 60
            else:
                self.hop_target = self.position
        
        self.hop_timer -= 1
        if self.hop_timer <= 0:
            self.is_hopping = False
        else:
            if self.hop_target:
                direction = self.hop_target - self.position
                if direction.length() > 1:
                    self.position += direction.normalize() * self.move_speed
                    self.rect.center = (round(self.position.x), round(self.position.y))

    def _fire(self, player, enemy_projectiles):
        target = pygame.Vector2(player.rect.center)
        enemy_projectiles.append(SlimeBall(self.rect.center, target, self.color))
        self.shoot_timer = self.shoot_interval

    def update(self, player, enemy_projectiles):
        if not self.alive:
            return
        self.shoot_timer -= 1
        self.anim_timer += 0.15
        dist = self._dist_to_player(player)

        # Track how far the player was last seen, to detect fleeing.
        prev_dist = self.prev_dist
        self.prev_dist = dist

        # Determine whether the player is moving away from this enemy.
        fleeing = dist > prev_dist and dist > self.shoot_range

        # Refresh aggro while the player is nearby.
        if dist <= self.aggro_range:
            self.is_aggro = True
            self.aggro_timer = 180  # 3 seconds at 60 FPS
            self.last_seen_pos = pygame.Vector2(player.rect.center)
            self.last_seen_timer = 180
        else:
            self.aggro_timer -= 1
            self.last_seen_timer -= 1
            if self.aggro_timer <= 0:
                self.is_aggro = False
                self.flee_cooldown = 0

        # When the player is fleeing, build up a shot cooldown so the
        # enemy eventually stops firing.
        if fleeing:
            self.flee_cooldown = min(self.flee_cooldown + 4, 120)

        if dist > self.aggro_range and not self.is_aggro:
            self._wander()
            self.is_hopping = False
            return

        if not self.is_aggro:
            self._wander()
            self.is_hopping = False
            return

        # Aggroed: chase toward the last-seen position (or the player if visible).
        target_pos = self.last_seen_pos if self.last_seen_timer > 0 else None
        if dist <= self.aggro_range:
            target_pos = player.rect.center

        if dist > 100:
            if target_pos:
                self._hop_toward(target_pos)
            if dist <= self.shoot_range and self.shoot_timer <= 0 and self.flee_cooldown <= 0:
                self._fire(player, enemy_projectiles)
        elif self.shoot_timer <= 0 and self.flee_cooldown <= 0:
            self._fire(player, enemy_projectiles)

    def take_damage(self, amount):
        if not self.alive:
            return
        self.health = max(0, self.health - amount)
        if self.health <= 0:
            self.alive = False

    def draw(self, screen, camera):
        x = self.rect.centerx - camera[0]
        y = self.rect.centery - camera[1]
        
        squish = 1.0
        if self.is_hopping:
            squish = 0.7 + abs(math.sin(self.hop_timer * 0.3)) * 0.3
        
        body_h = int(28 * squish)
        body_w = int(36 * (2 - squish))
        
        pygame.draw.ellipse(screen, (0, 0, 0, 50), (x - 18, y + 10, 36, 10))
        pygame.draw.ellipse(screen, self.color, (x - body_w//2, y - body_h//2, body_w, body_h))
        pygame.draw.ellipse(screen, (255, 255, 255, 100), (x - body_w//4, y - body_h//3, body_w//3, body_h//4))
        
        eye_y = y - 4
        pygame.draw.circle(screen, (255, 255, 255), (x - 6, eye_y), 5)
        pygame.draw.circle(screen, (255, 255, 255), (x + 6, eye_y), 5)
        pygame.draw.circle(screen, (0, 0, 0), (x - 5, eye_y), 2)
        pygame.draw.circle(screen, (0, 0, 0), (x + 7, eye_y), 2)
        
        if self.health < self.max_health:
            health_width = int(30 * max(0, self.health) / self.max_health)
            pygame.draw.rect(screen, (40, 40, 40), (x - 15, y - body_h//2 - 10, 30, 4))
            pygame.draw.rect(screen, (204, 58, 65), (x - 15, y - body_h//2 - 10, health_width, 4))


class SlimeBoss(Slime):
    """A giant slime boss - bigger, tougher, and has a slam attack."""
    
    def __init__(self, position, bounds=None):
        super().__init__(position, "green", bounds)
        self.name = "KING SLIME"
        self.color = (60, 160, 60)
        self.max_health = 300
        self.health = self.max_health
        self.damage = 25
        self.move_speed = 0.8
        self.shoot_interval = 50
        self.exp_reward = 100
        self.rect = pygame.Rect(0, 0, 64, 64)
        self.rect.center = position
        self.aggro_range = 500
        self.shoot_range = 400
        self.slam_timer = 180
        self.is_slamming = False
        self.slam_warning = 0

    def _fire(self, player, enemy_projectiles):
        base_target = pygame.Vector2(player.rect.center)
        for offset in (-0.3, -0.15, 0, 0.15, 0.3):
            direction = base_target - self.position
            angle = math.atan2(direction.y, direction.x) + offset
            target = self.position + pygame.Vector2(math.cos(angle), math.sin(angle)) * 400
            enemy_projectiles.append(SlimeBall(self.rect.center, target, self.color))
        self.shoot_timer = self.shoot_interval

    def _slam_attack(self, player, enemy_projectiles):
        for i in range(12):
            angle = i * math.pi / 6
            target = self.position + pygame.Vector2(math.cos(angle), math.sin(angle)) * 300
            enemy_projectiles.append(SlimeBall(self.rect.center, target, (100, 200, 100)))

    def update(self, player, enemy_projectiles):
        if not self.alive:
            return
        self.shoot_timer -= 1
        self.anim_timer += 0.1
        self.slam_timer -= 1
        
        if self.slam_timer <= 30 and not self.is_slamming:
            self.slam_warning = 30 - self.slam_timer
        if self.slam_timer <= 0:
            self.is_slamming = True
            self._slam_attack(player, enemy_projectiles)
            self.slam_timer = 180
            self.is_slamming = False
        
        dist = self._dist_to_player(player)

        # Persistent aggro state + fleeing detection.
        prev_dist = self.prev_dist
        self.prev_dist = dist
        fleeing = dist > prev_dist and dist > self.shoot_range

        if dist <= self.aggro_range:
            self.is_aggro = True
            self.aggro_timer = 180
            self.last_seen_pos = pygame.Vector2(player.rect.center)
            self.last_seen_timer = 180
        else:
            self.aggro_timer -= 1
            self.last_seen_timer -= 1
            if self.aggro_timer <= 0:
                self.is_aggro = False
                self.flee_cooldown = 0

        if fleeing:
            self.flee_cooldown = min(self.flee_cooldown + 4, 120)

        if not self.is_aggro and dist > self.aggro_range:
            self._wander()
            self.is_hopping = False
            return

        target_pos = self.last_seen_pos if self.last_seen_timer > 0 else None
        if dist <= self.aggro_range:
            target_pos = player.rect.center

        if dist > 80:
            if target_pos:
                self._hop_toward(target_pos)
            if dist <= self.shoot_range and self.shoot_timer <= 0 and self.flee_cooldown <= 0:
                self._fire(player, enemy_projectiles)
        elif self.shoot_timer <= 0 and self.flee_cooldown <= 0:
            self._fire(player, enemy_projectiles)

    def draw(self, screen, camera):
        x = self.rect.centerx - camera[0]
        y = self.rect.centery - camera[1]
        
        if self.slam_timer <= 30:
            pulse = abs(math.sin(self.slam_timer * 0.2)) * 0.5 + 0.5
            radius = int(120 + pulse * 30)
            temp = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(temp, (255, 100, 100, int(30 + pulse * 40)), (radius, radius), radius)
            screen.blit(temp, (x - radius, y - radius))
        
        squish = 1.0
        if self.is_hopping:
            squish = 0.7 + abs(math.sin(self.hop_timer * 0.3)) * 0.3
        
        body_h = int(48 * squish)
        body_w = int(64 * (2 - squish))
        
        pygame.draw.ellipse(screen, (0, 0, 0, 50), (x - 32, y + 20, 64, 16))
        pygame.draw.ellipse(screen, self.color, (x - body_w//2, y - body_h//2, body_w, body_h))
        pygame.draw.ellipse(screen, (255, 255, 255, 100), (x - body_w//4, y - body_h//3, body_w//3, body_h//4))
        
        crown_points = [(x - 20, y - body_h//2), (x - 10, y - body_h//2 - 15),
                       (x, y - body_h//2 - 5), (x + 10, y - body_h//2 - 15),
                       (x + 20, y - body_h//2)]
        pygame.draw.polygon(screen, (255, 215, 0), crown_points)
        pygame.draw.circle(screen, (255, 0, 0), (x, y - body_h//2 - 10), 3)
        
        eye_y = y - 8
        pygame.draw.circle(screen, (255, 255, 255), (x - 10, eye_y), 8)
        pygame.draw.circle(screen, (255, 255, 255), (x + 10, eye_y), 8)
        pygame.draw.circle(screen, (0, 0, 0), (x - 8, eye_y), 3)
        pygame.draw.circle(screen, (0, 0, 0), (x + 12, eye_y), 3)
        
        health_width = int(70 * max(0, self.health) / self.max_health)
        pygame.draw.rect(screen, (40, 40, 40), (x - 35, y - body_h//2 - 20, 70, 8))
        pygame.draw.rect(screen, (204, 58, 65), (x - 35, y - body_h//2 - 20, health_width, 8))
        
        font = pygame.font.Font(None, 20)
        name_surf = font.render(self.name, True, (255, 215, 0))
        screen.blit(name_surf, (x - name_surf.get_width()//2, y - body_h//2 - 35))


class Ninja:
    def __init__(self, position, bounds=None):
        self.position = pygame.Vector2(position)
        self.rect = pygame.Rect(0, 0, 48, 48)
        self.rect.center = position
        self.max_health = 180
        self.health = self.max_health
        self.shoot_timer = 0
        self.anim_timer = 0
        self.alive = True
        self.shoot_range = 520
        self.aggro_range = 700
        self.bounds = bounds
        self.wander_timer = 0
        self.wander_dir = pygame.Vector2(0, 0)
        self.name = "NINJA"
        self.gold_reward = 6
        self.attack_interval = 72
        self.exp_reward = 30
        # Persistent aggro state for smarter enemy behavior.
        self.is_aggro = False
        self.aggro_timer = 0
        self.prev_dist = float("inf")
        self.flee_cooldown = 0
        self.last_seen_pos = None
        self.last_seen_timer = 0

    def _dist_to_player(self, player):
        return (pygame.Vector2(player.rect.center) - self.position).length()

    def _wander(self):
        if self.bounds is None:
            return
        self.wander_timer -= 1
        if self.wander_timer <= 0:
            self.wander_timer = random.randint(60, 150)
            self.wander_dir = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
            if self.wander_dir.length_squared() == 0:
                self.wander_dir = pygame.Vector2(1, 0)
            self.wander_dir.scale_to_length(random.uniform(0.3, 0.9))
        self.position += self.wander_dir
        self.position.x = max(self.bounds.x + 24, min(self.position.x, self.bounds.right - 24))
        self.position.y = max(self.bounds.y + 24, min(self.position.y, self.bounds.bottom - 24))
        self.rect.center = (round(self.position.x), round(self.position.y))

    def _chase(self, player):
        """Move toward the player."""
        direction = pygame.Vector2(player.rect.center) - self.position
        if direction.length() > 0:
            self.position += direction.normalize() * 1.5
            self.rect.center = (round(self.position.x), round(self.position.y))

    def _fire(self, player, enemy_projectiles):
        for offset in (-0.28, 0, 0.28):
            target = pygame.Vector2(player.rect.center)
            direction = target - self.position
            angle = math.atan2(direction.y, direction.x) + offset
            target = self.position + pygame.Vector2(math.cos(angle), math.sin(angle)) * 500
            enemy_projectiles.append(NinjaStar(self.rect.center, target))
        self.shoot_timer = self.attack_interval

    def update(self, player, enemy_projectiles):
        self.shoot_timer -= 1
        self.anim_timer += 0.1
        dist = self._dist_to_player(player)

        # Persistent aggro state + fleeing detection.
        prev_dist = self.prev_dist
        self.prev_dist = dist
        fleeing = dist > prev_dist and dist > self.shoot_range

        if dist <= self.aggro_range:
            self.is_aggro = True
            self.aggro_timer = 240
            self.last_seen_pos = pygame.Vector2(player.rect.center)
            self.last_seen_timer = 240
        else:
            self.aggro_timer -= 1
            self.last_seen_timer -= 1
            if self.aggro_timer <= 0:
                self.is_aggro = False
                self.flee_cooldown = 0

        if fleeing:
            self.flee_cooldown = min(self.flee_cooldown + 3, 90)

        if not self.is_aggro and dist > self.aggro_range:
            self._wander()
            return

        # Chase the player (or last-seen position if they broke line of sight).
        target_pos = self.last_seen_pos if self.last_seen_timer > 0 else None
        if dist <= self.aggro_range:
            target_pos = player.rect.center

        if dist > 100:
            if target_pos:
                self._chase(player)
        
        if self.shoot_timer <= 0 and dist <= self.shoot_range and self.flee_cooldown <= 0:
            self._fire(player, enemy_projectiles)

    def take_damage(self, amount):
        if not self.alive:
            return
        self.health = max(0, self.health - amount)
        if self.health <= 0:
            self.alive = False

    def draw(self, screen, camera):
        x = self.rect.centerx - camera[0]
        y = self.rect.centery - camera[1] + int(math.sin(self.anim_timer) * 2)
        pygame.draw.ellipse(screen, (12, 17, 22), (x - 24, y + 18, 48, 12))
        pygame.draw.rect(screen, (37, 41, 53), (x - 16, y - 4, 32, 29))
        pygame.draw.rect(screen, (21, 24, 33), (x - 14, y - 20, 28, 18))
        pygame.draw.rect(screen, (118, 35, 49), (x - 19, y - 11, 38, 6))
        pygame.draw.rect(screen, (221, 215, 184), (x - 8, y - 5, 5, 3))
        pygame.draw.rect(screen, (221, 215, 184), (x + 3, y - 5, 5, 3))
        pygame.draw.rect(screen, (91, 29, 42), (x - 20, y + 4, 8, 20))
        pygame.draw.rect(screen, (91, 29, 42), (x + 12, y + 4, 8, 20))
        health_width = round(54 * max(0, self.health) / self.max_health)
        pygame.draw.rect(screen, (26, 30, 34), (x - 27, y - 34, 54, 6))
        pygame.draw.rect(screen, (204, 58, 65), (x - 27, y - 34, health_width, 6))


class NinjaBoss(Ninja):
    """The warlord of the hideout south of town: bigger, tougher, and he throws
    much wider fans of stars. Regular ninjas patrol all around his lair."""

    def __init__(self, position, bounds=None):
        super().__init__(position, bounds)
        self.rect = pygame.Rect(0, 0, 64, 64)
        self.rect.center = position
        self.max_health = 650
        self.health = self.max_health
        self.shoot_range = 640
        self.aggro_range = 950
        self.attack_interval = 55
        self.name = "NINJA WARLORD"
        self.gold_reward = 75
        # Special attack: radial bullet burst with warning indicator
        self.special_attack_timer = 300  # frames until next special
        self.special_attack_duration = 90  # frames the warning lasts
        self.is_charging_special = False

    def _fire(self, player, enemy_projectiles):
        for offset in (-0.4, -0.2, 0.0, 0.2, 0.4):
            target = pygame.Vector2(player.rect.center)
            direction = target - self.position
            angle = math.atan2(direction.y, direction.x) + offset
            aim = self.position + pygame.Vector2(math.cos(angle), math.sin(angle)) * 560
            enemy_projectiles.append(NinjaStar(self.rect.center, aim))
        self.shoot_timer = self.attack_interval

    def _fire_special(self, player, enemy_projectiles):
        """Radial bullet burst - 16 stars in all directions."""
        for i in range(16):
            angle = i * math.pi / 8
            aim = self.position + pygame.Vector2(math.cos(angle), math.sin(angle)) * 600
            enemy_projectiles.append(NinjaStar(self.rect.center, aim))

    def update(self, player, enemy_projectiles):
        super().update(player, enemy_projectiles)
        self.special_attack_timer -= 1
        if self.special_attack_timer <= self.special_attack_duration and not self.is_charging_special:
            self.is_charging_special = True
        if self.special_attack_timer <= 0:
            self._fire_special(player, enemy_projectiles)
            self.special_attack_timer = 300
            self.is_charging_special = False

    def _draw_special_indicator(self, screen, camera):
        """Draw a warning circle when charging the special radial burst."""
        x = self.rect.centerx - camera[0]
        y = self.rect.centery - camera[1]
        radius = int(self.shoot_range)
        temp = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        # Pulsing warning ring
        pulse = abs(math.sin(self.special_attack_timer * 0.1)) * 0.5 + 0.5
        alpha = int(40 + pulse * 40)
        pygame.draw.circle(temp, (255, 80, 80, alpha), (radius, radius), radius)
        pygame.draw.circle(temp, (255, 100, 100, alpha + 20), (radius, radius), radius, max(1, int(3 * (radius / 640))))
        # Inner danger zone
        inner_radius = int(radius * 0.6)
        pygame.draw.circle(temp, (255, 50, 50, int(alpha * 0.5)), (radius, radius), inner_radius)
        screen.blit(temp, (x - radius, y - radius))

    def draw(self, screen, camera):
        if self.is_charging_special:
            self._draw_special_indicator(screen, camera)
        x = self.rect.centerx - camera[0]
        y = self.rect.centery - camera[1] + int(math.sin(self.anim_timer) * 2)
        pygame.draw.ellipse(screen, (12, 17, 22), (x - 32, y + 24, 64, 16))
        pygame.draw.rect(screen, (37, 41, 53), (x - 22, y - 6, 44, 38))
        pygame.draw.rect(screen, (21, 24, 33), (x - 20, y - 28, 40, 24))
        # Gold warlord sash.
        pygame.draw.rect(screen, (204, 164, 60), (x - 26, y - 15, 52, 8))
        pygame.draw.rect(screen, (221, 215, 184), (x - 11, y - 7, 7, 4))
        pygame.draw.rect(screen, (221, 215, 184), (x + 4, y - 7, 7, 4))
        pygame.draw.rect(screen, (91, 29, 42), (x - 27, y + 5, 11, 27))
        pygame.draw.rect(screen, (91, 29, 42), (x + 16, y + 5, 11, 27))
        hp_w = round(90 * max(0, self.health) / self.max_health)
        pygame.draw.rect(screen, (26, 30, 34), (x - 45, y - 46, 90, 8))
        pygame.draw.rect(screen, (204, 58, 65), (x - 45, y - 46, hp_w, 8))
        pygame.draw.rect(screen, (244, 180, 60), (x - 45, y - 46, hp_w, 4))
        tag = pygame.font.Font(None, 18).render(self.name, True, (248, 214, 137))
        screen.blit(tag, tag.get_rect(midbottom=(x, y - 52)))


class Chicken:
    """A wandering tutorial chicken. Harmless, but must be defeated to open
    the tutorial gate (the ROTMG 'chicken level' style)."""

    def __init__(self, position, bounds):
        self.position = pygame.Vector2(position)
        self.rect = pygame.Rect(0, 0, 36, 36)
        self.rect.center = position
        self.max_health = 40
        self.health = self.max_health
        self.alive = True
        self.timer = 0
        self.anim_timer = 0
        self.vx = 0
        self.bounds = bounds

    def update(self):
        self.timer -= 1
        self.anim_timer += 0.15
        if self.timer <= 0:
            self.timer = random.randint(50, 100)
            self.vx = random.choice((-1, 1)) * random.uniform(0.4, 1.4)
        self.position.x += self.vx
        if self.position.x < self.bounds.x + 20:
            self.position.x = self.bounds.x + 20
            self.vx = abs(self.vx) if self.vx else 1
        if self.position.x > self.bounds.right - 20:
            self.position.x = self.bounds.right - 20
            self.vx = -abs(self.vx) if self.vx else -1
        self.rect.center = (round(self.position.x), round(self.position.y))

    def take_damage(self, amount):
        if not self.alive:
            return
        self.health = max(0, self.health - amount)
        if self.health <= 0:
            self.alive = False

    def draw(self, screen, camera):
        x = self.rect.centerx - camera[0]
        y = self.rect.centery - camera[1] + int(math.sin(self.anim_timer) * 2)
        pygame.draw.ellipse(screen, (12, 17, 22), (x - 16, y + 15, 32, 8))
        pygame.draw.rect(screen, (240, 235, 220), (x - 14, y - 2, 28, 20))
        pygame.draw.rect(screen, (246, 241, 226), (x - 10, y - 14, 20, 14))
        pygame.draw.polygon(screen, (255, 170, 40), [(x + 8, y - 12), (x + 16, y - 6), (x + 9, y - 4)])
        pygame.draw.rect(screen, (222, 62, 42), (x - 9, y - 20, 6, 6))
        pygame.draw.rect(screen, (222, 62, 42), (x + 3, y - 20, 6, 6))
        pygame.draw.rect(screen, (30, 30, 34), (x + 2, y - 12, 5, 5))
        pygame.draw.rect(screen, (225, 219, 210), (x - 14, y + 3, 8, 10))
        pygame.draw.rect(screen, (255, 170, 40), (x - 9, y + 16, 5, 9))
        pygame.draw.rect(screen, (255, 170, 40), (x + 4, y + 16, 5, 9))
        hp_width = round(40 * max(0, self.health) / self.max_health)
        pygame.draw.rect(screen, (26, 30, 34), (x - 20, y - 30, 40, 5))
        pygame.draw.rect(screen, (130, 205, 90), (x - 20, y - 30, hp_width, 5))


class EggProjectile:
    """A slow egg lobbed by the GiantChickenBoss."""

    def __init__(self, start_pos, target_pos):
        self.position = pygame.Vector2(start_pos)
        direction = pygame.Vector2(target_pos) - self.position
        self.velocity = direction.normalize() * 3.5 if direction.length() else pygame.Vector2(1, 0)
        self.rect = pygame.Rect(0, 0, 18, 22)
        self.rect.center = start_pos

    def update(self):
        self.position += self.velocity
        self.rect.center = (round(self.position.x), round(self.position.y))

    def draw(self, screen, camera):
        x = self.rect.centerx - camera[0]
        y = self.rect.centery - camera[1]
        pygame.draw.ellipse(screen, (245, 240, 225), (x - 8, y - 6, 16, 20))
        pygame.draw.ellipse(screen, (210, 200, 180), (x - 6, y - 2, 6, 8))
        pygame.draw.ellipse(screen, (255, 255, 245), (x - 7, y - 7, 6, 7))


class GiantChickenBoss:
    """The tutorial's gatekeeper: a giant, angry chicken that blocks the
    route and lobs eggs at the player. Must be defeated to call the ship."""

    def __init__(self, position, bounds):
        self.position = pygame.Vector2(position)
        self.rect = pygame.Rect(0, 0, 92, 84)
        self.rect.center = position
        self.max_health = 400
        self.health = self.max_health
        self.alive = True
        self.timer = 0
        self.anim_timer = 0
        self.shoot_timer = 120
        self.vx = 0
        self.bounds = bounds
        self.angry = False
        # Shooting distance: boss only opens fire inside this radius.
        self.shoot_range = 620
        self.aggro_range = 900

    def _dist_to_player(self, player):
        return (pygame.Vector2(player.rect.center) - self.position).length()

    def update(self, player, egg_projectiles):
        self.timer -= 1
        self.anim_timer += 0.1
        self.angry = self.health < self.max_health * 0.5
        if self.timer <= 0:
            self.timer = random.randint(80, 140)
            self.vx = random.choice((-1, 1)) * random.uniform(0.5, 1.5)
        self.position.x += self.vx
        self.position.x = max(self.bounds.x + 40, min(self.position.x, self.bounds.right - 40))
        self.rect.center = (round(self.position.x), round(self.position.y))
        self.shoot_timer -= 1
        if self.shoot_timer <= 0 and self._dist_to_player(player) <= self.shoot_range:
            offsets = (-0.15, 0.0, 0.15) if self.angry else (-0.1, 0.1)
            for offset in offsets:
                target = pygame.Vector2(player.rect.center)
                direction = target - self.position
                angle = math.atan2(direction.y, direction.x) + offset
                aim = self.position + pygame.Vector2(math.cos(angle), math.sin(angle)) * 600
                egg_projectiles.append(EggProjectile(self.rect.center, aim))
            self.shoot_timer = 70 if self.angry else 95

    def take_damage(self, amount):
        if not self.alive:
            return
        self.health = max(0, self.health - amount)
        if self.health <= 0:
            self.alive = False

    def draw(self, screen, camera):
        x = self.rect.centerx - camera[0]
        y = self.rect.centery - camera[1] + int(math.sin(self.anim_timer) * 2)
        pygame.draw.ellipse(screen, (12, 17, 22), (x - 44, y + 34, 88, 22))
        pygame.draw.rect(screen, (225, 219, 210), (x - 34, y + 22, 16, 16))
        pygame.draw.rect(screen, (255, 170, 40), (x - 30, y + 38, 12, 12))
        pygame.draw.rect(screen, (225, 219, 210), (x + 18, y + 22, 16, 16))
        pygame.draw.rect(screen, (255, 170, 40), (x + 18, y + 38, 12, 12))
        pygame.draw.rect(screen, (232, 224, 208), (x - 38, y - 14, 76, 52))
        pygame.draw.rect(screen, (246, 241, 226), (x - 30, y - 42, 60, 30))
        pygame.draw.polygon(screen, (214, 50, 50), [(x - 10, y - 40), (x + 2, y - 52), (x + 12, y - 40)])
        pygame.draw.rect(screen, (214, 50, 50), (x - 26, y - 44, 14, 12))
        pygame.draw.rect(screen, (214, 50, 50), (x + 12, y - 46, 14, 12))
        pygame.draw.rect(screen, (255, 255, 240), (x - 22, y - 36, 16, 12))
        pygame.draw.rect(screen, (255, 255, 240), (x + 6, y - 36, 16, 12))
        pygame.draw.rect(screen, (200, 40, 40), (x - 20, y - 33, 6, 5))
        pygame.draw.rect(screen, (200, 40, 40), (x + 9, y - 33, 6, 5))
        pygame.draw.polygon(screen, (250, 170, 40), [(x - 4, y - 28), (x + 26, y - 20), (x + 6, y - 6)])
        pygame.draw.polygon(screen, (200, 120, 30), [(x - 4, y - 28), (x + 24, y - 24), (x + 2, y - 12)])
        pygame.draw.rect(screen, (120, 96, 78), (x - 46, y - 6, 18, 34))
        pygame.draw.rect(screen, (110, 88, 70), (x + 28, y - 6, 18, 34))
        pygame.draw.rect(screen, (88, 70, 52), (x - 20, y + 6, 40, 6))
        pygame.draw.rect(screen, (255, 170, 40), (x - 40, y - 20, 10, 8))
        pygame.draw.rect(screen, (240, 120, 40), (x - 46, y - 12, 8, 8))
        hp_w = round(120 * max(0, self.health) / self.max_health)
        pygame.draw.rect(screen, (26, 30, 34), (x - 60, y - 66, 120, 8))
        pygame.draw.rect(screen, (214, 60, 65), (x - 60, y - 66, hp_w, 8))
        pygame.draw.rect(screen, (244, 180, 60), (x - 60, y - 66, hp_w, 4))