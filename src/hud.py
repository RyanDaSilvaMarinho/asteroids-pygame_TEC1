# ASTEROIDE SINGLEPLAYER v1.0
# This file renders all heads-up display (HUD) elements during gameplay.

import pygame as pg

import config as C


class HUD:
    """Responsible for drawing all on-screen UI elements during a match.

    Receives world-state data on each draw() call; holds no game state itself.
    """

    def draw(
        self,
        surf: pg.Surface,
        font: pg.font.Font,
        score: int,
        lives: int,
        wave: int,
        dash_cool: float,
        special_energy: float,
        special_active: bool,
        score_popups: list,
        repair_modules,
    ):
        """Draw score, lives, wave counter, dash indicator, special bar,
        score pop-ups, and the repair-module HUD hint."""

        self._draw_score_popups(surf, font, score_popups)
        self._draw_separator(surf)
        self._draw_main_stats(surf, font, score, lives, wave)
        self._draw_dash_indicator(surf, font, dash_cool)
        self._draw_special_bar(surf, font, special_energy, special_active)
        self._draw_repair_hint(surf, font, repair_modules)
        self._draw_life_icons(surf, lives)

    # ── Private drawing helpers ────────────────────────────────────────────

    def _draw_separator(self, surf: pg.Surface):
        pg.draw.line(surf, (60, 60, 60), (0, 50), (C.WIDTH, 50), width=1)

    def _draw_main_stats(
        self, surf: pg.Surface, font: pg.font.Font,
        score: int, lives: int, wave: int,
    ):
        txt = f"SCORE {score:06d}   LIVES {lives}   WAVE {wave}"
        label = font.render(txt, True, C.WHITE)
        surf.blit(label, (10, 10))

    def _draw_dash_indicator(self, surf: pg.Surface, font: pg.font.Font, dash_cool: float):
        if dash_cool > 0:
            label = font.render(f"DASH  {dash_cool:.1f}s", True, C.GRAY)
        else:
            label = font.render("DASH  PRONTO", True, C.DASH_TRAIL_COLOR)
        surf.blit(label, (10, 32))

    def _draw_special_bar(
        self, surf: pg.Surface, font: pg.font.Font,
        energy: float, active: bool,
    ):
        bar_w, bar_h = 200, 10
        bar_x = C.WIDTH - bar_w - 20
        bar_y = 20

        pg.draw.rect(surf, C.ORBIE_BAR_BG, (bar_x, bar_y, bar_w, bar_h))

        fill = int(bar_w * (energy / C.ORBIE_MAX_ENERGY))
        if fill > 0:
            is_full = energy >= C.ORBIE_MAX_ENERGY
            bar_color = C.ORBIE_FULL_COLOR if is_full else C.ORBIE_COLOR
            if active and (pg.time.get_ticks() // 80) % 2 == 0:
                bar_color = C.WHITE
            pg.draw.rect(surf, bar_color, (bar_x, bar_y, fill, bar_h))

        pg.draw.rect(surf, C.WHITE, (bar_x, bar_y, bar_w, bar_h), 1)

        esp_lbl = font.render("ESP", True, C.ORBIE_COLOR)
        surf.blit(esp_lbl, (bar_x - esp_lbl.get_width() - 8, bar_y - 2))

        if active and (pg.time.get_ticks() // 200) % 2 == 0:
            mg_lbl = font.render("MINIGUN!", True, C.ORBIE_COLOR)
            surf.blit(
                mg_lbl,
                (bar_x + bar_w // 2 - mg_lbl.get_width() // 2, bar_y + bar_h + 4),
            )
        elif energy >= C.ORBIE_MAX_ENERGY and not active:
            full_lbl = font.render("CHEIO! [CTRL]", True, C.ORBIE_FULL_COLOR)
            surf.blit(
                full_lbl,
                (bar_x + bar_w // 2 - full_lbl.get_width() // 2, bar_y + bar_h + 4),
            )

    def _draw_score_popups(self, surf: pg.Surface, font: pg.font.Font, popups: list):
        for pos, txt, ttl in popups:
            alpha = min(255, int(255 * (ttl / 1.2)))
            label = font.render(txt, True, (255, 220, 60))
            label.set_alpha(alpha)
            surf.blit(
                label,
                (int(pos.x) - label.get_width() // 2,
                 int(pos.y) - label.get_height() // 2),
            )

    def _draw_repair_hint(self, surf: pg.Surface, font: pg.font.Font, repair_modules):
        """Show a blinking 'REPARO!' hint when any module is on screen."""
        if not repair_modules:
            return
        # Only show hint when at least one module is expiring (urgency cue)
        expiring = any(rm.is_expiring for rm in repair_modules)
        if expiring and (pg.time.get_ticks() // 250) % 2 == 0:
            lbl = font.render("[ REPARO! ]", True, C.REPAIR_COLOR)
            surf.blit(lbl, (C.WIDTH // 2 - lbl.get_width() // 2, 8))

    def _draw_life_icons(self, surf: pg.Surface, lives: int):
        """Draw small ship-shaped icons representing remaining lives."""
        icon_x = 10
        icon_y = C.HEIGHT - 28
        spacing = 22
        for i in range(lives):
            cx = icon_x + i * spacing
            cy = icon_y
            # Mini triangle (pointing up)
            pts = [
                (cx, cy - 7),
                (cx - 5, cy + 5),
                (cx + 5, cy + 5),
            ]
            pg.draw.polygon(surf, C.REPAIR_COLOR, pts, 1)