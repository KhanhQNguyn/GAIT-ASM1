This file is a merged representation of the entire codebase, combined into a single document by Repomix.

<file_summary>
This section contains a summary of this file.

<purpose>
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.
</purpose>

<file_format>
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  - File path as an attribute
  - Full contents of the file
</file_format>

<usage_guidelines>
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.
</usage_guidelines>

<notes>
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)
</notes>

</file_summary>

<directory_structure>
entities/
  fly.py
  frog.py
  snake.py
debug_state.py
main.py
settings.py
steering.py
utils.py
world.py
</directory_structure>

<files>
This section contains the contents of the repository's files.

<file path="world.py">
# ============================================================================
# world.py
# Purpose
#   Build the arena and a list of rectangular obstacles.
#   Obstacles are static and are used by the snake for avoidance checks.
# Why rectangles
#   Rectangles are easy to draw and fast to test against with our helpers.
# ============================================================================

import random
import pygame

class World:
    def __init__(self, width, height):
        # Whole world bounds as a pygame.Rect for convenience
        self.rect = pygame.Rect(0, 0, width, height)

        # Container that holds all blocking rectangles
        self.obstacles = []

        # Build a reproducible obstacle set
        self._build_obstacles(width, height)

    def _build_obstacles(self, w, h):
        """Create a few rectangles with a fixed random seed for reproducibility."""
        rng = random.Random(9)
        for _ in range(9):
            ww = rng.randint(80, 180)
            hh = rng.randint(60, 140)
            x = rng.randint(40, w - ww - 40)
            y = rng.randint(40, h - hh - 40)
            rect = pygame.Rect(x, y, ww, hh)
            self.obstacles.append(rect)

    def draw(self, surf):
        """Render each obstacle with a fill and a subtle outline."""
        for r in self.obstacles:
            pygame.draw.rect(surf, (70, 85, 95), r, border_radius=10)
            pygame.draw.rect(surf, (110, 130, 145), r, 2, border_radius=10)
</file>

<file path="debug_state.py">
# ============================================================================
# debug_state.py
# Purpose
#   Global debug flag that can be toggled by F1 key.
#   Entities import this to check if debug mode is enabled.
#   Also holds a live FSM transition log for the debug overlay.
# ============================================================================

# Global debug toggle flag
DEBUG = False

# Live FSM transition log — list of (time_str, kind, index, old_state, new_state)
TRANSITION_LOG = []
MAX_LOG_ENTRIES = 10

def log_transition(kind, index, old_state, new_state):
    """Record a state transition to the live debug log."""
    import time as _time
    TRANSITION_LOG.append((_time.strftime("%H:%M:%S"), kind, index, old_state, new_state))
    if len(TRANSITION_LOG) > MAX_LOG_ENTRIES:
        TRANSITION_LOG.pop(0)
</file>

<file path="utils.py">
# ============================================================================
# utils.py
# Purpose
#   Small helper functions that do not belong to a specific agent.
#   Drawing helpers and collision checks live here.
# Notes
#   None of these helpers should change game rules or AI decisions.
# ============================================================================

import pygame
from pygame.math import Vector2 as V2
from settings import WIDTH, HEIGHT
import pygame.gfxdraw

# A soft grid color for the background
GRID = (36, 42, 48)

def draw_grid(surf):
    """
    Draw a light grid to help the eye judge motion and distance.
    The grid has no effect on gameplay. It is only visual.
    """
    gap = 36  # distance between grid lines
    # Draw vertical lines
    for x in range(0, WIDTH, gap):
        pygame.draw.line(surf, GRID, (x, 0), (x, HEIGHT))
    # Draw horizontal lines
    for y in range(0, HEIGHT, gap):
        pygame.draw.line(surf, GRID, (0, y), (WIDTH, y))

def clamp(x, a, b):
    """Limit a scalar value x so it stays between a and b inclusive."""
    return max(a, min(b, x))

def limit(v, max_len):
    """
    Limit a vector length.
    If v is longer than max_len, scale it down to exactly max_len.
    """
    if v.length_squared() > max_len * max_len:
        v.scale_to_length(max_len)
    return v

def nearest_point_on_rect(point, rect):
    """Return the closest point on an axis aligned rectangle to a given point."""
    x = clamp(point.x, rect.left, rect.right)
    y = clamp(point.y, rect.top, rect.bottom)
    return V2(x, y)

def circle_rect_intersect(center, radius, rect):
    """Return True if a circle touches or overlaps a rectangle."""
    np = nearest_point_on_rect(center, rect)
    return (center - np).length_squared() <= radius * radius

def segment_circlecast_hits_rect(p0, p1, radius, rect, step=6.0):
    """
    Approximate a circle cast along a line from p0 to p1.
    We sample points along the segment and test a circle intersect at each step.
    """
    d = p1 - p0
    length = d.length()
    if length == 0:
        return circle_rect_intersect(p0, radius, rect)
    n = max(1, int(length / step))
    for i in range(n + 1):
        t = i / n
        pos = p0 + d * t
        if circle_rect_intersect(pos, radius, rect):
            return True
    return False

def circlecast_hits_any_rect(p0, p1, radius, rects, step=6.0):
    """Return True if the swept circle between p0 and p1 hits any rect in the list."""
    for r in rects:
        if segment_circlecast_hits_rect(p0, p1, radius, r, step):
            return True
    return False

def draw_debug_overlay(surf, pos, vel, perception_radii, state_name=None, vel_color=(255, 100, 100)):
    """
    Draw debug overlay for an entity: velocity vector, perception radii, and state name.

    Parameters:
      surf: pygame surface to draw on
      pos: entity position (V2)
      vel: entity velocity (V2)
      perception_radii: list of (radius_value, color) tuples to draw as circles
      state_name: string name of state to render, or None to skip state text
      vel_color: color of the velocity arrow, so different entity types read distinctly
    """
    # Draw velocity vector — bigger scale, thicker line, solid filled arrowhead
    if vel.length_squared() > 0.01:
        vel_end = pos + vel * 0.45
        pygame.draw.line(surf, vel_color, pos, vel_end, 3)
        arrow_dir = vel.normalize()
        tip = vel_end + arrow_dir * 10
        left = vel_end + arrow_dir.rotate(140) * 9
        right = vel_end + arrow_dir.rotate(-140) * 9
        pygame.draw.polygon(surf, vel_color, [tip, left, right])

    # Draw perception radius circles
    for radius, color in perception_radii:
        pygame.draw.circle(surf, color, pos, radius, 1)

    # Draw state name as small text above entity, with a background for legibility
    if state_name is not None:
        from pygame.font import Font
        tiny_font = Font(None, 22)
        txt = tiny_font.render(state_name, True, (235, 235, 235))
        text_rect = txt.get_rect(midbottom=(int(pos.x), int(pos.y) - 20))
        bg_rect = text_rect.inflate(6, 4)
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 140))
        surf.blit(bg_surf, bg_rect.topleft)
        surf.blit(txt, text_rect)

def draw_heart(screen, x, y, color):
    pts = [
        (x + 6, y + 18),
        (x + 17, y + 12),
        (x + 20, y + 5),
        (x + 16, y - 1),
        (x + 10, y - 2),
        (x + 6, y + 2),
        (x + 2, y - 2),
        (x - 4, y - 1),
        (x - 8, y + 5),
        (x - 5, y + 12),
    ]

    pygame.gfxdraw.aapolygon(screen, pts, (30, 30, 30))
    pygame.gfxdraw.filled_polygon(screen, pts, color)
</file>

<file path="entities/frog.py">
# ============================================================================
# frog.py
# Purpose
#   Player controlled agent. Moves with Arrive. Shoots bubbles.
#   Holds a short Hurt state for temporary invulnerability after damage.
# Update order
#   Compute steering, integrate velocity with dt, clamp to bounds, update bubbles.
# Drawing
#   Draw the frog body and a simple eye that points in the facing direction.
# ============================================================================

import time
import pygame
from pygame.math import Vector2 as V2
from settings import (
    WIDTH, HEIGHT, WHITE, GREEN, BLUE,
    FROG_RADIUS, FROG_SPEED,
    BUBBLE_RADIUS, BUBBLE_SPEED, BUBBLE_LIFETIME,
    HURT_INVULN, FROG_FACING_MIN_SPEED_SQ,
    ARRIVE_STOP_RADIUS, ARRIVE_STOP_DAMPING, ARRIVE_STOP_SNAP
)
from utils import clamp, draw_debug_overlay, circle_rect_intersect, nearest_point_on_rect
import debug_state
from steering import arrive, integrate_velocity, apply_arrive_stop

class Bubble:
    """
    Simple projectile that moves in a straight line and pops after a short time.
    You can destroy it early when it hits a snake or an obstacle.
    """
    def __init__(self, pos, dir_vec):
        self.pos = V2(pos)
        self.vel = (dir_vec.normalize() if dir_vec.length_squared() > 0 else V2(1, 0)) * BUBBLE_SPEED
        self.birth = time.time()
        self.alive = True

    def update(self, dt):
        self.pos += self.vel * dt
        if time.time() - self.birth > BUBBLE_LIFETIME:
            self.alive = False

    def draw(self, surf):
        pygame.draw.circle(surf, BLUE, self.pos, BUBBLE_RADIUS)
        pygame.draw.circle(surf, WHITE, self.pos, BUBBLE_RADIUS, 2)

