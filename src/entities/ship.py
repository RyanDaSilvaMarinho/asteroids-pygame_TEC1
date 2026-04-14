# ASTEROIDE SINGLEPLAYER v1.0
# This file defines the player Ship entity and all its local behaviors.

import math
from random import uniform

import pygame as pg

import config as C
from utils import Vec, angle_to_vec, draw_circle, draw_poly, wrap_pos
from entities.bullets import Bullet, ChargeBullet


class Ship(pg.sprite.Sprite):
    """Player-controlled ship. Handles movement, shooting, dash, and charge logic."""

    def __init__(self, pos: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(0, 0)
        self.angle = -90.0
        self.cool = 0.0
        self.invuln = 0.0
        self.alive = True
        self.r = C.SHIP_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)
        self.charge_time = 0.0
        self.dash_cool = 0.0
        self.dash_trail: list = []

    def control(self, keys: pg.key.ScancodeWrapper, dt: float):
        """Apply rotation, thrust, and friction from the current input state."""
        if keys[pg.K_LEFT]:
            self.angle -= C.SHIP_TURN_SPEED * dt
        if keys[pg.K_RIGHT]:
            self.angle += C.SHIP_TURN_SPEED * dt
        if keys[pg.K_UP]:
            self.vel += angle_to_vec(self.angle) * C.SHIP_THRUST * dt
        self.vel *= C.SHIP_FRICTION

    def fire(self) -> "Bullet | None":
        """Spawn a player bullet when the fire cooldown allows it."""
        if self.cool > 0:
            return None
        dirv = angle_to_vec(self.angle)
        pos = self.pos + dirv * (self.r + 6)
        vel = self.vel + dirv * C.SHIP_BULLET_SPEED
        self.cool = C.SHIP_FIRE_RATE
        return Bullet(pos, vel)

    def fire_charged(self) -> "ChargeBullet | None":
        """Fire a charged bullet with power proportional to charge time."""
        if self.cool > 0 or self.charge_time < C.CHARGE_MIN:
            return None
        if self.charge_time >= C.CHARGE_TIER_L:
            power = "L"
        elif self.charge_time >= C.CHARGE_TIER_M:
            power = "M"
        else:
            power = "S"
        dirv = angle_to_vec(self.angle)
        pos = self.pos + dirv * (self.r + 6)
        vel = self.vel + dirv * C.CHARGE_BULLET_SPEED
        self.cool = C.SHIP_FIRE_RATE
        self.charge_time = 0.0
        return ChargeBullet(pos, vel, power)

    def hyperspace(self):
        """Teleport the ship to a random location and reset its momentum."""
        self.pos = Vec(uniform(0, C.WIDTH), uniform(0, C.HEIGHT))
        self.vel.xy = (0, 0)
        self.invuln = 1.0

    def quantum_dash(self) -> bool:
        """Teleport the ship forward by DASH_DISTANCE in the current facing direction.

        Returns True if executed, False if on cooldown.
        """
        if self.dash_cool > 0:
            return False
        old_pos = Vec(self.pos)
        dirv = angle_to_vec(self.angle)
        self.pos += dirv * C.DASH_DISTANCE
        self.pos = wrap_pos(self.pos)
        self.invuln = C.DASH_INVULN
        self.dash_cool = C.DASH_COOLDOWN
        for i in range(8):
            t = i / 8.0
            p = old_pos + (self.pos - old_pos) * t
            self.dash_trail.append([Vec(p), 0.4])
        return True

    def update(self, dt: float):
        """Advance cooldowns, move the ship, and wrap it on screen."""
        if self.cool > 0:
            self.cool -= dt
        if self.invuln > 0:
            self.invuln -= dt
        if self.dash_cool > 0:
            self.dash_cool -= dt
        self.dash_trail = [[p, t - dt] for p, t in self.dash_trail if t - dt > 0]
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        """Draw the ship, dash trail, invulnerability ring, and charge indicator."""
        # Dash trail particles
        for p, t in self.dash_trail:
            alpha_f = t / 0.4
            r = int(3 * alpha_f)
            if r > 0:
                color = (
                    int(C.DASH_TRAIL_COLOR[0] * alpha_f),
                    int(C.DASH_TRAIL_COLOR[1] * alpha_f),
                    int(C.DASH_TRAIL_COLOR[2] * alpha_f),
                )
                pg.draw.circle(surf, color, (int(p.x), int(p.y)), r)

        # Ship triangle
        dirv = angle_to_vec(self.angle)
        left = angle_to_vec(self.angle + 140)
        right = angle_to_vec(self.angle - 140)
        p1 = self.pos + dirv * self.r
        p2 = self.pos + left * self.r * 0.9
        p3 = self.pos + right * self.r * 0.9
        draw_poly(surf, [p1, p2, p3])

        # Invulnerability blink ring
        if self.invuln > 0 and int(self.invuln * 10) % 2 == 0:
            draw_circle(surf, self.pos, self.r + 6)

        # Dash cooldown arc
        if self.dash_cool > 0:
            frac = self.dash_cool / C.DASH_COOLDOWN
            angle = int(360 * (1.0 - frac))
            rect = pg.Rect(0, 0, (self.r + 10) * 2, (self.r + 10) * 2)
            rect.center = (int(self.pos.x), int(self.pos.y))
            if angle > 0:
                pg.draw.arc(
                    surf, C.DASH_TRAIL_COLOR, rect,
                    math.radians(-90),
                    math.radians(-90 + angle),
                    1,
                )

        # Charge ring
        if self.charge_time >= C.CHARGE_MIN:
            t = min(self.charge_time, C.CHARGE_MAX)
            if t >= C.CHARGE_TIER_L:
                color, radius = (255, 80, 80), self.r + 14
            elif t >= C.CHARGE_TIER_M:
                color, radius = (255, 200, 50), self.r + 10
            else:
                color, radius = (100, 200, 255), self.r + 6
            show = True
            if t >= C.CHARGE_TIER_L and int(t * 8) % 2 == 0:
                show = False
            if show:
                pg.draw.circle(
                    surf, color,
                    (int(self.pos.x), int(self.pos.y)),
                    radius, 1,
                )