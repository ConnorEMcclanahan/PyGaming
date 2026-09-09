import pygame


class Settings:
    def __init__(self):
        self.screen_width = 1024
        self.screen_height = 768
        self.arena_width = self.screen_width
        self.background_color = (27, 35, 43)
        self.world_width = 3200
        self.world_height = 2400
        self.camera_lerp = 0.14

        # Default keybinds: action name -> pygame key constant.
        # SPACE casts the equipped ability (starter = bubble shield).
        self.keybinds = {
            "move_left": pygame.K_a,
            "move_right": pygame.K_d,
            "move_up": pygame.K_w,
            "move_down": pygame.K_s,
            "shield": pygame.K_SPACE,
            "auto_shoot": pygame.K_x,
            "ability": pygame.K_SPACE,
        }

    def action_name(self, action):
        """Human-readable label for a keybind action, e.g. 'move_left' -> 'Move Left'."""
        return " ".join(part.capitalize() for part in action.split("_"))
