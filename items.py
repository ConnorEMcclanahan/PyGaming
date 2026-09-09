"""Sci-fi item definitions + procedural icon rendering."""
import pygame

def get_item_kind(item):
    if item is None:
        return None
    name = str(item[0]).upper()
    slot = item[3] if len(item) > 3 else None
    if "CLOAK" in name:
        return "cloak"
    if slot == "weapon":
        if any(k in name for k in ("BLASTER", "PISTOL", "RIFLE", "CANNON", "RAY")):
            return "gun"
        return "energy_sword"
    if slot == "helmet":
        return "sci_helm"
    if slot == "armor":
        return "sci_armor"
    if slot == "ability":
        return "data_chip"
    if "MANA" in name or "CELL" in name or "ENERGY" in name:
        return "energy_cell"
    if "HEALTH" in name or "REPAIR" in name or "MED" in name:
        return "repair_cell"
    if "RING" in name or "COIL" in name:
        return "plasma_ring"
    return "cache"

def draw_item_icon(surface, item, rect):
    if item is None:
        return
    color = item[1] if len(item) > 1 else (200, 200, 200)
    kind = get_item_kind(item)
    cx, cy = rect.centerx, rect.centery
    s = min(rect.width, rect.height) / 32.0
    if kind == "energy_sword":
        _draw_energy_sword(surface, cx, cy, s, color)
    elif kind == "gun":
        _draw_blaster(surface, cx, cy, s, color)
    elif kind == "sci_helm":
        _draw_sci_helm(surface, cx, cy, s, color)
    elif kind == "sci_armor":
        _draw_sci_armor(surface, cx, cy, s, color)
    elif kind == "data_chip":
        _draw_data_chip(surface, cx, cy, s, color)
    elif kind == "energy_cell":
        _draw_energy_cell(surface, cx, cy, s, color, False)
    elif kind == "repair_cell":
        _draw_energy_cell(surface, cx, cy, s, color, True)
    elif kind == "plasma_ring":
        _draw_plasma_ring(surface, cx, cy, s, color)
    elif kind == "cloak":
        _draw_cloak(surface, cx, cy, s, color)
    else:
        _draw_cache(surface, cx, cy, s, color)

def item_slot(item):
    """Equipment slot this item belongs in, or None for consumables."""
    if item is None or len(item) < 4:
        return None
    return item[3]

def is_consumable(item):
    return item is not None and item_slot(item) is None

def can_equip_in(equip_slot_name, item):
    """Strict rule: helmet->helmet, armor->armor, etc. Rings share L/R."""
    if item is None:
        return True  # always allowed to unequip / move empty
    slot = item_slot(item)
    if equip_slot_name in ("ring_l", "ring_r"):
        return slot == "ring"
    return slot == equip_slot_name

def can_place_in_belt(item):
    return item is None or is_consumable(item)

def get_weapon_profile(item):
    """Per-weapon combat profile: cooldown frames, damage, speed, color, shape."""
    name = str(item[0]).upper() if item is not None else ""
    rarity = item[2] if item is not None and len(item) > 2 else "common"
    mult = {"common": 1.0, "uncommon": 1.25, "rare": 1.6, "epic": 2.1}.get(rarity, 1.0)
    base = (sum(ord(c) for c in name) % 5) + 2
    damage = round((10 + base * 3) * mult)
    # Named weapons each get a distinct feel + look.
    if "NOVA SABER" in name:
        return {"cooldown": 14, "damage": round(26 * mult), "speed": 13, "color": (255, 170, 60), "shape": "comet", "shots": 1, "spread": 0.0}
    if "PLASMA SABER" in name:
        return {"cooldown": 22, "damage": round(18 * mult), "speed": 11, "color": (90, 220, 255), "shape": "bolt", "shots": 1, "spread": 0.0}
    if "PULSE BLADE" in name:
        return {"cooldown": 30, "damage": round(14 * mult), "speed": 10, "color": (180, 200, 255), "shape": "arc", "shots": 1, "spread": 0.0}
    if "PLASMA RIFLE" in name or "BLASTER" in name or "RAY" in name or "CANNON" in name:
        return {"cooldown": 10, "damage": round(9 * mult), "speed": 15, "color": (150, 255, 170), "shape": "pellet", "shots": 1, "spread": 0.0}
    if "SCATTER" in name or "SPLIT" in name:
        return {"cooldown": 34, "damage": round(8 * mult), "speed": 10, "color": (220, 150, 255), "shape": "shard", "shots": 3, "spread": 0.16}
    # Fallback: generic blade tuned by name hash.
    return {"cooldown": 24, "damage": damage, "speed": 11, "color": item[1] if item else (200, 200, 210), "shape": "bolt", "shots": 1, "spread": 0.0}

