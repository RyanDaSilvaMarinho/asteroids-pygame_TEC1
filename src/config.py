# ASTEROIDE SINGLEPLAYER v1.0
# This file stores the gameplay, rendering, and balancing constants.

WIDTH = 960
HEIGHT = 720
FPS = 60

START_LIVES = 3
SAFE_SPAWN_TIME = 2.0
WAVE_DELAY = 2.0

SHIP_RADIUS = 15
SHIP_TURN_SPEED = 220.0
SHIP_THRUST = 220.0
SHIP_FRICTION = 0.995
SHIP_FIRE_RATE = 0.2
SHIP_BULLET_SPEED = 420.0
HYPERSPACE_COST = 250

AST_VEL_MIN = 30.0
AST_VEL_MAX = 90.0
AST_SIZES = {
    "L": {"r": 46, "score": 20,  "split": ["M", "M"]},
    "M": {"r": 24, "score": 50,  "split": ["S", "S"]},
    "S": {"r": 12, "score": 100, "split": []},
}

BULLET_RADIUS = 2
BULLET_TTL = 1.0
MAX_BULLETS = 4

UFO_SPAWN_EVERY  = 15.0
UFO_SPEED        = 80.0
UFO_FIRE_EVERY   = 1.2
UFO_BULLET_SPEED = 260.0
UFO_BULLET_TTL   = 1.8
UFO_BIG          = {"r": 18, "score": 200,  "aim": 0.2}
UFO_SMALL        = {"r": 12, "score": 1000, "aim": 0.6}

WHITE = (240, 240, 240)
GRAY  = (120, 120, 120)
BLACK = (0, 0, 0)

RANDOM_SEED = None

# Duração do fade-in da tela de game over (segundos)
GAME_OVER_FADE_DURATION = 1.5

# ── Orbie / Habilidade Especial ───────────────────────────────────────────
# Cada orbie coletado adiciona ORBIE_ENERGY segundos à barra especial.
# O limite máximo é ORBIE_MAX_ENERGY (= 10 orbies × 3 s = 30 s).

ORBIE_RADIUS        = 8
ORBIE_ENERGY        = 3.0     # segundos adicionados por orbie coletado
ORBIE_MAX_ENERGY    = 30.0    # 10 orbies = barra cheia
ORBIE_SPAWN_EVERY   = 7.0     # intervalo entre tentativas de spawn (s)
ORBIE_MAX_ON_SCREEN = 3       # máximo de orbies simultâneos no campo
ORBIE_SPEED         = 35.0    # velocidade de deriva (px/s)
ORBIE_COLOR         = (80, 220, 255)   # ciano-azulado
ORBIE_FULL_COLOR    = (255, 220, 60)   # dourado quando a barra está cheia
ORBIE_BAR_BG        = (20, 55, 80)     # fundo da barra no HUD

# Modo minigun (barra parcial): disparos contínuos enquanto Ctrl pressionado.
SPECIAL_MINIGUN_RATE = 0.07   # segundos entre cada tiro do minigun
SPECIAL_DRAIN_RATE   = 1.0    # energia drenada por segundo no modo minigun

# Modo radial (barra cheia): disparo instantâneo em múltiplas direções.
SPECIAL_RADIAL_BULLETS = 24   # número de direções do disparo radial