"""Safe-town layer for the overworld: layout, NPCs and the shop / sell /
vault menus. game.py drives everything from here so the world stays modular:

* Spawn inside the walls - enemies can never hurt you in town.
* OUTFITTER (buy), BAZAAR (sell) and THE VAULT (storage) buildings.
* Talk to townsfolk with the Interact key to open the matching menu.
* The gate in the east wall is the only way out into the wilderness.
"""
import math
import random

import pygame

from items import (
    LOOT_TABLE,
    ORB_ITEMS,
    ORB_NAMES,
    ORB_ORDER,
    ORB_VALUES,
    draw_item_icon,
    item_slot,
    upgrade_rarity,
)
from ui import BAD_RED, GOLD, RARITY_BORDER, TEXT_DIM, TEXT_LIGHT

# ------------------------------------------------------------------ layout
TOWN_RECT = pygame.Rect(0, 1800, 1250, 1480)   # the walled safe zone (below the water)
WALL = 26
GATE_TOP, GATE_BOTTOM = 2420, 2660            # gap in the east wall
WALL_RECTS = [
    pygame.Rect(0, TOWN_RECT.top - WALL, TOWN_RECT.width, WALL),                       # north
    pygame.Rect(0, TOWN_RECT.bottom, TOWN_RECT.width, WALL),                           # south
    pygame.Rect(0, TOWN_RECT.top - WALL, WALL, TOWN_RECT.height + 2 * WALL),           # west
    pygame.Rect(TOWN_RECT.right - WALL, TOWN_RECT.top - WALL, WALL, GATE_TOP - (TOWN_RECT.top - WALL)),   # east (above gate)
    pygame.Rect(TOWN_RECT.right - WALL, GATE_BOTTOM, WALL, (TOWN_RECT.bottom + WALL) - GATE_BOTTOM),      # east (below gate)
]
GATE_RECT = pygame.Rect(TOWN_RECT.right - WALL, GATE_TOP, WALL, GATE_BOTTOM - GATE_TOP)
SPAWN_POINT = (600, 2300)                     # Inside the town
FOUNTAIN = pygame.Rect(575, 2150, 104, 104)

BUILDINGS = [
    {"key": "shop", "rect": pygame.Rect(150, 1980, 300, 220), "label": "OUTFITTER", "mode": "shop"},
    {"key": "sell", "rect": pygame.Rect(810, 1980, 300, 220), "label": "BAZAAR", "mode": "sell"},
    {"key": "vault", "rect": pygame.Rect(810, 2900, 300, 220), "label": "THE VAULT", "mode": "vault"},
    {"key": "forge", "rect": pygame.Rect(150, 2900, 300, 220), "label": "THE FORGE", "mode": "forge"},
]

# The ninja boss lair - now south of town
HIDEOUT_RECT = pygame.Rect(1700, 4500, 900, 900)
HIDEOUT_CENTER = HIDEOUT_RECT.center

# ------------------------------------------------------------------ npcs
class NPC:
    """A townsperson. Keepers stand at their building and open menus;
    villagers wander the plaza and chat when talked to."""

    def __init__(self, name, pos, color, role=None, line=None, bounds=None):
        self.name = name
        self.role = role            # "shop" | "sell" | "vault" | None (villager)
        self.line = line
        self.position = pygame.Vector2(pos)
        self.rect = pygame.Rect(0, 0, 30, 30)
        self.rect.center = (round(pos[0]), round(pos[1]))
        self.color = color
        self.bounds = bounds
        self.timer = random.randint(30, 120)
        self.dir = pygame.Vector2()
        self.anim = random.uniform(0, 6)

    @property
    def is_keeper(self):
        return self.role is not None

    def prompt_label(self):
        return {"shop": "SHOP", "sell": "SELL", "vault": "VAULT", "forge": "FORGE", "respec": "RESPEC"}.get(self.role, "TALK")

    def update(self):
        self.anim += 0.08
        if self.is_keeper or self.bounds is None:
            self.rect.center = (round(self.position.x), round(self.position.y))
            return
        self.timer -= 1
        if self.timer <= 0:
            self.timer = random.randint(70, 160)
            self.dir = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
            if self.dir.length_squared() == 0:
                self.dir = pygame.Vector2(1, 0)
            self.dir.scale_to_length(random.uniform(0.3, 0.8))
        self.position += self.dir
        self.position.x = max(self.bounds.x + 20, min(self.position.x, self.bounds.right - 20))
        self.position.y = max(self.bounds.y + 20, min(self.position.y, self.bounds.bottom - 20))
        self.rect.center = (round(self.position.x), round(self.position.y))

    def draw(self, screen, camera):
        x = self.rect.centerx - camera[0]
        y = self.rect.centery - camera[1] + int(math.sin(self.anim) * 2)
        pygame.draw.ellipse(screen, (12, 17, 22), (x - 13, y + 11, 26, 7))
        pygame.draw.rect(screen, self.color, (x - 10, y - 4, 20, 16))
        pygame.draw.circle(screen, (233, 214, 184), (x, y - 11), 7)
        pygame.draw.rect(screen, (40, 34, 30), (x - 7, y - 16, 14, 5))
        pygame.draw.rect(screen, self.color, (x - 9, y + 10, 7, 5))
        pygame.draw.rect(screen, self.color, (x + 2, y + 10, 7, 5))
        font = pygame.font.Font(None, 16)
        color = (255, 224, 130) if self.is_keeper else (210, 205, 195)
        label = font.render(self.name, True, color)
        screen.blit(label, label.get_rect(midbottom=(x, y - 22)))


