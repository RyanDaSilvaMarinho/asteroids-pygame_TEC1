# ASTEROIDE SINGLEPLAYER v1.0
# This file defines the Orbie collectible entity for the special energy bar.

import math

import pygame as pg

import config as C
from utils import Vec, rand_unit_vec, wrap_pos


class Orbie(pg.sprite.Sprite):
    """Special-energy collectible that drifts slowly across the screen.

    When touched by the ship, adds ORBIE_ENERGY seconds to the special bar.
    Visual: pulsating outer ring + inner diamond + center dot.
    """

    def __init__(self, pos: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = rand_unit_vec() * C.ORBIE_SPEED
        self.r = C.ORBIE_RADIUS
        self.pulse = 0.0
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def update(self, dt: float):
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.pulse += dt * 4.0
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        cx, cy = int(self.pos.x), int(self.pos.y)
        pulse_r = int(self.r + math.sin(self.pulse) * 2.5)

        pg.draw.circle(surf, C.ORBIE_COLOR, (cx, cy), pulse_r, 1)

        inner = self.r - 3
        diamond = [
            (cx, cy - inner),
            (cx + inner, cy),
            (cx, cy + inner),
            (cx - inner, cy),
        ]
        pg.draw.polygon(surf, C.ORBIE_COLOR, diamond, 1)
        pg.draw.circle(surf, C.ORBIE_COLOR, (cx, cy), 2)