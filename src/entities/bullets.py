# ASTEROIDE SINGLEPLAYER v1.0
# This file defines all projectile entities: player bullets, charged shots, and UFO bullets.

import pygame as pg

import config as C
from utils import Vec, draw_circle, wrap_pos


class Bullet(pg.sprite.Sprite):
    """Standard player bullet fired from the ship."""

    def __init__(self, pos: Vec, vel: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.ttl = C.BULLET_TTL
        self.r = C.BULLET_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def update(self, dt: float):
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        draw_circle(surf, self.pos, self.r)


class ChargeBullet(pg.sprite.Sprite):
    """Charged shot. power = 'S' | 'M' | 'L' indicates which tier it destroys directly."""

    def __init__(self, pos: Vec, vel: Vec, power: str):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.power = power
        self.ttl = C.BULLET_TTL
        radius_map = {"S": 4, "M": 7, "L": 11}
        self.r = radius_map[power]
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def update(self, dt: float):
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        draw_circle(surf, self.pos, self.r)


class UfoBullet(pg.sprite.Sprite):
    """Bullet fired by a UFO enemy."""

    def __init__(self, pos: Vec, vel: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.ttl = C.UFO_BULLET_TTL
        self.r = C.BULLET_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def update(self, dt: float):
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        draw_circle(surf, self.pos, self.r)