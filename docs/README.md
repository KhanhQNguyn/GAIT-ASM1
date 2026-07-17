# GAIT-ASM1: Frog, Flies, and Snakes

An autonomous agent simulation built with Pygame where a frog (player) navigates a dynamic ecosystem of boids-based flies and FSM-driven snakes.

## How to Run
Ensure you have Python and `pygame` installed.
```bash
python main.py
```
To run the automated tests:
```bash
pytest tests/
```

## Controls
- **Left Click**: Move the frog to the clicked position.
- **Space**: Shoot a fast-moving bubble that pacifies aggressive snakes upon hit.
- **R**: Restart the simulation round.
- **F1**: Toggle Developer Debug HUD and live-tuning sliders.

## Debug Mode (F1)
Pressing F1 toggles the `debug_state.DEBUG` overlay, revealing live vector rendering for agents:
- Visualization of steering forces, bounding logic, and FSM states (e.g., `Aggro`, `Confused`, `Flock`, `Fleeing`).
- Interactive live sliders dynamically tweak configuration (Separation, Cohesion, Alignment weights, and Aggro range) in real-time.
- HUD counters provide metric tracking (e.g., pursuit closing speed).
