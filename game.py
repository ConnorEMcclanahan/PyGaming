import pygame
from player import Player
from bullet import Bullet
from ninja import Ninja
from settings import Settings

class Game:
    def __init__(self):
        self.settings = Settings()
        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        self.clock = pygame.time.Clock()
        self.player = Player(self.screen)
        self.ninja = Ninja(self.screen)
        self.bullets = []

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.bullets.append(Bullet(self.screen, self.player.rect.center))

            self.player.update(pygame.key.get_pressed())
            self.ninja.update()

            self.screen.fill((0, 0, 0))
            self.player.draw(self.screen)
            self.ninja.draw(self.screen)
            for bullet in self.bullets:
                bullet.update()
                bullet.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(60)

class Ninja:
    def __init__(self, screen):
        self.screen = screen
        self.image = pygame.image.load('ninja.png').convert_alpha()
        self.rect = self.image.get_rect()
        self.speed = 2
        self.shoot_timer = pygame.USEREVENT + 1
        pygame.time.set_timer(self.shoot_timer, 1000)

    def update(self):
        self.rect.x += self.speed
        if self.rect.x > self.screen.get_width():
            self.rect.x = 0

        if pygame.time.get_ticks() > self.shoot_timer_last:
            self.shoot_stars()
            self.shoot_timer_last = pygame.time.get_ticks()

    def shoot_stars(self):
        for i in range(5):
            star = Star(self.screen)
            star.rect.centerx = self.rect.centerx
            star.rect.bottom = self.rect.top
            star.speed_y = 5
            self.screen.blits(star)

class Star:
    def __init__(self, screen):
        self.screen = screen
        self.image = pygame.image.load('star.png').convert_alpha()
        self.rect = self.image.get_rect()

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.bottom > self.screen.get_height():
            self.kill()

settings.py
