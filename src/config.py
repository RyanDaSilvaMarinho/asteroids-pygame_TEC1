# ASTEROIDE SINGLEPLAYER v1.0
# This file stores the gameplay, rendering, and balancing constants.

WIDTH = 960
HEIGHT = 720
FPS = 60

START_LIVES = 3
MAX_LIVES = 3               # Limite máximo de vidas (cap da recuperação)
SAFE_SPAWN_TIME = 2.0
WAVE_DELAY = 2.0

SHIP_RADIUS = 15
SHIP_TURN_SPEED = 220.0
SHIP_THRUST = 220.0
SHIP_FRICTION = 0.995
SHIP_FIRE_RATE = 0.2
SHIP_BULLET_SPEED = 420.0
HYPERSPACE_COST = 250

DASH_DISTANCE = 120.0
DASH_COOLDOWN = 3.5
DASH_INVULN = 0.3
DASH_TRAIL_COLOR = (0, 200, 255)

AST_VEL_MIN = 30.0
AST_VEL_MAX = 90.0
AST_SIZES = {
    "L": {"r": 46, "score": 20, "split": ["M", "M"]},
    "M": {"r": 24, "score": 50, "split": ["S", "S"]},
    "S": {"r": 12, "score": 100, "split": []},
}

BULLET_RADIUS = 2
BULLET_TTL = 1.0
MAX_BULLETS = 4

# Tiro carregado
CHARGE_MIN = 0.4
CHARGE_TIER_S = 0.4
CHARGE_TIER_M = 1.0
CHARGE_TIER_L = 2.0
CHARGE_MAX = 2.0
CHARGE_BULLET_SPEED = 420.0

# Legado de wave
LEGACY_MAX = 1
LEGACY_SPEED_MULT = 1.4

# Bônus de proximidade
PROXIMITY_MAX_DIST = 180
PROXIMITY_MAX_MULT = 2.0

UFO_SPAWN_EVERY = 15.0
UFO_SPEED = 80.0
UFO_FIRE_EVERY = 1.2
UFO_BULLET_SPEED = 260.0
UFO_BULLET_TTL = 1.8
UFO_BIG = {"r": 18, "score": 200, "aim": 0.2}
UFO_SMALL = {"r": 12, "score": 1000, "aim": 0.6}

WHITE = (240, 240, 240)
GRAY = (120, 120, 120)
BLACK = (0, 0, 0)

RANDOM_SEED = None

GAME_OVER_FADE_DURATION = 1.5

# ── Orbie / Habilidade Especial ───────────────────────────────────────────
ORBIE_RADIUS = 8
ORBIE_ENERGY = 3.0
ORBIE_MAX_ENERGY = 30.0
ORBIE_SPAWN_EVERY = 7.0
ORBIE_MAX_ON_SCREEN = 3
ORBIE_SPEED = 35.0
ORBIE_COLOR = (80, 220, 255)
ORBIE_FULL_COLOR = (255, 220, 60)
ORBIE_BAR_BG = (20, 55, 80)

SPECIAL_MINIGUN_RATE = 0.07
SPECIAL_DRAIN_RATE = 1.0
SPECIAL_RADIAL_BULLETS = 24

# ── Módulo de Reparo (item de recuperação de vida) ────────────────────────
# Surge ao destruir asteroides com probabilidade REPAIR_SPAWN_CHANCE.
# Fica na tela por REPAIR_TTL segundos; pisca nos últimos REPAIR_BLINK_TIME s.
# Coletar recupera 1 vida, respeitando MAX_LIVES.

REPAIR_SPAWN_CHANCE = 0.18   # 18% de chance por asteroide destruído
REPAIR_TTL = 6.0    # segundos até desaparecer
REPAIR_BLINK_TIME = 2.0    # inicia o piscar nos últimos N segundos
REPAIR_RADIUS = 10     # raio de colisão e visual
REPAIR_SPEED = 22.0   # velocidade de deriva (px/s)
REPAIR_COLOR = (80, 255, 130)   # verde claro
REPAIR_ICON_SIZE = 7      # metade do comprimento do braço da cruz