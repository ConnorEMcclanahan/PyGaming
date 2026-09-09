import pygame
from player import Player
from settings import Settings
from game_testing_environment import GameTestingEnvironment
from ui import UI

class Game:
    def __init__(self):
        self.settings = Settings()
        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        pygame.display.set_caption("ROTGM-Style Bullet Hell Test")
        self.clock = pygame.time.Clock()
        self.player = Player(self.screen)
        self.projectiles = []
        self.ui = UI(self.screen, self.settings)

    def run(self):
        running = True
        while running:
            self.ui.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click: Shoot big sword
                        sword = self.player.attack(pygame.mouse.get_pos())
                        self.projectiles.append(sword)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:  # Space: Shield bash
                        self.player.shield_bash()
            self.player.update(pygame.key.get_pressed())
            self.player.draw(self.screen)
            for proj in self.projectiles:
                proj.update()
                if not self.screen.get_rect().collidepoint(proj.rect.center):
                    self.projectiles.remove(proj)
            self.screen.fill((30, 30, 30))  # Dark floor background
            self.ui.draw()
            pygame.display.flip()
            self.clock.tick(60)

    def run_testing_environment(self):
        testing_environment = GameTestingEnvironment(self)
        testing_environment.run_testing_environment()
