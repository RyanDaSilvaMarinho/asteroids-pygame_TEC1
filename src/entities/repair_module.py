# ASTEROIDE SINGLEPLAYER v1.0
# This file defines the RepairModule collectible entity for life recovery.

import math

import pygame as pg

import config as C
from utils import Vec, rand_unit_vec, wrap_pos


class RepairModule(pg.sprite.Sprite):
    """Life-recovery collectible spawned when asteroids are destroyed.

    Drifts slowly across the screen and disappears after REPAIR_TTL seconds.
    Blinks during the last REPAIR_BLINK_TIME seconds to warn the player.
    Collecting it restores 1 life (capped at MAX_LIVES).

    Visual design:
      - Green pulsating outer ring
      - Cross/plus icon in the center (medical cross)
      - Small dot in the center
    """

    def __init__(self, pos: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = rand_unit_vec() * C.REPAIR_SPEED
        self.r = C.REPAIR_RADIUS
        self.ttl = C.REPAIR_TTL
        self.pulse = 0.0
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def update(self, dt: float):
        """Move, wrap, pulse, and expire the item."""
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.pulse += dt * 3.5
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        """Draw the repair module; blink when close to expiring."""
        # Blinking logic: skip every other frame in the last REPAIR_BLINK_TIME seconds
        if self.ttl < C.REPAIR_BLINK_TIME and int(self.ttl * 7) % 2 == 0:
            return

        cx, cy = int(self.pos.x), int(self.pos.y)
        color = C.REPAIR_COLOR
        s = C.REPAIR_ICON_SIZE

        # Outer pulsating ring
        pulse_r = int(self.r + math.sin(self.pulse) * 2.0)
        pg.draw.circle(surf, color, (cx, cy), pulse_r, 1)

        # Medical cross (plus sign) — thick lines
        pg.draw.line(surf, color, (cx, cy - s), (cx, cy + s), 2)   # vertical
        pg.draw.line(surf, color, (cx - s, cy), (cx + s, cy), 2)   # horizontal

        # Center dot
        pg.draw.circle(surf, color, (cx, cy), 2)

    @property
    def is_expiring(self) -> bool:
        """True when the item is in the blinking phase."""
        return self.ttl < C.REPAIR_BLINK_TIME