# ASTEROIDE SINGLEPLAYER v1.0
# This file defines the Asteroid entity and its visual/movement behavior.

import math
from random import uniform

import pygame as pg

import config as C
from utils import Vec, wrap_pos


class Asteroid(pg.sprite.Sprite):
    """Asteroid obstacle. Supports size tiers (L/M/S) and legacy wave upgrades."""

    def __init__(self, pos: Vec, vel: Vec, size: str, legacy: int = 0):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.legacy = max(0, min(legacy, C.LEGACY_MAX))

        tier_up = {"S": "M", "M": "L", "L": "L"}
        for _ in range(self.legacy):
            size = tier_up[size]
        self.size = size
        self.vel = self.vel * (C.LEGACY_SPEED_MULT ** self.legacy)

        self.r = C.AST_SIZES[size]["r"]
        self.poly = self._make_poly()
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def _make_poly(self):
        steps = 12 if self.size == "L" else 10 if self.size == "M" else 8
        pts = []
        for i in range(steps):
            ang = i * (360 / steps)
            jitter = uniform(0.75, 1.2)
            r = self.r * jitter
            v = Vec(math.cos(math.radians(ang)), math.sin(math.radians(ang)))
            pts.append(v * r)
        return pts

    def update(self, dt: float):
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        pts = [(self.pos + p) for p in self.poly]
        width = 3 if self.legacy > 0 else 1
        pg.draw.polygon(surf, C.WHITE, pts, width=width)