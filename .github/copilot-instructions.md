# Copilot instructions for GAIT-ASM1

## Project scope and entrypoint
- The active Python project is in `GAIT-ASM1/` (this directory). Run commands from here.
- Main entrypoint: `python main.py`

## Build, test, and lint commands
- This project does not define a build system.
- This project does not include an automated test suite (`tests/`, `pytest.ini`, `pyproject.toml`, `tox.ini` were not found).
- This project does not define a lint configuration (`.flake8`, `ruff`, `pylint`, etc. were not found).
- Manual runtime check:
  - `python main.py`

## High-level architecture
- `main.py` is the game loop and orchestrator:
  - Creates world and agents in `reset()`
  - Per-frame order is: input -> update frog -> update flies -> update snakes -> collision/rule checks -> draw
  - Global `DEBUG` flag is toggled with `F1`
- `settings.py` is the single source of gameplay constants (sizes, speeds, ranges, weights, win/health rules).
- `steering.py` contains steering primitives and motion helpers (seek/flee/arrive, boids parts, obstacle-avoid blend, velocity integration).
- `entities/` contains agent logic:
  - `frog.py`: player agent + bubble projectiles + hurt/invulnerability timer
  - `fly.py`: fly FSM (`Flock`, `Fleeing`, `Idle`) combining boids and threat reactions
  - `snake.py`: snake FSM (`PatrolAway`, `PatrolHome`, `Aggro`, `Harmless`, `Confused`) with chase/patrol behaviors
- `world.py` defines static rectangular obstacles (deterministic seeded generation) used by snake avoidance and rendering.
- `utils.py` provides shared math/collision/drawing utilities (clamp/limit, circlecast helpers, debug overlay, background grid).

## Key codebase conventions
- **FSM update pattern**: both fly and snake evaluate state transitions first, then run behavior for the resulting state in the same `update()` call.
- **Steering contract**: steering functions return force vectors; entities handle integration with `dt` and speed clamping (usually via `integrate_velocity` or `limit` + local integration).
- **Config centralization**: gameplay tuning values belong in `settings.py`, not hardcoded across entities.
- **Distance checks**: collision/proximity checks generally use squared distance comparisons (`length_squared`) for efficiency.
- **Debug overlay wiring**: entities conditionally render debug overlays by checking `main.DEBUG` (importing `main` inside draw paths).
- **Obstacle interaction model**: path blocking/avoidance should use existing circlecast helpers in `utils.py` and `seek_with_avoid()` in `steering.py`.
- **Intentional scaffolding**: several functions/blocks are left as guided TODOs/NotImplemented placeholders; preserve this instructional structure unless explicitly asked to complete it.
