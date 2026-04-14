# ASTEROIDE SINGLEPLAYER v1.0
# This file coordinates world state, spawning, collisions, scoring, and progression.

import math
from random import uniform

import pygame as pg

import config as C
from sprites import Asteroid, Bullet, ChargeBullet, Orbie, Ship, UFO
from utils import Vec, angle_to_vec, rand_edge_pos, rand_unit_vec


class World:
    # Initialize the world state, entity groups, timers, and player progress.
    def __init__(self):
        self.ship        = Ship(Vec(C.WIDTH / 2, C.HEIGHT / 2))
        self.bullets     = pg.sprite.Group()
        self.ufo_bullets = pg.sprite.Group()
        self.charge_bullets = pg.sprite.Group()
        self.asteroids   = pg.sprite.Group()
        self.ufos        = pg.sprite.Group()
        self.orbies      = pg.sprite.Group()
        self.all_sprites = pg.sprite.Group(self.ship)

        self.score     = 0
        self.lives     = C.START_LIVES
        self.wave      = 0
        self.wave_cool = C.WAVE_DELAY
        self.safe      = C.SAFE_SPAWN_TIME
        self.ufo_timer = C.UFO_SPAWN_EVERY
        self.game_over = False   # Sinaliza fim de jogo para a cena principal

        # ── Popups de bônus de proximidade ────────────────────────────────
        # Cada entrada: [pos, texto, tempo_restante]
        self.score_popups: list = []

        # ── Habilidade especial ────────────────────────────────────────────
        self.orbie_timer    = C.ORBIE_SPAWN_EVERY
        self.special_energy = 0.0    # energia acumulada (em segundos, 0–30)
        self.special_active = False  # True enquanto o modo minigun estiver ativo
        self.minigun_cool   = 0.0    # contador de cooldown entre tiros do minigun

    # ── Waves e spawning ──────────────────────────────────────────────────

    def start_wave(self):
        # Spawn a new asteroid wave with difficulty based on the current round.
        self.wave += 1

        # Promove asteroides que sobreviveram à wave anterior
        survivors = list(self.asteroids)
        for ast in survivors:
            new_legacy = min(ast.legacy + 1, C.LEGACY_MAX)
            pos = Vec(ast.pos)
            vel = Vec(ast.vel)
            # Guarda o size original (antes do tier-up do legacy atual)
            # Para promover corretamente, passamos o size base e legacy novo
            size_base = ast.size  # já está upado; reverter tier para recalcular
            # Revertemos o tier para o original antes de repassar ao construtor
            tier_down = {"M": "S", "L": "M"}
            for _ in range(ast.legacy):
                size_base = tier_down.get(size_base, size_base)
            # Velocidade base (sem o multiplicador de legacy atual)
            vel_base = vel / (C.LEGACY_SPEED_MULT ** ast.legacy)
            ast.kill()
            self.spawn_asteroid(pos, vel_base, size_base, new_legacy)

        count = 3 + self.wave
        for _ in range(count):
            pos = rand_edge_pos()
            while (pos - self.ship.pos).length() < 150:
                pos = rand_edge_pos()
            ang   = uniform(0, math.tau)
            speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX)
            vel   = Vec(math.cos(ang), math.sin(ang)) * speed
            self.spawn_asteroid(pos, vel, "L")

    def spawn_asteroid(self, pos: Vec, vel: Vec, size: str, legacy: int = 0):
        # Create an asteroid and register it in the world groups.
        a = Asteroid(pos, vel, size, legacy)
        self.asteroids.add(a)
        self.all_sprites.add(a)

    def spawn_ufo(self):
        # Spawn a single UFO at a screen edge and send it across the playfield.
        if self.ufos:
            return
        small = uniform(0, 1) < 0.5
        y     = uniform(0, C.HEIGHT)
        x     = 0 if uniform(0, 1) < 0.5 else C.WIDTH
        ufo   = UFO(Vec(x, y), small)
        ufo.dir.xy = (1, 0) if x == 0 else (-1, 0)
        self.ufos.add(ufo)
        self.all_sprites.add(ufo)

    def spawn_orbie(self):
        # Cria um orbie em posição aleatória, longe da nave.
        for _ in range(15):
            pos = Vec(uniform(0, C.WIDTH), uniform(0, C.HEIGHT))
            if (pos - self.ship.pos).length() > 150:
                break
        o = Orbie(pos)
        self.orbies.add(o)
        self.all_sprites.add(o)

    # ── Ações do jogador ──────────────────────────────────────────────────

    def ufo_try_fire(self):
        # Let every active UFO attempt to fire at the ship.
        for ufo in self.ufos:
            bullet = ufo.fire_at(self.ship.pos)
            if bullet:
                self.ufo_bullets.add(bullet)
                self.all_sprites.add(bullet)

    def try_fire(self):
        # Fire a player bullet when the bullet cap allows it.
        if len(self.bullets) >= C.MAX_BULLETS:
            return
        b = self.ship.fire()
        if b:
            self.bullets.add(b)
            self.all_sprites.add(b)

    def try_fire_charged(self) -> bool:
        # Dispara a bala carregada se não houver outra na tela. Retorna True se disparou.
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
        # Trigger the ship hyperspace action and apply its score penalty.
        self.ship.hyperspace()
        self.score = max(0, self.score - C.HYPERSPACE_COST)

    # ── Habilidade especial ───────────────────────────────────────────────

    def activate_special(self):
        """Ativado no KEYDOWN de Ctrl.

        Barra cheia  → disparo radial instantâneo (consume tudo).
        Barra parcial → ativa o modo minigun (continua enquanto Ctrl pressionado).
        """
        if self.special_energy <= 0:
            return

        if self.special_energy >= C.ORBIE_MAX_ENERGY:
            # ── Modo radial (barra cheia) ──────────────────────────────────
            self._fire_radial()
            self.special_energy = 0.0
        else:
            # ── Modo minigun (barra parcial) ──────────────────────────────
            self.special_active = True
            self.minigun_cool   = 0.0   # dispara imediatamente na ativação

    def deactivate_special(self):
        """Ativado no KEYUP de Ctrl — encerra o minigun."""
        self.special_active = False

    def _fire_minigun(self):
        # Dispara um único projétil do minigun na direção atual da nave.
        dirv = angle_to_vec(self.ship.angle)
        pos  = self.ship.pos + dirv * (self.ship.r + 6)
        vel  = self.ship.vel + dirv * C.SHIP_BULLET_SPEED
        b    = Bullet(pos, vel)
        self.bullets.add(b)
        self.all_sprites.add(b)

    def _fire_radial(self):
        # Dispara SPECIAL_RADIAL_BULLETS projéteis em todas as direções.
        n = C.SPECIAL_RADIAL_BULLETS
        for i in range(n):
            angle = (360.0 / n) * i
            dirv  = angle_to_vec(angle)
            pos   = self.ship.pos + dirv * (self.ship.r + 6)
            vel   = self.ship.vel + dirv * C.SHIP_BULLET_SPEED
            b     = Bullet(pos, vel)
            self.bullets.add(b)
            self.all_sprites.add(b)

    # ── Loop principal ────────────────────────────────────────────────────

    def update(self, dt: float, keys):
        # Update the world simulation, timers, enemy behavior, and progression.
        self.ship.control(keys, dt)

        # Acumula carga enquanto espaço estiver pressionado (teto em CHARGE_MAX)
        if keys[pg.K_SPACE]:
            self.ship.charge_time = min(
                self.ship.charge_time + dt, C.CHARGE_MAX
            )

        self.all_sprites.update(dt)

        if self.safe > 0:
            self.safe -= dt
            self.ship.invuln = 0.5

        # UFO
        if self.ufos:
            self.ufo_try_fire()
        else:
            self.ufo_timer -= dt
        if not self.ufos and self.ufo_timer <= 0:
            self.spawn_ufo()
            self.ufo_timer = C.UFO_SPAWN_EVERY

        # Spawn de orbies
        self.orbie_timer -= dt
        if self.orbie_timer <= 0:
            if len(self.orbies) < C.ORBIE_MAX_ON_SCREEN:
                self.spawn_orbie()
            self.orbie_timer = C.ORBIE_SPAWN_EVERY

        # Modo minigun: drena energia e dispara enquanto ativo
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

        # Atualiza popups de bônus
        self.score_popups = [
            [p[0] + Vec(0, -30) * dt, p[1], p[2] - dt]
            for p in self.score_popups if p[2] > 0
        ]

        if not self.asteroids and self.wave_cool <= 0:
            self.start_wave()
            self.wave_cool = C.WAVE_DELAY
        elif not self.asteroids:
            self.wave_cool -= dt

    # ── Colisões ──────────────────────────────────────────────────────────

    def handle_collisions(self):
        # Resolve collisions between bullets, asteroids, UFOs, and the ship.

        # Balas do jogador vs asteroides
        hits = pg.sprite.groupcollide(
            self.asteroids, self.bullets, False, True,
            collided=lambda a, b: (a.pos - b.pos).length() < a.r,
        )
        for ast in hits:
            self.split_asteroid(ast)

        # Bala carregada vs asteroides
        # Se o tier da bala >= tamanho do asteroide: destrói direto (sem fragmentar).
        # Senão: fragmenta normalmente e a bala some.
        TIER_ORDER = {"S": 0, "M": 1, "L": 2}
        charge_hits = pg.sprite.groupcollide(
            self.asteroids, self.charge_bullets, False, False,
            collided=lambda a, b: (a.pos - b.pos).length() < a.r,
        )
        for ast, bullets_hit in charge_hits.items():
            b = bullets_hit[0]
            if TIER_ORDER[b.power] >= TIER_ORDER[ast.size]:
                # Destrói direto — aplica bônus de proximidade manualmente
                base  = C.AST_SIZES[ast.size]["score"]
                mult  = self._proximity_mult(ast.pos)
                awarded = int(base * mult)
                self.score += awarded
                if mult > 1.05:
                    self.score_popups.append([Vec(ast.pos), f"{mult:.1f}x", 1.2])
                ast.kill()
                b.kill()
            else:
                # Asteroide maior que o tier: fragmenta normalmente, bala some
                self.split_asteroid(ast)
                b.kill()

        # Balas de UFO vs asteroides
        ufo_hits = pg.sprite.groupcollide(
            self.asteroids, self.ufo_bullets, False, True,
            collided=lambda a, b: (a.pos - b.pos).length() < a.r,
        )
        for ast in ufo_hits:
            self.split_asteroid(ast)

        # Nave vs asteroides / UFOs / balas de UFO
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

        # Balas do jogador vs UFOs
        for ufo in list(self.ufos):
            for b in list(self.bullets):
                if (ufo.pos - b.pos).length() < (ufo.r + b.r):
                    score = (C.UFO_SMALL["score"] if ufo.small
                             else C.UFO_BIG["score"])
                    self.score += score
                    ufo.kill()
                    b.kill()

        # Bala carregada vs UFOs
        for ufo in list(self.ufos):
            for b in list(self.charge_bullets):
                if (ufo.pos - b.pos).length() < (ufo.r + b.r):
                    score = (C.UFO_SMALL["score"] if ufo.small
                             else C.UFO_BIG["score"])
                    self.score += score
                    ufo.kill()
                    b.kill()

        # Nave coleta orbies
        for orbie in list(self.orbies):
            if (orbie.pos - self.ship.pos).length() < (orbie.r + self.ship.r):
                self.special_energy = min(
                    C.ORBIE_MAX_ENERGY,
                    self.special_energy + C.ORBIE_ENERGY,
                )
                orbie.kill()

    def _proximity_mult(self, pos: Vec) -> float:
        # Retorna o multiplicador de pontos baseado na distância nave↔pos.
        dist = (pos - self.ship.pos).length()
        if dist < C.PROXIMITY_MAX_DIST:
            t = 1.0 - (dist / C.PROXIMITY_MAX_DIST)
            return 1.0 + t * (C.PROXIMITY_MAX_MULT - 1.0)
        return 1.0

    def split_asteroid(self, ast: Asteroid):
        # Destroy an asteroid, award score, and spawn its smaller fragments.
        base_score = C.AST_SIZES[ast.size]["score"]
        mult       = self._proximity_mult(ast.pos)
        awarded    = int(base_score * mult)
        self.score += awarded
        if mult > 1.05:
            self.score_popups.append([Vec(ast.pos), f"{mult:.1f}x", 1.2])

        split       = C.AST_SIZES[ast.size]["split"]
        pos         = Vec(ast.pos)
        frag_legacy = max(0, ast.legacy - 1)
        ast.kill()
        for s in split:
            dirv       = rand_unit_vec()
            base_speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX) * 1.2
            vel = dirv * (base_speed / (C.LEGACY_SPEED_MULT ** frag_legacy))
            self.spawn_asteroid(pos, vel, s, frag_legacy)

    def ship_die(self):
        # Remove uma vida; cancela minigun, sinaliza game over ou reposiciona.
        self.special_active = False   # encerra o minigun na morte
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True     # Game.run() detecta e muda de cena
            return
        self.ship.pos.xy    = (C.WIDTH / 2, C.HEIGHT / 2)
        self.ship.vel.xy    = (0, 0)
        self.ship.angle     = -90
        self.ship.invuln    = C.SAFE_SPAWN_TIME
        self.safe           = C.SAFE_SPAWN_TIME

    # ── Desenho ───────────────────────────────────────────────────────────

    def draw(self, surf: pg.Surface, font: pg.font.Font):
        # Draw all world entities and the current HUD information.
        for spr in self.all_sprites:
            spr.draw(surf)

        # Popups de bônus de proximidade
        for pos, txt, ttl in self.score_popups:
            alpha  = min(255, int(255 * (ttl / 1.2)))
            color  = (255, 220, 60)
            label  = font.render(txt, True, color)
            label.set_alpha(alpha)
            surf.blit(label, (int(pos.x) - label.get_width() // 2,
                               int(pos.y) - label.get_height() // 2))

        self._draw_hud(surf, font)

    def _draw_hud(self, surf: pg.Surface, font: pg.font.Font):
        # Desenha pontuação, vidas, wave e barra especial.

        # ── Linha de separação ──────────────────────────────────────────
        pg.draw.line(surf, (60, 60, 60), (0, 50), (C.WIDTH, 50), width=1)

        # ── Score / lives / wave (esquerda) ────────────────────────────
        txt   = f"SCORE {self.score:06d}   LIVES {self.lives}   WAVE {self.wave}"
        label = font.render(txt, True, C.WHITE)
        surf.blit(label, (10, 10))

        # ── Barra especial (direita do HUD) ────────────────────────────
        bar_w, bar_h = 200, 10
        bar_x = C.WIDTH - bar_w - 20
        bar_y = 20

        # Fundo da barra
        pg.draw.rect(surf, C.ORBIE_BAR_BG, (bar_x, bar_y, bar_w, bar_h))

        # Preenchimento proporcional à energia acumulada
        fill = int(bar_w * (self.special_energy / C.ORBIE_MAX_ENERGY))
        if fill > 0:
            is_full   = self.special_energy >= C.ORBIE_MAX_ENERGY
            bar_color = C.ORBIE_FULL_COLOR if is_full else C.ORBIE_COLOR
            # Pisca quando o minigun está ativo
            if self.special_active and (pg.time.get_ticks() // 80) % 2 == 0:
                bar_color = C.WHITE
            pg.draw.rect(surf, bar_color, (bar_x, bar_y, fill, bar_h))

        # Borda da barra
        pg.draw.rect(surf, C.WHITE, (bar_x, bar_y, bar_w, bar_h), 1)

        # Rótulo "ESP" à esquerda da barra
        esp_lbl = font.render("ESP", True, C.ORBIE_COLOR)
        surf.blit(esp_lbl, (bar_x - esp_lbl.get_width() - 8, bar_y - 2))

        # Indicador de modo: MINIGUN! piscando quando ativo
        if self.special_active and (pg.time.get_ticks() // 200) % 2 == 0:
            mg_lbl = font.render("MINIGUN!", True, C.ORBIE_COLOR)
            surf.blit(mg_lbl, (bar_x + bar_w // 2 - mg_lbl.get_width() // 2,
                                bar_y + bar_h + 4))

        # Indicador CHEIO! quando barra atinge o máximo e não está em uso
        elif self.special_energy >= C.ORBIE_MAX_ENERGY and not self.special_active:
            full_lbl = font.render("CHEIO! [CTRL]", True, C.ORBIE_FULL_COLOR)
            surf.blit(full_lbl, (bar_x + bar_w // 2 - full_lbl.get_width() // 2,
                                  bar_y + bar_h + 4))