class Frog:
    def __init__(self, pos, rects=None):
        self.pos = V2(pos)
        self.vel = V2()
        self.target = V2(pos)
        self.radius = FROG_RADIUS
        self.speed = FROG_SPEED
        self.facing = V2(1, 0)   # used to aim bubbles when frog is not moving
        self.bubbles = []
        self.rects = rects if rects is not None else []

        # Hurt state setup. When hurt_timer > 0 the frog cannot be hit again.
        self.hurt_timer = 0.0

    def set_target(self, p):
        """Set a new target the frog will move toward using Arrive."""
        self.target = V2(p)

    def shoot(self):
        """Spawn a bubble just in front of the frog, moving along the facing direction."""
        dir_vec = self.vel if self.vel.length_squared() > FROG_FACING_MIN_SPEED_SQ else self.facing
        origin = self.pos + dir_vec.normalize() * (self.radius + 6)
        self.bubbles.append(Bubble(origin, dir_vec))

    def start_hurt(self):
        """Begin the invulnerability window after damage."""
        if self.hurt_timer <= 0:
            self.hurt_timer = HURT_INVULN

    def can_be_hurt(self):
        """Return True if the frog can take damage right now."""
        return self.hurt_timer <= 0

    def update(self, dt):
        steer = arrive(
            self.pos,
            self.vel,
            self.target,
            self.speed,
        )

        self.vel = integrate_velocity(
            self.vel,
            steer,
            dt,
            self.speed,
        )

        self.vel = apply_arrive_stop(
            self.pos,
            self.vel,
            self.target,
            dt,
        )

        # Move the frog
        self.pos += self.vel * dt

        # Face in the direction of motion when moving
        if self.vel.length_squared() > FROG_FACING_MIN_SPEED_SQ:
            self.facing = self.vel.normalize()

        # Keep inside bounds
        self.pos.x = clamp(self.pos.x, self.radius, WIDTH - self.radius)
        self.pos.y = clamp(self.pos.y, self.radius, HEIGHT - self.radius)

        # Push frog out of any obstacle rectangle it overlaps
        for rect in self.rects:
            if circle_rect_intersect(self.pos, self.radius, rect):
                nearest = nearest_point_on_rect(self.pos, rect)
                diff = self.pos - nearest
                if diff.length_squared() > 0:
                    push_dir = diff.normalize()
                else:
                    push_dir = V2(0, -1)
                self.pos = nearest + push_dir * self.radius
                # Kill velocity component pushing further into the obstacle
                into_wall = self.vel.dot(push_dir)
                if into_wall < 0:
                    self.vel -= push_dir * into_wall

        # Update bubbles and remove popped ones
        for b in list(self.bubbles):
            b.update(dt)
            if not b.alive:
                self.bubbles.remove(b)

        # Count down invulnerability
        if self.hurt_timer > 0:
            self.hurt_timer -= dt

    def draw(self, surf):
        # Flash while hurt. This provides player feedback and helps debugging.
        color = GREEN
        if self.hurt_timer > 0:
            t = int(pygame.time.get_ticks() * 0.01) % 2
            color = (220, 220, 220) if t == 0 else (160, 160, 160)

        # Body
        pygame.draw.circle(surf, color, self.pos, self.radius)

        # Eye looks in facing direction
        eye = self.pos + self.facing * (self.radius - 4)
        pygame.draw.circle(surf, WHITE, eye, 5)
        pygame.draw.circle(surf, (30, 30, 30), eye, 2)

        # Bubbles
        for b in self.bubbles:
            b.draw(surf)
        
        # Debug overlay when enabled
        if debug_state.DEBUG:
            draw_debug_overlay(surf, self.pos, self.vel, [], "n/a", vel_color=(120, 255, 160))
            
            # Draw crosshair at target
            pygame.draw.circle(surf, (200, 200, 200), self.target, 3)
            pygame.draw.line(surf, (200, 200, 200), self.target - V2(8, 0), self.target + V2(8, 0), 1)
            pygame.draw.line(surf, (200, 200, 200), self.target - V2(0, 8), self.target + V2(0, 8), 1)
            
            # Draw ARRIVE_SLOW_RADIUS and ARRIVE_STOP_RADIUS around the target
            from settings import ARRIVE_SLOW_RADIUS, ARRIVE_STOP_RADIUS
            pygame.draw.circle(surf, (255, 200, 100), self.target, ARRIVE_SLOW_RADIUS, 1)
            pygame.draw.circle(surf, (255, 100, 100), self.target, ARRIVE_STOP_RADIUS, 1)
</file>

<file path="entities/snake.py">
# ============================================================================
# snake.py
# Purpose
#   Predator agent with a five-state FSM.
#   States: PatrolAway, PatrolHome, Aggro, Harmless, Confused.
#   Aggro chases the frog. Harmless returns home after pacification.
#   Confused wanders briefly after reaching home, then resumes patrol.
# Update order
#   Evaluate transitions first, then run the behavior for the active state.
# Drawing
#   Simple circle with a tiny eye that turns toward the current velocity.
# ============================================================================

from enum import Enum, auto
import math, random
import pygame
from pygame.math import Vector2 as V2
import settings
from settings import (
    WIDTH, HEIGHT, WHITE,
    SNAKE_RADIUS, SNAKE_SPEED, DEAGGRO_RANGE
)
from utils import draw_debug_overlay, nearest_point_on_rect, clamp, circle_rect_intersect
import debug_state
from steering import arrive, seek, seek_with_avoid, integrate_velocity, pursue, wander_force, predict_future_position, arrive_with_avoid

class SnakeState(Enum):
    PatrolAway = auto()
    PatrolHome = auto()
    Aggro      = auto()
    Harmless   = auto()
    Confused   = auto()

