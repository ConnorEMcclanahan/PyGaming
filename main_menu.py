# main_menu.py

import pygame
import sys

def main_menu():
    pygame.init()

    # Set the screen dimensions
    screen_width = 800
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))

    # Set the background color
    background_color = (255, 255, 255)

    # Game title
    game_title = pygame.font.SysFont('Arial', 50).render('PyGaming', True, (0, 0, 0))

    # Game version
    game_version = pygame.font.SysFont('Arial', 30).render('Version 1.0', True, (0, 0, 0))

    # Menu options
    options = [
        ('Start Game', 100, 200),
        ('Quit', 100, 300)
    ]

    # Game loop
    running = True
    while running:
        screen.fill(background_color)
        screen.blit(game_title, (screen_width // 2 - game_title.get_width() // 2, 50))
        screen.blit(game_version, (screen_width // 2 - game_version.get_width() // 2, 100))

        for option in options:
            text = pygame.font.SysFont('Arial', 30).render(option[0], True, (0, 0, 0))
            screen.blit(text, option[1:])

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for option in options:
                    if pygame.mouse.get_pos() in option[1: option[2]]:
                        if option[0] == 'Start Game':
                            from game import Game
                            game = Game()
                            game.run()
                        if option[0] == 'Quit':
                            pygame.quit()
                            sys.exit()

        pygame.display.update()

if __name__ == "__main__":
    main_menu()