def get_ability_profile(item):
    """Each ability item is a different spell. Returns cooldown/mana/effect."""
    name = str(item[0]).upper() if item is not None else ""
    if "NOVA" in name or "BURST" in name:
        return {"key": "nova", "name": "Nova Burst", "cooldown": 420, "mana": 30, "desc": "Radial plasma nova (8 bolts)"}
    if "BLINK" in name or "DASH" in name or "PHASE" in name:
        return {"key": "blink", "name": "Phase Blink", "cooldown": 300, "mana": 25, "desc": "Dash toward cursor + brief shield"}
    if "DRONE" in name or "TURRET" in name or "SENTRY" in name:
        return {"key": "drone", "name": "Sentry Drone", "cooldown": 540, "mana": 35, "desc": "Drone fires 6 bolts at aim"}
    if "OVERDRIVE" in name or "RAGE" in name or "SURGE" in name:
        return {"key": "overdrive", "name": "Overdrive", "cooldown": 600, "mana": 20, "desc": "2x fire rate for 5s"}
    if "REPAIR" in name or "HEAL" in name:
        return {"key": "repair", "name": "Aegis Repair", "cooldown": 480, "mana": 30, "desc": "Restore 50 HP + shield"}
    if "HOLO" in name or "SHIELD" in name or "BUBBLE" in name or "AEGIS" in name:
        return {"key": "shield", "name": "Bubble Shield", "cooldown": 480, "mana": 20, "desc": "Bubble blocks damage for 5s"}
    # default starter ability = bubble shield
    return {"key": "shield", "name": "Bubble Shield", "cooldown": 480, "mana": 20, "desc": "Bubble blocks damage for 5s"}

def get_item_stats(item):
    """Deterministic tooltip stats for any item tuple."""
    if item is None:
        return []
    name = str(item[0]).upper()
    rarity = item[2] if len(item) > 2 else "common"
    slot = item_slot(item)
    mult = {"common": 1.0, "uncommon": 1.25, "rare": 1.6, "epic": 2.1}.get(rarity, 1.0)
    base = (sum(ord(c) for c in name) % 7) + 3  # stable per-name variety
    if slot == "weapon":
        prof = get_weapon_profile(item)
        rate = round(60 / max(1, prof["cooldown"]), 1)
        if prof["shape"] in ("pellet",):
            return [f"Damage: {prof['damage']}", f"Shots: {prof['shots']}", f"Fire rate: {rate}/s", "Energy projectile"]
        if prof["shots"] > 1:
            return [f"Damage: {prof['damage']} x{prof['shots']}", f"Fire rate: {rate}/s", "Split fire", "Plasma edge"]
        return [f"Damage: {prof['damage']}", f"Fire rate: {rate}/s", "Plasma edge"]
    if slot == "helmet":
        return [f"Defense: {round((2 + base) * mult)}", f"Vitality: +{round(base * mult)}", "Head systems"]
    if slot == "armor":
        return [f"Defense: {round((4 + base * 1.5) * mult)}", f"Shield: +{round(base * 2 * mult)}", "Body plating"]
    if slot == "ability":
        prof = get_ability_profile(item)
        secs = round(prof["cooldown"] / 60, 1)
        return [prof["name"], f"Cooldown: {secs}s", f"Mana: {prof['mana']}", prof["desc"]]
    if slot == "ring":
        return [f"Power: +{round(base * mult)}", f"Focus: +{round(base * mult)}", "Attunement ring"]
    # consumables
    uname = name.upper()
    if "REPAIR" in uname or "HEALTH" in uname or "MED" in uname:
        return ["Use: restores 40 HP", "Drag to belt, press 1-4", "Consumable"]
    if "ENERGY" in uname or "MANA" in uname or "CELL" in uname:
        return ["Use: restores 40 energy", "Drag to belt, press 1-4", "Consumable"]
    return ["Strange tech", "Consumable"]