class Snake:
    def __init__(self, pos, patrol_point, rects):
        # Motion and shape
        self.pos = V2(pos)
        self.vel = V2(1, 0)
        self.radius = SNAKE_RADIUS
        self.speed = SNAKE_SPEED

        # Home base and patrol destination
        self.home = V2(pos)
        self.patrol_point = V2(patrol_point)

        # Initial state
        self.state = SnakeState.PatrolAway

        # Obstacles for avoidance
        self.rects = rects

        # Drawing hint for head direction
        self.heading_deg = 0.0

        # Color varies by state for quick visual debug
        self.color = (190, 130, 110)

        # Confused state timer
        self.confused_timer = 0.0

        # RNG for wander if needed
        self._rng_seed = random.randint(0, 999999)
        self._avoid_angle = 0.0

        # Debug overlay info
        self._debug_target = None
        self._debug_steer = V2()
        self._debug_avoid = V2()

    def set_state(self, st):
        """Switch to a new FSM state and log the transition for debug overlay."""
        if st != self.state:
            debug_state.log_transition("Snake", id(self) % 1000, self.state.name, st.name)
        self.state = st
        
        # Start the confused timer immediately when entering the state
        if self.state == SnakeState.Confused:
            self.confused_timer = settings.SNAKE_CONFUSED_DURATION

    def update(self, dt, frog):
        """
        Update state transitions based on distance to frog and timers.
        Then compute a steering force for the active state and integrate motion.
        """

        # Distance to frog for transitions
        dist = (frog.pos - self.pos).length()

        # ---------------- FSM transitions ----------------
        if self.state == SnakeState.Aggro:
            if dist > DEAGGRO_RANGE:
                self.set_state(SnakeState.PatrolHome)

        elif self.state in (SnakeState.PatrolHome, SnakeState.PatrolAway):
            if dist < settings.AGGRO_RANGE:
                self.set_state(SnakeState.Aggro)

        elif self.state == SnakeState.Confused:
            self.confused_timer -= dt
            if self.confused_timer <= 0:
                self.set_state(SnakeState.Harmless)

        elif self.state == SnakeState.Harmless:
            # Walk home, then resume patrol
            if (self.home - self.pos).length() < settings.SNAKE_ARRIVE_THRESHOLD:
                self.set_state(SnakeState.PatrolAway)

        # ---------------- State behaviours ----------------
        # min_obstacle_dist = float('inf')
        # for r in self.rects:
        #     np = nearest_point_on_rect(self.pos, r)
        #     d = (self.pos - np).length()
        #     if d < min_obstacle_dist:
        #         min_obstacle_dist = d
        
        # # Scale avoid_weight from min (far from obstacle) up to max (right next to one)
        # t = clamp((settings.SNAKE_AVOID_NEAR_DIST - min_obstacle_dist) / settings.SNAKE_AVOID_NEAR_DIST, 0.0, 1.0)
        # avoid_weight = settings.SNAKE_AVOID_WEIGHT_MIN + (settings.SNAKE_AVOID_WEIGHT_MAX - settings.SNAKE_AVOID_WEIGHT_MIN) * t

        if self.state == SnakeState.Aggro:
            self.color = (255, 150, 150)
            predicted = predict_future_position(self.pos, frog.pos, frog.vel, self.speed)
            self._debug_target = predicted
            steer, self._avoid_angle = seek_with_avoid(
                self.pos, self.vel, predicted, self.speed, self.radius, self.rects,
                preferred_angle=self._avoid_angle)
            self._debug_steer = steer
            self._debug_avoid = V2() # seek_with_avoid blends natively

        elif self.state == SnakeState.PatrolAway:
            self.color = (180, 200, 255)
            self._debug_target = self.patrol_point
            steer, self._avoid_angle = arrive_with_avoid(
                self.pos, self.vel, self.patrol_point, self.speed, self.radius, self.rects,
                preferred_angle=self._avoid_angle)
            self._debug_steer = steer
            self._debug_avoid = V2()
            if (self.patrol_point - self.pos).length() < settings.SNAKE_ARRIVE_THRESHOLD:
                self.set_state(SnakeState.PatrolHome)

        elif self.state == SnakeState.PatrolHome:
            self.color = (180, 220, 180)
            self._debug_target = self.home
            steer, self._avoid_angle = arrive_with_avoid(
                self.pos, self.vel, self.home, self.speed, self.radius, self.rects,
                preferred_angle=self._avoid_angle)
            self._debug_steer = steer
            self._debug_avoid = V2()
            if (self.home - self.pos).length() < settings.SNAKE_ARRIVE_THRESHOLD:
                self.set_state(SnakeState.PatrolAway)

        elif self.state == SnakeState.Harmless:
            self.color = (190, 180, 255)
            self._debug_target = self.home
            steer, self._avoid_angle = arrive_with_avoid(
                self.pos, self.vel, self.home, self.speed * settings.SNAKE_HARMLESS_SPEED_MULT,
                self.radius, self.rects, preferred_angle=self._avoid_angle)
            self._debug_steer = steer
            self._debug_avoid = V2()

        else:  # Confused
            self.color = (245, 210, 160)
            self._debug_target = None
            steer = wander_force(self.vel, self.speed, rng_seed=self._rng_seed)
            self._debug_steer = steer
            self._debug_avoid = V2()

        # Integrate velocity and update position
        self.vel = integrate_velocity(self.vel, steer, dt, self.speed)
        self.pos += self.vel * dt

        # Hard fallback: guarantee the snake never ends up overlapping an obstacle, even on
        # frames where the soft avoidance steering wasn't enough (tight corners, high speed)
        for rect in self.rects:
            if circle_rect_intersect(self.pos, self.radius, rect):
                nearest = nearest_point_on_rect(self.pos, rect)
                diff = self.pos - nearest
                if diff.length_squared() > 0:
                    push_dir = diff.normalize()
                else:
                    push_dir = V2(0, -1)
                self.pos = nearest + push_dir * self.radius
                into_wall = self.vel.dot(push_dir)
                if into_wall < 0:
                    self.vel -= push_dir * into_wall

        # Smooth eye heading based on velocity
        spd = self.vel.length()
        if spd > 4:
            def lerp(a, b, t): return a + (b - a) * t
            self.heading_deg = lerp(self.heading_deg, math.degrees(math.atan2(self.vel.y, self.vel.x)), 0.15)

        # Keep inside arena
        if self.pos.x < self.radius: self.pos.x = self.radius
        if self.pos.x > WIDTH - self.radius: self.pos.x = WIDTH - self.radius
        if self.pos.y < self.radius: self.pos.y = self.radius
        if self.pos.y > HEIGHT - self.radius: self.pos.y = HEIGHT - self.radius

    def draw(self, surf):
        # Body
        pygame.draw.circle(surf, self.color, self.pos, self.radius)
        # Simple eye in heading direction
        head = self.pos + V2(1, 0).rotate(self.heading_deg) * (self.radius - 2)
        pygame.draw.circle(surf, (30, 30, 30), head, 3)
        pygame.draw.circle(surf, WHITE, head, 5, 1)
        
        # Debug overlay when enabled
        if debug_state.DEBUG:
            perception_radii = [
                (settings.AGGRO_RANGE, (255, 100, 100)),
                (DEAGGRO_RANGE, (100, 100, 255))
            ]
            draw_debug_overlay(surf, self.pos, self.vel, perception_radii, self.state.name, vel_color=(255, 130, 100))
            
            # Draw individual forces
            scale = 0.3
            if self._debug_steer.length_squared() > 0.01:
                pygame.draw.line(surf, (100, 255, 100), self.pos, self.pos + self._debug_steer * scale, 2) # Green for base steer
            if self._debug_avoid.length_squared() > 0.01:
                pygame.draw.line(surf, (255, 200, 100), self.pos, self.pos + self._debug_avoid * scale, 2) # Orange for avoid force
                
            # Draw marker at active target
            if self._debug_target:
                pygame.draw.line(surf, (255, 50, 50), self._debug_target - V2(6, 6), self._debug_target + V2(6, 6), 2)
                pygame.draw.line(surf, (255, 50, 50), self._debug_target - V2(6, -6), self._debug_target + V2(6, -6), 2)
</file>

<file path="entities/fly.py">
# ============================================================================
# fly.py
# Purpose
#   Autonomous flocking agent with a small FSM.
#   States: Flock, Fleeing, Idle.
#   Flock uses boids separation, cohesion, alignment.
#   Fleeing uses flee or the new evade behavior.
#   Idle uses a gentle wander to drift when far from danger.
# Update order
#   Compute state transitions from triggers, then apply the behavior for state.
# ============================================================================

import random
from enum import Enum, auto
import pygame
from pygame.math import Vector2 as V2
import settings
from settings import (
    WIDTH, HEIGHT, WHITE, YELLOW, PURPLE,
    FLY_RADIUS, FLY_SPEED, NEIGHBOR_RADIUS,
    ANCHOR_WEIGHT
)
from utils import limit, draw_debug_overlay
import debug_state
from steering import (
    boids_separation, boids_cohesion, boids_alignment,
    flee, evade, wander_force, seek
)

class FlyState(Enum):
    Flock   = auto()
    Fleeing = auto()
    Idle    = auto()

