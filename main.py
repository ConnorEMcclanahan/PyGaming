import sys

import pygame

from main_menu import MainMenu


def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption("ROTGM-Style Bullet Hell Test")
    main_menu = MainMenu(screen)
    main_menu.run()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
