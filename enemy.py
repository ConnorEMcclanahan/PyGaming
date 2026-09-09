import math

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
    def __init__(self, position):
        self.position = pygame.Vector2(position)
        self.rect = pygame.Rect(0, 0, 48, 48)
        self.rect.center = position
        self.max_health = 180
        self.health = self.max_health
        self.shoot_timer = 0
        self.anim_timer = 0

    def update(self, player, enemy_projectiles):
        self.shoot_timer -= 1
        self.anim_timer += 0.1
        if self.shoot_timer <= 0:
            for offset in (-0.28, 0, 0.28):
                target = pygame.Vector2(player.rect.center)
                direction = target - self.position
                angle = math.atan2(direction.y, direction.x) + offset
                target = self.position + pygame.Vector2(math.cos(angle), math.sin(angle)) * 500
                enemy_projectiles.append(NinjaStar(self.rect.center, target))
            self.shoot_timer = 72

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