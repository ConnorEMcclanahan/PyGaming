import pygame
from player import Player
from bullet import Bullet
from ninja import Ninja
from settings import Settings
from inventory import Inventory
from pixel_art_knights import Knight
from pixel_art_ui import UI

class Game:
    def __init__(self):
        self.settings = Settings()
        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        self.clock = pygame.time.Clock()
        self.player = Knight(self.screen)
        self.ninja = Ninja(self.screen)
        self.bullets = []
        self.ui = UI(self.screen, self.player)
        self.inventory = Inventory()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.player.attack()
                    elif event.button == 3:
                        self.player.shield()
                elif event.type == self.player.INVENTORY_ITEM_ADDED:
                    self.ui.update_inventory()
                elif event.type == self.player.INVENTORY_ITEM_USED:
                    self.ui.update_inventory()

            self.player.update(pygame.mouse.get_pos())
            self.ninja.update()

            self.screen.fill((0, 0, 0))
            self.player.draw(self.screen)
            self.ninja.draw(self.screen)
            for bullet in self.bullets:
                bullet.update()
                bullet.draw(self.screen)
            self.ui.draw(self.screen)

class Inventory:
    def __init__(self):
        self.items = []

class Ninja:
    # ... existing code ...

class Player:
    # ... existing code ...
    def attack(self):
        # ... create a sword bullet ...

    def shield(self):
        # ... create a shield effect ...

    def add_item(self, item):
        self.inventory.items.append(item)

    def use_item(self, item_index):
        # ... use the item ...