def get_item_blurb(item):
    if item is None:
        return ""
    kind = get_item_kind(item)
    blurbs = {
        "energy_sword": "Superheated plasma edge.",
        "gun": "Compact pulse projector.",
        "sci_helm": "Sealed recon helm.",
        "sci_armor": "Ion-weave plating.",
        "data_chip": "Encrypted tech lore.",
        "energy_cell": "Spare ship energy.",
        "repair_cell": "Field repair nano-gel.",
        "plasma_ring": "Stabilized plasma loop.",
        "cloak": "Light-bending weave.",
        "cache": "Salvaged parts.",
    }
    return blurbs.get(kind, "")

def _glow(surface, x0, y0, x1, y1, s, color):
    pygame.draw.line(surface, (18, 20, 26), (x0, y0), (x1, y1), max(2, int(7 * s)))
    pygame.draw.line(surface, color, (x0, y0), (x1, y1), max(1, int(4 * s)))
    pygame.draw.line(surface, (255, 255, 255), (x0, y0), (x1, y1), max(1, int(1.5 * s)))

def _draw_energy_sword(surface, cx, cy, s, color):
    x0, y0 = cx - 10 * s, cy + 10 * s
    x1, y1 = cx + 11 * s, cy - 11 * s
    _glow(surface, x0, y0, x1, y1, s, color)
    gx, gy = x0 + 2 * s, y0 - 2 * s
    pygame.draw.line(surface, (40, 44, 55), (gx - 4 * s, gy + 4 * s), (gx + 4 * s, gy - 4 * s), max(2, int(3 * s)))
    pygame.draw.line(surface, (30, 32, 40), (x0, y0), (x0 - 5 * s, y0 + 5 * s), max(2, int(5 * s)))
    pygame.draw.circle(surface, (255, 220, 90), (x0 - 5 * s, y0 + 5 * s), max(2, int(2.2 * s)))

def _draw_blaster(surface, cx, cy, s, color):
    pygame.draw.rect(surface, (28, 32, 40), (cx - 11 * s, cy - 2 * s, 20 * s, 7 * s))
    pygame.draw.rect(surface, color, (cx - 11 * s, cy - 2 * s, 20 * s, 3 * s))
    pygame.draw.rect(surface, (15, 17, 22), (cx - 4 * s, cy + 4 * s, 6 * s, 6 * s))
    pygame.draw.rect(surface, (255, 240, 160), (cx + 7 * s, cy - 1 * s, 4 * s, 2 * s))
    pygame.draw.circle(surface, (90, 220, 255), (cx - 8 * s, cy + 1 * s), max(1, int(1.8 * s)))

def _draw_sci_helm(surface, cx, cy, s, color):
    pygame.draw.ellipse(surface, (22, 26, 34), (cx - 10 * s, cy - 9 * s, 20 * s, 18 * s))
    pygame.draw.ellipse(surface, color, (cx - 8 * s, cy - 8 * s, 16 * s, 15 * s))
    hi = tuple(min(255, c + 40) for c in color)
    pygame.draw.ellipse(surface, hi, (cx - 6 * s, cy - 7 * s, 8 * s, 6 * s))
    pygame.draw.rect(surface, (12, 18, 26), (cx - 7 * s, cy - 1 * s, 14 * s, 4 * s))
    pygame.draw.rect(surface, (120, 230, 255), (cx - 7 * s, cy - 1 * s, 14 * s, 1.6 * s))
    pygame.draw.line(surface, color, (cx + 8 * s, cy - 8 * s), (cx + 11 * s, cy - 13 * s), 2)
    pygame.draw.circle(surface, (255, 100, 100), (cx + 11 * s, cy - 13 * s), max(1, int(1.8 * s)))