def make_npcs():
    """The town population: a keeper for every service plus wandering folk."""
    npcs = [
        NPC("MARLA", (350, 2050), (70, 110, 190), role="shop"),
        NPC("FENN", (900, 2050), (70, 150, 90), role="sell"),
        NPC("GRUM", (900, 2850), (190, 150, 60), role="vault"),
        NPC("VULCAN", (350, 2850), (200, 90, 50), role="forge"),
        NPC("SAGE", (625, 2200), (180, 100, 200), role="respec"),
        NPC("PIP", (560, 2400), (150, 110, 80),
            line="They say the NINJA WARLORD hoards treasure in his hideout, far south past the gate."),
        NPC("MIRA", (700, 2600), (130, 105, 150),
            line="Slimes infest the ruins to the east. They're weak — good for beginners!"),
        NPC("OLD TOM", (430, 2700), (110, 120, 130),
            line="The beach to the north is nice, but don't swim too deep or you'll drown!"),
    ]
    plaza = TOWN_RECT.inflate(-160, -160)
    for npc in npcs:
        if not npc.is_keeper:
            npc.bounds = plaza
    return npcs

# ------------------------------------------------------------------ drawing
def _label(screen, text, center, color):
    font = pygame.font.Font(None, 20)
    surf = font.render(text, True, color)
    screen.blit(surf, surf.get_rect(center=center))


def _draw_building(screen, rect, label):
    pygame.draw.rect(screen, (46, 38, 36), rect.move(6, 8))
    pygame.draw.rect(screen, (77, 62, 58), rect)
    pygame.draw.rect(screen, (123, 93, 69), rect, 8)
    pygame.draw.rect(screen, (26, 29, 34), (rect.centerx - 34, rect.bottom - 40, 68, 40))
    pygame.draw.rect(screen, (54, 43, 42), (rect.x + 24, rect.y + 34, 62, 48))
    pygame.draw.rect(screen, (54, 43, 42), (rect.right - 86, rect.y + 34, 62, 48))
    _label(screen, label, (rect.centerx, rect.y + 16), (248, 214, 137))


def draw_town(screen, camera):
    """Draw the safe town: plaza, walls, gate, buildings and fountain."""
    ox, oy = round(camera[0]), round(camera[1])

    def r(rect):
        return rect.move(-ox, -oy)

    # Plaza floor + cobble pattern.
    pygame.draw.rect(screen, (54, 60, 52), r(TOWN_RECT))
    pygame.draw.rect(screen, (64, 72, 60), r(TOWN_RECT.inflate(-12, -12)))
    for gx in range(TOWN_RECT.left + 70, TOWN_RECT.right - 30, 110):
        for gy in range(TOWN_RECT.top + 70, TOWN_RECT.bottom - 30, 110):
            pygame.draw.rect(screen, (70, 78, 66), r(pygame.Rect(gx, gy, 6, 6)))

    # Stone walls (the gate gap in the east wall is the only opening).
    for wall in WALL_RECTS:
        pygame.draw.rect(screen, (96, 90, 78), r(wall))
        pygame.draw.rect(screen, (62, 58, 50), r(wall), 2)
        for by in range(wall.top + 10, wall.bottom - 6, 24):
            pygame.draw.line(screen, (76, 72, 62), (wall.x - ox, by - oy), (wall.right - ox, by - oy), 2)

    pygame.draw.rect(screen, (140, 104, 62), r(GATE_RECT.inflate(8, 0)))
    _label(screen, "TOWN GATE", (GATE_RECT.centerx - ox, GATE_RECT.top - oy - 12), (255, 224, 130))
    _label(screen, "SAFE ZONE - NO ENEMIES", (TOWN_RECT.centerx - ox, TOWN_RECT.top - oy + 26), (150, 220, 150))

    for spec in BUILDINGS:
        _draw_building(screen, r(spec["rect"]), spec["label"])

    # Fountain (decor).
    f = r(FOUNTAIN)
    pygame.draw.ellipse(screen, (108, 118, 128), f)
    pygame.draw.ellipse(screen, (80, 160, 220), f.inflate(-18, -18))
    pygame.draw.ellipse(screen, (150, 220, 255), f.inflate(-18, -18), 2)
    pygame.draw.circle(screen, (190, 240, 255), f.center, 8)

