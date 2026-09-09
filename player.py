import math

import pygame


class Projectile:
    def __init__(self, start_pos, target_pos, speed=10):
        self.position = pygame.Vector2(start_pos)
        direction = pygame.Vector2(target_pos) - self.position
        self.velocity = direction.normalize() * speed if direction.length() else pygame.Vector2(1, 0)
        self.angle = math.atan2(self.velocity.y, self.velocity.x)
        self.image = pygame.Surface((38, 16), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (238, 238, 196), (10, 5, 25, 6))
        pygame.draw.rect(self.image, (255, 214, 83), (4, 3, 8, 10))
        pygame.draw.rect(self.image, (125, 76, 39), (1, 1, 4, 14))
        pygame.draw.rect(self.image, (255, 244, 163), (26, 4, 9, 2))
        self.rotated_image = pygame.transform.rotate(self.image, -math.degrees(self.angle))
        self.rect = self.rotated_image.get_rect(center=start_pos)

    def update(self):
        self.position += self.velocity
        self.rect.center = (round(self.position.x), round(self.position.y))

    def draw(self, screen):
        screen.blit(self.rotated_image, self.rect)

class Player:
    def __init__(self, screen, settings):
        self.screen = screen
        self.settings = settings
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

    def update(self, keys):
        self.is_moving = False
        keys_pressed = keys
        if keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            self.x -= self.speed
            self.is_moving = True
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            self.x += self.speed
            self.is_moving = True
        if keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]:
            self.y -= self.speed
            self.is_moving = True
        if keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
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
        if self.shield_timer > 0:
            self.shield_timer -= 1
            self.is_shielding = True
        else:
            self.is_shielding = False

    def attack(self, world_mouse_pos):
        self.aim_angle = math.atan2(world_mouse_pos[1] - self.rect.centery, world_mouse_pos[0] - self.rect.centerx)
        return Projectile(self.rect.center, world_mouse_pos)

    def bubble_shield(self):
        self.shield_timer = 15
        self.is_shielding = True

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

        sword_x = center_x + round(math.cos(self.aim_angle) * 20)
        sword_y = center_y + round(math.sin(self.aim_angle) * 20)
        pygame.draw.line(screen, (226, 226, 204), (center_x, center_y), (sword_x, sword_y), 5)
        pygame.draw.line(screen, (255, 245, 173), (center_x, center_y), (sword_x, sword_y), 2)
        pygame.draw.line(screen, (126, 77, 42), (center_x - 5, center_y - 5), (center_x + 5, center_y + 5), 3)
        if self.is_shielding:
            pygame.draw.circle(screen, (144, 226, 255), (center_x, center_y), 29, 3)
