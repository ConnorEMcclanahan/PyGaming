import pygame
from settings import Settings

class Player:
    def __init__(self, screen):
        self.screen = screen
        self.width = 32
        self.height = 32
        self.x = 400
        self.y = 300
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.speed = 4
        self.health = 100
        self.is_moving = False
        self.is_shielding = False
        self.shield_timer = 0

    def update(self, keys):
        self.is_moving = False
        keys_pressed = pygame.key.get_pressed()
        if keys_pressed[pygame.K_LEFT]:
            self.x -= self.speed
        if keys_pressed[pygame.K_RIGHT]:
            self.x += self.speed
        if keys_pressed[pygame.K_UP]:
            self.y -= self.speed
        if keys_pressed[pygame.K_DOWN]:
            self.y += self.speed
        if self.x < 0:
            self.x = 0
        if self.x + self.width > self.screen.get_width():
            self.x = self.screen.get_width() - self.width
        if self.y < 0:
            self.y = 0
        if self.y + self.height > self.screen.get_height():
            self.y = self.screen.get_height() - self.height

    def attack(self, mouse_pos):
        # Attack logic
        pass

    def shield_bash(self):
        # Shield bash logic
        pass

    def draw(self, screen):
        # Draw player sprite
        pass
