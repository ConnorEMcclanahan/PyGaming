"""Sci-fi item definitions + procedural icon rendering."""
import pygame

def get_item_kind(item):
    if item is None:
        return None
    name = str(item[0]).upper()
    slot = item[3] if len(item) > 3 else None
    if slot == "currency":
        return "orb"
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
    if slot == "ring":
        return "plasma_ring"
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
    elif kind == "orb":
        _draw_orb(surface, cx, cy, s, color)
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
    mult = {"common": 1.0, "uncommon": 1.25, "rare": 1.6, "epic": 2.1, "legendary": 2.8}.get(rarity, 1.0)
    base = (sum(ord(c) for c in name) % 5) + 2
    damage = round((10 + base * 3) * mult)
    # Named weapons each get a distinct feel + look.
    if "SINGULARITY EDGE" in name:
        return {"cooldown": 20, "damage": round(34 * mult), "speed": 14, "color": (255, 224, 130), "shape": "comet", "shots": 1, "spread": 0.0}
    if "EVENT HORIZON" in name:
        return {"cooldown": 26, "damage": round(22 * mult), "speed": 13, "color": (255, 96, 96), "shape": "comet", "shots": 3, "spread": 0.14}
    if "TEMPEST RIFLE" in name:
        return {"cooldown": 9, "damage": round(10 * mult), "speed": 15, "color": (170, 200, 255), "shape": "pellet", "shots": 2, "spread": 0.08}
    if "AURORA BLADE" in name:
        return {"cooldown": 17, "damage": round(20 * mult), "speed": 12, "color": (140, 255, 230), "shape": "arc", "shots": 1, "spread": 0.0}
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
    if "CRYO PULSE" in name:
        return {"key": "cryo", "name": "Cryo Pulse", "cooldown": 420, "mana": 20, "desc": "Frost burst (45 dmg) + 2s shield"}
    if "TEMPEST SURGE" in name:
        return {"key": "ring", "name": "Tempest Surge", "cooldown": 420, "mana": 25, "desc": "A 12-bolt ring erupts around you"}
    if "GRAVITY WELL" in name:
        return {"key": "well", "name": "Gravity Well", "cooldown": 480, "mana": 35, "desc": "Collapses nearby shots + 45 dmg pulse"}
    if "PHOENIX CORE" in name:
        return {"key": "phoenix", "name": "Phoenix Core", "cooldown": 720, "mana": 50, "desc": "Heal 60, 6s shield, fiery nova"}
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
    mult = {"common": 1.0, "uncommon": 1.25, "rare": 1.6, "epic": 2.1, "legendary": 2.8}.get(rarity, 1.0)
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
    if slot == "currency":
        key = orb_key(item)
        return [f"Trade value: {ORB_VALUES[key]}", "Ninjas sometimes drop these", "Spend at the shop or THE FORGE"]
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
        "orb": "Trade currency of the realm.",
    }
    return blurbs.get(kind, "")

def _glow(surface, x0, y0, x1, y1, s, color):
    pygame.draw.line(surface, (18, 20, 26), (x0, y0), (x1, y1), max(2, int(7 * s)))
    pygame.draw.line(surface, color, (x0, y0), (x1, y1), max(1, int(4 * s)))
    pygame.draw.line(surface, (255, 255, 255), (x0, y0), (x1, y1), max(1, int(1.5 * s)))

