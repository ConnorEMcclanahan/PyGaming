import sys

import pygame

from character_select import CharacterSelect
from game import Game
from settings import Settings
from tutorial import Tutorial

MENU_BACKGROUND = (27, 35, 43)
BUTTON_BG = (43, 53, 62)
BUTTON_HOVER = (60, 78, 96)
BUTTON_BORDER = (122, 139, 148)
TEXT = (255, 255, 255)
TEXT_SOFT = (230, 230, 220)
TEXT_DIM = (200, 200, 190)
ACCENT = (241, 214, 135)


class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.running = True
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 30)
        self.tiny_font = pygame.font.Font(None, 22)

        cx = screen.get_width() // 2
        cy = screen.get_height() // 2

        self.title_surf = self.font.render("ROTGM-Style Bullet Hell Test", True, TEXT)
        self.title_rect = self.title_surf.get_rect(center=(cx, cy - 130))

        self.play_surf = self.font.render("Play", True, TEXT)
        self.play_rect = self.play_surf.get_rect(center=(cx, cy))

        self.settings_surf = self.font.render("Settings", True, TEXT)
        self.settings_rect = self.settings_surf.get_rect(center=(cx, cy + 90))

        self.game_settings = Settings()

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.play_rect.collidepoint(event.pos):
                        self._start_game()
                    elif self.settings_rect.collidepoint(event.pos):
                        self.show_settings()

            self.screen.fill(MENU_BACKGROUND)
            mouse_pos = pygame.mouse.get_pos()
            self.screen.blit(self.title_surf, self.title_rect)
            self._draw_menu_button(self.play_rect, self.play_surf, mouse_pos)
            self._draw_menu_button(self.settings_rect, self.settings_surf, mouse_pos)
            pygame.display.flip()
            clock.tick(60)

    def _start_game(self):
        select = CharacterSelect(self.screen, self.game_settings)
        character = select.run()
        if character == "quit":
            self.running = False
            return
        if character is None:
            return
        tutorial = Tutorial(self.screen, self.game_settings, character)
        tutorial_result = tutorial.run()
        if tutorial_result == "quit":
            self.running = False
            return
        game = Game(self.game_settings, character=character)
        should_exit = game.run()
        if should_exit:
            self.running = False

    def _draw_menu_button(self, button_rect, label, mouse_pos):
        base = button_rect.inflate(16, 10)
        color = BUTTON_HOVER if base.collidepoint(mouse_pos) else BUTTON_BG
        pygame.draw.rect(self.screen, color, base)
        pygame.draw.rect(self.screen, BUTTON_BORDER, base, 2)
        self.screen.blit(label, button_rect)

    def show_settings(self):
        clock = pygame.time.Clock()
        cx = self.screen.get_width() // 2
        back_surf = self.small_font.render("Back", True, TEXT)
        back_rect = back_surf.get_rect(center=(cx, self.screen.get_height() - 55))
        rebind_action = None
        key_rows = []

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if back_rect.collidepoint(event.pos):
                        return
                    for action, row_rect in key_rows:
                        if row_rect.collidepoint(event.pos):
                            rebind_action = action
                            break
                elif event.type == pygame.KEYDOWN:
                    if rebind_action is not None:
                        if event.key == pygame.K_ESCAPE:
                            rebind_action = None
                        else:
                            self.game_settings.keybinds[rebind_action] = event.key
                            rebind_action = None

            self.screen.fill(MENU_BACKGROUND)
            self._center_text("Settings", (cx, 70), self.font, TEXT)
            self._center_text("Click a key, then press a new key to rebind.", (cx, 122), self.tiny_font, TEXT_DIM)

            key_rows = []
            start_y = 170
            for index, action in enumerate(self.game_settings.keybinds):
                row_rect = pygame.Rect(cx - 240, start_y + index * 48, 480, 38)
                listening = rebind_action == action
                pygame.draw.rect(self.screen, BUTTON_BG, row_rect)
                pygame.draw.rect(self.screen, BUTTON_BORDER, row_rect, 2)
                name_label = self.small_font.render(self.game_settings.action_name(action), True, TEXT_SOFT)
                self.screen.blit(name_label, name_label.get_rect(midleft=(row_rect.x + 16, row_rect.centery)))
                if listening:
                    value_label = self.small_font.render("Press a key...", True, ACCENT)
                else:
                    value_label = self.small_font.render(
                        pygame.key.name(self.game_settings.keybinds[action]).upper(), True, TEXT
                    )
                self.screen.blit(value_label, value_label.get_rect(midright=(row_rect.right - 16, row_rect.centery)))
                key_rows.append((action, row_rect))

            base = back_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, BUTTON_BG, base)
            pygame.draw.rect(self.screen, BUTTON_BORDER, base, 2)
            self.screen.blit(back_surf, back_rect)

            pygame.display.flip()
            clock.tick(60)

    def _center_text(self, text, center, font, color):
        label = font.render(text, True, color)
        rect = label.get_rect(center=center)
        self.screen.blit(label, rect)


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption("ROTGM-Style Bullet Hell Test")
    main_menu = MainMenu(screen)
    main_menu.run()
    pygame.quit()
    sys.exit(0)