# ------------------------------------------------------------------ menus
SELL_PRICE = {"common": 6, "uncommon": 15, "rare": 45, "epic": 110, "legendary": 260}
BUY_PRICE = {"common": 25, "uncommon": 60, "rare": 180, "epic": 450, "legendary": 950}
SHOP_STOCK = [
    ("REPAIR CELL", (220, 70, 70), "common", None),
    ("ENERGY CELL", (78, 200, 255), "uncommon", None),
    ("PLASMA SABER", (90, 220, 255), "common", "weapon"),
    ("ION MAIL", (100, 160, 220), "uncommon", "armor"),
    ("AURORA BLADE", (140, 255, 230), "rare", "weapon"),
    ("NOVA SCROLL", (255, 190, 110), "rare", "ability"),
    ("VOID CLOAK", (150, 90, 220), "rare", "armor"),
]
VAULT_SIZE = 16

# Forge recipes: costs are exact per-orb-type dicts.
UPGRADE_COST = {
    "common": {"scrap": 4, "phase": 1},
    "uncommon": {"phase": 6, "quantum": 1},
    "rare": {"quantum": 4, "singularity": 1},
    "epic": {"quantum": 8, "singularity": 2},
}
REROLL_COST = {"phase": 3, "quantum": 1}


def fmt_cost(cost):
    return " + ".join("{} {}".format(n, ORB_NAMES[k]) for k, n in cost.items())


def _reroll_item(item):
    """Chaos-orb style: a random item of the same slot and rarity."""
    slot = item_slot(item)
    pool = [it for it in LOOT_TABLE if item_slot(it) == slot and it[2] == item[2]]
    if not pool:
        pool = [it for it in LOOT_TABLE if item_slot(it) == slot]
    if not pool:
        return item
    return random.choice(pool)


