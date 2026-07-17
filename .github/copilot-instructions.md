# Copilot instructions for GAIT-ASM1

## Project scope and entrypoint
- The active Python project is in `GAIT-ASM1/` (this directory). Run commands from here.
- Main entrypoint: `python main.py`

## Build, test, and lint commands
- This project does not define a build system.
- This project includes a comprehensive pytest automated test suite in `tests/test_steering.py` with 15+ passing tests covering all steering behaviors.
- This project does not define a lint configuration (`.flake8`, `ruff`, `pylint`, etc. were not found).
- Manual runtime check:
  - `python main.py`

## High-level architecture
- `main.py` is the game loop and orchestrator:
  - Creates world and agents in `reset()` using clustered spawn points with a nearest-group regroup fallback.
  - Per-frame order is: input -> update frog -> update flies -> update snakes -> collision/rule checks -> draw
- `debug_state.py` contains the global `DEBUG` flag which is toggled with `F1`.
- `settings.py` is the single source of gameplay constants (sizes, speeds, ranges, weights, win/health rules).
- `steering.py` contains steering primitives and motion helpers (seek/flee/arrive, boids parts, obstacle-avoid blend, velocity integration).
- `pursue`, `evade`, and `wander_force` are fully implemented and wired into agents.
- `seek_with_avoid` returns a `(force, chosen_angle)` tuple with sticky-angle hysteresis to fix obstacle pathfinding jitter.