class Fly:
    def __init__(self, pos):
        self.pos = V2(pos)
        self.vel = V2(random.uniform(-1, 1), random.uniform(-1, 1))
        if self.vel.length_squared() == 0:
            self.vel = V2(1, 0)
        self.vel.scale_to_length(FLY_SPEED * 0.5)

        self.radius = FLY_RADIUS
        self.state = FlyState.Flock

        # Timers and cached values
        self.scare_timer = 0.0   # counts down while nervous before calming
        self.idle_timer  = 0.0   # time spent far from frog
        self._catching_up = False  # True while hurrying to merge into a bigger flock
        self._rng_seed   = random.randint(0, 999999)
        self._debug_neighbors = []   # cached neighbor list for debug neighbor-link drawing

    def sense_bubbles_close(self, bubbles, r):
        """Return True if any bubble is within range r of the fly."""
        for b in bubbles:
            if (b.pos - self.pos).length_squared() <= r * r:
                return True
        return False

    def _set_state(self, new_state):
        """Switch FSM state and log the transition when it actually changes."""
        if new_state != self.state:
            debug_state.log_transition("Fly", id(self) % 1000, self.state.name, new_state.name)
        self.state = new_state

    def update(self, dt, flies, frog, bounds_rect, bubbles, neighbor_counts=None, neighbors=None, neighbor_ids=None):
        """
        Update FSM and behavior. Flies use perception to switch states.
        Parameters
          flies: list of all flies for neighborhood queries
          frog:  player agent used as a threat source
          bounds_rect: world rectangle for anchor force and containment
          bubbles: list of active bubbles to trigger panic
        """

        # Perception radii and timers for the FSM
        BubbleFleeRange  = settings.FLY_BUBBLE_FLEE_RANGE
        StopFleeingRange = settings.FLY_CALM_RANGE
        IdleDistance     = settings.FLY_IDLE_DISTANCE
        IdleDelay        = settings.FLY_IDLE_DELAY

        # Triggers based on the frog and bubbles
        dist_to_frog = (frog.pos - self.pos).length()
        scared_by_frog   = dist_to_frog < settings.FLY_SCARED_RANGE
        scared_by_bubble = self.sense_bubbles_close(bubbles, BubbleFleeRange)

        # Cheap neighbor-presence check: true if any other fly is within NEIGHBOR_RADIUS
        has_nearby_flockmate = bool(neighbors)

        # ---------------- FSM transitions ----------------
        if self.state == FlyState.Flock:
            if scared_by_frog or scared_by_bubble:
                self._set_state(FlyState.Fleeing)
                self.scare_timer = settings.FLY_SCARE_TIMER
                # One-time velocity kick directly away from threat
                burst_dir = self.pos - frog.pos
                if burst_dir.length_squared() > 0:
                    burst_dir = burst_dir.normalize()
                else:
                    burst_dir = V2(0, -1)
                self.vel += burst_dir * settings.FLEE_BURST_STRENGTH
            else:
                # Chuyển sang Idle khi ở xa Ếch (Áp dụng cho toàn bộ bầy)
                if dist_to_frog > IdleDistance:
                    self.idle_timer += dt
                    if self.idle_timer >= IdleDelay:
                        self._set_state(FlyState.Idle)
                else:
                    self.idle_timer = 0.0

        elif self.state == FlyState.Fleeing:
            calm = dist_to_frog > StopFleeingRange and not self.sense_bubbles_close(bubbles, StopFleeingRange)
            if calm:
                self.scare_timer -= dt
                if self.scare_timer <= 0:
                    self._set_state(FlyState.Flock)
                    self.idle_timer = 0.0
            else:
                self.scare_timer = settings.FLY_SCARE_TIMER

        elif self.state == FlyState.Idle:
            if scared_by_frog or scared_by_bubble:
                self._set_state(FlyState.Fleeing)
                self.scare_timer = settings.FLY_SCARE_TIMER
                # One-time velocity kick directly away from threat
                burst_dir = self.pos - frog.pos
                if burst_dir.length_squared() > 0:
                    burst_dir = burst_dir.normalize()
                else:
                    burst_dir = V2(0, -1)
                self.vel += burst_dir * settings.FLEE_BURST_STRENGTH
            # Chỉ thức tỉnh và quay lại Flock khi Ếch tiến lại gần
            elif dist_to_frog <= IdleDistance:
                self._set_state(FlyState.Flock)
                self.idle_timer = 0.0

        # ---------------- State behaviours ----------------
        if self.state == FlyState.Flock:
            # Neighbor list and neighbor-id set are precomputed once per frame in main.py
            # (single O(N^2) pass shared by every fly) and passed in here — no need to
            # rebuild them per-fly anymore.
            neighbors = neighbors if neighbors is not None else []
            neighbor_ids = neighbor_ids if neighbor_ids is not None else set()
            self._debug_neighbors = neighbors   # cache for debug drawing

            self._catching_up = False  # will be set True only if we decide to catch up below

            my_group_size = len(neighbors)
            best_bigger = None
            best_bigger_size = my_group_size

            # Only genuinely small/isolated groups should ever consider catching up —
            # density variation inside an already-joined flock should not re-trigger this
            # Only a genuinely small-but-real flock (not a lone straggler or a pair) should
            # actively hurry toward a meaningfully bigger one nearby. A lone fly or pair just
            # flocks normally and merges naturally whenever it happens to encounter a group —
            # no active cross-map hunting for those.
            if (neighbor_counts is not None
                    and settings.CATCHUP_MIN_OWN_GROUP <= my_group_size <= settings.CATCHUP_MAX_OWN_GROUP):
                for f in flies:
                    if f is self:
                        continue
                    # Skip flies already in my own neighbor set — cohesion handles them
                    if id(f) in neighbor_ids:
                        continue
                    d = (f.pos - self.pos).length()
                    if d <= settings.CATCHUP_SEARCH_RADIUS:
                        f_count = neighbor_counts.get(id(f), 0)
                        if f_count > best_bigger_size + settings.CATCHUP_GROUP_DELTA:
                            best_bigger_size = f_count
                            best_bigger = f

            if best_bigger is not None:
                # A meaningfully bigger flock is nearby — hurry to join it
                self._catching_up = True
                force = seek(
                    self.pos, self.vel, best_bigger.pos, FLY_SPEED * settings.CATCHUP_SPEED_MULT
                ) * settings.CATCHUP_WEIGHT
            elif len(neighbors) == 0:
                nearest = None
                min_dist = settings.REGROUP_RADIUS
                for f in flies:
                    if f is self:
                        continue
                    d = (f.pos - self.pos).length()
                    if d < min_dist:
                        min_dist = d
                        nearest = f

                if nearest is not None:
                    force = seek(self.pos, self.vel, nearest.pos, FLY_SPEED) * settings.REGROUP_WEIGHT
                else:
                    force = V2()
            else:
                sep = boids_separation(self.pos, self.vel, neighbors, settings.SEP_RADIUS, FLY_SPEED)
                coh = boids_cohesion(self.pos, self.vel, neighbors, FLY_SPEED)
                ali = boids_alignment(self.vel, neighbors, FLY_SPEED)
                force = sep * settings.SEP_WEIGHT + coh * settings.COH_WEIGHT + ali * settings.ALI_WEIGHT

            # Gentle anchor toward arena center to avoid drifting out of bounds
            center = V2(bounds_rect.centerx, bounds_rect.centery)
            force += (center - self.pos) * ANCHOR_WEIGHT * 0.002

            # Integrate velocity
            self.vel += limit(force, 240.0) * dt

        elif self.state == FlyState.Fleeing:
            force = evade(self.pos, self.vel, frog.pos, frog.vel, FLY_SPEED, threat_max_speed=frog.speed)

            # Scale evade force by proximity — the closer the frog, the sharper the panic
            closeness = 1.0 - min(dist_to_frog, settings.FLEE_PANIC_RANGE) / settings.FLEE_PANIC_RANGE
            panic_mult = 1.0 + (settings.FLEE_PANIC_MAX_MULT - 1.0) * (closeness ** settings.FLEE_PANIC_EXPONENT)
            force *= panic_mult

            # Mild separation so panicking flies scatter apart instead of overlapping each
            # other — reuse the neighbor list precomputed once per frame in main.py instead
            # of rebuilding it here.
            neighbors = neighbors if neighbors is not None else []
            self._debug_neighbors = neighbors
            if neighbors:
                sep = boids_separation(self.pos, self.vel, neighbors, settings.SEP_RADIUS, FLY_SPEED)
                force += sep * settings.SEP_WEIGHT * 0.6

            # Anchor blend so the group does not disappear off screen
            center = V2(bounds_rect.centerx, bounds_rect.centery)
            force += (center - self.pos) * ANCHOR_WEIGHT * 0.002

            self.vel += limit(force, 420.0) * dt

        elif self.state == FlyState.Idle:
            force = wander_force(self.vel, FLY_SPEED, rng_seed=self._rng_seed)
            self.vel += limit(force, 120.0) * dt
            self.vel *= 0.98  # mild damping so idle feels soft

        # Speed clamp and position integrate — allow a temporary higher cap while catching up
        if self.state == FlyState.Fleeing:
            effective_max_speed = FLY_SPEED * settings.FLEE_PANIC_MAX_MULT
        elif self._catching_up:
            effective_max_speed = FLY_SPEED * settings.CATCHUP_SPEED_MULT
        else:
            effective_max_speed = FLY_SPEED

        if self.vel.length() > effective_max_speed:
            self.vel.scale_to_length(effective_max_speed)
        self.pos += self.vel * dt

        # Soft containment inside arena
        if self.pos.x < self.radius:
            self.pos.x = self.radius; self.vel.x *= -0.4
        if self.pos.x > WIDTH - self.radius:
            self.pos.x = WIDTH - self.radius; self.vel.x *= -0.4
        if self.pos.y < self.radius:
            self.pos.y = self.radius; self.vel.y *= -0.4
        if self.pos.y > HEIGHT - self.radius:
            self.pos.y = HEIGHT - self.radius; self.vel.y *= -0.4

    def draw(self, surf):
        color = YELLOW if self.state in (FlyState.Flock, FlyState.Idle) else PURPLE
        pygame.draw.circle(surf, color, self.pos, self.radius)
        
        # Debug overlay when enabled
        if debug_state.DEBUG:
            # Draw faint lines to each boid neighbor
            for n_pos, n_vel in self._debug_neighbors:
                pygame.draw.line(surf, (60, 90, 110), self.pos, n_pos, 1)
            # Draw velocity vector, NEIGHBOR_RADIUS perception, and state name
            perception_radii = [(NEIGHBOR_RADIUS, (100, 200, 255))]
            draw_debug_overlay(surf, self.pos, self.vel, perception_radii, self.state.name, vel_color=(230, 220, 100))
</file>

<file path="main.py">
# ============================================================================
# main.py
# Purpose
#   Entry point and game loop. Handles input, updates agents, and draws frames.
# Mental model
#   Each frame: measure dt, process input, update world and agents, draw UI.
#   Agents do not draw themselves until update is finished for the frame.
# Controls
#   Left click sets a target for the frog. Space shoots a bubble. R restarts.
# ============================================================================

from utils import circle_rect_intersect, draw_heart
import sys, random, math
import pygame
from settings import *
from utils import draw_grid, draw_debug_overlay, nearest_point_on_rect
from world import World
from entities.frog import Frog
from entities.fly import Fly
from entities.snake import Snake, SnakeState
import debug_state
from pygame.math import Vector2 as V2

class Particle:
    def __init__(self, pos, color):
        self.pos = V2(pos)
        raw_dir = V2(random.uniform(-1, 1), random.uniform(-1, 1))
        direction = raw_dir.normalize() if raw_dir.length_squared() > 0 else V2(1, 0)
        self.vel = direction * random.uniform(50, 150)
        self.lifetime = PARTICLE_LIFETIME
        self.age = 0.0
        self.color = color

    def update(self, dt):
        self.pos += self.vel * dt
        self.age += dt

    def draw(self, surf):
        if self.age < self.lifetime:
            radius = max(1, int(5 * (1 - self.age / self.lifetime)))
            pygame.draw.circle(surf, self.color, self.pos, radius)

class KeySlider:
    def __init__(self, x, y, min_v, max_v, step, initial, label, key_dec, key_inc, key_names):
        self.x = x
        self.y = y
        self.min_v = min_v
        self.max_v = max_v
        self.step = step
        self.val = initial
        self.label = label
        self.key_dec = key_dec
        self.key_inc = key_inc
        self.key_names = key_names

    def handle_event(self, e):

        if e.type == pygame.KEYDOWN:
            if e.key == self.key_dec:
                self.val = max(self.min_v, self.val - self.step)
            elif e.key == self.key_inc:
                self.val = min(self.max_v, self.val + self.step)

    def draw(self, surf, font):
        txt = font.render(f"[{self.key_names}] {self.label}: {self.val:.1f}", True, (230, 230, 255))
        bg_rect = txt.get_rect(topleft=(self.x, self.y))
        bg_rect.inflate_ip(12, 6)
        
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (0, 0, 0, 160), bg_surf.get_rect(), border_radius=4)
        surf.blit(bg_surf, bg_rect.topleft)
        
        surf.blit(txt, (self.x, self.y))

