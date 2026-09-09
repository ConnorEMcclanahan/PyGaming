"""Skill system for the game."""

import random

ALL_SKILLS = {
    "power_strike": {"name": "Power Strike", "description": "+15% weapon damage", "category": "combat", "effect": {"damage_mult": 1.15}, "max_rank": 5},
    "rapid_fire": {"name": "Rapid Fire", "description": "+20% attack speed", "category": "combat", "effect": {"attack_speed_mult": 1.20}, "max_rank": 3},
    "tough_skin": {"name": "Tough Skin", "description": "+20 max health", "category": "defense", "effect": {"max_health": 20}, "max_rank": 5},
    "swift_feet": {"name": "Swift Feet", "description": "+15% movement speed", "category": "utility", "effect": {"speed_mult": 1.15}, "max_rank": 3},
    "exp_boost": {"name": "EXP Boost", "description": "+20% experience gain", "category": "utility", "effect": {"exp_mult": 1.20}, "max_rank": 3},
}


class SkillTree:
    def __init__(self):
        self.ranks = {skill_id: 0 for skill_id in ALL_SKILLS}
        self.total_points_spent = 0

    def get_available_skills(self):
        return [sid for sid, s in ALL_SKILLS.items() if self.ranks[sid] < s["max_rank"]]

    def get_random_choices(self, count=3):
        available = self.get_available_skills()
        if len(available) <= count:
            return available
        return random.sample(available, count)

    def upgrade_skill(self, skill_id):
        if skill_id not in ALL_SKILLS:
            return False
        if self.ranks[skill_id] >= ALL_SKILLS[skill_id]["max_rank"]:
            return False
        self.ranks[skill_id] += 1
        self.total_points_spent += 1
        return True

    def get_rank(self, skill_id):
        return self.ranks.get(skill_id, 0)

    def reset(self):
        self.ranks = {skill_id: 0 for skill_id in ALL_SKILLS}
        self.total_points_spent = 0

    def get_total_effect(self):
        total = {"damage_mult": 1.0, "attack_speed_mult": 1.0, "extra_projectiles": 0,
                "max_health": 0, "speed_mult": 1.0, "exp_mult": 1.0, "loot_mult": 1.0}
        for sid, rank in self.ranks.items():
            if rank > 0:
                eff = ALL_SKILLS[sid]["effect"]
                for k, v in eff.items():
                    if k in total:
                        if k in ("damage_mult", "attack_speed_mult", "speed_mult", "exp_mult", "loot_mult"):
                            total[k] *= (1 + (v - 1) * rank)
                        else:
                            total[k] += v * rank
        return total


def get_exp_for_level(level):
    return 50 + (level - 1) * 25