def _draw_sci_armor(surface, cx, cy, s, color):
    pygame.draw.rect(surface, (20, 24, 32), (cx - 9 * s, cy - 8 * s, 18 * s, 18 * s))
    pygame.draw.rect(surface, color, (cx - 7 * s, cy - 7 * s, 14 * s, 16 * s))
    pygame.draw.rect(surface, (22, 26, 34), (cx - 3 * s, cy - 7 * s, 6 * s, 16 * s))
    hi = tuple(min(255, c + 30) for c in color)
    pygame.draw.polygon(surface, hi, [(cx - 7 * s, cy - 7 * s), (cx + 7 * s, cy - 7 * s), (cx, cy - 2 * s)])
    pygame.draw.circle(surface, (120, 235, 255), (cx, cy + 3 * s), max(2, int(3.2 * s)))
    pygame.draw.circle(surface, (230, 250, 255), (cx, cy + 3 * s), max(1, int(1.4 * s)))

def _draw_data_chip(surface, cx, cy, s, color):
    pygame.draw.rect(surface, (16, 20, 28), (cx - 8 * s, cy - 10 * s, 16 * s, 20 * s))
    pygame.draw.rect(surface, color, (cx - 8 * s, cy - 10 * s, 16 * s, 20 * s), max(1, int(2 * s)))
    pygame.draw.rect(surface, (30, 38, 52), (cx - 5 * s, cy - 7 * s, 10 * s, 14 * s))
    for i in range(3):
        y = cy - 4 * s + i * 4 * s
        pygame.draw.line(surface, color, (cx - 4 * s, y), (cx + 4 * s, y), 1)
    pygame.draw.circle(surface, (140, 240, 255), (cx, cy + 9 * s), max(1, int(1.8 * s)))

def _draw_energy_cell(surface, cx, cy, s, color, is_repair):
    pygame.draw.rect(surface, (200, 230, 240), (cx - 5 * s, cy - 10 * s, 10 * s, 20 * s))
    pygame.draw.rect(surface, (30, 40, 55), (cx - 4 * s, cy - 9 * s, 8 * s, 18 * s))
    pygame.draw.rect(surface, color, (cx - 4 * s, cy - 2 * s, 8 * s, 11 * s))
    pygame.draw.rect(surface, (255, 255, 255), (cx - 3 * s, cy - 8 * s, 2 * s, 6 * s))
    pygame.draw.rect(surface, (60, 66, 80), (cx - 6 * s, cy - 12 * s, 12 * s, 3 * s))
    if is_repair:
        pygame.draw.rect(surface, (255, 255, 255), (cx - 1.2 * s, cy + 1 * s, 2.4 * s, 6 * s))
        pygame.draw.rect(surface, (255, 255, 255), (cx - 2.5 * s, cy + 2.6 * s, 5 * s, 2.4 * s))

def _draw_plasma_ring(surface, cx, cy, s, color):
    pygame.draw.circle(surface, color, (cx, cy), max(2, int(9 * s)), max(1, int(4 * s)))
    pygame.draw.circle(surface, (255, 255, 255), (cx, cy), max(2, int(9 * s)), 1)
    pygame.draw.circle(surface, (140, 235, 255), (cx + 5 * s, cy - 5 * s), max(1, int(2 * s)))

def _draw_cloak(surface, cx, cy, s, color):
    pygame.draw.polygon(surface, color, [(cx, cy - 10 * s), (cx - 8 * s, cy + 9 * s), (cx + 8 * s, cy + 9 * s)])
    pygame.draw.polygon(surface, (20, 22, 30), [(cx, cy - 10 * s), (cx - 8 * s, cy + 9 * s), (cx + 8 * s, cy + 9 * s)], 2)
    pygame.draw.circle(surface, (140, 235, 255), (cx, cy - 6 * s), max(1, int(2 * s)))

def _draw_cache(surface, cx, cy, s, color):
    pygame.draw.rect(surface, (22, 26, 34), (cx - 8 * s, cy - 6 * s, 16 * s, 12 * s))
    pygame.draw.rect(surface, color, (cx - 8 * s, cy - 6 * s, 16 * s, 12 * s), 2)
    pygame.draw.line(surface, color, (cx - 8 * s, cy), (cx + 8 * s, cy), 1)