class ShopMenu:
    """Modal town menu: buy gear at the OUTFITTER, sell loot at the BAZAAR,
    deposit/withdraw gear at THE VAULT. The world pauses while it's open."""

    def __init__(self, screen, ui, player, mode, vault=None):
        self.screen = screen
        self.ui = ui
        self.player = player
        self.mode = mode
        self.vault = vault
        self.done = False
        self.message = ""
        self.message_color = TEXT_LIGHT
        self.font = pygame.font.Font(None, 30)
        self.small = pygame.font.Font(None, 20)
        self.mini = pygame.font.Font(None, 16)
        w, h = screen.get_size()
        arena_cx = max(w - ui.panel.width, 1) // 2
        if mode == "shop":
            self.window = pygame.Rect(0, 0, 500, 78 * len(SHOP_STOCK) + 100)
        elif mode == "vault":
            self.window = pygame.Rect(0, 0, 640, 370)
        elif mode == "forge":
            self.window = pygame.Rect(0, 0, 680, 450)
            self.selected = None
            self.recipe_rects = []
        else:
            self.window = pygame.Rect(0, 0, 440, 360)
        self.window.center = (arena_cx, h // 2)
        self.title = {"shop": "OUTFITTER", "sell": "BAZAAR", "vault": "THE VAULT", "forge": "THE FORGE"}[mode]
        self.close_rect = pygame.Rect(0, 0, 28, 28)
        self.close_rect.topright = (self.window.right - 8, self.window.top + 8)
        self.item_cells = []
        self._build_slots()
        self.hint = {
            "shop": "Click an item to buy it (paid in orb value).",
            "sell": "Click an item to sell it (paid in orbs).",
            "vault": "Click VAULT items to withdraw, BACKPACK items to deposit.",
            "forge": "Select a backpack item, then pick a recipe.",
        }[mode]

    def _build_slots(self):
        self.item_cells = []
        if self.mode == "shop":
            for i in range(len(SHOP_STOCK)):
                row = pygame.Rect(self.window.x + 18, self.window.y + 64 + i * 78, self.window.w - 36, 66)
                self.item_cells.append((i, row))
        elif self.mode == "vault":
            cell, gap = 52, 10
            grid_w = 4 * cell + 3 * gap
            vx, vy = self.window.x + 40, self.window.y + 96
            for row in range(4):
                for col in range(4):
                    idx = row * 4 + col
                    rect = pygame.Rect(vx + col * (cell + gap), vy + row * (cell + gap), cell, cell)
                    self.item_cells.append(("vault", idx, rect))
            bx, by = self.window.right - 40 - grid_w, self.window.y + 96
            for row in range(3):
                for col in range(4):
                    idx = row * 4 + col
                    rect = pygame.Rect(bx + col * (cell + gap), by + row * (cell + gap), cell, cell)
                    self.item_cells.append(("backpack", idx, rect))
        elif self.mode == "forge":
            cell, gap = 52, 10
            vx, vy = self.window.x + 36, self.window.y + 116
            for row in range(3):
                for col in range(4):
                    idx = row * 4 + col
                    rect = pygame.Rect(vx + col * (cell + gap), vy + row * (cell + gap), cell, cell)
                    self.item_cells.append(("backpack", idx, rect))
            rx = self.window.x + 380
            self.recipe_rects = [
                ("upgrade", pygame.Rect(rx, self.window.y + 116, 264, 62)),
                ("reroll", pygame.Rect(rx, self.window.y + 196, 264, 62)),
            ]
        else:  # sell: mirrors the 4x3 backpack
            cell, gap, cols = 56, 12, 4
            grid_w = cols * cell + (cols - 1) * gap
            start_x = self.window.centerx - grid_w // 2
            start_y = self.window.y + 100
            for row in range(3):
                for col in range(cols):
                    idx = row * cols + col
                    rect = pygame.Rect(start_x + col * (cell + gap), start_y + row * (cell + gap), cell, cell)
                    self.item_cells.append((idx, rect))

    # ------------------------------------------------------------- handling
    def _say(self, text, color):
        self.message = text
        self.message_color = color

    def handle_click(self, pos):
        """Route a click into the menu. Returns True if the click was inside
        the window (consumed); sets self.done when the menu should close."""
        if not self.window.collidepoint(pos):
            return False
        if self.close_rect.collidepoint(pos):
            self.done = True
            return True
        if self.mode == "shop":
            self._handle_buy(pos)
        elif self.mode == "sell":
            self._handle_sell(pos)
        elif self.mode == "vault":
            self._handle_vault(pos)
        elif self.mode == "forge":
            self._handle_forge(pos)
        return True

    def _handle_buy(self, pos):
        for i, row in self.item_cells:
            if not row.collidepoint(pos):
                continue
            item = SHOP_STOCK[i]
            price = BUY_PRICE[item[2]]
            if not self.player.spend_orbs(price):
                self._say("NOT ENOUGH ORB VALUE (need {})".format(price), BAD_RED)
            elif not self.ui.add_item(item):
                self.player.credit_orbs(price)
                self._say("BACKPACK FULL", BAD_RED)
            else:
                self._say("TRADED for {} (-{} VALUE)".format(item[0], price), (140, 235, 140))
            return

    def _handle_sell(self, pos):
        for idx, cell in self.item_cells:
            if not cell.collidepoint(pos):
                continue
            item = self.ui.backpack[idx]
            if item is None:
                return
            price = SELL_PRICE.get(item[2], 5)
            self.ui.backpack[idx] = None
            self.player.credit_orbs(price)
            self._say("TRADED {} (+{} VALUE IN ORBS)".format(item[0], price), (240, 200, 90))
            return

    def _handle_vault(self, pos):
        for where, idx, cell in self.item_cells:
            if not cell.collidepoint(pos):
                continue
            if where == "vault":
                item = self.vault[idx]
                if item is None:
                    return
                if self.ui.add_item(item):
                    self.vault[idx] = None
                    self._say("WITHDREW {}".format(item[0]), TEXT_LIGHT)
                else:
                    self._say("BACKPACK FULL", BAD_RED)
            else:
                item = self.ui.backpack[idx]
                if item is None:
                    return
                slot = next((k for k, v in enumerate(self.vault) if v is None), None)
                if slot is None:
                    self._say("VAULT FULL", BAD_RED)
                else:
                    self.vault[slot] = item
                    self.ui.backpack[idx] = None
                    self._say("DEPOSITED {}".format(item[0]), TEXT_LIGHT)
            return

    def _handle_forge(self, pos):
        for where, idx, cell in self.item_cells:
            if not cell.collidepoint(pos):
                continue
            if self.ui.backpack[idx] is not None:
                self.selected = idx
                self._say("SELECTED {}".format(self.ui.backpack[idx][0]), TEXT_LIGHT)
            return
        for action, rect in getattr(self, "recipe_rects", []):
            if not rect.collidepoint(pos):
                continue
            item = self.ui.backpack[self.selected] if self.selected is not None else None
            if action == "upgrade":
                self._forge_upgrade(item)
            else:
                self._forge_reroll(item)
            return

    def _forge_upgrade(self, item):
        if item is None:
            self._say("SELECT A BACKPACK ITEM FIRST", BAD_RED)
            return
        rarity = item[2] if len(item) > 2 else "common"
        cost = UPGRADE_COST.get(rarity)
        if cost is None:
            self._say("{} IS ALREADY LEGENDARY".format(item[0]), GOLD)
            return
        if not self.player.pay_orbs(cost):
            self._say("MISSING ORBS: {}".format(fmt_cost(cost)), BAD_RED)
            return
        upgraded = upgrade_rarity(item)
        self.ui.backpack[self.selected] = upgraded
        self._say("FORGED {} -> {} {}".format(item[0], upgraded[2].upper(), upgraded[0]), (140, 235, 140))

    def _forge_reroll(self, item):
        if item is None:
            self._say("SELECT A BACKPACK ITEM FIRST", BAD_RED)
            return
        if not self.player.pay_orbs(REROLL_COST):
            self._say("MISSING ORBS: {}".format(fmt_cost(REROLL_COST)), BAD_RED)
            return
        new_item = _reroll_item(item)
        self.ui.backpack[self.selected] = new_item
        self._say("REROLLED INTO {}".format(new_item[0]), (240, 200, 90))

    def _orb_header(self):
        counts = "  ".join("{} {}".format(ORB_NAMES[k], self.player.orbs.get(k, 0)) for k in ORB_ORDER)
        return "ORBS: {}  (VALUE {})".format(counts, self.player.orb_balance())

    # ------------------------------------------------------------- drawing
    def _draw_cell(self, cell, item, selected=False):
        pygame.draw.rect(self.screen, (34, 30, 26), cell)
        if item is not None:
            draw_item_icon(self.screen, item, cell.inflate(-10, -10))
            border = GOLD if selected else RARITY_BORDER.get(item[2], (140, 142, 148))
            pygame.draw.rect(self.screen, border, cell, 3 if selected else 2)
        else:
            pygame.draw.rect(self.screen, (74, 62, 44), cell, 2)

    def draw(self):
        view_w = self.screen.get_width() - self.ui.panel.width
        dim = pygame.Surface((view_w, self.screen.get_height()), pygame.SRCALPHA)
        dim.fill((8, 8, 12, 150))
        self.screen.blit(dim, (0, 0))
        win = self.window
        pygame.draw.rect(self.screen, (20, 17, 14), win)
        pygame.draw.rect(self.screen, (110, 92, 58), win, 3)
        title = self.font.render(self.title, True, GOLD)
        self.screen.blit(title, title.get_rect(midtop=(win.centerx, win.y + 12)))
        orb_lbl = self.mini.render(self._orb_header(), True, GOLD)
        self.screen.blit(orb_lbl, (win.x + 16, win.y + 18))
        pygame.draw.rect(self.screen, (34, 30, 26), self.close_rect)
        pygame.draw.rect(self.screen, BAD_RED, self.close_rect, 2)
        x_lbl = self.small.render("X", True, TEXT_LIGHT)
        self.screen.blit(x_lbl, x_lbl.get_rect(center=self.close_rect.center))

        mouse = pygame.mouse.get_pos()
        hover_text = None
        if self.mode == "shop":
            for i, row in self.item_cells:
                item = SHOP_STOCK[i]
                border = RARITY_BORDER.get(item[2], (140, 142, 148))
                hovered = row.collidepoint(mouse)
                if hovered:
                    border = GOLD
                pygame.draw.rect(self.screen, (34, 30, 26), row)
                pygame.draw.rect(self.screen, border, row, 2)
                icon = row.inflate(-30, -30)
                icon.midleft = (row.x + 8, row.centery)
                draw_item_icon(self.screen, item, icon)
                name = self.small.render(item[0], True, TEXT_LIGHT)
                self.screen.blit(name, (row.x + 56, row.y + 12))
                kind = self.small.render("WEAPON" if item[3] else "CONSUMABLE", True, TEXT_DIM)
                self.screen.blit(kind, (row.x + 56, row.y + 36))
                price = self.small.render("{} GOLD".format(BUY_PRICE[item[2]]), True, GOLD)
                self.screen.blit(price, price.get_rect(midright=(row.right - 14, row.centery)))
                if hovered:
                    hover_text = "{} - {} value".format(item[0], BUY_PRICE[item[2]])
        elif self.mode == "sell":
            for idx, cell in self.item_cells:
                item = self.ui.backpack[idx]
                self._draw_cell(cell, item)
                if item is not None and cell.collidepoint(mouse):
                    hover_text = "{} - trades for {} value".format(item[0], SELL_PRICE.get(item[2], 5))
        elif self.mode == "forge":
            for where, idx, cell in self.item_cells:
                item = self.ui.backpack[idx]
                self._draw_cell(cell, item, selected=(self.selected == idx))
                if item is not None and cell.collidepoint(mouse):
                    hover_text = "{} ({}) - select to forge".format(item[0], item[2].upper())
            grid_top = self.item_cells[0][2].top
            b_lbl = self.small.render("BACKPACK - CLICK TO SELECT", True, GOLD)
            self.screen.blit(b_lbl, b_lbl.get_rect(midbottom=(self.item_cells[0][2].centerx, grid_top - 8)))
            for action, rect in self.recipe_rects:
                hovered = rect.collidepoint(mouse)
                pygame.draw.rect(self.screen, (34, 30, 26), rect)
                pygame.draw.rect(self.screen, GOLD if hovered else (110, 92, 58), rect, 2)
                sel_item = self.ui.backpack[self.selected] if self.selected is not None else None
                if action == "upgrade":
                    line1 = "UPGRADE RARITY"
                    rarity = sel_item[2] if sel_item is not None else "common"
                    cost = UPGRADE_COST.get(rarity)
                    line2 = fmt_cost(cost) if cost else "MAX TIER REACHED"
                else:
                    line1 = "REROLL ITEM"
                    line2 = fmt_cost(REROLL_COST)
                l1 = self.small.render(line1, True, TEXT_LIGHT)
                l2 = self.mini.render(line2, True, GOLD)
                self.screen.blit(l1, (rect.x + 12, rect.y + 10))
                self.screen.blit(l2, (rect.x + 12, rect.y + 34))
            if sel_item is not None:
                info = self.mini.render(
                    "SELECTED: {} ({})".format(sel_item[0], sel_item[2].upper()), True, TEXT_LIGHT
                )
            else:
                info = self.mini.render("NOTHING SELECTED", True, TEXT_DIM)
            self.screen.blit(info, (self.window.x + 380, self.window.y + 86))
            r_lbl = self.small.render("FORGE RECIPES", True, GOLD)
            self.screen.blit(r_lbl, (self.window.x + 380, self.window.y + 64))
        else:  # vault
            for where, idx, cell in self.item_cells:
                item = self.vault[idx] if where == "vault" else self.ui.backpack[idx]
                self._draw_cell(cell, item)
                if item is not None and cell.collidepoint(mouse):
                    hover_text = "{} - click to {}".format(item[0], "withdraw" if where == "vault" else "deposit")
            v_cells = [c for w_, _i, c in self.item_cells if w_ == "vault"]
            v_lbl = self.small.render("VAULT", True, GOLD)
            self.screen.blit(v_lbl, v_lbl.get_rect(midbottom=(v_cells[0].centerx, v_cells[0].top - 8)))
            b_cells = [c for w_, _i, c in self.item_cells if w_ == "backpack"]
            b_lbl = self.small.render("BACKPACK", True, GOLD)
            self.screen.blit(b_lbl, b_lbl.get_rect(midbottom=(b_cells[0].centerx, b_cells[0].top - 8)))

        status = hover_text or self.message or self.hint
        color = self.message_color if (self.message and not hover_text) else TEXT_DIM
        st = self.mini.render(status, True, color)
        self.screen.blit(st, st.get_rect(midbottom=(win.centerx, win.bottom - 10)))





