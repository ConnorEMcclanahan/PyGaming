import pygame
from game import Game

class TestingEnvironment:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.clock = game.clock
        self.player = game.player
        self.ninja = game.ninja
        self.bullets = game.bullets
        self.ui = game.ui
        self.inventory = game.inventory

    def run_testing_environment(self):
        self.game.settings.screen_width = 800
        self.game.settings.screen_height = 600

        self.game.screen = pygame.display.set_mode((self.game.settings.screen_width, self.game.settings.screen_height))
        self.game.clock = pygame.time.Clock()

        self.game.player = self.player
        self.game.ninja = self.ninja
        self.game.bullets = self.bullets
        self.game.ui = self.ui
        self.game.inventory = self.inventory

        self.game.run()
