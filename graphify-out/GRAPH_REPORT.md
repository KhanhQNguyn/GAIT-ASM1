# Graph Report - .  (2026-07-14)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 117 nodes · 202 edges · 9 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3cd57473`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fly.py
- arrive
- Frog
- snake.py
- Fly
- seek_with_avoid
- integrate_velocity
- Snake

## God Nodes (most connected - your core abstractions)
1. `arrive()` - 16 edges
2. `Frog` - 10 edges
3. `integrate_velocity()` - 10 edges
4. `draw_debug_overlay()` - 9 edges
5. `Fly` - 7 edges
6. `Snake` - 7 edges
7. `Bubble` - 6 edges
8. `main()` - 6 edges
9. `TestArriveBasicBehavior` - 6 edges
10. `limit()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `Frog`  [EXTRACTED]
  main.py → entities/frog.py
- `main()` --calls--> `Snake`  [EXTRACTED]
  main.py → entities/snake.py
- `main()` --calls--> `draw_grid()`  [EXTRACTED]
  main.py → utils.py
- `integrate_velocity()` --calls--> `limit()`  [EXTRACTED]
  steering.py → utils.py
- `main()` --calls--> `Fly`  [EXTRACTED]
  main.py → entities/fly.py

## Import Cycles
- None detected.

## Communities (9 total, 0 thin omitted)

### Community 0 - "fly.py"
Cohesion: 0.15
Nodes (18): FlyState, Enum, # TODO: compute boids forces, # TODO: replace simple flee with predictive evade for extra credit, # TODO: use wander_force to provide gentle drifting, Update FSM and behavior. Flies use perception to switch states.         Paramete, boids_alignment(), boids_cohesion() (+10 more)

### Community 1 - "arrive"
Cohesion: 0.13
Nodes (13): arrive(), Like seek when far, but slow down near the target.     Returns a steering force, Test basic arrive() behavior at different distances., Test 1: Far away from target         Returns a force whose magnitude is within 5, Test edge cases and corner scenarios., Test arrive() when entity already has velocity., Test arrive() with very small max_speed., Test arrive() exactly at slow_radius boundary. (+5 more)

### Community 2 - "Frog"
Cohesion: 0.12
Nodes (7): Bubble, Frog, Simple projectile that moves in a straight line and pops after a short time., Set a new target the frog will move toward using Arrive., Spawn a bubble just in front of the frog, moving along the facing direction., Begin the invulnerability window after damage., Return True if the frog can take damage right now.

### Community 3 - "snake.py"
Cohesion: 0.27
Nodes (8): Enum, # TODO: use wander_force for a gentle random walk during confusion, # TODO: replace seek with pursue for smarter interception, SnakeState, draw_debug_overlay(), draw_grid(), Draw a light grid to help the eye judge motion and distance.     The grid has no, Draw debug overlay for an entity: velocity vector, perception radii, and state n

### Community 4 - "Fly"
Cohesion: 0.17
Nodes (6): Fly, Return True if any bubble is within range r of the fly., main(), Create a few rectangles with a fixed random seed for reproducibility., Render each obstacle with a fill and a subtle outline., World

### Community 5 - "seek_with_avoid"
Cohesion: 0.15
Nodes (12): Move towards a target, but sweep a path ahead using circle casts.     If the dir, seek_with_avoid(), circle_rect_intersect(), circlecast_hits_any_rect(), clamp(), nearest_point_on_rect(), Limit a scalar value x so it stays between a and b inclusive., Return the closest point on an axis aligned rectangle to a given point. (+4 more)

### Community 6 - "integrate_velocity"
Cohesion: 0.24
Nodes (7): integrate_velocity(), Apply a steering force to velocity using Euler integration.     Then clamp to ma, Comprehensive pytest cases for steering.py arrive() function. Tests frame-rate i, Test that arrive() produces frame-rate-independent motion., Test 5: Frame-rate independence         Simulate integrate_velocity() across:, Extended frame-rate independence test with diagonal target.         Same 60 vs 1, TestArriveFrameRateIndependence

### Community 7 - "Snake"
Cohesion: 0.25
Nodes (5): Switch to a new FSM state., Update state transitions based on distance to frog and timers.         Then comp, Snake, Move toward a target. Returns a steering force.     desired = direction_to_targe, seek()

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `arrive()` connect `arrive` to `fly.py`, `snake.py`, `seek_with_avoid`, `integrate_velocity`, `Snake`?**
  _High betweenness centrality (0.282) - this node is a cross-community bridge._
- **Why does `Frog` connect `Frog` to `snake.py`, `Fly`, `seek_with_avoid`?**
  _High betweenness centrality (0.149) - this node is a cross-community bridge._
- **Why does `World` connect `Fly` to `snake.py`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Should `arrive` be split into smaller, more focused modules?**
  _Cohesion score 0.12631578947368421 - nodes in this community are weakly interconnected._
- **Should `Frog` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._