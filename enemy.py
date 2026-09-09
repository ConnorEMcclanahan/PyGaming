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
        # Shooting distance: only fires when player is within this range.
        self.shoot_range = 520
        self.aggro_range = 700
        # Patrol: ninjas drift around their post while the player is far away.
        self.bounds = bounds
        self.wander_timer = 0
        self.wander_dir = pygame.Vector2(0, 0)
        self.name = "NINJA"
        self.gold_reward = 6
        self.attack_interval = 72

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
        if self._dist_to_player(player) > self.aggro_range:
            self._wander()  # player too far away: patrol the area
            return
        if self.shoot_timer <= 0 and self._dist_to_player(player) <= self.shoot_range:
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
    """The warlord of the hideout east of town: bigger, tougher, and he throws
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

    def _fire(self, player, enemy_projectiles):
        for offset in (-0.4, -0.2, 0.0, 0.2, 0.4):
            target = pygame.Vector2(player.rect.center)
            direction = target - self.position
            angle = math.atan2(direction.y, direction.x) + offset
            aim = self.position + pygame.Vector2(math.cos(angle), math.sin(angle)) * 560
            enemy_projectiles.append(NinjaStar(self.rect.center, aim))
        self.shoot_timer = self.attack_interval

    def draw(self, screen, camera):
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