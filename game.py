import pygame
from player import Player
from bullet import Bullet
from ninja import Ninja
from settings import Settings
from inventory import Inventory

class Game:
    def __init__(self):
        self.settings = Settings()
        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        self.clock = pygame.time.Clock()
        self.player = Player(self.screen)
        self.ninja = Ninja(self.screen)
        self.bullets = []
        self.inventory = Inventory()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.bullets.append(Bullet(self.screen, self.player.rect.center))
                    elif event.type == self.player.INVENTORY_ITEM_ADDED:
                        # ... update UI to show new item ...
                elif event.type == self.player.INVENTORY_ITEM_USED:
                    # ... update UI to show changes after using an item ...

            self.player.update(pygame.key.get_pressed())
            self.ninja.update()

            self.screen.fill((0, 0, 0))
            self.player.draw(self.screen)
            self.ninja.draw(self.screen)
            for bullet in self.bullets:
                bullet.update()
                bullet.draw(self.screen)

class Inventory:
    def __init__(self):
        self.items = []

class Ninja:
    # ... existing code ...

class Player:
    # ... existing code ...
    def add_item(self, item):
        self.inventory.items.append(item)

    def use_item(self, item_index):
        # ... existing code ...
        item = self.inventory.items[item_index]
        # ... use the item ...
