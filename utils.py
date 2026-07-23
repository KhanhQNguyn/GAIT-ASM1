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