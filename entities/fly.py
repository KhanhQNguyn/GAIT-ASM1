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

    def update(self, dt, flies, frog, bounds_rect, bubbles):
        """
        Update FSM and behavior. Flies use perception to switch states.
        Parameters
          flies: list of all flies for neighborhood queries
          frog:  player agent used as a threat source
          bounds_rect: world rectangle for anchor force and containment
          bubbles: list of active bubbles to trigger panic
        """

        # Perception radii and timers for the FSM
        BubbleFleeRange = 140.0      # panic if bubble comes within this range
        StopFleeingRange = 220.0     # calm down when both frog and bubbles are beyond this
        IdleDistance = 380.0         # far enough to consider idling
        IdleDelay    = 2.0           # seconds of safety before entering Idle

        # Triggers based on the frog and bubbles
        dist_to_frog = (frog.pos - self.pos).length()
        scared_by_frog   = dist_to_frog < 160.0
        scared_by_bubble = self.sense_bubbles_close(bubbles, BubbleFleeRange)

        # ---------------- FSM transitions ----------------
        if self.state == FlyState.Flock:
            if scared_by_frog or scared_by_bubble:
                self._set_state(FlyState.Fleeing)
                self.scare_timer = 0.6
                # One-time velocity kick directly away from threat
                burst_dir = self.pos - frog.pos
                if burst_dir.length_squared() > 0:
                    burst_dir = burst_dir.normalize()
                else:
                    burst_dir = V2(0, -1)
                self.vel += burst_dir * settings.FLEE_BURST_STRENGTH
            else:
                # Build idle time only when calm and far
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
                self.scare_timer = 0.6

        elif self.state == FlyState.Idle:
            if scared_by_frog or scared_by_bubble:
                self._set_state(FlyState.Fleeing)
                self.scare_timer = 0.6
                # One-time velocity kick directly away from threat
                burst_dir = self.pos - frog.pos
                if burst_dir.length_squared() > 0:
                    burst_dir = burst_dir.normalize()
                else:
                    burst_dir = V2(0, -1)
                self.vel += burst_dir * settings.FLEE_BURST_STRENGTH
            elif dist_to_frog <= IdleDistance:
                self._set_state(FlyState.Flock)
                self.idle_timer = 0.0

        # ---------------- State behaviours ----------------
        if self.state == FlyState.Flock:
            # Build neighbor list for boids
            neighbors = []
            for f in flies:
                if f is self:
                    continue
                if (f.pos - self.pos).length_squared() <= NEIGHBOR_RADIUS ** 2:
                    neighbors.append((f.pos, f.vel))
            self._debug_neighbors = neighbors   # cache for debug drawing

            if len(neighbors) == 0:
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
                sep = boids_separation(self.pos, neighbors, sep_radius=settings.SEP_RADIUS)
                coh = boids_cohesion(self.pos, neighbors)
                ali = boids_alignment(self.vel, neighbors)
                force = sep * settings.SEP_WEIGHT + coh * settings.COH_WEIGHT + ali * settings.ALI_WEIGHT

            # Gentle anchor toward arena center to avoid drifting out of bounds
            center = V2(bounds_rect.centerx, bounds_rect.centery)
            force += (center - self.pos) * ANCHOR_WEIGHT * 0.002

            # Integrate velocity
            self.vel += limit(force, 240.0) * dt

        elif self.state == FlyState.Fleeing:
            force = evade(self.pos, self.vel, frog.pos, frog.vel, FLY_SPEED)

            # Scale evade force by proximity — the closer the frog, the sharper the panic
            closeness = 1.0 - min(dist_to_frog, settings.FLEE_PANIC_RANGE) / settings.FLEE_PANIC_RANGE
            panic_mult = 1.0 + (settings.FLEE_PANIC_MAX_MULT - 1.0) * (closeness ** settings.FLEE_PANIC_EXPONENT)
            force *= panic_mult

            # Anchor blend so the group does not disappear off screen
            center = V2(bounds_rect.centerx, bounds_rect.centery)
            force += (center - self.pos) * ANCHOR_WEIGHT * 0.002

            self.vel += limit(force, 420.0) * dt

        elif self.state == FlyState.Idle:
            force = wander_force(self.vel, rng_seed=self._rng_seed)
            self.vel += limit(force, 120.0) * dt
            self.vel *= 0.98  # mild damping so idle feels soft

        # Speed clamp and position integrate
        if self.vel.length() > FLY_SPEED:
            self.vel.scale_to_length(FLY_SPEED)
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
            draw_debug_overlay(surf, self.pos, self.vel, perception_radii, self.state.name)
