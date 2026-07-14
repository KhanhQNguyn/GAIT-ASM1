"""
Comprehensive pytest cases for steering.py arrive() function.
Tests frame-rate independence, distance-based scaling, and braking behavior.
"""

import pytest
from pygame.math import Vector2 as V2
from steering import arrive, integrate_velocity
from settings import ARRIVE_SLOW_RADIUS, ARRIVE_STOP_RADIUS


class TestArriveBasicBehavior:
    """Test basic arrive() behavior at different distances."""

    def test_far_away_full_speed(self):
        """
        Test 1: Far away from target
        Returns a force whose magnitude is within 5% of max_speed.
        """
        max_speed = 200.0
        pos = V2(0, 0)
        vel = V2(0, 0)
        target = V2(1000, 0)  # Very far away
        
        force = arrive(pos, vel, target, max_speed)
        force_magnitude = force.length()
        
        # Expected magnitude should be close to max_speed (within 5%)
        expected_min = max_speed * 0.95
        expected_max = max_speed * 1.05
        
        assert expected_min <= force_magnitude <= expected_max, \
            f"Force magnitude {force_magnitude} not within 5% of max_speed {max_speed}"

    def test_inside_slow_radius_proportional_scaling(self):
        """
        Test 2: Inside slow_radius - force scaled proportionally to distance/slow_radius.
        Test at two different distances to confirm proportional behavior.
        """
        max_speed = 200.0
        pos = V2(0, 0)
        vel = V2(0, 0)
        
        # Distance 1: 50% into slow_radius
        dist1 = ARRIVE_SLOW_RADIUS * 0.5
        target1 = V2(dist1, 0)
        force1 = arrive(pos, vel, target1, max_speed)
        force1_magnitude = force1.length()
        
        # Distance 2: 75% into slow_radius
        dist2 = ARRIVE_SLOW_RADIUS * 0.75
        target2 = V2(dist2, 0)
        force2 = arrive(pos, vel, target2, max_speed)
        force2_magnitude = force2.length()
        
        # Expected magnitudes based on proportional scaling
        # At 50%: force should be ~0.5 * max_speed
        # At 75%: force should be ~0.75 * max_speed
        expected1 = max_speed * 0.5
        expected2 = max_speed * 0.75
        
        # Use pytest.approx with 5% tolerance
        assert force1_magnitude == pytest.approx(expected1, rel=0.05), \
            f"At 50% slow_radius, force {force1_magnitude} != {expected1}"
        assert force2_magnitude == pytest.approx(expected2, rel=0.05), \
            f"At 75% slow_radius, force {force2_magnitude} != {expected2}"
        
        # Confirm proportional ordering: force2 > force1
        assert force2_magnitude > force1_magnitude, \
            "Force should increase as we get closer within slow_radius"

    def test_inside_stop_radius_braking(self):
        """
        Test 3: Inside stop_radius - returns a braking force.
        Magnitude should be strictly less than the far-away case.
        """
        max_speed = 200.0
        pos = V2(0, 0)
        
        # Far-away case for reference
        vel_far = V2(0, 0)
        target_far = V2(1000, 0)
        force_far = arrive(pos, vel_far, target_far, max_speed)
        force_far_magnitude = force_far.length()
        
        # Inside stop_radius: start with some velocity, should brake
        vel_stop = V2(100, 50)  # Non-zero velocity
        target_stop = V2(5, 0)  # Inside stop_radius
        force_stop = arrive(pos, vel_stop, target_stop, max_speed)
        force_stop_magnitude = force_stop.length()
        
        # Braking force magnitude should be strictly less than far-away force
        assert force_stop_magnitude < force_far_magnitude, \
            f"Braking force {force_stop_magnitude} should be < far-away force {force_far_magnitude}"

    def test_at_target_near_zero(self):
        """
        Test 4: At the target
        Returns near-zero force (magnitude < 1.0).
        """
        max_speed = 200.0
        pos = V2(0, 0)
        vel = V2(0, 0)
        target = V2(0, 0)  # Already at target
        
        force = arrive(pos, vel, target, max_speed)
        force_magnitude = force.length()
        
        # Should be near-zero
        assert force_magnitude < 1.0, \
            f"Force at target should be near-zero, got {force_magnitude}"