def _draw_energy_sword(surface, cx, cy, s, color):
    """Sci-fi energy sword: textured hilt + crossguard + glowing plasma blade."""
    grip_w, grip_h = max(2, int(2.5 * s)), max(3, int(7 * s))
    pygame.draw.rect(surface, (35, 38, 46), (cx - grip_w // 2, cy + int(2 * s), grip_w, grip_h))
    for i in range(3):
        gy = cy + int(3 * s) + i * int(2 * s)
        pygame.draw.line(surface, (50, 54, 64), (cx - grip_w // 2, gy), (cx + grip_w // 2, gy), 1)
    gw, gh = max(4, int(8 * s)), max(2, int(2.5 * s))
    pygame.draw.rect(surface, (55, 60, 72), (cx - gw, cy + int(0.5 * s), gw * 2, gh))
    pygame.draw.rect(surface, color, (cx - gw, cy + int(0.5 * s), gw * 2, gh), max(1, int(1 * s)))
    cap_r = max(1, int(1.5 * s))
    pygame.draw.circle(surface, (80, 86, 100), (cx - gw, cy + int(1.7 * s)), cap_r)
    pygame.draw.circle(surface, (80, 86, 100), (cx + gw, cy + int(1.7 * s)), cap_r)
    blade_top = cy - int(12 * s)
    glow_color = tuple(min(255, c + 30) for c in color)
    outer_pts = [(cx - int(3 * s), cy + int(0.5 * s)), (cx + int(3 * s), cy + int(0.5 * s)), (cx + int(1.2 * s), blade_top), (cx - int(1.2 * s), blade_top)]
    pygame.draw.polygon(surface, glow_color, outer_pts)
    core_pts = [(cx - int(1.2 * s), cy), (cx + int(1.2 * s), cy), (cx + int(0.5 * s), blade_top + int(2 * s)), (cx - int(0.5 * s), blade_top + int(2 * s))]
    pygame.draw.polygon(surface, (220, 240, 255), core_pts)
    pygame.draw.line(surface, (255, 255, 255), (cx, cy), (cx, blade_top + int(3 * s)), max(1, int(1 * s)))
    pygame.draw.circle(surface, (255, 255, 255), (cx, blade_top), max(1, int(1.5 * s)))
    hi = tuple(min(255, c + 80) for c in color)
    pygame.draw.line(surface, hi, (cx + int(1 * s), cy - int(3 * s)), (cx + int(3 * s), cy - int(5 * s)), max(1, int(1 * s)))
    pygame.draw.line(surface, hi, (cx - int(1 * s), cy - int(6 * s)), (cx - int(3 * s), cy - int(8 * s)), max(1, int(1 * s)))
    pygame.draw.line(surface, hi, (cx + int(0.5 * s), cy - int(8 * s)), (cx + int(2.5 * s), cy - int(10 * s)), max(1, int(1 * s)))

def _draw_blaster(surface, cx, cy, s, color):
    """Sci-fi blaster: barrel + body + grip + energy cell + muzzle glow."""
    pygame.draw.rect(surface, (28, 32, 40), (cx - int(6 * s), cy - int(3 * s), int(18 * s), int(6 * s)))
    pygame.draw.rect(surface, (40, 44, 54), (cx - int(6 * s), cy - int(3 * s), int(18 * s), max(1, int(2 * s))))
    pygame.draw.rect(surface, (20, 24, 32), (cx + int(11 * s), cy - int(2.5 * s), int(3 * s), int(5 * s)))
    pygame.draw.circle(surface, (255, 240, 160), (cx + int(13 * s), cy), max(1, int(1.8 * s)))
    pygame.draw.circle(surface, color, (cx + int(13 * s), cy), max(1, int(1 * s)))
    pygame.draw.rect(surface, (32, 36, 46), (cx - int(8 * s), cy - int(2 * s), int(10 * s), int(7 * s)))
    pygame.draw.rect(surface, color, (cx - int(8 * s), cy - int(2 * s), int(10 * s), max(1, int(2 * s))))
    pygame.draw.rect(surface, (15, 17, 22), (cx - int(4 * s), cy + int(0.5 * s), int(5 * s), int(3 * s)))
    pygame.draw.rect(surface, (90, 220, 255), (cx - int(4 * s), cy + int(0.5 * s), int(5 * s), max(1, int(1.5 * s))))
    pygame.draw.rect(surface, (22, 24, 30), (cx - int(3 * s), cy + int(4 * s), int(5 * s), int(7 * s)))
    pygame.draw.rect(surface, (35, 38, 48), (cx - int(2.5 * s), cy + int(5 * s), int(4 * s), int(5 * s)))
    pygame.draw.arc(surface, (40, 44, 54), (cx - int(2 * s), cy + int(3 * s), int(4 * s), int(4 * s)), 0, 3.14, max(1, int(1 * s)))
    pygame.draw.rect(surface, (60, 66, 78), (cx + int(8 * s), cy - int(5 * s), max(1, int(2 * s)), max(1, int(2 * s))))

def _draw_sci_helm(surface, cx, cy, s, color):
    """Sci-fi helmet: dome + visor slit + antenna + vents."""
    pygame.draw.ellipse(surface, (22, 26, 34), (cx - int(10 * s), cy - int(9 * s), int(20 * s), int(18 * s)))
    pygame.draw.ellipse(surface, color, (cx - int(8 * s), cy - int(8 * s), int(16 * s), int(15 * s)))
    pygame.draw.rect(surface, (12, 18, 26), (cx - int(7 * s), cy - int(2 * s), int(14 * s), int(4 * s)))
    pygame.draw.rect(surface, (120, 230, 255), (cx - int(7 * s), cy - int(1 * s), int(14 * s), max(1, int(1.6 * s))))
    hi = tuple(min(255, c + 40) for c in color)
    pygame.draw.ellipse(surface, hi, (cx - int(5 * s), cy - int(8 * s), int(10 * s), int(4 * s)))
    pygame.draw.line(surface, color, (cx + int(8 * s), cy - int(8 * s)), (cx + int(11 * s), cy - int(13 * s)), max(1, int(2 * s)))
    pygame.draw.circle(surface, (255, 100, 100), (cx + int(11 * s), cy - int(13 * s)), max(1, int(1.8 * s)))
    for i in range(2):
        vx = cx - int(6 * s) + i * int(5 * s)
        pygame.draw.line(surface, (30, 34, 44), (vx, cy + int(3 * s)), (vx, cy + int(5 * s)), 1)
    pygame.draw.rect(surface, (30, 34, 44), (cx - int(5 * s), cy + int(5 * s), int(10 * s), max(1, int(2 * s))))

def _draw_sci_armor(surface, cx, cy, s, color):
    """Sci-fi chest armor: pauldrons + chest plate + energy core."""
    pygame.draw.ellipse(surface, (20, 24, 32), (cx - int(11 * s), cy - int(6 * s), int(7 * s), int(8 * s)))
    pygame.draw.ellipse(surface, (20, 24, 32), (cx + int(4 * s), cy - int(6 * s), int(7 * s), int(8 * s)))
    pygame.draw.ellipse(surface, color, (cx - int(10 * s), cy - int(5 * s), int(5 * s), int(6 * s)))
    pygame.draw.ellipse(surface, color, (cx + int(5 * s), cy - int(5 * s), int(5 * s), int(6 * s)))
    pygame.draw.rect(surface, (20, 24, 32), (cx - int(8 * s), cy - int(7 * s), int(16 * s), int(16 * s)))
    pygame.draw.rect(surface, color, (cx - int(7 * s), cy - int(6 * s), int(14 * s), int(14 * s)))
    pygame.draw.rect(surface, (22, 26, 34), (cx - max(1, int(1.5 * s)), cy - int(6 * s), max(1, int(3 * s)), int(14 * s)))
    hi = tuple(min(255, c + 30) for c in color)
    pygame.draw.polygon(surface, hi, [(cx - int(6 * s), cy - int(5 * s)), (cx + int(6 * s), cy - int(5 * s)), (cx, cy + int(1 * s))])
    pygame.draw.circle(surface, (120, 235, 255), (cx, cy + int(3 * s)), max(2, int(3.2 * s)))
    pygame.draw.circle(surface, (230, 250, 255), (cx, cy + int(3 * s)), max(1, int(1.4 * s)))
    pygame.draw.rect(surface, (30, 34, 44), (cx - int(7 * s), cy + int(8 * s), int(14 * s), max(1, int(2 * s))))

def _draw_data_chip(surface, cx, cy, s, color):
    """Sci-fi data chip: circuit board + traces + pins + glow."""
    pygame.draw.rect(surface, (16, 20, 28), (cx - int(8 * s), cy - int(10 * s), int(16 * s), int(20 * s)))
    pygame.draw.rect(surface, color, (cx - int(8 * s), cy - int(10 * s), int(16 * s), int(20 * s)), max(1, int(2 * s)))
    pygame.draw.rect(surface, (30, 38, 52), (cx - int(5 * s), cy - int(7 * s), int(10 * s), int(14 * s)))
    for i in range(3):
        y = cy - int(4 * s) + i * int(4 * s)
        pygame.draw.line(surface, color, (cx - int(4 * s), y), (cx + int(4 * s), y), 1)
    for i in range(4):
        px = cx - int(5 * s) + i * int(3.5 * s)
        pygame.draw.rect(surface, (180, 190, 200), (px, cy - int(10 * s), max(1, int(2 * s)), max(1, int(2 * s))))
        pygame.draw.rect(surface, (180, 190, 200), (px, cy + int(8 * s), max(1, int(2 * s)), max(1, int(2 * s))))
    pygame.draw.circle(surface, (12, 14, 20), (cx - int(6 * s), cy - int(8 * s)), max(1, int(1.5 * s)))
    pygame.draw.circle(surface, (140, 240, 255), (cx, cy + int(9 * s)), max(1, int(1.8 * s)))

def _draw_energy_cell(surface, cx, cy, s, color, is_repair):
    """Sci-fi energy cell: battery body + core glow + terminals."""
    pygame.draw.rect(surface, (200, 230, 240), (cx - int(5 * s), cy - int(10 * s), int(10 * s), int(20 * s)))
    pygame.draw.rect(surface, (30, 40, 55), (cx - int(4 * s), cy - int(9 * s), int(8 * s), int(18 * s)))
    pygame.draw.rect(surface, color, (cx - int(4 * s), cy - int(2 * s), int(8 * s), int(11 * s)))
    for i in range(3):
        ly = cy - int(1 * s) + i * int(3 * s)
        pygame.draw.line(surface, tuple(min(255, c + 60) for c in color), (cx - int(3 * s), ly), (cx + int(3 * s), ly), 1)
    pygame.draw.rect(surface, (255, 255, 255), (cx - int(3 * s), cy - int(8 * s), max(1, int(2 * s)), max(1, int(6 * s))))
    pygame.draw.rect(surface, (60, 66, 80), (cx - int(6 * s), cy - int(12 * s), int(12 * s), max(1, int(3 * s))))
    pygame.draw.rect(surface, (60, 66, 80), (cx - int(3 * s), cy + int(9 * s), int(6 * s), max(1, int(2 * s))))
    if is_repair:
        pygame.draw.rect(surface, (255, 255, 255), (cx - max(1, int(1.2 * s)), cy + int(1 * s), max(1, int(2.4 * s)), max(1, int(6 * s))))
        pygame.draw.rect(surface, (255, 255, 255), (cx - max(1, int(2.5 * s)), cy + int(2.6 * s), max(1, int(5 * s)), max(1, int(2.4 * s))))

def _draw_plasma_ring(surface, cx, cy, s, color):
    """Sci-fi plasma ring: glowing energy band with sparks."""
    pygame.draw.circle(surface, tuple(min(255, c + 20) for c in color), (cx, cy), max(2, int(10 * s)), max(1, int(5 * s)))
    pygame.draw.circle(surface, color, (cx, cy), max(2, int(9 * s)), max(1, int(4 * s)))
    pygame.draw.circle(surface, (255, 255, 255), (cx, cy), max(2, int(9 * s)), 1)
    pygame.draw.circle(surface, (140, 235, 255), (cx + int(5 * s), cy - int(5 * s)), max(1, int(2 * s)))
    pygame.draw.circle(surface, (255, 255, 255), (cx - int(4 * s), cy + int(5 * s)), max(1, int(1.5 * s)))
    pygame.draw.circle(surface, (200, 240, 255), (cx + int(6 * s), cy + int(3 * s)), max(1, int(1 * s)))

def _draw_cloak(surface, cx, cy, s, color):
    """Sci-fi cloak: flowing cape with clasp and fabric folds."""
    pygame.draw.polygon(surface, color, [(cx, cy - int(10 * s)), (cx - int(8 * s), cy + int(9 * s)), (cx + int(8 * s), cy + int(9 * s))])
    pygame.draw.polygon(surface, (20, 22, 30), [(cx, cy - int(10 * s)), (cx - int(8 * s), cy + int(9 * s)), (cx + int(8 * s), cy + int(9 * s))], max(1, int(2 * s)))
    pygame.draw.circle(surface, (180, 190, 200), (cx, cy - int(7 * s)), max(1, int(2.5 * s)))
    pygame.draw.circle(surface, (140, 235, 255), (cx, cy - int(7 * s)), max(1, int(1.5 * s)))
    pygame.draw.line(surface, (30, 33, 40), (cx - int(3 * s), cy - int(2 * s)), (cx - int(5 * s), cy + int(7 * s)), 1)
    pygame.draw.line(surface, (30, 33, 40), (cx + int(3 * s), cy - int(2 * s)), (cx + int(5 * s), cy + int(7 * s)), 1)
    pygame.draw.line(surface, (40, 44, 54), (cx - int(6 * s), cy + int(8 * s)), (cx + int(6 * s), cy + int(8 * s)), 1)

def _draw_cache(surface, cx, cy, s, color):
    """Sci-fi storage cache: sealed container with latches + glow seam."""
    pygame.draw.rect(surface, (22, 26, 34), (cx - int(8 * s), cy - int(6 * s), int(16 * s), int(12 * s)))
    pygame.draw.rect(surface, color, (cx - int(8 * s), cy - int(6 * s), int(16 * s), int(12 * s)), max(1, int(2 * s)))
    pygame.draw.line(surface, color, (cx - int(8 * s), cy), (cx + int(8 * s), cy), 1)
    pygame.draw.rect(surface, (180, 190, 200), (cx - int(6 * s), cy - int(2 * s), max(1, int(3 * s)), max(1, int(4 * s))))
    pygame.draw.rect(surface, (180, 190, 200), (cx + int(3 * s), cy - int(2 * s), max(1, int(3 * s)), max(1, int(4 * s))))
    pygame.draw.line(surface, tuple(min(255, c + 50) for c in color), (cx - int(6 * s), cy), (cx + int(6 * s), cy), 1)
    for rx in [cx - int(7 * s), cx + int(7 * s)]:
        for ry in [cy - int(5 * s), cy + int(5 * s)]:
            pygame.draw.circle(surface, (60, 66, 78), (rx, ry), max(1, int(1 * s)))

def _draw_orb(surface, cx, cy, s, color):
    """POE-style trade orb: a swirling energy sphere."""
    pygame.draw.circle(surface, (14, 16, 24), (cx, cy), max(2, int(10 * s)))
    pygame.draw.circle(surface, color, (cx, cy), max(2, int(8 * s)))
    hi = tuple(min(255, c + 70) for c in color)
    pygame.draw.circle(surface, hi, (cx - int(2 * s), cy - int(2 * s)), max(1, int(3.2 * s)))
    pygame.draw.circle(surface, (255, 255, 255), (cx - int(3 * s), cy - int(3 * s)), max(1, int(1.4 * s)))
    pygame.draw.circle(surface, (20, 22, 30), (cx + int(3 * s), cy + int(2 * s)), max(1, int(2.4 * s)))

# --------------------------------------------------------------------------
# POE-style trade currency: orbs are items enemies drop, the shop trades in
# them, and THE FORGE consumes them to craft / upgrade / reroll gear.
ORB_ITEMS = {
    "scrap": ("SCRAP SHARD", (208, 208, 216), "common", "currency"),
    "phase": ("PHASE CRYSTAL", (96, 190, 255), "uncommon", "currency"),
    "quantum": ("QUANTUM ORB", (255, 208, 84), "rare", "currency"),
    "singularity": ("SINGULARITY CORE", (255, 96, 168), "epic", "currency"),
}
ORB_VALUES = {"scrap": 1, "phase": 5, "quantum": 25, "singularity": 100}
ORB_NAMES = {"scrap": "SCRAP", "phase": "CRYSTAL", "quantum": "ORB", "singularity": "CORE"}
ORB_ORDER = ("scrap", "phase", "quantum", "singularity")

def orb_key(item):
    name = str(item[0]).upper() if item is not None else ""
    if "SCRAP" in name:
        return "scrap"
    if "CRYSTAL" in name:
        return "phase"
    if "QUANTUM" in name:
        return "quantum"
    if "SINGULARITY" in name:
        return "singularity"
    return "scrap"

RARITY_ORDER = ["common", "uncommon", "rare", "epic", "legendary"]

def upgrade_rarity(item):
    """Return the item bumped one rarity tier (at legendary it stays)."""
    if item is None:
        return item
    rarity = item[2] if len(item) > 2 else "common"
    if rarity not in RARITY_ORDER:
        return item
    idx = RARITY_ORDER.index(rarity)
    if idx >= len(RARITY_ORDER) - 1:
        return item
    upgraded = list(item)
    upgraded[2] = RARITY_ORDER[idx + 1]
    return tuple(upgraded)

# Master loot table (shared by the overworld drops and the FORGE reroll).
LOOT_TABLE = [
    ("PLASMA SABER", (90, 220, 255), "common", "weapon"),
    ("PULSE BLADE", (200, 200, 215), "common", "weapon"),
    ("NANO HELM", (150, 160, 175), "common", "helmet"),
    ("ION MAIL", (100, 160, 220), "uncommon", "armor"),
    ("ENERGY CELL", (78, 200, 255), "uncommon", None),
    ("REPAIR CELL", (220, 70, 70), "common", None),
    ("NOVA SCROLL", (255, 190, 110), "rare", "ability"),
    ("BLINK DRIVE", (140, 240, 255), "rare", "ability"),
    ("SENTRY DRONE", (150, 255, 170), "epic", "ability"),
    ("OVERDRIVE CORE", (255, 120, 120), "epic", "ability"),
    ("AEGIS PROTOCOL", (170, 220, 255), "rare", "ability"),
    ("VOID CLOAK", (150, 90, 220), "rare", "armor"),
    ("NOVA SABER", (255, 190, 90), "rare", "weapon"),
    ("PLASMA RIFLE", (140, 255, 170), "epic", "weapon"),
    ("SCATTER CANNON", (220, 150, 255), "epic", "weapon"),
    # Higher-tier gear.
    ("AURORA BLADE", (140, 255, 230), "rare", "weapon"),
    ("TEMPEST RIFLE", (170, 200, 255), "epic", "weapon"),
    ("EVENT HORIZON", (255, 96, 96), "legendary", "weapon"),
    ("SINGULARITY EDGE", (255, 224, 130), "legendary", "weapon"),
    ("TITAN PLATE", (255, 150, 70), "epic", "armor"),
    ("CHRONO CROWN", (190, 140, 255), "legendary", "helmet"),
    ("WARP BAND", (255, 120, 200), "rare", "ring"),
    ("ECHO BAND", (120, 255, 200), "epic", "ring"),
    # New abilities.
    ("CRYO PULSE", (150, 230, 255), "uncommon", "ability"),
    ("TEMPEST SURGE", (170, 220, 255), "rare", "ability"),
    ("GRAVITY WELL", (150, 120, 255), "epic", "ability"),
    ("PHOENIX CORE", (255, 120, 40), "legendary", "ability"),
]
