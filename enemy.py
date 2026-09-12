"""Backward-compatible facade: imports moved to enemies/. (no logic here)."""
from enemies.projectiles import EggProjectile, NinjaStar, SlimeBall
from enemies.slimes import Slime, SlimeBoss
from enemies.ninjas import Ninja, NinjaBoss
from enemies.chickens import Chicken, GiantChickenBoss


__all__ = [
    "NinjaStar", "SlimeBall", "EggProjectile",
    "Slime", "SlimeBoss", "Ninja", "NinjaBoss",
    "Chicken", "GiantChickenBoss",
]
