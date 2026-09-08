import pygame
from player import Player
from bullet import Bullet
from ninja import Ninja
from settings import Settings
from inventory import Inventory
from pixel_art_knights import Knight
from pixel_art_ui import UI
from testing_environment import TestingEnvironment

class Game:
    def __init__(self):
        self.settings = Settings()
        self.screen = None
        self.clock = None
        self.player = None
        self.ninja = None
        self.bullets = []
        self.ui = None
        self.inventory = None

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

    def run_testing_environment(self):
        testing_environment = TestingEnvironment(self)
        testing_environment.run_testing_environment()
