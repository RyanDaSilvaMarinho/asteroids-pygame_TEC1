# ASTEROIDE SINGLEPLAYER v1.0
# This file manages the application loop, scenes, input handling, and screen drawing.

import random
import sys
from dataclasses import dataclass

import pygame as pg

import config as C
from world import World
from utils import text


@dataclass
class Scene:
    name: str


class Game:
    """Top-level application controller.

    Owns the display, clock, fonts, and the active scene.
    Delegates all gameplay logic to the World instance.
    """

    def __init__(self):
        pg.init()
        if C.RANDOM_SEED is not None:
            random.seed(C.RANDOM_SEED)
        self.screen = pg.display.set_mode((C.WIDTH, C.HEIGHT))
        pg.display.set_caption("Asteroides")
        self.clock = pg.time.Clock()
        self.font = pg.font.SysFont("consolas", 20)
        self.big = pg.font.SysFont("consolas", 48)
        self.scene = Scene("menu")
        self.world = World()
        self.final_score = 0
        self.go_fade = 0.0

    def run(self):
        """Main loop: process events, update the active scene, render."""
        while True:
            dt = self.clock.tick(C.FPS) / 1000.0

            for e in pg.event.get():
                if e.type == pg.QUIT:
                    pg.quit()
                    sys.exit(0)

                if e.type == pg.KEYDOWN:
                    if e.key == pg.K_ESCAPE:
                        if self.scene.name == "game_over":
                            self.scene = Scene("menu")
                        else:
                            pg.quit()
                            sys.exit(0)

                    elif self.scene.name == "play":
                        if e.key == pg.K_LSHIFT:
                            self.world.try_dash()
                        if e.key in (pg.K_LCTRL, pg.K_RCTRL):
                            self.world.activate_special()

                    elif self.scene.name == "menu":
                        self.world = World()
                        self.scene = Scene("play")

                    elif self.scene.name == "game_over":
                        if e.key in (pg.K_RETURN, pg.K_SPACE):
                            self.world = World()
                            self.go_fade = 0.0
                            self.scene = Scene("play")

                elif e.type == pg.KEYUP:
                    if self.scene.name == "play":
                        if e.key == pg.K_SPACE:
                            if not self.world.try_fire_charged():
                                self.world.ship.charge_time = 0.0
                                self.world.try_fire()
                        if e.key in (pg.K_LCTRL, pg.K_RCTRL):
                            self.world.deactivate_special()

            keys = pg.key.get_pressed()
            self.screen.fill(C.BLACK)

            if self.scene.name == "menu":
                self.draw_menu()

            elif self.scene.name == "play":
                self.world.update(dt, keys)
                self.world.draw(self.screen, self.font)
                if self.world.game_over:
                    self.final_score = self.world.score
                    self.go_fade = 0.0
                    self.scene = Scene("game_over")

            elif self.scene.name == "game_over":
                self.go_fade += dt
                self.draw_game_over()

            pg.display.flip()

    def draw_game_over(self):
        """Fade-in game over screen with final score and restart instructions."""
        alpha = min(255, int(255 * self.go_fade / C.GAME_OVER_FADE_DURATION))

        overlay = pg.Surface((C.WIDTH, C.HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))

        if alpha < 60:
            return

        text(self.screen, self.big, "GAME OVER",
             C.WIDTH // 2 - 130, C.HEIGHT // 2 - 100)
        text(self.screen, self.font,
             f"Pontuacao final: {self.final_score:06d}",
             C.WIDTH // 2 - 110, C.HEIGHT // 2 - 20)
        text(self.screen, self.font,
             "Enter / Espaco: jogar novamente",
             C.WIDTH // 2 - 150, C.HEIGHT // 2 + 40)
        text(self.screen, self.font,
             "ESC: menu principal",
             C.WIDTH // 2 - 90, C.HEIGHT // 2 + 80)

    def draw_menu(self):
        """Draw the title screen and control instructions."""
        text(self.screen, self.big, "ASTEROIDS",
             C.WIDTH // 2 - 150, 160)
        text(self.screen, self.font,
             "Setas: virar / acelerar     Espaco: tiro",
             195, 280)
        text(self.screen, self.font,
             "Shift: dash quantico (cd 3.5s)    Ctrl: especial",
             155, 315)
        text(self.screen, self.font,
             "Barra parcial = minigun  |  barra cheia = radial",
             155, 350)
        text(self.screen, self.font,
             "Colete os orbies ciano para carregar a barra especial!",
             155, 385)
        text(self.screen, self.font,
             "Modulos de reparo (verde) recuperam 1 vida!",
             195, 420)
        text(self.screen, self.font,
             "Pressione qualquer tecla para comecar...", 225, 460)