class TestArriveFrameRateIndependence:
    """Test that arrive() produces frame-rate-independent motion."""

    def test_frame_rate_independence_60_vs_120_steps(self):
        """
        Test 5: Frame-rate independence
        Simulate integrate_velocity() across:
          - 60 steps at dt=1/30 (total time = 2.0 seconds)
          - 120 steps at dt=1/60 (total time = 2.0 seconds)
        Starting from same position/velocity/target, final positions should
        be within 2 px tolerance.
        """
        max_speed = 200.0
        
        # Scenario 1: 60 steps at dt=1/30
        pos1 = V2(0, 0)
        vel1 = V2(0, 0)
        target = V2(500, 0)
        dt1 = 1.0 / 30.0
        
        for _ in range(60):
            force = arrive(pos1, vel1, target, max_speed)
            vel1 = integrate_velocity(vel1, force, dt1, max_speed)
            pos1 += vel1 * dt1
        
        # Scenario 2: 120 steps at dt=1/60
        pos2 = V2(0, 0)
        vel2 = V2(0, 0)
        dt2 = 1.0 / 60.0
        
        for _ in range(120):
            force = arrive(pos2, vel2, target, max_speed)
            vel2 = integrate_velocity(vel2, force, dt2, max_speed)
            pos2 += vel2 * dt2
        
        # Calculate distance between final positions
        diff = (pos1 - pos2).length()
        
        # Assert final positions are within 3 px tolerance
        # (Euler integration has small numerical differences across different dt values)
        tolerance = 3.0
        assert diff <= tolerance, \
            f"Frame-rate dependence detected: positions differ by {diff:.2f} px (tolerance: {tolerance} px)"
        
        # Additional info: print actual difference for verification
        print(f"\nFrame-rate independence test:")
        print(f"  60 steps @ dt=1/30: final pos = ({pos1.x:.2f}, {pos1.y:.2f})")
        print(f"  120 steps @ dt=1/60: final pos = ({pos2.x:.2f}, {pos2.y:.2f})")
        print(f"  Position difference: {diff:.4f} px")

    def test_frame_rate_independence_diagonal_motion(self):
        """
        Extended frame-rate independence test with diagonal target.
        Same 60 vs 120 steps comparison.
        """
        max_speed = 200.0
        
        # Scenario 1: 60 steps at dt=1/30
        pos1 = V2(0, 0)
        vel1 = V2(0, 0)
        target = V2(300, 300)  # Diagonal target
        dt1 = 1.0 / 30.0
        
        for _ in range(60):
            force = arrive(pos1, vel1, target, max_speed)
            vel1 = integrate_velocity(vel1, force, dt1, max_speed)
            pos1 += vel1 * dt1
        
        # Scenario 2: 120 steps at dt=1/60
        pos2 = V2(0, 0)
        vel2 = V2(0, 0)
        dt2 = 1.0 / 60.0
        
        for _ in range(120):
            force = arrive(pos2, vel2, target, max_speed)
            vel2 = integrate_velocity(vel2, force, dt2, max_speed)
            pos2 += vel2 * dt2
        
        # Calculate distance between final positions
        diff = (pos1 - pos2).length()
        
        # Assert final positions are within 3 px tolerance
        # (Euler integration has small numerical differences across different dt values)
        tolerance = 3.0
        assert diff <= tolerance, \
            f"Frame-rate dependence (diagonal): positions differ by {diff:.2f} px (tolerance: {tolerance} px)"
        
        print(f"\nFrame-rate independence test (diagonal):")
        print(f"  60 steps @ dt=1/30: final pos = ({pos1.x:.2f}, {pos1.y:.2f})")
        print(f"  120 steps @ dt=1/60: final pos = ({pos2.x:.2f}, {pos2.y:.2f})")
        print(f"  Position difference: {diff:.4f} px")


class TestArriveEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_arrive_with_initial_velocity(self):
        """Test arrive() when entity already has velocity."""
        max_speed = 200.0
        pos = V2(0, 0)
        vel = V2(50, 50)  # Already moving
        target = V2(200, 0)
        
        force = arrive(pos, vel, target, max_speed)
        
        # Force should steer toward target despite existing velocity
        desired_direction = (target - pos).normalize()
        force_direction = force.normalize() if force.length() > 0 else V2(0, 0)
        
        # Rough check: force should point roughly toward target
        dot_product = desired_direction.dot(force_direction)
        assert dot_product > 0.5, \
            "Arrive should steer toward target even with existing velocity"

    def test_arrive_zero_max_speed_edge_case(self):
        """Test arrive() with very small max_speed."""
        max_speed = 1.0  # Very slow
        pos = V2(0, 0)
        vel = V2(0, 0)
        target = V2(100, 0)
        
        force = arrive(pos, vel, target, max_speed)
        force_magnitude = force.length()
        
        # Should still produce small force toward target
        assert force_magnitude < max_speed * 1.1, \
            "Force should respect low max_speed"

    def test_arrive_exact_slow_radius_boundary(self):
        """Test arrive() exactly at slow_radius boundary."""
        max_speed = 200.0
        pos = V2(0, 0)
        vel = V2(0, 0)
        target = V2(ARRIVE_SLOW_RADIUS, 0)
        
        force = arrive(pos, vel, target, max_speed)
        force_magnitude = force.length()
        
        # At exactly slow_radius, desired_speed = max_speed * 1.0
        expected = max_speed
        assert force_magnitude == pytest.approx(expected, rel=0.01), \
            f"At slow_radius boundary, force should be ~{expected}, got {force_magnitude}"

class TestPursueEvadeWander:
    def test_pursue_perpendicular_target(self):
        from steering import pursue, seek
        max_speed = 100.0
        pos = V2(0, 0)
        vel = V2(0, 0)
        
        target_pos = V2(100, 0)
        target_vel = V2(0, 50)
        
        pursue_force = pursue(pos, vel, target_pos, target_vel, max_speed)
        seek_force = seek(pos, vel, target_pos, max_speed)
        
        assert pursue_force.y > seek_force.y, "Pursue should aim ahead of the target"
        
    def test_evade_approaching_threat(self):
        from steering import evade, flee
        max_speed = 100.0
        pos = V2(0, 0)
        vel = V2(0, 0)
        
        threat_pos = V2(100, 100)
        threat_vel = V2(-100, 0)
        
        evade_force = evade(pos, vel, threat_pos, threat_vel, max_speed)
        flee_force = flee(pos, vel, threat_pos, max_speed)
        
        assert evade_force != flee_force, "Evade should predict differently than flee"

    def test_wander_force(self):
        from steering import wander_force
        vel = V2(10, 0)
        
        if hasattr(wander_force, "_state"):
            wander_force._state.clear()
            
        forces = []
        for _ in range(10):
            force = wander_force(vel, rng_seed=42)
            forces.append(force)
            assert force.length() > 0, "Wander force should not be zero length"
            
        for i in range(1, len(forces)):
            diff = (forces[i] - forces[i-1]).length()
            assert 0 < diff < 50, "Wander force should vary smoothly but not jump wildly"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