def resolve_fly_overlaps(flies, iterations=2):
    """
    Hard position-based separation: guarantees no two flies end up visually
    overlapping, regardless of how the steering forces balance out. Runs after
    all flies have moved for the frame. Cheap: O(n^2) with n=30 is trivial.
    """
    for _ in range(iterations):
        for i in range(len(flies)):
            a = flies[i]
            for j in range(i + 1, len(flies)):
                b = flies[j]
                diff = a.pos - b.pos
                dist = diff.length()
                min_dist = a.radius + b.radius
                if dist == 0:
                    # Perfectly stacked (rare) — nudge apart along a fixed axis
                    push = V2(1, 0) * (min_dist * 0.5)
                    a.pos += push
                    b.pos -= push
                elif dist < min_dist:
                    overlap = min_dist - dist
                    push = diff.normalize() * (overlap * 0.5)
                    a.pos += push
                    b.pos -= push

def main():
    # Initialize Pygame and create a window and a clock
    pygame.init()
    pygame.display.set_caption("Frog, Flies, and Snakes")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # Fonts for text and overlay
    font = pygame.font.SysFont("consolas", 22)
    bigfont = pygame.font.SysFont("consolas", 48, bold=True)

    def reset():
        """
        Create a fresh world and agents. Called at start and when the player restarts.
        Returns a tuple of (world, frog, flies, snakes).
        """
        world = World(WIDTH, HEIGHT)

        # Helper to push spawn/target points out of obstacles
        def get_safe_point(x, y, radius):
            p = V2(x, y)
            for _ in range(5): # Iteratively push out of overlapping obstacles
                hit = False
                for rect in world.obstacles:
                    if circle_rect_intersect(p, radius, rect):
                        hit = True
                        nearest = nearest_point_on_rect(p, rect)
                        diff = p - nearest
                        if diff.length_squared() > 0:
                            p = nearest + diff.normalize() * (radius + 10)
                        else:
                            # Fallback push if perfectly centered
                            p += V2(0, -1) * (radius + 10)
                if not hit:
                    break
            
            # Clamp the final point to ensure it wasn't pushed off-screen
            p.x = max(radius, min(WIDTH - radius, p.x))
            p.y = max(radius, min(HEIGHT - radius, p.y))
            return p.x, p.y

        # Spawn Frog safely
        fx, fy = get_safe_point(WIDTH * 0.5, HEIGHT * 0.5, FROG_RADIUS)
        frog = Frog((fx, fy), world.obstacles)

        # Generate cluster centers for flies
        centers = []
        while len(centers) < FLY_CLUSTER_COUNT:
            cx = random.randint(60, WIDTH - 60)
            cy = random.randint(60, HEIGHT - 60)
            candidate = V2(cx, cy)
            if all((candidate - c).length() >= 250 for c in centers):
                centers.append(candidate)
            
        flies = []
        for i in range(NUM_FLIES):
            center = centers[i % FLY_CLUSTER_COUNT]
            radius = FLY_CLUSTER_SPAWN_RADIUS * math.sqrt(random.random())
            angle = random.uniform(0, 2 * math.pi)
            fly_x = center.x + radius * math.cos(angle)
            fly_y = center.y + radius * math.sin(angle)
            fly_x = max(FLY_RADIUS + 4, min(WIDTH - (FLY_RADIUS + 4), fly_x))
            fly_y = max(FLY_RADIUS + 4, min(HEIGHT - (FLY_RADIUS + 4), fly_y))
            flies.append(Fly((fly_x, fly_y)))

        # Create snakes with safely adjusted patrol and home points
        snakes = []
        for i in range(NUM_SNAKES):
            px = 140 + i * 320
            py = 120 if i % 2 == 0 else HEIGHT - 140
            
            # Ensure both the spawn (home) point and the patrol point are safe
            home_x, home_y = get_safe_point(px, py, SNAKE_RADIUS)
            patrol_x, patrol_y = get_safe_point(WIDTH - px, HEIGHT - py, SNAKE_RADIUS)
            
            snakes.append(Snake((home_x, home_y), (patrol_x, patrol_y), world.obstacles))

        return world, frog, flies, snakes

    # Build initial state
    world, frog, flies, snakes = reset()

    import settings
    sliders = [
        KeySlider(20, 100, 0.0, 5.0, 0.1, settings.SEP_WEIGHT, "SEP_WEIGHT", pygame.K_1, pygame.K_2, "1/2"),
        KeySlider(20, 130, 0.0, 5.0, 0.1, settings.COH_WEIGHT, "COH_WEIGHT", pygame.K_3, pygame.K_4, "3/4"),
        KeySlider(20, 160, 0.0, 5.0, 0.1, settings.ALI_WEIGHT, "ALI_WEIGHT", pygame.K_5, pygame.K_6, "5/6"),
        KeySlider(20, 190, 50.0, 500.0, 10.0, settings.AGGRO_RANGE, "AGGRO_RANGE", pygame.K_7, pygame.K_8, "7/8"),
    ]

    DEFAULT_SLIDER_VALS = [sl.val for sl in sliders]

    particles = []
    red_flash_timer = 0.0
    avg_close_speed = 0.0
    last_aggro_dist = None

    # Click-to-inspect state for debug mode
    inspected_entity = None

    # Game state for health, scoring, and endings
    health = START_HEALTH
    fly_count = 0
    game_over = False
    win = False

    running = True
    while running:
        # ---------------- Measure dt ----------------
        # Convert milliseconds to seconds for frame rate independent movement
        dt = clock.tick(FPS) / 1000.0

        # ---------------- Input ----------------
        for e in pygame.event.get():
            if debug_state.DEBUG:
                for sl in sliders:
                    sl.handle_event(e)
                settings.SEP_WEIGHT = sliders[0].val
                settings.COH_WEIGHT = sliders[1].val
                settings.ALI_WEIGHT = sliders[2].val
                settings.AGGRO_RANGE = sliders[3].val

            if e.type == pygame.QUIT:
                running = False

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False

                if e.key == pygame.K_F1:
                    # F1 toggles debug overlay; clear inspect selection when turning off
                    debug_state.DEBUG = not debug_state.DEBUG
                    if not debug_state.DEBUG:
                        inspected_entity = None

                if not game_over and e.key == pygame.K_SPACE:
                    # Space shoots a bubble from the frog mouth
                    frog.shoot()

                if game_over and e.key == pygame.K_r:
                    # R restarts the whole scene
                    world, frog, flies, snakes = reset()
                    health = START_HEALTH
                    fly_count = 0
                    game_over = False
                    win = False
                    for sl, default_val in zip(sliders, DEFAULT_SLIDER_VALS):
                        sl.val = default_val
                    settings.SEP_WEIGHT = DEFAULT_SLIDER_VALS[0]
                    settings.COH_WEIGHT = DEFAULT_SLIDER_VALS[1]
                    settings.ALI_WEIGHT = DEFAULT_SLIDER_VALS[2]
                    settings.AGGRO_RANGE = DEFAULT_SLIDER_VALS[3]

            if not game_over and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # Left click sets a new move target for the frog
                frog.set_target(pygame.mouse.get_pos())

            if debug_state.DEBUG and e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                # Right-click: click-to-inspect nearest agent whose radius contains the click
                mx, my = pygame.mouse.get_pos()
                click_pos = V2(mx, my)
                best = None
                best_dist = float('inf')
                candidates = list(flies) + list(snakes) + [frog]
                for agent in candidates:
                    d = (agent.pos - click_pos).length()
                    if d <= agent.radius and d < best_dist:
                        best_dist = d
                        best = agent
                inspected_entity = best  # None if nothing clicked = clear selection

        # ---------------- Update ----------------
        if not game_over:
            # Update frog first since other agents may query frog position
            frog.update(dt)

            # Precompute neighbor counts for catch-up detection
