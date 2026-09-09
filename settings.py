class Settings:
    def __init__(self):
        self.screen_width = 1024
        self.screen_height = 768
        self.sidebar_width = 256
        self.arena_width = self.screen_width - self.sidebar_width
        self.background_color = (27, 35, 43)
        self.world_width = 3200
        self.world_height = 2400
        self.camera_lerp = 0.14
