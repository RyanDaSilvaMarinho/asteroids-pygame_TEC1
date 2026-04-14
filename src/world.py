# ASTEROIDE SINGLEPLAYER v1.0
# This file coordinates world state, spawning, collisions, scoring, and progression.

import math
from random import uniform, random

import pygame as pg

import config as C
from entities import Asteroid, Bullet, Orbie, RepairModule, Ship, UFO
from hud import HUD
from utils import Vec, angle_to_vec, rand_edge_pos, rand_unit_vec


class World:
    """Central coordinator for all in-game objects and systems.

    Manages entity groups, game state, spawning, collision resolution,
    scoring, wave progression, and delegating drawing to the HUD.
    """

    def __init__(self):
        self.ship = Ship(Vec(C.WIDTH / 2, C.HEIGHT / 2))
        self.bullets = pg.sprite.Group()
        self.ufo_bullets = pg.sprite.Group()
        self.charge_bullets = pg.sprite.Group()
        self.asteroids = pg.sprite.Group()
        self.ufos = pg.sprite.Group()
        self.orbies = pg.sprite.Group()
        self.repair_modules = pg.sprite.Group()   # ← new group
        self.all_sprites = pg.sprite.Group(self.ship)

        self.score = 0
        self.lives = C.START_LIVES
        self.wave = 0
        self.wave_cool = C.WAVE_DELAY
        self.safe = C.SAFE_SPAWN_TIME
        self.ufo_timer = C.UFO_SPAWN_EVERY
        self.game_over = False

        self.score_popups: list = []

        # Special ability
        self.orbie_timer = C.ORBIE_SPAWN_EVERY
        self.special_energy = 0.0
        self.special_active = False
        self.minigun_cool = 0.0

        self.hud = HUD()

    # ── Wave & spawning ───────────────────────────────────────────────────

    def start_wave(self):
        """Promote survivors and spawn a new asteroid wave."""
        self.wave += 1

        survivors = list(self.asteroids)
        for ast in survivors:
            new_legacy = min(ast.legacy + 1, C.LEGACY_MAX)
            pos = Vec(ast.pos)
            vel = Vec(ast.vel)
            size_base = ast.size
            tier_down = {"M": "S", "L": "M"}
            for _ in range(ast.legacy):
                size_base = tier_down.get(size_base, size_base)
            vel_base = vel / (C.LEGACY_SPEED_MULT ** ast.legacy)
            ast.kill()
            self.spawn_asteroid(pos, vel_base, size_base, new_legacy)

        count = 3 + self.wave
        for _ in range(count):
            pos = rand_edge_pos()
            while (pos - self.ship.pos).length() < 150:
                pos = rand_edge_pos()
            ang = uniform(0, math.tau)
            speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX)
            vel = Vec(math.cos(ang), math.sin(ang)) * speed
            self.spawn_asteroid(pos, vel, "L")

    def spawn_asteroid(self, pos: Vec, vel: Vec, size: str, legacy: int = 0):
        a = Asteroid(pos, vel, size, legacy)
        self.asteroids.add(a)
        self.all_sprites.add(a)

    def spawn_ufo(self):
        if self.ufos:
            return
        small = uniform(0, 1) < 0.5
        y = uniform(0, C.HEIGHT)
        x = 0 if uniform(0, 1) < 0.5 else C.WIDTH
        ufo = UFO(Vec(x, y), small)
        ufo.dir.xy = (1, 0) if x == 0 else (-1, 0)
        self.ufos.add(ufo)
        self.all_sprites.add(ufo)

    def spawn_orbie(self):
        for _ in range(15):
            pos = Vec(uniform(0, C.WIDTH), uniform(0, C.HEIGHT))
            if (pos - self.ship.pos).length() > 150:
                break
        o = Orbie(pos)
        self.orbies.add(o)
        self.all_sprites.add(o)

    def spawn_repair_module(self, pos: Vec):
        """Spawn a RepairModule at the given position (asteroid destruction site)."""
        rm = RepairModule(pos)
        self.repair_modules.add(rm)
        self.all_sprites.add(rm)

    # ── Player actions ────────────────────────────────────────────────────

    def ufo_try_fire(self):
        for ufo in self.ufos:
            bullet = ufo.fire_at(self.ship.pos)
            if bullet:
                self.ufo_bullets.add(bullet)
                self.all_sprites.add(bullet)

    def try_fire(self):
        if len(self.bullets) >= C.MAX_BULLETS:
            return
        b = self.ship.fire()
        if b:
            self.bullets.add(b)
            self.all_sprites.add(b)

    def try_fire_charged(self) -> bool:
        if self.charge_bullets:
            self.ship.charge_time = 0.0
            return False
        b = self.ship.fire_charged()
        if b:
            self.charge_bullets.add(b)
            self.all_sprites.add(b)
            return True
        return False

    def hyperspace(self):
        self.ship.hyperspace()
        self.score = max(0, self.score - C.HYPERSPACE_COST)

    def try_dash(self) -> bool:
        return self.ship.quantum_dash()

    # ── Special ability ───────────────────────────────────────────────────

    def activate_special(self):
        if self.special_energy <= 0:
            return
        if self.special_energy >= C.ORBIE_MAX_ENERGY:
            self._fire_radial()
            self.special_energy = 0.0
        else:
            self.special_active = True
            self.minigun_cool = 0.0

    def deactivate_special(self):
        self.special_active = False

    def _fire_minigun(self):
        dirv = angle_to_vec(self.ship.angle)
        pos = self.ship.pos + dirv * (self.ship.r + 6)
        vel = self.ship.vel + dirv * C.SHIP_BULLET_SPEED
        b = Bullet(pos, vel)
        self.bullets.add(b)
        self.all_sprites.add(b)

    def _fire_radial(self):
        n = C.SPECIAL_RADIAL_BULLETS
        for i in range(n):
            angle = (360.0 / n) * i
            dirv = angle_to_vec(angle)
            pos = self.ship.pos + dirv * (self.ship.r + 6)
            vel = self.ship.vel + dirv * C.SHIP_BULLET_SPEED
            b = Bullet(pos, vel)
            self.bullets.add(b)
            self.all_sprites.add(b)

    # ── Main loop ─────────────────────────────────────────────────────────

    def update(self, dt: float, keys):
        self.ship.control(keys, dt)

        if keys[pg.K_SPACE]:
            self.ship.charge_time = min(self.ship.charge_time + dt, C.CHARGE_MAX)

        self.all_sprites.update(dt)

        if self.safe > 0:
            self.safe -= dt
            self.ship.invuln = 0.5

        # UFO spawning
        if self.ufos:
            self.ufo_try_fire()
        else:
            self.ufo_timer -= dt
        if not self.ufos and self.ufo_timer <= 0:
            self.spawn_ufo()
            self.ufo_timer = C.UFO_SPAWN_EVERY

        # Orbie spawning
        self.orbie_timer -= dt
        if self.orbie_timer <= 0:
            if len(self.orbies) < C.ORBIE_MAX_ON_SCREEN:
                self.spawn_orbie()
            self.orbie_timer = C.ORBIE_SPAWN_EVERY

        # Minigun drain
        if self.special_active:
            self.special_energy -= C.SPECIAL_DRAIN_RATE * dt
            if self.special_energy <= 0:
                self.special_energy = 0.0
                self.special_active = False
            else:
                self.minigun_cool -= dt
                if self.minigun_cool <= 0:
                    self._fire_minigun()
                    self.minigun_cool = C.SPECIAL_MINIGUN_RATE

        self.handle_collisions()

        # Score popup drift
        self.score_popups = [
            [p[0] + Vec(0, -30) * dt, p[1], p[2] - dt]
            for p in self.score_popups if p[2] > 0
        ]

        if not self.asteroids and self.wave_cool <= 0:
            self.start_wave()
            self.wave_cool = C.WAVE_DELAY
        elif not self.asteroids:
            self.wave_cool -= dt

    # ── Collision handling ────────────────────────────────────────────────

    def handle_collisions(self):
        """Resolve all collisions between entity groups."""

        # Player bullets vs asteroids
        hits = pg.sprite.groupcollide(
            self.asteroids, self.bullets, False, True,
            collided=lambda a, b: (a.pos - b.pos).length() < a.r,
        )
        for ast in hits:
            self.split_asteroid(ast)

        # Charged bullet vs asteroids
        TIER_ORDER = {"S": 0, "M": 1, "L": 2}
        charge_hits = pg.sprite.groupcollide(
            self.asteroids, self.charge_bullets, False, False,
            collided=lambda a, b: (a.pos - b.pos).length() < a.r,
        )
        for ast, bullets_hit in charge_hits.items():
            b = bullets_hit[0]
            if TIER_ORDER[b.power] >= TIER_ORDER[ast.size]:
                base = C.AST_SIZES[ast.size]["score"]
                mult = self._proximity_mult(ast.pos)
                awarded = int(base * mult)
                self.score += awarded
                if mult > 1.05:
                    self.score_popups.append([Vec(ast.pos), f"{mult:.1f}x", 1.2])
                self._try_spawn_repair(ast.pos)   # ← repair chance
                ast.kill()
                b.kill()
            else:
                self.split_asteroid(ast)
                b.kill()

        # UFO bullets vs asteroids
        ufo_hits = pg.sprite.groupcollide(
            self.asteroids, self.ufo_bullets, False, True,
            collided=lambda a, b: (a.pos - b.pos).length() < a.r,
        )
        for ast in ufo_hits:
            self.split_asteroid(ast)

        # Ship vs asteroids / UFOs / UFO bullets
        if self.ship.invuln <= 0 and self.safe <= 0:
            for ast in self.asteroids:
                if (ast.pos - self.ship.pos).length() < (ast.r + self.ship.r):
                    self.ship_die()
                    break
            for ufo in self.ufos:
                if (ufo.pos - self.ship.pos).length() < (ufo.r + self.ship.r):
                    self.ship_die()
                    break
            for bullet in self.ufo_bullets:
                if (bullet.pos - self.ship.pos).length() < (bullet.r + self.ship.r):
                    bullet.kill()
                    self.ship_die()
                    break

        # Player bullets vs UFOs
        for ufo in list(self.ufos):
            for b in list(self.bullets):
                if (ufo.pos - b.pos).length() < (ufo.r + b.r):
                    score = C.UFO_SMALL["score"] if ufo.small else C.UFO_BIG["score"]
                    self.score += score
                    ufo.kill()
                    b.kill()

        # Charged bullet vs UFOs
        for ufo in list(self.ufos):
            for b in list(self.charge_bullets):
                if (ufo.pos - b.pos).length() < (ufo.r + b.r):
                    score = C.UFO_SMALL["score"] if ufo.small else C.UFO_BIG["score"]
                    self.score += score
                    ufo.kill()
                    b.kill()

        # Ship collects orbies
        for orbie in list(self.orbies):
            if (orbie.pos - self.ship.pos).length() < (orbie.r + self.ship.r):
                self.special_energy = min(
                    C.ORBIE_MAX_ENERGY,
                    self.special_energy + C.ORBIE_ENERGY,
                )
                orbie.kill()

        # ── Ship collects repair modules ──────────────────────────────────
        for rm in list(self.repair_modules):
            if (rm.pos - self.ship.pos).length() < (rm.r + self.ship.r):
                if self.lives < C.MAX_LIVES:
                    self.lives += 1
                    self.score_popups.append(
                        [Vec(rm.pos), "+VIDA!", 1.5]
                    )
                rm.kill()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _proximity_mult(self, pos: Vec) -> float:
        dist = (pos - self.ship.pos).length()
        if dist < C.PROXIMITY_MAX_DIST:
            t = 1.0 - (dist / C.PROXIMITY_MAX_DIST)
            return 1.0 + t * (C.PROXIMITY_MAX_MULT - 1.0)
        return 1.0

    def _try_spawn_repair(self, pos: Vec):
        """Roll for a repair module drop at the given position."""
        if random() < C.REPAIR_SPAWN_CHANCE:
            self.spawn_repair_module(pos)

    def split_asteroid(self, ast: Asteroid):
        """Destroy an asteroid, award score, maybe drop a repair module,
        and spawn its smaller fragments."""
        base_score = C.AST_SIZES[ast.size]["score"]
        mult = self._proximity_mult(ast.pos)
        awarded = int(base_score * mult)
        self.score += awarded
        if mult > 1.05:
            self.score_popups.append([Vec(ast.pos), f"{mult:.1f}x", 1.2])

        self._try_spawn_repair(ast.pos)   # ← repair drop chance

        split = C.AST_SIZES[ast.size]["split"]
        pos = Vec(ast.pos)
        frag_legacy = max(0, ast.legacy - 1)
        ast.kill()
        for s in split:
            dirv = rand_unit_vec()
            base_speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX) * 1.2
            vel = dirv * (base_speed / (C.LEGACY_SPEED_MULT ** frag_legacy))
            self.spawn_asteroid(pos, vel, s, frag_legacy)

    def ship_die(self):
        """Remove a life; cancel minigun; signal game over or respawn."""
        self.special_active = False
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True
            return
        self.ship.pos.xy = (C.WIDTH / 2, C.HEIGHT / 2)
        self.ship.vel.xy = (0, 0)
        self.ship.angle = -90
        self.ship.invuln = C.SAFE_SPAWN_TIME
        self.safe = C.SAFE_SPAWN_TIME

    # ── Drawing ───────────────────────────────────────────────────────────

    def draw(self, surf: pg.Surface, font: pg.font.Font):
        """Draw all world entities and delegate HUD rendering."""
        for spr in self.all_sprites:
            spr.draw(surf)

        self.hud.draw(
            surf=surf,
            font=font,
            score=self.score,
            lives=self.lives,
            wave=self.wave,
            dash_cool=self.ship.dash_cool,
            special_energy=self.special_energy,
            special_active=self.special_active,
            score_popups=self.score_popups,
            repair_modules=list(self.repair_modules),
        )