# Precompute each fly's neighbor list (positions+velocities) and neighbor-id
            # set ONCE per frame, in a single O(N^2) pass. This replaces the previous
            # separate neighbor-counting pass plus the redundant per-fly neighbor rebuilds
            # that used to happen again inside Fly.update()'s Flock branch, Fleeing branch,
            # and has_nearby_flockmate check. Note: like the old neighbor_counts pass, this
            # snapshot is taken before any fly moves this frame, so behavior (which flies
            # count as neighbors of which) is unchanged from before — just computed once.
            fly_neighbors = {}
            fly_neighbor_ids = {}
            for f in flies:
                f_neighbors = []
                f_neighbor_ids = set()
                for g in flies:
                    if g is f:
                        continue
                    if (g.pos - f.pos).length_squared() <= NEIGHBOR_RADIUS ** 2:
                        f_neighbors.append((g.pos, g.vel))
                        f_neighbor_ids.add(id(g))
                fly_neighbors[id(f)] = f_neighbors
                fly_neighbor_ids[id(f)] = f_neighbor_ids
            neighbor_counts = {fid: len(nbrs) for fid, nbrs in fly_neighbors.items()}

            # Update flies and check if any fly gets caught by the frog
            for f in list(flies):
                f.update(
                    dt, flies, frog, world.rect, frog.bubbles,
                    neighbor_counts=neighbor_counts,
                    neighbors=fly_neighbors.get(id(f), []),
                    neighbor_ids=fly_neighbor_ids.get(id(f), set()),
                )

                # Eat a fly when close enough to the frog center
                if (f.pos - frog.pos).length_squared() <= (f.radius + FROG_RADIUS) ** 2:
                    for _ in range(8):
                        particles.append(Particle(f.pos, YELLOW))
                    flies.remove(f)
                    fly_count += 1
                    if fly_count >= FLIES_TO_WIN:
                        game_over = True
                        win = True

            # Hard positional correction — guarantee no two flies visually overlap
            resolve_fly_overlaps(flies)

            # Update snakes and their FSM decisions
            for s in snakes:
                s.update(dt, frog)

            # ------------- Bubble hit logic -------------
            for s in snakes:
                for b in frog.bubbles:
                    if (b.pos - s.pos).length_squared() <= (BUBBLE_RADIUS + s.radius) ** 2:
                        b.alive = False
                        if s.state == SnakeState.Aggro:
                            for _ in range(8):
                                particles.append(Particle(s.pos, (200, 200, 255)))
                            # Transition exactly as required: Aggro -> Harmless -> Confused
                            s.set_state(SnakeState.Harmless)
                            s.set_state(SnakeState.Confused)

            # Bubbles also pop early if they hit an obstacle rect (optional per brief)
                for b in frog.bubbles:
                        for rect in world.obstacles:
                            if circle_rect_intersect(b.pos, BUBBLE_RADIUS, rect):
                                b.alive = False
                                for _ in range(4):
                                    particles.append(Particle(b.pos, (200, 200, 255)))
                                break

            # ------------- Damage logic -------------
            for s in snakes:
                if s.state == SnakeState.Aggro and (s.pos - frog.pos).length_squared() <= (s.radius + FROG_RADIUS) ** 2:
                    if frog.can_be_hurt():
                        health -= 1
                        red_flash_timer = HURT_FLASH_DURATION
                        frog.start_hurt()
                        s.set_state(SnakeState.Harmless)
                        
                        if health <= 0:
                            game_over = True
                            win = False

            # Particles
            for p in list(particles):
                p.update(dt)
                if p.age >= p.lifetime:
                    particles.remove(p)

            # Red flash
            if red_flash_timer > 0:
                red_flash_timer -= dt

            # HUD Counter
            if debug_state.DEBUG:
                aggro_snakes = [s for s in snakes if s.state == SnakeState.Aggro]
                if aggro_snakes:
                    nearest = min(aggro_snakes, key=lambda s: (s.pos - frog.pos).length_squared())
                    dist = (nearest.pos - frog.pos).length()
                    if last_aggro_dist is not None and dt > 0:
                        close_speed = (last_aggro_dist - dist) / dt
                        avg_close_speed = avg_close_speed * 0.95 + close_speed * 0.05
                    last_aggro_dist = dist
                else:
                    last_aggro_dist = None
                    avg_close_speed = 0.0

        # ---------------- Draw ----------------
        screen.fill(BG)           # clear background
        draw_grid(screen)         # draw a soft grid
        world.draw(screen)        # draw obstacles

        for f in flies:           # draw flies
            f.draw(screen)
        for s in snakes:          # draw snakes
            s.draw(screen)
        frog.draw(screen)         # draw frog and bubbles

        # Draw particles
        for p in particles:
            p.draw(screen)

        # Draw Red Flash
        if red_flash_timer > 0:
            flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            alpha = min(255, max(0, int(255 * (red_flash_timer / HURT_FLASH_DURATION))))
            pygame.draw.rect(flash_surf, (255, 0, 0, alpha), flash_surf.get_rect(), width=10)
            screen.blit(flash_surf, (0, 0))

        # Draw hearts for health
        for i in range(START_HEALTH):
            color = RED if i < health else (80, 60, 60)
            draw_heart(screen, 16 + i * 26, 18, color)

        # Draw fly counter and control hint
        txt = font.render(f"Flies: {fly_count}/{FLIES_TO_WIN}", True, (240, 240, 240))
        screen.blit(txt, (16, 42))
        tips = font.render("Click to move, Space to bubble, R to restart", True, MUTED)
        screen.blit(tips, (16, 68))

        if debug_state.DEBUG:
            from entities.fly import FlyState
            from entities.snake import SnakeState as _SnakeState

            for sl in sliders:
                sl.draw(screen, font)
            if last_aggro_dist is not None:
                hud_txt = font.render(f"Pursue closing speed: {avg_close_speed:.1f} px/s", True, (255, 150, 150))
                screen.blit(hud_txt, (20, 220))

            #-- Transition log (bottom-left corner) ---
            log_y_start = HEIGHT - 20 - len(debug_state.TRANSITION_LOG) * 22
            for i, (ts, kind, idx, old_st, new_st) in enumerate(debug_state.TRANSITION_LOG):
                entry = f"{ts} {kind}#{idx} {old_st} -> {new_st}"
                log_surf = font.render(entry, True, (200, 230, 200))
                screen.blit(log_surf, (16, log_y_start + i * 22))

            # --- Stats panel (top-right corner) ---
            # fps_val   = clock.get_fps()
            # fly_flock   = sum(1 for f in flies if f.state == FlyState.Flock)
            # fly_flee    = sum(1 for f in flies if f.state == FlyState.Fleeing)
            # fly_idle    = sum(1 for f in flies if f.state == FlyState.Idle)
            # sn_counts   = {st: sum(1 for s in snakes if s.state == st) for st in _SnakeState}
            # stats_lines = [
            #     f"FPS: {fps_val:.1f}",
            #     f"Flies: Flock {fly_flock} | Fleeing {fly_flee} | Idle {fly_idle}",
            #     f"Snakes: Patrol {sn_counts[_SnakeState.PatrolAway]+sn_counts[_SnakeState.PatrolHome]}"
            #     f" | Aggro {sn_counts[_SnakeState.Aggro]}"
            #     f" | Harmless {sn_counts[_SnakeState.Harmless]}"
            #     f" | Confused {sn_counts[_SnakeState.Confused]}",
            #     f"Bubbles: {len(frog.bubbles)}",
            #     f"Particles: {len(particles)}",
            # # ]
            # panel_w = 480
            # panel_h = len(stats_lines) * 22 + 10
            # panel_x = WIDTH - panel_w - 10
            # panel_y = 10
            # panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            # panel_surf.fill((0, 0, 0, 140))
            # screen.blit(panel_surf, (panel_x, panel_y))
            # for li, line in enumerate(stats_lines):
            #     ls = font.render(line, True, (220, 220, 255))
            #     screen.blit(ls, (panel_x + 6, panel_y + 5 + li * 22))

            # --- Click-to-inspect floating info box ---
            # Clear selection if the inspected fly was caught
            if inspected_entity in flies or inspected_entity is None or inspected_entity is frog or inspected_entity in snakes:
                pass  # still valid
            else:
                inspected_entity = None

            if inspected_entity is not None:
                from entities.fly import Fly as _Fly
                from entities.snake import Snake as _Snake
                from entities.frog import Frog as _Frog
                ent = inspected_entity
                if isinstance(ent, _Fly):
                    etype = "Fly"
                elif isinstance(ent, _Snake):
                    etype = "Snake"
                else:
                    etype = "Frog"

                info_lines = [
                    f"{etype}#{id(ent) % 1000}",
                    f"Pos: ({int(ent.pos.x)}, {int(ent.pos.y)})",
                    f"Speed: {ent.vel.length():.1f} px/s",
                ]
                if isinstance(ent, _Fly):
                    info_lines.append(f"State: {ent.state.name}")
                    if ent.state == FlyState.Fleeing:
                        info_lines.append(f"scare_timer: {ent.scare_timer:.2f}s")
                    elif ent.state == FlyState.Idle:
                        info_lines.append(f"idle_timer: {ent.idle_timer:.2f}s")
                elif isinstance(ent, _Snake):
                    info_lines.append(f"State: {ent.state.name}")
                    if ent.state == _SnakeState.Confused:
                        info_lines.append(f"confused_timer: {ent.confused_timer:.2f}s")

                ibox_w = 220
                ibox_h = len(info_lines) * 22 + 10
                ibox_x = int(ent.pos.x) + ent.radius + 8
                ibox_y = int(ent.pos.y) - ibox_h - 8
                # Clamp to screen
                ibox_x = min(ibox_x, WIDTH - ibox_w - 4)
                ibox_y = max(ibox_y, 4)
                ibox_surf = pygame.Surface((ibox_w, ibox_h), pygame.SRCALPHA)
                ibox_surf.fill((0, 0, 0, 180))
                screen.blit(ibox_surf, (ibox_x, ibox_y))
                pygame.draw.rect(screen, (100, 200, 255), (ibox_x, ibox_y, ibox_w, ibox_h), 1)
                for li, line in enumerate(info_lines):
                    ls = font.render(line, True, (230, 230, 255))
                    screen.blit(ls, (ibox_x + 6, ibox_y + 5 + li * 22))

        # If game over, dim the screen and show a message
        if game_over:
            shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 160))
            screen.blit(shade, (0, 0))
            msg = "You won!" if win else "You died!"
            col = (90, 220, 120) if win else RED
            text = bigfont.render(msg, True, col)
            hint = font.render("Press R to restart", True, (240, 240, 240))
            rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10))
            screen.blit(text, rect)
            screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 44)))

        # Present the frame
        pygame.display.flip()

    # Clean shutdown
    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
