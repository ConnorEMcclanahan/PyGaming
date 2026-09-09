import pygame
from enemy import Ninja
from player import Player
from settings import Settings
from game_testing_environment_module import GameTestingEnvironment
from ui import UI

class Game:
    def __init__(self):
        self.settings = Settings()
        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        pygame.display.set_caption("ROTGM-Style Bullet Hell Test")
        self.clock = pygame.time.Clock()
        self.player = Player(self.screen, self.settings)
        self.ninja = Ninja((self.settings.world_width // 2, self.settings.world_height // 2 - 160))
        self.projectiles = []
        self.enemy_projectiles = []
        self.camera = pygame.Vector2()
        self.ui = UI(self.screen, self.settings)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse = pygame.mouse.get_pos()
                        if mouse[0] < self.settings.arena_width:
                            world_mouse = (mouse[0] + self.camera.x, mouse[1] + self.camera.y)
                            sword = self.player.attack(world_mouse)
                            self.projectiles.append(sword)
                        else:
                            self.ui.handle_click(event.pos)
                    elif event.button == 3:
                        self.ui.handle_click(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.ui.handle_release(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.ui.handle_drag(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.player.bubble_shield()
            self.player.update(pygame.key.get_pressed())
            self._update_camera()
            self.ninja.update(self.player, self.enemy_projectiles)
            for proj in self.projectiles[:]:
                proj.update()
                if not self._in_world(proj.rect) or proj.rect.colliderect(self.ninja.rect):
                    if proj.rect.colliderect(self.ninja.rect):
                        self.ninja.health = max(0, self.ninja.health - 18)
                    self.projectiles.remove(proj)
            for star in self.enemy_projectiles[:]:
                star.update()
                if not self._in_world(star.rect):
                    self.enemy_projectiles.remove(star)
                elif star.rect.colliderect(self.player.rect):
                    if not self.player.is_shielding:
                        self.player.health = max(0, self.player.health - 8)
                    self.enemy_projectiles.remove(star)
            self._draw_world()
            self.ui.draw(self.player)
            pygame.display.flip()
            self.clock.tick(60)

    def run_testing_environment(self):
        testing_environment = GameTestingEnvironment(self)
        testing_environment.run_testing_environment()

    def _update_camera(self):
        target_x = self.player.rect.centerx - self.settings.arena_width // 2
        target_y = self.player.rect.centery - self.settings.screen_height // 2
        max_x = self.settings.world_width - self.settings.arena_width
        max_y = self.settings.world_height - self.settings.screen_height
        target_x = max(0, min(target_x, max_x))
        target_y = max(0, min(target_y, max_y))
        self.camera.x += (target_x - self.camera.x) * self.settings.camera_lerp
        self.camera.y += (target_y - self.camera.y) * self.settings.camera_lerp

    def _in_world(self, rect):
        return rect.right > 0 and rect.left < self.settings.world_width and rect.bottom > 0 and rect.top < self.settings.world_height

    def _draw_world(self):
        self.screen.fill(self.settings.background_color)
        arena = pygame.Rect(0, 0, self.settings.arena_width, self.settings.screen_height)
        pygame.draw.rect(self.screen, (34, 45, 53), arena)
        tile = 48
        start_x = int(self.camera.x // tile) * tile
        start_y = int(self.camera.y // tile) * tile
        for x in range(start_x, int(self.camera.x) + self.settings.arena_width + tile, tile):
            screen_x = x - round(self.camera.x)
            pygame.draw.line(self.screen, (38, 50, 59), (screen_x, 0), (screen_x, self.settings.screen_height))
        for y in range(start_y, int(self.camera.y) + self.settings.screen_height + tile, tile):
            screen_y = y - round(self.camera.y)
            pygame.draw.line(self.screen, (38, 50, 59), (0, screen_y), (self.settings.arena_width, screen_y))

        building = pygame.Rect(self.settings.world_width // 2 - 260, self.settings.world_height // 2 - 290, 520, 230)
        building_screen = building.move(-round(self.camera.x), -round(self.camera.y))
        pygame.draw.rect(self.screen, (77, 62, 58), building_screen)
        pygame.draw.rect(self.screen, (123, 93, 69), building_screen, 8)
        pygame.draw.rect(self.screen, (26, 29, 34), (building_screen.x + 190, building_screen.bottom - 12, 140, 22))
        pygame.draw.rect(self.screen, (54, 43, 42), (building_screen.x + 24, building_screen.y + 32, 78, 58))
        pygame.draw.rect(self.screen, (54, 43, 42), (building_screen.right - 102, building_screen.y + 32, 78, 58))
        self._draw_label("NINJA HIDEOUT", (building_screen.x + 168, building_screen.y + 14), (248, 214, 137))

        for star in self.enemy_projectiles:
            star.draw(self.screen, (round(self.camera.x), round(self.camera.y)))
        self.ninja.draw(self.screen, (round(self.camera.x), round(self.camera.y)))
        for proj in self.projectiles:
            proj_screen = proj.rect.move(-round(self.camera.x), -round(self.camera.y))
            self.screen.blit(proj.rotated_image, proj_screen)
        self.player.draw(self.screen, (round(self.camera.x), round(self.camera.y)))

    def _draw_label(self, text, position, color):
        font = pygame.font.Font(None, 22)
        self.screen.blit(font.render(text, True, color), position)
