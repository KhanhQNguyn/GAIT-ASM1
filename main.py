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

from utils import draw_heart
import sys, random, math
import pygame
from settings import *
from utils import draw_grid, draw_debug_overlay
from world import World
from entities.frog import Frog
from entities.fly import Fly
from entities.snake import Snake, SnakeState
import debug_state
from pygame.math import Vector2 as V2

class Particle:
    def __init__(self, pos, color):
        self.pos = V2(pos)
        self.vel = V2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * random.uniform(50, 150)
        self.lifetime = PARTICLE_LIFETIME
        self.age = 0.0
        self.color = color

    def update(self, dt):
        self.pos += self.vel * dt
        self.age += dt

    def draw(self, surf):
        if self.age < self.lifetime:
            radius = max(1, int(4 * (1 - self.age / self.lifetime)))
            pygame.draw.circle(surf, self.color, self.pos, radius)

class Slider:
    def __init__(self, x, y, w, h, min_v, max_v, initial, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_v = min_v
        self.max_v = max_v
        self.val = initial
        self.label = label
        self.dragging = False

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.rect.collidepoint(e.pos):
                self.dragging = True
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.dragging = False
        elif e.type == pygame.MOUSEMOTION:
            if self.dragging:
                rel_x = max(0, min(e.pos[0] - self.rect.x, self.rect.width))
                self.val = self.min_v + (self.max_v - self.min_v) * (rel_x / self.rect.width)

    def draw(self, surf, font):
        pygame.draw.rect(surf, (100, 100, 100), self.rect)
        rel_w = int((self.val - self.min_v) / (self.max_v - self.min_v) * self.rect.width)
        pygame.draw.rect(surf, (200, 200, 200), (self.rect.x, self.rect.y, rel_w, self.rect.height))
        txt = font.render(f"{self.label}: {self.val:.1f}", True, (255, 255, 255))
        surf.blit(txt, (self.rect.x + self.rect.width + 10, self.rect.y))

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
        frog = Frog((WIDTH * 0.5, HEIGHT * 0.5), world.obstacles)

        # Generate cluster centers
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
            fx = center.x + radius * math.cos(angle)
            fy = center.y + radius * math.sin(angle)
            fx = max(FLY_RADIUS + 4, min(WIDTH - (FLY_RADIUS + 4), fx))
            fy = max(FLY_RADIUS + 4, min(HEIGHT - (FLY_RADIUS + 4), fy))
            flies.append(Fly((fx, fy)))

        # Create snakes with patrol points mirrored across the screen
        snakes = []
        for i in range(NUM_SNAKES):
            px = 140 + i * 320
            py = 120 if i % 2 == 0 else HEIGHT - 140
            patrol = (WIDTH - px, HEIGHT - py)
            snakes.append(Snake((px, py), patrol, world.obstacles))

        return world, frog, flies, snakes

    # Build initial state
    world, frog, flies, snakes = reset()

    import settings
    sliders = [
        Slider(20, 100, 100, 20, 0.0, 5.0, settings.SEP_WEIGHT, "SEP_WEIGHT"),
        Slider(20, 130, 100, 20, 0.0, 5.0, settings.COH_WEIGHT, "COH_WEIGHT"),
        Slider(20, 160, 100, 20, 0.0, 5.0, settings.ALI_WEIGHT, "ALI_WEIGHT"),
        Slider(20, 190, 100, 20, 50.0, 500.0, settings.AGGRO_RANGE, "AGGRO_RANGE"),
    ]

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
            neighbor_counts = {}
            for f in flies:
                cnt = sum(
                    1 for g in flies
                    if g is not f and (g.pos - f.pos).length_squared() <= NEIGHBOR_RADIUS ** 2
                )
                neighbor_counts[id(f)] = cnt

            # Update flies and check if any fly gets caught by the frog
            for f in list(flies):
                f.update(dt, flies, frog, world.rect, frog.bubbles, neighbor_counts)

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
                            s.set_state(SnakeState.Harmless)

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

            # Live FSM transition log — bottom-left corner, most recent at bottom
            log_y_start = HEIGHT - 20 - len(debug_state.TRANSITION_LOG) * 22
            for i, (ts, kind, idx, old_st, new_st) in enumerate(debug_state.TRANSITION_LOG):
                entry = f"{ts} {kind}#{idx} {old_st} -> {new_st}"
                log_surf = font.render(entry, True, (200, 230, 200))
                screen.blit(log_surf, (16, log_y_start + i * 22))

            # --- Stats panel (top-right corner) ---
            fps_val   = clock.get_fps()
            fly_flock   = sum(1 for f in flies if f.state == FlyState.Flock)
            fly_flee    = sum(1 for f in flies if f.state == FlyState.Fleeing)
            fly_idle    = sum(1 for f in flies if f.state == FlyState.Idle)
            sn_counts   = {st: sum(1 for s in snakes if s.state == st) for st in _SnakeState}
            stats_lines = [
                f"FPS: {fps_val:.1f}",
                f"Flies: Flock {fly_flock} | Fleeing {fly_flee} | Idle {fly_idle}",
                f"Snakes: Patrol {sn_counts[_SnakeState.PatrolAway]+sn_counts[_SnakeState.PatrolHome]}"
                f" | Aggro {sn_counts[_SnakeState.Aggro]}"
                f" | Harmless {sn_counts[_SnakeState.Harmless]}"
                f" | Confused {sn_counts[_SnakeState.Confused]}",
                f"Bubbles: {len(frog.bubbles)}",
                f"Particles: {len(particles)}",
            ]
            panel_w = 480
            panel_h = len(stats_lines) * 22 + 10
            panel_x = WIDTH - panel_w - 10
            panel_y = 10
            panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel_surf.fill((0, 0, 0, 140))
            screen.blit(panel_surf, (panel_x, panel_y))
            for li, line in enumerate(stats_lines):
                ls = font.render(line, True, (220, 220, 255))
                screen.blit(ls, (panel_x + 6, panel_y + 5 + li * 22))

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
