import pygame

from items import can_equip_in, can_place_in_belt, draw_item_icon, get_item_blurb, get_item_stats, is_consumable

RARITY_COLORS = {
    "common": (205, 205, 210),
    "uncommon": (130, 195, 255),
    "rare": (255, 212, 110),
    "epic": (205, 125, 255),
}
RARITY_TEXT = {
    "common": "COMMON",
    "uncommon": "UNCOMMON",
    "rare": "RARE",
    "epic": "EPIC",
}
SLOT_LABEL = {
    "helmet": "Helmet",
    "armor": "Armor",
    "weapon": "Weapon",
    "ability": "Ability",
    "ring": "Ring",
    None: "Consumable",
}
PANEL_BG = (20, 17, 14)
PANEL_EDGE = (110, 92, 58)
SLOT_BG = (34, 30, 26)
SLOT_BORDER = (74, 62, 44)
GOLD = (230, 190, 90)
GOLD_DIM = (150, 124, 78)
TEXT_LIGHT = (235, 232, 218)
TEXT_DIM = (180, 174, 162)
BAD_RED = (225, 90, 90)
RARITY_BORDER = {
    "common": (140, 142, 148),
    "uncommon": (84, 152, 200),
    "rare": (216, 176, 72),
    "epic": (176, 88, 216),
}
SLOT_TITLES = {
    "helmet": "HELMET",
    "armor": "ARMOR",
    "weapon": "WEAPON",
    "ability": "ABILITY",
    "ring_l": "RING (L)",
    "ring_r": "RING (R)",
}
EQUIP_ORDER = ["helmet", "armor", "weapon", "ability", "ring_l", "ring_r"]


