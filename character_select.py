import pygame

MENU_BACKGROUND = (27, 35, 43)
CARD_BG = (43, 53, 62)
CARD_HOVER = (60, 78, 96)
CARD_BORDER = (90, 100, 112)
TEXT = (255, 255, 255)
TEXT_SOFT = (230, 230, 220)
TEXT_DIM = (200, 200, 190)
ACCENT = (241, 214, 135)

CHARACTERS = [
    {
        "id": "knight",
        "name": "Knight",
        "title": "The Knight",
        "desc": "A balanced melee fighter clad in steel. Wields a glowing arcblade.",
        "color": (211, 216, 215),
        "locked": False,
    },
    {
        "id": "archer",
        "name": "Archer",
        "title": "The Archer",
        "desc": "A swift marksman who strikes from afar.",
        "color": (120, 190, 90),
        "locked": True,
    },
    {
        "id": "mage",
        "name": "Mage",
        "title": "The Mage",
        "desc": "A master of arcane destruction.",
        "color": (140, 100, 220),
        "locked": True,
    },
    {
        "id": "rogue",
        "name": "Rogue",
        "title": "The Rogue",
        "desc": "A shadowy assassin with twin daggers.",
        "color": (96, 96, 118),
        "locked": True,
    },
]


class CharacterSelect:
    """Character selection screen. run() returns a character id, 'quit',
    or None if the player went back to the main menu."""

    def __init__(self, screen, settings):
        self.screen = screen
        self.settings = settings
        self.font = pygame.font.Font(None, 46)
        self.small_font = pygame.font.Font(None, 26)
        self.tiny_font = pygame.font.Font(None, 19)
        self.locked_hint = None
        self.locked_timer = 0
        self._build_layout()

    def _build_layout(self):
        w, h = self.screen.get_size()
        cx = w // 2
        self.title_center = (cx, 92)
        self.sub_center = (cx, 130)

        card_w, card_h = 210, 330
        spacing = 26
        total = len(CHARACTERS) * card_w + (len(CHARACTERS) - 1) * spacing
        start_x = cx - total // 2
        y = h // 2 - card_h // 2 + 46
        self.cards = []
        for index, data in enumerate(CHARACTERS):
            rect = pygame.Rect(start_x + index * (card_w + spacing), y, card_w, card_h)
            self.cards.append((data, rect))

        back = self.small_font.render("Back", True, TEXT)
        self.back_rect = back.get_rect(center=(cx - 80, h - 55))
        self.back_surf = back

    def run(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.back_rect.collidepoint(event.pos):
                        return None
                    for data, rect in self.cards:
                        if rect.collidepoint(event.pos):
                            if data["locked"]:
                                self.locked_hint = "{} is coming soon!".format(data["title"])
                                self.locked_timer = 120
                            else:
                                return data["id"]

            self._draw()
            if self.locked_timer > 0:
                self.locked_timer -= 1
            pygame.display.flip()
            clock.tick(60)

    # ------------------------------------------------------------------ draw
    def _draw(self):
        self.screen.fill(MENU_BACKGROUND)
        w, h = self.screen.get_size()
        cx = w // 2
        title = self.font.render("SELECT YOUR CHARACTER", True, TEXT)
        self.screen.blit(title, title.get_rect(center=self.title_center))
        sub = self.tiny_font.render("Choose your class to begin the adventure.", True, TEXT_DIM)
        self.screen.blit(sub, sub.get_rect(center=self.sub_center))

        mouse = pygame.mouse.get_pos()
        for data, rect in self.cards:
            self._draw_card(data, rect, mouse)

        base = self.back_rect.inflate(26, 12)
        hovered = base.collidepoint(mouse)
        pygame.draw.rect(self.screen, CARD_HOVER if hovered else CARD_BG, base)
        pygame.draw.rect(self.screen, CARD_BORDER, base, 2)
        self.screen.blit(self.back_surf, self.back_rect)

        if self.locked_timer > 0 and self.locked_hint:
            hint = self.tiny_font.render(self.locked_hint, True, ACCENT)
            self.screen.blit(hint, hint.get_rect(center=(cx, h - 55)))

    def _draw_card(self, data, rect, mouse):
        over = rect.collidepoint(mouse)
        bg = CARD_HOVER if over else CARD_BG
        if data["locked"]:
            bg = (bg[0] // 2, bg[1] // 2, bg[2] // 2)
        pygame.draw.rect(self.screen, bg, rect)
        border = ACCENT if over and not data["locked"] else CARD_BORDER
        pygame.draw.rect(self.screen, border, rect, 3)

        portrait = pygame.Rect(rect.x + 20, rect.y + 24, rect.w - 40, 128)
        pygame.draw.rect(self.screen, (32, 38, 46), portrait)
        if data["locked"]:
            pygame.draw.circle(self.screen, (70, 70, 82), portrait.center, 36, 3)
            qmark = self.font.render("?", True, TEXT_DIM)
            self.screen.blit(qmark, qmark.get_rect(center=portrait.center))
        else:
            self._draw_knight_portrait(portrait)

        name = self.small_font.render(data["title"], True, TEXT_SOFT if not data["locked"] else TEXT_DIM)
        self.screen.blit(name, name.get_rect(midtop=(rect.centerx, portrait.bottom + 14)))

        for index, line in enumerate(self._wrap(data["desc"], 25)):
            label = self.tiny_font.render(line, True, TEXT_DIM)
            self.screen.blit(label, label.get_rect(midtop=(rect.centerx, portrait.bottom + 48 + index * 20)))

        label = "PLAY" if not data["locked"] else "LOCKED"
        color = ACCENT if not data["locked"] else (150, 150, 160)
        play = self.small_font.render(label, True, color)
        self.screen.blit(play, play.get_rect(midbottom=(rect.centerx, rect.bottom - 12)))

    def _draw_knight_portrait(self, portrait):
        cx, cy = portrait.centerx, portrait.centery
        pygame.draw.ellipse(self.screen, (12, 17, 22), (cx - 30, cy + 26, 60, 14))
        pygame.draw.rect(self.screen, (55, 62, 76), (cx - 22, cy - 10, 44, 38))
        pygame.draw.rect(self.screen, (177, 183, 192), (cx - 18, cy - 16, 36, 32))
        pygame.draw.rect(self.screen, (211, 216, 215), (cx - 14, cy - 40, 28, 22))
        pygame.draw.rect(self.screen, (106, 116, 132), (cx - 19, cy - 24, 38, 8))
        pygame.draw.rect(self.screen, (34, 39, 50), (cx - 10, cy - 18, 20, 5))
        pygame.draw.line(self.screen, (226, 226, 204), (cx, cy + 8), (cx + 42, cy - 20), 7)
        pygame.draw.line(self.screen, (255, 245, 173), (cx, cy + 8), (cx + 42, cy - 20), 3)

    def _wrap(self, text, width):
        words = text.split()
        lines = []
        current = ""
        for word in words:
            if len(current) + len(word) + 1 > width:
                lines.append(current)
                current = word
            else:
                current = current + " " + word if current else word
        if current:
            lines.append(current)
        return lines