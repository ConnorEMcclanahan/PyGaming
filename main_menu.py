import pygame
import sys
from game import Game

class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 48)
        self.title = self.font.render("ROTGM-Style Bullet Hell Test", True, (255, 255, 255))
        self.title_rect = self.title.get_rect(center=(screen.get_width() // 2, screen.get_height() // 3))
        self.play_button = self.font.render("Play", True, (255, 255, 255))
        self.play_button_rect = self.play_button.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
        self.settings_button = self.font.render("Settings", True, (255, 255, 255))
        self.settings_button_rect = self.settings_button.get_rect(center=(screen.get_width() // 2, screen.get_height() // 1.5))

    def run(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.play_button_rect.collidepoint(event.pos):
                        game = Game()
                        game.run()
                    if self.settings_button_rect.collidepoint(event.pos):
                        self.show_settings()

            self.screen.fill((27, 35, 43))
            self.screen.blit(self.title, self.title_rect)
            self.screen.blit(self.play_button, self.play_button_rect)
            self.screen.blit(self.settings_button, self.settings_button_rect)
            pygame.display.flip()
            clock.tick(60)

    def show_settings(self):
        settings_font = pygame.font.Font(None, 36)
        back_button = settings_font.render("Back", True, (255, 255, 255))
        back_button_rect = back_button.get_rect(center=(self.screen.get_width() // 2, screen.get_height() // 2))

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if back_button_rect.collidepoint(event.pos):
                        return

            self.screen.fill((27, 35, 43))
            settings_font = pygame.font.Font(None, 36)
            settings_text = settings_font.render("Settings", True, (255, 255, 255))
            settings_text_rect = settings_text.get_rect(center=(self.screen.get_width() // 2, screen.get_height() // 3))
            self.screen.blit(settings_text, settings_text_rect)
            self.screen.blit(back_button, back_button_rect)
            pygame.display.flip()
            clock.tick(60)

if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption("ROTGM-Style Bullet Hell Test")
    main_menu = MainMenu(screen)
    main_menu.run()