</file>

<file path="settings.py">
# ============================================================================
# settings.py
# Purpose
#   Central place for all constants and tuning values.
#   You can tweak speeds, radii, and counts here without touching logic.
# Reading guide
#   Each variable has a short note so you know what it controls.
# ============================================================================

# Window size in pixels
WIDTH, HEIGHT = 1280, 720

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
FROG_SPEED  = 300.0       # top speed for the frog in pixels per second
HURT_INVULN = 3.0         # seconds of temporary invulnerability after damage
FROG_FACING_MIN_SPEED_SQ = 16.0 # speed for facing shotting
# Bubble setup
BUBBLE_RADIUS   = 8       # visual radius and collision radius
BUBBLE_SPEED    = 380.0   # how fast the bubble travels
BUBBLE_LIFETIME = 2.0     # seconds before the bubble pops automatically

# Fly setup
FLY_CLUSTER_COUNT = 4        # number of initial flock clusters
FLY_CLUSTER_SPAWN_RADIUS = 90.0  # max offset from a cluster center when spawning
NUM_FLIES = 10           # how many flies spawn
FLY_RADIUS = 8            # fly draw and collision radius
FLY_SPEED  = 120.0        # fly max speed

# Fly panic/fleeing tuning
FLEE_PANIC_RANGE    = 220.0   # distance at which panic scaling starts kicking in
FLEE_PANIC_EXPONENT = 2.4     # >1 = sharper, more dramatic ramp-up as distance shrinks
FLEE_PANIC_MAX_MULT = 3.0     # maximum multiplier applied to evade force at point-blank range
FLEE_BURST_STRENGTH = 360.0   # one-time velocity kick applied the instant a fly starts fleeing

# Fly FSM perception radii and timers
FLY_SCARED_RANGE      = 160.0   # frog proximity that triggers Fleeing
FLY_BUBBLE_FLEE_RANGE = 140.0   # bubble proximity that triggers Fleeing
FLY_CALM_RANGE        = 220.0   # frog and bubbles must both clear this to start calming
FLY_IDLE_DISTANCE     = 380.0   # frog distance beyond which an isolated fly may idle
FLY_IDLE_DELAY        = 10     # seconds of isolation+distance before entering Idle
FLY_SCARE_TIMER       = 0.6     # seconds a fly stays nervous after the last scare

# Boids neighborhood and weights
# These determine how flies react to neighbors
NEIGHBOR_RADIUS = 150.0   # how far a fly considers other flies as neighbors
REGROUP_RADIUS  = 500.0   # search radius for the nearest fly when totally alone
REGROUP_WEIGHT  = 0.6     # how gently an isolated fly steers back toward the group
SEP_RADIUS      = 40.0    # separation threshold distance
SEP_WEIGHT      = 2.0     # weight for separation force
COH_WEIGHT      = 0.8     # weight for cohesion force
ALI_WEIGHT      = 1.1     # weight for alignment force
ALI_STRENGTH    = 1.5     # base scale for the alignment force before ALI_WEIGHT is applied
ANCHOR_WEIGHT   = 0.6     # small pull to arena center to keep flock on screen
CATCHUP_GROUP_DELTA  = 1     # how many more neighbors the other group needs to trigger catch-up
CATCHUP_SPEED_MULT   = 1.6   # speed multiplier while hurrying to join a bigger group
CATCHUP_WEIGHT       = 1.4   # steering weight while catching up
CATCHUP_MIN_OWN_GROUP = 2     # only consider catch-up if my own group is this small or smaller 
CATCHUP_MAX_OWN_GROUP = 4    # only consider catch-up if my own group is this small or smaller
CATCHUP_SEARCH_RADIUS = 350.0 
COH_DEAD_ZONE_RADIUS  = 6.0  # boids cohesion: no pull if within this distance of flock center
COH_SLOW_ZONE_RADIUS  = 30.0 # boids cohesion: full-strength pull begins beyond this distance

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

# Snake FSM thresholds and obstacle-avoidance weight curve
SNAKE_ARRIVE_THRESHOLD    = 10.0  # distance considered "reached" for patrol/home targets
SNAKE_CONFUSED_DURATION   = 1.5   # seconds a snake wanders confused after reaching home
SNAKE_HARMLESS_SPEED_MULT = 0.9   # Harmless state moves slightly slower than normal
SNAKE_AVOID_WEIGHT_MIN    = 0.25  # avoid_weight floor, far from any obstacle
SNAKE_AVOID_WEIGHT_MAX    = 0.65  # avoid_weight ceiling, right next to an obstacle
SNAKE_AVOID_NEAR_DIST     = 80.0  # obstacle distance at which avoid_weight reaches max

# Obstacle avoidance tuning
AVOID_LOOKAHEAD       = 260.0   # how far the snake looks ahead when checking a corridor
AVOID_ANGLE_INCREMENT = 12      # degrees to rotate per step when searching for a free path
AVOID_MAX_ANGLE       = 160     # maximum deviation to try on either side
AVOID_MAX_ANGLE       = 160     # maximum deviation to try on either side
SNAKE_AVOID_RETREAT_RADIUS_MULT = 3.0  # if nearest obstacle is closer than radius * this, retreat instead of creeping forward

# Game rules
START_HEALTH = 3                 # how many hits the frog can take
FLIES_TO_WIN = 10                # win condition counter

# Visual/effect timing
PARTICLE_LIFETIME   = 2   # seconds a burst particle stays visible
HURT_FLASH_DURATION = 0.15  # seconds the red damage flash stays on screen
</file>

<file path="steering.py">
# ============================================================================
# steering.py
# Purpose
#   Implement all steering behaviours here. Each function computes a steering
#   force vector. Entities apply that force to their velocity each frame.
# Key idea
#   desired_velocity minus current_velocity gives the steering force.
#   Use dt in update loops when integrating velocity to keep motion consistent.
# ============================================================================

import math
from pygame.math import Vector2 as V2
from utils import limit, circlecast_hits_any_rect, nearest_point_on_rect
from settings import (
    ARRIVE_SLOW_RADIUS, ARRIVE_STOP_DAMPING, ARRIVE_STOP_RADIUS, ARRIVE_STOP_SNAP,
    AVOID_LOOKAHEAD, AVOID_ANGLE_INCREMENT, AVOID_MAX_ANGLE,
    ALI_STRENGTH, COH_DEAD_ZONE_RADIUS, COH_SLOW_ZONE_RADIUS,
    SNAKE_AVOID_RETREAT_RADIUS_MULT
)

# ---------------- Base behaviours ----------------

def seek(pos, vel, target, max_speed):
    """
    Move toward a target. Returns a steering force.
    desired = direction_to_target * max_speed
    steering = desired - current_velocity
    """
    d = target - pos
    if d.length_squared() == 0:
        return V2()
    desired = d.normalize() * max_speed
    return desired - vel

def flee(pos, vel, target, max_speed):
    """
    Move away from a target. This is the opposite of seek.
    You need to implement the mirror of seek using direction from threat to self.
    """
    d = pos - target
    if d.length_squared() == 0:
        return V2()
    desired = d.normalize() * max_speed
    return desired - vel

def arrive(pos, vel, target, max_speed, slow_radius=ARRIVE_SLOW_RADIUS, stop_radius=ARRIVE_STOP_RADIUS):
    """
    Like seek when far, but slow down near the target.
    Uses a smoothstep curve in the slow zone for natural ease-in/ease-out deceleration.
    Also actively damps the sideways (tangential) velocity component while inside the
    slow zone, so a fast approach from an angle settles in a straight line instead of
    arcing/orbiting around the target.
    """
    d = target - pos
    dist = d.length()

    if dist < stop_radius:
        return -vel  # Cancel velocity to stop

    direction = d.normalize()

    if dist < slow_radius:
        t = dist / slow_radius
        eased = t * t * (3.0 - 2.0 * t)
        desired_speed = max_speed * eased
        desired_vel = direction * desired_speed

        # Actively cancel the part of the current velocity that's sideways relative to
        # the target direction - this is what actually prevents orbiting, rather than
        # just giving the correction more distance to work with.
        radial_speed = vel.dot(direction)
        tangential = vel - direction * radial_speed
        desired_vel -= tangential * (1.0 - t)  # damp harder the closer we get
    else:
        desired_vel = direction * max_speed

    return desired_vel - vel

def apply_arrive_stop(
    pos,
    vel,
    target,
    dt,
    stop_radius=ARRIVE_STOP_RADIUS,
    damping=ARRIVE_STOP_DAMPING,
    snap=ARRIVE_STOP_SNAP,
):
    """
    Apply the final convergence after velocity integration.
    """

    if (target - pos).length() < stop_radius:
        vel *= max(0.0, 1.0 - dt * damping)

        if vel.length() < snap:
            vel = V2()

    return vel

def integrate_velocity(vel, force, dt, max_speed):
    """
    Apply a steering force to velocity using Euler integration.
    Then clamp to max speed and return the new velocity.
    Use this inside agent update methods after computing steering forces.
    """
    vel += limit(force, 500.0) * dt
    if vel.length() > max_speed:
        vel.scale_to_length(max_speed)
    return vel

# ---------------- Boids components ----------------

