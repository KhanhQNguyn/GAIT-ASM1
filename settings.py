# ============================================================================
# settings.py
# Purpose
#   Central place for all constants and tuning values.
#   You can tweak speeds, radii, and counts here without touching logic.
# Reading guide
#   Each variable has a short note so you know what it controls.
# ============================================================================

# Window size in pixels
WIDTH, HEIGHT = 1920, 1080

# Target frames per second for the game loop
FPS = 60

# Colors as RGB tuples. Used by drawing code for the UI and agents.
BG    = (28, 33, 38)     # background color
WHITE = (240, 240, 240)  # text and highlights
GREEN = (90, 220, 120)   # frog color
BLUE  = (120, 180, 250)  # bubble color
YELLOW= (250, 225, 120)  # fly color when flocking or idle
PURPLE= (185, 120, 250)  # fly color when fleeing
RED   = (232, 88, 88)    # health hearts
MUTED = (180, 188, 196)  # hint text

# Frog setup
FROG_RADIUS = 16          # draw size and collision size for the frog
FROG_SPEED  = 200.0       # top speed for the frog in pixels per second
HURT_INVULN = 1.0         # seconds of temporary invulnerability after damage

# Bubble setup
BUBBLE_RADIUS   = 8       # visual radius and collision radius
BUBBLE_SPEED    = 380.0   # how fast the bubble travels
BUBBLE_LIFETIME = 2.0     # seconds before the bubble pops automatically

# Fly setup
FLY_CLUSTER_COUNT = 4        # number of initial flock clusters
FLY_CLUSTER_SPAWN_RADIUS = 90.0  # max offset from a cluster center when spawning
NUM_FLIES = 30           # how many flies spawn
FLY_RADIUS = 8            # fly draw and collision radius
FLY_SPEED  = 120.0        # fly max speed

# Fly panic/fleeing tuning
FLEE_PANIC_RANGE    = 220.0   # distance at which panic scaling starts kicking in
FLEE_PANIC_EXPONENT = 2.4     # >1 = sharper, more dramatic ramp-up as distance shrinks
FLEE_PANIC_MAX_MULT = 3.0     # maximum multiplier applied to evade force at point-blank range
FLEE_BURST_STRENGTH = 260.0   # one-time velocity kick applied the instant a fly starts fleeing

# Boids neighborhood and weights
# These determine how flies react to neighbors
NEIGHBOR_RADIUS = 150.0   # how far a fly considers other flies as neighbors
REGROUP_RADIUS  = 500.0   # search radius for the nearest fly when totally alone
REGROUP_WEIGHT  = 0.6     # how gently an isolated fly steers back toward the group
SEP_RADIUS      = 34.0    # separation threshold distance
SEP_WEIGHT      = 1.2     # weight for separation force
COH_WEIGHT      = 1.6     # weight for cohesion force
ALI_WEIGHT      = 0.8     # weight for alignment force
ANCHOR_WEIGHT   = 0.6     # small pull to arena center to keep flock on screen

# Arrive behavior
# Slow inside slow radius and stop inside stop radius
ARRIVE_SLOW_RADIUS  = 120.0
ARRIVE_STOP_RADIUS  = 8.0
ARRIVE_STOP_DAMPING = 14.0   # 1/seconds — higher = faster hard stop once inside stop radius
ARRIVE_STOP_SNAP    = 2.0    # px/s — below this speed, snap directly to zero

# Snake setup
NUM_SNAKES  = 3
SNAKE_RADIUS = 18
SNAKE_SPEED  = 160.0

# Snake perception ranges for FSM transitions
AGGRO_RANGE   = 260.0     # start chasing when frog gets this close
DEAGGRO_RANGE = 360.0     # stop chasing when frog moves this far

# Obstacle avoidance tuning
AVOID_LOOKAHEAD       = 260.0   # how far the snake looks ahead when checking a corridor
AVOID_ANGLE_INCREMENT = 12      # degrees to rotate per step when searching for a free path
AVOID_MAX_ANGLE       = 84      # maximum deviation to try on either side

# Game rules
START_HEALTH = 3                 # how many hits the frog can take
FLIES_TO_WIN = 10                # win condition counter
