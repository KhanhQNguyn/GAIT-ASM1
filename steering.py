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
from numpy import diff
from pygame.math import Vector2 as V2
from utils import limit, circlecast_hits_any_rect
from settings import (
    ARRIVE_SLOW_RADIUS, ARRIVE_STOP_RADIUS,
    AVOID_LOOKAHEAD, AVOID_ANGLE_INCREMENT, AVOID_MAX_ANGLE
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
    Returns a steering force following the desired_velocity - current_velocity pattern.
    Rules:
      If distance < stop_radius, return a force that cancels leftover velocity
      If distance < slow_radius, scale desired speed by distance / slow_radius
      Otherwise use full speed
    This removes overshoot and jitter around the target.
    """
    d = target - pos
    dist = d.length()
    
    if dist < stop_radius:
        return -vel  # Cancel velocity to stop
    
    if dist < slow_radius:
        desired_speed = max_speed * (dist / slow_radius)
        desired_vel = d.normalize() * desired_speed
    else:
        desired_vel = d.normalize() * max_speed
    
    return desired_vel - vel

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

def boids_separation(me_pos, neighbors, sep_radius):
    """
    Push away from neighbors that are too close.
    neighbors: list of tuples (neighbor_pos, neighbor_vel)
    Typical approach
      For each neighbor inside sep_radius, add a vector pointing away with
      magnitude inversely proportional to distance. Normalize at the end.
    """
    steering = V2()
    count = 0
    for n_pos, n_vel in neighbors:
        d = me_pos - n_pos
        dist = d.length()
        if 0 < dist < sep_radius:
            steering += d.normalize() / dist  # Inverse proportional to distance
            count += 1
    if count > 0:
        steering /= count
        if steering.length() > 0:
            return steering
    return V2()

def boids_cohesion(me_pos, neighbors):
    """
    Pull toward the average position of neighbors.
    Typical approach
      Compute the center of mass of neighbors then steer toward that point.
    """
    if not neighbors:
        return V2()
    avg_pos = V2()
    for n_pos, n_vel in neighbors:
        avg_pos += n_pos
        
    avg_pos /= len(neighbors)

    desired = avg_pos - me_pos
    if desired.length() > 0:
        desired = desired.normalize()
    return desired

def boids_alignment(me_vel, neighbors):
    """
    Match the average velocity of neighbors.
    Typical approach
    Compute the average heading of neighbors then steer toward that heading.
    """
    if not neighbors:
        return V2()
    avg_vel = V2()
    for n_pos, n_vel in neighbors:
        avg_vel += n_vel
    avg_vel /= len(neighbors)
    
    steering = avg_vel - me_vel
    
    return steering * 0.1

# ---------------- Obstacle avoidance blend ----------------

def seek_with_avoid(pos, vel, target, max_speed, radius, rects):
    """
    Move towards a target, but sweep a path ahead using circle casts.
    If the direct path is blocked, try looking left and right at increasing angles
    until a clear path is found.
    """
    d = target - pos
    if d.length_squared() == 0:
        return V2(0, 0)
        
    base_dir = d.normalize()
    look_ahead = AVOID_LOOKAHEAD  # Tầm nhìn xa của con Rắn (khoảng cách quét)
    
    # Các góc lệch để kiểm tra hướng đi: ưu tiên đi thẳng (0 độ), sau đó quét từ từ sang 2 bên
    angles_to_check = [0]
    angle = AVOID_ANGLE_INCREMENT
    while angle <= AVOID_MAX_ANGLE:
        angles_to_check.extend([-angle, angle])
        angle += AVOID_ANGLE_INCREMENT
    
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
            return desired - vel
            
    # Nếu bị bao vây 4 phía không còn đường thoát, ráng lách thẳng hướng cũ nhưng chậm lại
    desired = base_dir * max_speed
    return desired - vel

# ---------------- New behaviours to be implemented ----------------

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
    small_eps = 1e-6
    distance = (target_pos - pos).length()
    time_horizon = distance / (max_speed + small_eps)
    predicted = target_pos + target_vel * time_horizon
    return seek(pos, vel, predicted, max_speed)

def evade(pos, vel, threat_pos, threat_vel, max_speed):
    """
    Predict the future position of a threat then flee from that point.
    This is the inverse of pursue. Use the same prediction idea.
    """
    small_eps = 1e-6
    distance = (threat_pos - pos).length()
    time_horizon = distance / (max_speed + small_eps)
    predicted = threat_pos + threat_vel * time_horizon
    return flee(pos, vel, predicted, max_speed)
import random

def wander_force(me_vel, jitter_deg=12.0, circle_distance=24.0, circle_radius=18.0, rng_seed=None):
    """
    Return a small random steering vector for gentle drift.
    Classic wander
      Project a small circle ahead along current heading, then jitter the
      target point on that circle by a tiny random angle each update.
    Use this for Fly Idle and Snake Confused.
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
    
    desired = circle_center + displacement
    return desired - me_vel