def boids_separation(me_pos, me_vel, neighbors, sep_radius, max_speed):
    """
    Push away from neighbors that are too close.
    """
    steering = V2()
    count = 0
    for n_pos, n_vel in neighbors:
        d = me_pos - n_pos
        dist = d.length()
        if 0 < dist < sep_radius:
            # Scale the repulsion so closer neighbors push harder
            steering += d.normalize() * (sep_radius / dist)
            count += 1
            
    if count > 0:
        steering /= count
        # Calculate standard steering force
        steering = steering.normalize() * max_speed
        return steering - me_vel
        
    return V2()

def boids_cohesion(me_pos, me_vel, neighbors, max_speed, dead_zone_radius=COH_DEAD_ZONE_RADIUS, slow_zone_radius=COH_SLOW_ZONE_RADIUS):
    """
    Pull toward the center of mass of neighbors.
    """
    if not neighbors:
        return V2()
        
    avg_pos = V2()
    for n_pos, n_vel in neighbors:
        avg_pos += n_pos
    avg_pos /= len(neighbors)

    target_vec = avg_pos - me_pos
    dist = target_vec.length()

    # Cancel out velocity if perfectly centered
    if dist < dead_zone_radius:
        return -me_vel * 0.5 
        
    # Scale desired speed similar to Arrive behavior
    if dist < slow_zone_radius:
        desired_speed = max_speed * (dist / slow_zone_radius)
    else:
        desired_speed = max_speed
        
    desired_vel = target_vec.normalize() * desired_speed
    return desired_vel - me_vel

def boids_alignment(me_vel, neighbors, max_speed):
    """
    Match the average velocity of neighbors.
    """
    if not neighbors:
        return V2()
        
    avg_vel = V2()
    for n_pos, n_vel in neighbors:
        avg_vel += n_vel
    avg_vel /= len(neighbors)

    if avg_vel.length_squared() == 0:
        return V2()

    # The average velocity direction is our desired direction
    desired_vel = avg_vel.normalize() * max_speed
    return desired_vel - me_vel

# ---------------- Obstacle avoidance blend ----------------

def seek_with_avoid(pos, vel, target, max_speed, radius, rects, preferred_angle=0.0):
    """
    Move towards a target, but sweep a path ahead using circle casts.
    If the direct path is blocked, try looking left and right at increasing angles
    until a clear path is found.
    """
    d = target - pos
    if d.length_squared() == 0:
        return (V2(0, 0), 0.0)
        
    base_dir = d.normalize()
    look_ahead = AVOID_LOOKAHEAD  # Tầm nhìn xa của con Rắn (khoảng cách quét)
    
    # Các góc lệch để kiểm tra hướng đi: ưu tiên đi thẳng (0 độ), sau đó quét từ từ sang 2 bên
    angles_to_check = [0]
    angle = AVOID_ANGLE_INCREMENT
    while angle <= AVOID_MAX_ANGLE:
        angles_to_check.extend([-angle, angle])
        angle += AVOID_ANGLE_INCREMENT
        
    if preferred_angle != 0.0 and preferred_angle in angles_to_check:
        angles_to_check.remove(preferred_angle)
        angles_to_check.insert(1, preferred_angle)  # right after 0, not before it
    
    for angle in angles_to_check:
        # Tạo hướng nhìn mới bằng cách xoay hướng gốc
        check_dir = base_dir.rotate(angle)
        
        # Điểm mút của tia quét
        p1 = pos + check_dir * look_ahead
        
        # Dùng hàm có sẵn của Pygame / utils để quét xem đường này có bị chặn không
        # (radius là bán kính con rắn, rects là danh sách các bức tường/vật cản)
        hit_wall = circlecast_hits_any_rect(pos, p1, radius, rects)
        
        if not hit_wall:
            # Nếu đường này thoáng (không hit_wall), ta sẽ di chuyển theo hướng này
            desired = check_dir * max_speed
            return (desired - vel, angle)
            
    # If every tested angle is still blocked, don't ram forward — back away from the nearest
    # obstacle instead, so the snake repositions and gets a fresh angle to search from next frame
    nearest_obstacle_point = None
    nearest_dist = float('inf')
    for r in rects:
        np = nearest_point_on_rect(pos, r)
        d = (pos - np).length()
        if d < nearest_dist:
            nearest_dist = d
            nearest_obstacle_point = np

    if nearest_obstacle_point is not None and nearest_dist < radius * SNAKE_AVOID_RETREAT_RADIUS_MULT:
        away = pos - nearest_obstacle_point
        retreat_dir = away.normalize() if away.length_squared() > 0 else -base_dir
        desired = retreat_dir * max_speed * 0.6
    else:
        # Not actually touching anything nearby — safe to creep forward slowly and re-try
        desired = base_dir * max_speed * 0.4

    return (desired - vel, 0.0)

def arrive_with_avoid(pos, vel, target, max_speed, radius, rects, preferred_angle=0.0,
                       slow_radius=ARRIVE_SLOW_RADIUS, stop_radius=ARRIVE_STOP_RADIUS):
    """
    Unified Arrive + obstacle avoidance for Patrol-style states.

    Picks ONE direction — whatever seek_with_avoid() decides on — and applies Arrive's
    slow/stop-radius speed taper to that single direction, instead of computing arrive()
    and seek_with_avoid() as two independent forces and summing them (which can fight
    each other near an obstacle and stall progress). Mirrors how Aggro already trusts
    seek_with_avoid completely rather than blending against it.

    Returns (force, angle) — same shape as seek_with_avoid, so callers can keep passing
    the returned angle back in as preferred_angle next frame.
    """
    d = target - pos
    dist = d.length()

    if dist < stop_radius:
        return -vel, preferred_angle

    avoid_force, angle = seek_with_avoid(pos, vel, target, max_speed, radius, rects,
                                          preferred_angle=preferred_angle)
    desired_dir_vel = avoid_force + vel
    direction = desired_dir_vel.normalize() if desired_dir_vel.length_squared() > 0 else d.normalize()

    if dist < slow_radius:
        t = dist / slow_radius
        eased = t * t * (3.0 - 2.0 * t)
        desired_speed = max_speed * eased
    else:
        desired_speed = max_speed

    desired_vel = direction * desired_speed
    return desired_vel - vel, angle

# ---------------- New behaviours to be implemented ----------------

def predict_future_position(pos, target_pos, target_vel, max_speed):
    """
    Shared prediction helper used by pursue(), evade(), and Aggro's unified
    seek_with_avoid call.
    Refined: Sử dụng tổng tốc độ tiếp cận để tính time_horizon chính xác hơn.
    """
    distance = (target_pos - pos).length()
    target_speed = target_vel.length()
    
    # Nếu mục tiêu gần như đang đứng im, không cần dự đoán tương lai
    if target_speed < 5.0:
        return target_pos
        
    # Tính tổng tốc độ tiếp cận để xác định thời gian gặp nhau thực tế
    closing_speed = max_speed + target_speed
    
    # Giảm cap xuống 1.5 giây để các pha rượt đuổi ở cự ly xa không bị nội suy quá đà
    time_horizon = min(distance / closing_speed, 1.5)
    
    return target_pos + target_vel * time_horizon

def pursue(pos, vel, target_pos, target_vel, max_speed):
    """
    Predict the future position of the target then seek that point.
    Suggested
      distance = |target_pos - pos|
      time_horizon = distance / (max_speed + small_eps)
      predicted    = target_pos + target_vel * time_horizon
      return seek toward predicted
    Replace simple seek in Snake Aggro with pursue for better interception.
    """
    predicted = predict_future_position(pos, target_pos, target_vel, max_speed)
    return seek(pos, vel, predicted, max_speed)

def evade(pos, vel, threat_pos, threat_vel, max_speed, threat_max_speed=None):
    """
    Predict the future position of a threat then flee from that point.
    Uses threat_max_speed for the prediction time horizon if provided, 
    preventing overshoot when the threat is much faster than the evader.
    """
    # Use the threat's actual speed for predicting its future position
    prediction_speed = threat_max_speed if threat_max_speed is not None else max_speed
    
    predicted = predict_future_position(pos, threat_pos, threat_vel, prediction_speed)
    return flee(pos, vel, predicted, max_speed)
import random

def wander_force(me_vel, max_speed, jitter_deg=12.0, circle_distance=24.0, circle_radius=18.0, rng_seed=None):
    """
    Return a small random steering vector for gentle drift.
    Classic wander
      Project a small circle ahead along current heading, then jitter the
      target point on that circle by a tiny random angle each update.
    """
    if not hasattr(wander_force, "_state"):
        wander_force._state = {}
        
    if rng_seed not in wander_force._state:
        rng = random.Random(rng_seed) if rng_seed is not None else random.Random()
        wander_force._state[rng_seed] = {
            'angle': rng.uniform(0, 360),
            'rng': rng
        }
        
    state = wander_force._state[rng_seed]
    rng = state['rng']
    
    # Jitter the angle
    state['angle'] += rng.uniform(-jitter_deg, jitter_deg)
    
    if me_vel.length_squared() == 0:
        heading = V2(1, 0)
    else:
        heading = me_vel.normalize()
        
    circle_center = heading * circle_distance
    
    displacement = V2(circle_radius, 0).rotate(state['angle'])
    
    wander_dir = circle_center + displacement
    
    if wander_dir.length_squared() > 0:
        desired_vel = wander_dir.normalize() * max_speed
    else:
        desired_vel = V2()
        
    return desired_vel - me_vel
</file>

</files>
