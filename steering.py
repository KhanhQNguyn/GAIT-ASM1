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
    seek_with_avoid call. Returns the predicted future position of a moving target.
    """
    small_eps = 1e-6
    distance = (target_pos - pos).length()
    time_horizon = min(distance / (max_speed + small_eps), 2.0)
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

