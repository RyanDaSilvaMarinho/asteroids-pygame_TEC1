# ASTEROIDE SINGLEPLAYER v1.0
# This file defines the interactive game entities and their local behaviors.

import math
from random import uniform

import pygame as pg

import config as C
from utils import Vec, angle_to_vec, draw_circle, draw_poly, rand_unit_vec, wrap_pos


class Bullet(pg.sprite.Sprite):
    # Initialize a player bullet with position, velocity, and lifetime.
    def __init__(self, pos: Vec, vel: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.ttl = C.BULLET_TTL
        self.r = C.BULLET_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def update(self, dt: float):
        # Move the bullet, wrap it on screen, and expire it over time.
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        # Draw the bullet on the target surface.
        draw_circle(surf, self.pos, self.r)


class ChargeBullet(pg.sprite.Sprite):
    # Bala carregada: raio proporcional à carga, destrói direto até certo tamanho.
    # power = "S" | "M" | "L" indica qual tier destrói sem fragmentar.
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
    # Initialize a UFO bullet with position, velocity, and lifetime.
    def __init__(self, pos: Vec, vel: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.ttl = C.UFO_BULLET_TTL
        self.r = C.BULLET_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def update(self, dt: float):
        # Move the UFO bullet, wrap it on screen, and expire it over time.
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        # Draw the UFO bullet on the target surface.
        draw_circle(surf, self.pos, self.r)


class Asteroid(pg.sprite.Sprite):
    # Initialize an asteroid with its position, velocity, and size profile.
    def __init__(self, pos: Vec, vel: Vec, size: str, legacy: int = 0):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.legacy = max(0, min(legacy, C.LEGACY_MAX))

        # Cada nível de legacy sobe 1 tier e aumenta a velocidade
        tier_up = {"S": "M", "M": "L", "L": "L"}
        for _ in range(self.legacy):
            size = tier_up[size]
        self.size = size
        self.vel = self.vel * (C.LEGACY_SPEED_MULT**self.legacy)

        self.r = C.AST_SIZES[size]["r"]
        self.poly = self._make_poly()
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def _make_poly(self):
        # Build an irregular polygon outline based on the asteroid size.
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
        # Move the asteroid and wrap it across the screen.
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        # Draw the asteroid outline on the target surface.
        pts = [(self.pos + p) for p in self.poly]
        width = 3 if self.legacy > 0 else 1
        pg.draw.polygon(surf, C.WHITE, pts, width=width)


class Ship(pg.sprite.Sprite):
    # Initialize the player ship and its gameplay state.
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
        self.charge_time = 0.0  # segundos segurando espaço
        self.dash_cool = 0.0
        self.dash_trail: list = []

    def control(self, keys: pg.key.ScancodeWrapper, dt: float):
        # Apply rotation, thrust, and friction from the current input state.
        if keys[pg.K_LEFT]:
            self.angle -= C.SHIP_TURN_SPEED * dt
        if keys[pg.K_RIGHT]:
            self.angle += C.SHIP_TURN_SPEED * dt
        if keys[pg.K_UP]:
            self.vel += angle_to_vec(self.angle) * C.SHIP_THRUST * dt
        self.vel *= C.SHIP_FRICTION

    def fire(self) -> "Bullet | None":
        # Spawn a player bullet when the fire cooldown allows it.
        if self.cool > 0:
            return None
        dirv = angle_to_vec(self.angle)
        pos = self.pos + dirv * (self.r + 6)
        vel = self.vel + dirv * C.SHIP_BULLET_SPEED
        self.cool = C.SHIP_FIRE_RATE
        return Bullet(pos, vel)

    def fire_charged(self) -> "ChargeBullet | None":
        # Dispara bala carregada com power proporcional ao tempo de carga.
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
        # Teleport the ship to a random location and reset its momentum.
        self.pos = Vec(uniform(0, C.WIDTH), uniform(0, C.HEIGHT))
        self.vel.xy = (0, 0)
        self.invuln = 1.0

    def quantum_dash(self) -> bool:
        """Dash quântico: teleporta a nave na direção atual por DASH_DISTANCE.

        Retorna True se o dash foi executado, False se em cooldown.
        """
        if self.dash_cool > 0:
            return False
        old_pos = Vec(self.pos)
        dirv = angle_to_vec(self.angle)
        self.pos += dirv * C.DASH_DISTANCE
        self.pos = wrap_pos(self.pos)
        self.invuln = C.DASH_INVULN
        self.dash_cool = C.DASH_COOLDOWN
        # Gera partículas de rastro entre a posição antiga e a nova
        for i in range(8):
            t = i / 8.0
            p = old_pos + (self.pos - old_pos) * t
            self.dash_trail.append([Vec(p), 0.4])  # (posição, tempo de vida)
        return True

    def update(self, dt: float):
        # Advance cooldowns, move the ship, and wrap it on screen.
        if self.cool > 0:
            self.cool -= dt
        if self.invuln > 0:
            self.invuln -= dt
        if self.dash_cool > 0:
            self.dash_cool -= dt
        # Atualiza partículas do rastro de dash
        self.dash_trail = [[p, t - dt] for p, t in self.dash_trail if t - dt > 0]
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        # Desenha partículas do rastro de dash quântico
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

        # Draw the ship and its temporary invulnerability indicator.
        dirv = angle_to_vec(self.angle)
        left = angle_to_vec(self.angle + 140)
        right = angle_to_vec(self.angle - 140)
        p1 = self.pos + dirv * self.r
        p2 = self.pos + left * self.r * 0.9
        p3 = self.pos + right * self.r * 0.9
        draw_poly(surf, [p1, p2, p3])
        if self.invuln > 0 and int(self.invuln * 10) % 2 == 0:
            draw_circle(surf, self.pos, self.r + 6)

        # Indicador de cooldown do dash quântico (arco ao redor da nave)
        if self.dash_cool > 0:
            frac = self.dash_cool / C.DASH_COOLDOWN
            angle = int(360 * (1.0 - frac))
            rect = pg.Rect(0, 0, (self.r + 10) * 2, (self.r + 10) * 2)
            rect.center = (int(self.pos.x), int(self.pos.y))
            if angle > 0:
                pg.draw.arc(
                    surf,
                    C.DASH_TRAIL_COLOR,
                    rect,
                    math.radians(-90),
                    math.radians(-90 + angle),
                    1,
                )

        # Anel de carga: cor e raio indicam o tier atingido
        if self.charge_time >= C.CHARGE_MIN:
            t = min(self.charge_time, C.CHARGE_MAX)
            if t >= C.CHARGE_TIER_L:
                color = (255, 80, 80)  # vermelho = tier L
                radius = self.r + 14
            elif t >= C.CHARGE_TIER_M:
                color = (255, 200, 50)  # amarelo = tier M
                radius = self.r + 10
            else:
                color = (100, 200, 255)  # azul = tier S
                radius = self.r + 6
            # Pisca quando atingiu o tier máximo da carga atual
            show = True
            if t >= C.CHARGE_TIER_L and int(t * 8) % 2 == 0:
                show = False
            if show:
                pg.draw.circle(
                    surf, color, (int(self.pos.x), int(self.pos.y)), radius, 1
                )


class UFO(pg.sprite.Sprite):
    # Initialize a UFO enemy with its size profile and movement state.
    def __init__(self, pos: Vec, small: bool):
        super().__init__()
        self.pos = Vec(pos)
        self.small = small
        profile = C.UFO_SMALL if small else C.UFO_BIG
        self.r = profile["r"]
        self.aim = profile["aim"]
        self.speed = C.UFO_SPEED
        self.cool = C.UFO_FIRE_EVERY
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)
        self.dir = Vec(1, 0) if uniform(0, 1) < 0.5 else Vec(-1, 0)

    def update(self, dt: float):
        # Move the UFO, advance its fire cooldown, and remove it off screen.
        self.pos += self.dir * self.speed * dt
        self.cool -= dt
        if self.pos.x < -self.r * 2 or self.pos.x > C.WIDTH + self.r * 2:
            self.kill()
        self.rect.center = self.pos

    def fire_at(self, target_pos: Vec) -> "UfoBullet | None":
        # Fire a bullet toward the ship with accuracy based on the UFO type.
        if self.cool > 0:
            return None
        aim_vec = Vec(target_pos) - self.pos
        if aim_vec.length_squared() == 0:
            aim_vec = self.dir.normalize()
        else:
            aim_vec = aim_vec.normalize()
        max_error = (1.0 - self.aim) * 60.0
        shot_dir = aim_vec.rotate(uniform(-max_error, max_error))
        self.cool = C.UFO_FIRE_EVERY
        spawn_pos = self.pos + shot_dir * (self.r + 6)
        vel = shot_dir * C.UFO_BULLET_SPEED
        return UfoBullet(spawn_pos, vel)

    def draw(self, surf: pg.Surface):
        # Draw the UFO body on the target surface.
        w, h = self.r * 2, self.r
        rect = pg.Rect(0, 0, w, h)
        rect.center = self.pos
        pg.draw.ellipse(surf, C.WHITE, rect, width=1)
        cup = pg.Rect(0, 0, w * 0.5, h * 0.7)
        cup.center = (self.pos.x, self.pos.y - h * 0.3)
        pg.draw.ellipse(surf, C.WHITE, cup, width=1)


class Orbie(pg.sprite.Sprite):
    """Colecionável de energia que deriva lentamente pela tela.

    Ao ser tocado pela nave, adiciona ORBIE_ENERGY segundos à barra especial.
    Visualmente: anel pulsante externo + losango interno + ponto central.
    """

    def __init__(self, pos: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = rand_unit_vec() * C.ORBIE_SPEED
        self.r = C.ORBIE_RADIUS
        self.pulse = 0.0  # fase da animação de pulso
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def update(self, dt: float):
        # Move o orbie, envolve na tela e avança a fase de pulso.
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.pulse += dt * 4.0
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        # Desenha o orbie: anel externo pulsante, losango e ponto central.
        cx, cy = int(self.pos.x), int(self.pos.y)
        pulse_r = int(self.r + math.sin(self.pulse) * 2.5)

        # Anel externo pulsante
        pg.draw.circle(surf, C.ORBIE_COLOR, (cx, cy), pulse_r, 1)

        # Losango interno
        inner = self.r - 3
        diamond = [
            (cx, cy - inner),
            (cx + inner, cy),
            (cx, cy + inner),
            (cx - inner, cy),
        ]
        pg.draw.polygon(surf, C.ORBIE_COLOR, diamond, 1)

        # Ponto central sólido
        pg.draw.circle(surf, C.ORBIE_COLOR, (cx, cy), 2)
