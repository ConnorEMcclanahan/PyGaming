import pygame
from game import Game

def main():
    pygame.init()
    game = Game()
    game.run_testing_environment()

if __name__ == "__main__":
    main()
