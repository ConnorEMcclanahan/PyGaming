import pygame


class UI:
    def __init__(self, screen, settings):
        self.screen = screen
        self.settings = settings
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 19)
        self.active_tab = "Inventory"
        self.panel_x = settings.arena_width
        self.items = [("IRON HELM", (150, 160, 175)), ("STEEL MAIL", (100, 125, 155)), ("MANA POT", (78, 155, 220))]
        self.dragging_item = None
        self.drag_position = None

    def draw(self, player):
        panel = pygame.Rect(self.panel_x, 0, self.settings.sidebar_width, self.settings.screen_height)
        pygame.draw.rect(self.screen, (20, 25, 31), panel)
        pygame.draw.line(self.screen, (105, 121, 133), (self.panel_x, 0), (self.panel_x, self.settings.screen_height), 2)
        self._text("PLAYER / LEVEL 1", (self.panel_x + 16, 18), (241, 214, 135), self.font)
        self._bar("HP", player.health, player.max_health, (205, 68, 68), 52)
        self._bar("MP", player.mana, 100, (67, 133, 216), 78)
        tab_y = 112
        for name, offset in (("Inventory", 0), ("Status", 88)):
            tab = pygame.Rect(self.panel_x + 10 + offset, tab_y, 82, 28)
            color = (87, 105, 116) if self.active_tab == name else (43, 53, 62)
            pygame.draw.rect(self.screen, color, tab)
            pygame.draw.rect(self.screen, (122, 139, 148), tab, 1)
            self._text(name, (tab.x + 10, tab.y + 7), (235, 235, 220), self.small_font)
        if self.active_tab == "Inventory":
            self._draw_inventory(player)
        else:
            self._draw_status(player)

    def handle_click(self, position):
        if position[0] < self.panel_x:
            return
        if 112 <= position[1] <= 140:
            self.active_tab = "Inventory" if position[0] < self.panel_x + 98 else "Status"
            return
        slot = self._slot_at(position)
        if slot is not None and slot < len(self.items):
            self.dragging_item = self.items.pop(slot)
            self.drag_position = position

    def handle_drag(self, position):
        if self.dragging_item is not None:
            self.drag_position = position

    def handle_release(self, position):
        if self.dragging_item is None:
            return
        target = self._slot_at(position)
        if target is None:
            self.items.append(self.dragging_item)
        else:
            self.items.insert(min(target, len(self.items)), self.dragging_item)
        self.dragging_item = None
        self.drag_position = None

    def _slot_at(self, position):
        if position[0] < self.panel_x + 18 or position[0] > self.panel_x + 230:
            return None
        if position[1] < 196 or position[1] > 554:
            return None
        column = (position[0] - self.panel_x - 18) // 54
        row = (position[1] - 196) // 54
        return int(row * 4 + column)

    def _draw_inventory(self, player):
        self._text("EQUIPMENT", (self.panel_x + 16, 160), (241, 214, 135), self.small_font)
        slots = [(0, 196), (1, 196), (0, 246), (1, 246), (0, 296), (1, 296)]
        for index, (column, y) in enumerate(slots):
            x = self.panel_x + 18 + column * 58
            slot = pygame.Rect(x, y, 46, 46)
            pygame.draw.rect(self.screen, (43, 51, 58), slot)
            pygame.draw.rect(self.screen, (105, 121, 133), slot, 2)
            if index < len(self.items):
                pygame.draw.rect(self.screen, self.items[index][1], slot.inflate(-16, -16))
        self._text("BACKPACK", (self.panel_x + 16, 372), (241, 214, 135), self.small_font)
        for index in range(12):
            x = self.panel_x + 18 + (index % 4) * 54
            y = 402 + (index // 4) * 54
            pygame.draw.rect(self.screen, (38, 46, 54), (x, y, 44, 44))
            pygame.draw.rect(self.screen, (86, 101, 111), (x, y, 44, 44), 1)
        if self.dragging_item is not None and self.drag_position is not None:
            pygame.draw.rect(self.screen, self.dragging_item[1], (self.drag_position[0] - 12, self.drag_position[1] - 12, 24, 24))

    def _draw_status(self, player):
        self._text("CHARACTER STATUS", (self.panel_x + 16, 160), (241, 214, 135), self.small_font)
        for index, label in enumerate(("Attack       12", "Defense      8", "Dexterity    9", "Vitality     10", "Magic        6")):
            self._text(label, (self.panel_x + 20, 198 + index * 30), (220, 224, 219), self.small_font)
        self._text("A knight's journey begins.", (self.panel_x + 16, 372), (155, 166, 170), self.small_font)

    def _bar(self, name, value, maximum, color, y):
        self._text(name, (self.panel_x + 16, y), (225, 229, 220), self.small_font)
        bar = pygame.Rect(self.panel_x + 52, y + 1, 174, 14)
        pygame.draw.rect(self.screen, (42, 47, 53), bar)
        pygame.draw.rect(self.screen, color, (bar.x, bar.y, round(bar.width * value / maximum), bar.height))
        pygame.draw.rect(self.screen, (110, 120, 125), bar, 1)

    def _text(self, text, position, color, font):
        self.screen.blit(font.render(text, True, color), position)