class UI:
    def __init__(self, screen, settings):
        self.screen = screen
        self.settings = settings
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 19)
        self.mini_font = pygame.font.Font(None, 15)
        self.title_font = pygame.font.Font(None, 34)
        self.tip_font = pygame.font.Font(None, 17)
        self.active_tab = "Inventory"
        self.drag = None
        self.drag_pos = None
        self.hover_pos = pygame.mouse.get_pos()
        self.flash_slot = None
        self.flash_timer = 0
        self._build_layout()

    # ------------------------------------------------------------------ layout
    # Right-anchored inventory panel (ROTMG style): a vertical list of
    # equipment slots with the backpack grid underneath.
    def _build_layout(self):
        w, h = self.screen.get_size()
        self.panel = pygame.Rect(w - 330, 40, 330, h - 76)
        cx = self.panel.centerx
        top = self.panel.y

        self.tab_inv = pygame.Rect(cx - 143, top + 8, 140, 28)
        self.tab_char = pygame.Rect(cx + 3, top + 8, 140, 28)

        # Minimap sits at the top of the panel (where the armor section was).
        self.minimap_rect = pygame.Rect(self.panel.x + 8, self.tab_inv.bottom + 8, self.panel.w - 16, 118)

        # Equipment slots are listed BELOW the minimap (armor, helmet, etc).
        size, gap = 40, 10
        slot_x = self.panel.right - size - 16
        y = self.minimap_rect.bottom + 12
        self.equip_slots = {}
        for name in EQUIP_ORDER:
            self.equip_slots[name] = pygame.Rect(slot_x, y, size, size)
            y += size + gap
        self.equipment = {name: None for name in self.equip_slots}

        cols, rows = 4, 3
        bsize, bgap = 42, 8
        grid_w = cols * bsize + (cols - 1) * bgap
        start_x = cx - grid_w // 2
        start_y = y + 20
        self.backpack_rects = []
        for row in range(rows):
            for col in range(cols):
                self.backpack_rects.append(
                    pygame.Rect(start_x + col * (bsize + bgap), start_y + row * (bsize + bgap), bsize, bsize)
                )
        self.backpack = [None] * (cols * rows)
        self.backpack[0] = ("NANO HELM", (150, 170, 200), "common", "helmet")
        self.backpack[1] = ("ION MAIL", (100, 160, 220), "uncommon", "armor")
        self.backpack[4] = ("ENERGY CELL", (78, 200, 255), "uncommon", None)

        self.char_rect = pygame.Rect(cx - 32, self.minimap_rect.bottom + 20, 64, 100)
        self.backpack_label_y = self.backpack_rects[0].y - 18

        bw, bh, bgap2 = 44, 44, 8
        bx = 18
        by = h - 32 - 22 - bh - 10
        self.belt_rects = [pygame.Rect(bx + i * (bw + bgap2), by, bw, bh) for i in range(4)]
        self.belt = [None] * 4
        self.belt[0] = ("REPAIR CELL", (220, 70, 70), "common", None)
        self.belt[1] = ("ENERGY CELL", (78, 200, 255), "uncommon", None)

    # ------------------------------------------------------------------ input
    def handle_click(self, position):
        if not self.panel.collidepoint(position):
            return
        if self.tab_inv.collidepoint(position):
            self.active_tab = "Inventory"
            return
        if self.tab_char.collidepoint(position):
            self.active_tab = "Stats"
            return
        if self.active_tab != "Inventory":
            return
        found = self._item_at(position)
        if found is None:
            return
        source, index, item = found
        self.drag = (source, index, item)
        self.drag_pos = position
        if source == "backpack":
            self.backpack[index] = None
        else:
            self.equipment[source] = None

    def handle_world_click(self, position):
        """Start a drag from the POE-style belt (outside the panel)."""
        for i, rect in enumerate(self.belt_rects):
            if rect.collidepoint(position) and self.belt[i] is not None:
                self.drag = ("belt", i, self.belt[i])
                self.drag_pos = position
                self.belt[i] = None
                return True
        return False

    def handle_drag(self, position):
        if self.drag is not None:
            self.drag_pos = position
        self.hover_pos = position

    def handle_hover(self, position):
        self.hover_pos = position

    def handle_release(self, position):
        if self.drag is None:
            return
        source, index, item = self.drag
        target = self._drop_target(position)
        if target is None:
            self._return_to_source(source, index, item)
            self.drag = None
            self.drag_pos = None
            return
        target_type, target_index = target
        if target_type == "equip" and source == target_index:
            self.equipment[source] = item
            self.drag = None
            self.drag_pos = None
            return
        if target_type == "backpack" and source == "backpack" and target_index == index:
            self.backpack[index] = item
            self.drag = None
            self.drag_pos = None
            return
        if target_type == "belt" and source == "belt" and target_index == index:
            self.belt[index] = item
            self.drag = None
            self.drag_pos = None
            return
        # ---- strict rules ----
        if target_type == "equip":
            if not can_equip_in(target_index, item):
                self._reject("equip", target_index)
                self._return_to_source(source, index, item)
                self.drag = None
                self.drag_pos = None
                return
            displaced = self.equipment[target_index]
            self.equipment[target_index] = item
            self._place_displaced(source, index, displaced)
        elif target_type == "belt":
            if not can_place_in_belt(item):
                self._reject("belt", target_index)
                self._return_to_source(source, index, item)
                self.drag = None
                self.drag_pos = None
                return
            displaced = self.belt[target_index]
            self.belt[target_index] = item
            self._place_displaced(source, index, displaced)
        else:
            displaced = self.backpack[target_index]
            self.backpack[target_index] = item
            self._place_displaced(source, index, displaced)
        self.drag = None
        self.drag_pos = None

    def _return_to_source(self, source, index, item):
        if source == "backpack":
            self.backpack[index] = item
        elif source == "belt":
            self.belt[index] = item
        else:
            self.equipment[source] = item

    def _place_displaced(self, source, index, displaced):
        if displaced is None:
            return
        if source == "backpack":
            self.backpack[index] = displaced
        elif source == "belt":
            self.belt[index] = displaced
        else:
            self.equipment[source] = displaced

    def _reject(self, kind, key):
        self.flash_slot = (kind, key)
        self.flash_timer = 30

    def _item_at(self, position):
        for name, rect in self.equip_slots.items():
            if rect.collidepoint(position) and self.equipment[name] is not None:
                return (name, 0, self.equipment[name])
        for index, rect in enumerate(self.backpack_rects):
            if rect.collidepoint(position) and self.backpack[index] is not None:
                return ("backpack", index, self.backpack[index])
        return None

    def _drop_target(self, position):
        for name, rect in self.equip_slots.items():
            if rect.collidepoint(position):
                return ("equip", name)
        for index, rect in enumerate(self.backpack_rects):
            if rect.collidepoint(position):
                return ("backpack", index)
        for index, rect in enumerate(self.belt_rects):
            if rect.collidepoint(position):
                return ("belt", index)
        return None

    def item_at(self, position):
        """Item under the mouse (panel slots, belt, drag ghost)."""
        if self.drag is not None and self.drag_pos is not None:
            ghost = pygame.Rect(self.drag_pos[0] - 14, self.drag_pos[1] - 14, 28, 28)
            if ghost.collidepoint(position):
                return self.drag[2]
        if self.panel.collidepoint(position):
            for name, rect in self.equip_slots.items():
                if rect.collidepoint(position) and self.equipment[name] is not None:
                    return self.equipment[name]
            for index, rect in enumerate(self.backpack_rects):
                if rect.collidepoint(position) and self.backpack[index] is not None:
                    return self.backpack[index]
        for i, rect in enumerate(self.belt_rects):
            if rect.collidepoint(position) and self.belt[i] is not None:
                return self.belt[i]
        return None

    def add_item(self, item):
        if self._first_free_backpack(item):
            return True
        if is_consumable(item):
            for i, slot in enumerate(self.belt):
                if slot is None:
                    self.belt[i] = item
                    return True
        return False

    def _first_free_backpack(self, item):
        for i, slot in enumerate(self.backpack):
            if slot is None:
                self.backpack[i] = item
                return True
        return False

    def use_belt_slot(self, index, player=None):
        if 0 <= index < len(self.belt) and self.belt[index] is not None:
            item = self.belt[index]
            name = str(item[0]).upper()
            if player is not None:
                if "REPAIR" in name or "HEALTH" in name or "MED" in name:
                    player.health = min(player.max_health, player.health + 40)
                elif "ENERGY" in name or "MANA" in name or "CELL" in name:
                    player.mana = min(100, player.mana + 40)
                else:
                    player.health = min(player.max_health, player.health + 15)
            self.belt[index] = None
            return True
        return False

    def handle_key(self, event, player=None):
        if event.key == pygame.K_1:
            return self.use_belt_slot(0, player)
        if event.key == pygame.K_2:
            return self.use_belt_slot(1, player)
        if event.key == pygame.K_3:
            return self.use_belt_slot(2, player)
        if event.key == pygame.K_4:
            return self.use_belt_slot(3, player)
        return False

    # ------------------------------------------------------------------ hud
    def draw_hud(self, player, auto_shoot=True, show_auto_shoot=True, show_gold=False):
        w, h = self.screen.get_size()
        self._hud_bar(player.mana, 100, (67, 133, 216), (18, h - 54))
        self._hud_bar(player.health, player.max_health, (205, 68, 68), (18, h - 32))
        y = 158
        if show_gold:
            gold = getattr(player, "gold", 0)
            gold_surf = self.mini_font.render("GOLD: {}".format(gold), True, GOLD)
            self.screen.blit(gold_surf, (18, y))
            y += 20
        if show_auto_shoot:
            # Tutorial-only helper text; the real world drops the hand-holding.
            key = self.settings.keybinds.get("auto_shoot", pygame.K_x)
            key_name = pygame.key.name(key).upper()
            status = "ON" if auto_shoot else "OFF"
            auto_surf = self.mini_font.render("AUTO SHOOT: {} ({})".format(status, key_name), True, (215, 210, 195))
            self.screen.blit(auto_surf, (18, y))
        self._draw_belt()
        self._draw_ability(player)

    def _draw_belt(self):
        for i, rect in enumerate(self.belt_rects):
            pygame.draw.rect(self.screen, SLOT_BG, rect)
            item = self.belt[i]
            if item is not None:
                draw_item_icon(self.screen, item, rect.inflate(-10, -10))
                border = RARITY_BORDER.get(item[2], (140, 142, 148))
            else:
                border = SLOT_BORDER
            if self.flash_slot == ("belt", i) and self.flash_timer > 0:
                border = BAD_RED
            pygame.draw.rect(self.screen, border, rect, 2)
            key_lbl = self.mini_font.render(str(i + 1), True, TEXT_DIM)
            self.screen.blit(key_lbl, (rect.x + 3, rect.y + 1))

    def _draw_ability(self, player):
        from items import get_ability_profile
        ability = self.equipment.get("ability")
        if ability is not None and (len(ability) < 4 or ability[3] != "ability"):
            ability = None
        if ability is None:
            w, h = self.screen.get_size()
            box = pygame.Rect(18, h - 32 - 22 - 44 - 56, 44, 44)
            pygame.draw.rect(self.screen, SLOT_BG, box)
            pygame.draw.rect(self.screen, SLOT_BORDER, box, 2)
            key_lbl = self.mini_font.render("SPACE", True, TEXT_DIM)
            self.screen.blit(key_lbl, (box.x + 3, box.y + 1))
            nm = self.mini_font.render("No ability", True, TEXT_DIM)
            self.screen.blit(nm, (box.right + 8, box.y + 4))
            st = self.mini_font.render("equip one", True, TEXT_DIM)
            self.screen.blit(st, (box.right + 8, box.y + 22))
            return
        try:
            prof = get_ability_profile(ability)
            mana_cost = int(prof.get("mana", 20))
            cd_total = max(1, int(prof.get("cooldown", 360)))
            ab_name = str(prof.get("name", ability[0]))
        except Exception:
            mana_cost, cd_total, ab_name = 20, 360, str(ability[0])
        w, h = self.screen.get_size()
        box = pygame.Rect(18, h - 32 - 22 - 44 - 56, 44, 44)
        pygame.draw.rect(self.screen, SLOT_BG, box)
        draw_item_icon(self.screen, ability, box.inflate(-10, -10))
        cd = getattr(player, "ability_cd", 0)
        total = cd_total
        if cd > 0:
            frac = min(1.0, cd / total)
            dark_h = int(box.height * frac)
            dark = pygame.Surface((box.width, dark_h), pygame.SRCALPHA)
            dark.fill((10, 10, 14, 170))
            self.screen.blit(dark, (box.x, box.y))
            secs = self.mini_font.render(f"{cd / 60:.1f}", True, (255, 255, 255))
            self.screen.blit(secs, secs.get_rect(center=box.center))
        border = RARITY_BORDER.get(ability[2], SLOT_BORDER)
        pygame.draw.rect(self.screen, border, box, 2)
        key = self.settings.keybinds.get("ability", pygame.K_SPACE)
        key_lbl = self.mini_font.render("SPACE", True, TEXT_DIM)
        self.screen.blit(key_lbl, (box.x + 3, box.y + 1))
        nm = self.mini_font.render(ab_name, True, TEXT_LIGHT)
        self.screen.blit(nm, (box.right + 8, box.y + 4))
        st = self.mini_font.render(f"{mana_cost} mana", True, (130, 170, 230) if player.mana >= mana_cost else BAD_RED)
        self.screen.blit(st, (box.right + 8, box.y + 22))

    def _draw_minimap_panel(self, player=None, camera=None, enemies=(), drops=(), landmarks=(), world_size=None):
        """Minimap drawn INSIDE the right-side inventory panel (same on every
        level so the UI matches everywhere)."""
        rect = self.minimap_rect
        pygame.draw.rect(self.screen, (13, 14, 13), rect)
        pygame.draw.rect(self.screen, (120, 100, 62), rect, 2)
        ws, hs = world_size if world_size is not None else (self.settings.world_width, self.settings.world_height)

        def to_mini(x, y):
            return (rect.x + x / ws * rect.width, rect.y + y / hs * rect.height)

        for wrect, color in landmarks:
            if wrect is None:
                continue
            display = pygame.Rect(
                rect.x + wrect.x / ws * rect.width,
                rect.y + wrect.y / hs * rect.height,
                wrect.w / ws * rect.width,
                wrect.h / hs * rect.height,
            )
            display = display.clip(rect)
            if display.width > 0 and display.height > 0:
                pygame.draw.rect(self.screen, color, display)
        for enemy in enemies:
            if enemy is None or not getattr(enemy, "alive", True):
                continue
            px, py = to_mini(enemy.rect.centerx, enemy.rect.centery)
            pygame.draw.circle(self.screen, (214, 60, 62), (round(px), round(py)), 3)
        for drop in drops:
            px, py = to_mini(drop["pos"].x, drop["pos"].y)
            pygame.draw.circle(self.screen, (230, 190, 90), (round(px), round(py)), 2)
        if player is not None:
            px, py = to_mini(player.rect.centerx, player.rect.centery)
            pygame.draw.circle(self.screen, (110, 220, 110), (round(px), round(py)), 4)
        if camera is not None:
            vw = self.settings.screen_width - self.panel.width
            vh = self.settings.screen_height
            view = pygame.Rect(
                rect.x + camera.x / ws * rect.width,
                rect.y + camera.y / hs * rect.height,
                vw / ws * rect.width,
                vh / hs * rect.height,
            )
            view = view.clip(rect)
            pygame.draw.rect(self.screen, (255, 255, 255), view, 1)

    def _hud_bar(self, value, maximum, color, topleft):
        bar = pygame.Rect(topleft, (210, 16))
        pygame.draw.rect(self.screen, (28, 26, 24), bar)
        fill = round(bar.width * max(0, value) / max(1, maximum))
        pygame.draw.rect(self.screen, color, (bar.x, bar.y, fill, bar.height))
        pygame.draw.rect(self.screen, (90, 76, 54), bar, 1)
        label = self.mini_font.render("{}/{}".format(int(value), int(maximum)), True, TEXT_LIGHT)
        self.screen.blit(label, (bar.x + bar.width + 8, bar.y + 2))

    # ------------------------------------------------------------------ draw
    def draw_inventory(self, player=None, camera=None, enemies=(), drops=(), landmarks=(), world_size=None):
        if self.flash_timer > 0:
            self.flash_timer -= 1
        pygame.draw.rect(self.screen, PANEL_BG, self.panel)
        pygame.draw.rect(self.screen, PANEL_EDGE, self.panel, 4)
        pygame.draw.rect(self.screen, GOLD_DIM, self.panel.inflate(-16, -16), 2)
        self._draw_minimap_panel(player, camera, enemies, drops, landmarks, world_size)
        self._draw_tab(self.tab_inv, "GEAR", self.active_tab == "Inventory")
        self._draw_tab(self.tab_char, "STATS", self.active_tab == "Stats")
        if self.active_tab == "Inventory":
            self._draw_equipment()
            self._draw_backpack()
            self._draw_help()
        else:
            self._draw_status(player)
        if self.drag is not None and self.drag_pos is not None:
            self._draw_item(self.drag_pos, self.drag[2])
        self._draw_tooltip()

    def _draw_tab(self, rect, label, active):
        color = (120, 96, 56) if active else (70, 58, 40)
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, GOLD if active else GOLD_DIM, rect, 2)
        text = self.font.render(label, True, TEXT_LIGHT if active else TEXT_DIM)
        self.screen.blit(text, text.get_rect(center=rect.center))

    def _draw_equipment(self):
        for name in EQUIP_ORDER:
            rect = self.equip_slots[name]
            label = self.mini_font.render(SLOT_TITLES[name], True, TEXT_DIM)
            self.screen.blit(label, label.get_rect(midleft=(self.panel.x + 16, rect.centery)))
            self._draw_slot(rect, self.equipment[name], "", flash_key=("equip", name))

    def _draw_backpack(self):
        for index, rect in enumerate(self.backpack_rects):
            self._draw_slot(rect, self.backpack[index], "")

    def _draw_slot(self, rect, item, title, flash_key=None):
        pygame.draw.rect(self.screen, SLOT_BG, rect)
        if item is not None:
            draw_item_icon(self.screen, item, rect.inflate(-10, -10))
            border = RARITY_BORDER.get(item[2], (140, 142, 148))
        else:
            border = SLOT_BORDER
        if flash_key is not None and self.flash_slot == flash_key and self.flash_timer > 0:
            border = BAD_RED
        pygame.draw.rect(self.screen, border, rect, 2)

    def _draw_help(self):
        label = self.mini_font.render("Gear -> matching slot | Cells -> belt (1-4)", True, TEXT_DIM)
        self.screen.blit(label, label.get_rect(center=(self.panel.centerx, self.panel.bottom - 20)))

    def _draw_item(self, position, item, half=12):
        box = pygame.Rect(position[0] - half, position[1] - half, half * 2, half * 2)
        pygame.draw.rect(self.screen, SLOT_BG, box)
        draw_item_icon(self.screen, item, box.inflate(-6, -6))
        border = RARITY_BORDER.get(item[2], (140, 142, 148))
        pygame.draw.rect(self.screen, border, box, 2)

    def _draw_tooltip(self):
        item = self.item_at(self.hover_pos)
        if item is None:
            return
        name = str(item[0])
        rarity = item[2] if len(item) > 2 else "common"
        slot = item[3] if len(item) > 3 else None
        lines = [(name, RARITY_COLORS.get(rarity, TEXT_LIGHT), True)]
        lines.append((str(rarity).upper(), RARITY_COLORS.get(rarity, TEXT_DIM), False))
        kind_label = {None: "Consumable", "ring": "Ring"}.get(slot, str(slot).capitalize() if slot else "Consumable")
        lines.append((kind_label, TEXT_DIM, False))
        blurb = get_item_blurb(item)
        if blurb:
            lines.append((blurb, TEXT_DIM, False))
        for stat in get_item_stats(item):
            lines.append((stat, TEXT_LIGHT, False))
        if is_consumable(item):
            lines.append(("Drag to belt, press 1-4 to use", GOLD, False))
        elif slot == "ring":
            lines.append(("Only fits: RING slots", GOLD, False))
        elif slot is not None:
            lines.append(("Only fits: {} slot".format(str(slot).upper()), GOLD, False))
        width = 0
        rendered = []
        for text, color, big in lines:
            surf = (self.small_font if big else self.tip_font).render(text, True, color)
            rendered.append(surf)
            width = max(width, surf.get_width())
        width += 20
        height = sum(s.get_height() + 2 for s in rendered) + 14
        x = min(max(8, self.hover_pos[0] + 16), self.screen.get_width() - width - 8)
        y = min(max(8, self.hover_pos[1] + 12), self.screen.get_height() - height - 8)
        box = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (12, 12, 16), box)
        pygame.draw.rect(self.screen, RARITY_BORDER.get(rarity, SLOT_BORDER), box, 2)
        cy = y + 8
        for surf in rendered:
            self.screen.blit(surf, (x + 10, cy))
            cy += surf.get_height() + 2

    def _draw_character_emblem(self):
        cx, cy = self.char_rect.centerx, self.char_rect.centery
        pygame.draw.circle(self.screen, (60, 50, 34), (cx, cy), 46, 3)
        pygame.draw.circle(self.screen, GOLD_DIM, (cx, cy), 46, 1)
        pygame.draw.ellipse(self.screen, (12, 15, 17), (cx - 18, cy + 46, 36, 10))
        pygame.draw.rect(self.screen, (55, 62, 76), (cx - 13, cy - 8, 26, 42))
        pygame.draw.rect(self.screen, (177, 183, 192), (cx - 11, cy - 14, 22, 36))
        pygame.draw.rect(self.screen, (76, 84, 101), (cx - 9, cy + 14, 18, 8))
        pygame.draw.rect(self.screen, (211, 216, 215), (cx - 8, cy - 38, 16, 24))
        pygame.draw.rect(self.screen, (106, 116, 132), (cx - 11, cy - 24, 22, 8))
        pygame.draw.rect(self.screen, (34, 39, 50), (cx - 6, cy - 18, 12, 4))
        pygame.draw.line(self.screen, (226, 226, 204), (cx, cy + 4), (cx + 24, cy - 10), 5)
        pygame.draw.line(self.screen, (255, 245, 173), (cx, cy + 4), (cx + 24, cy - 10), 2)

    def _draw_status(self, player=None):
        self._draw_character_emblem()
        y = self.panel.y + 240
        cls = getattr(player, "character", "knight").capitalize() if player else "Knight"
        lvl = str(getattr(player, "level", 1)) if player else "1"
        rows = [
            ("Level", lvl),
            ("Class", cls),
            ("Attack", "12"),
            ("Defense", "8"),
            ("Dexterity", "9"),
            ("Vitality", "10"),
            ("Magic", "6"),
        ]
        for name, value in rows:
            self._stat_row(name, value, y)
            y += 28
        footer = self.mini_font.render("'A {}'s journey begins.'".format(cls.lower()), True, TEXT_DIM)
        self.screen.blit(footer, footer.get_rect(center=(self.panel.centerx, self.panel.bottom - 26)))

    def _stat_row(self, name, value, y):
        label = self.small_font.render(name, True, TEXT_LIGHT)
        self.screen.blit(label, (self.panel.x + 24, y))
        value_surf = self.small_font.render(value, True, GOLD)
        self.screen.blit(value_surf, (self.panel.x + 150, y))