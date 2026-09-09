# Project Instructions & Agent Guidelines

## Code Style & Architecture
- Maintain a strictly modular structure for the game project, cleanly separating game entry points (`main.py`), core loop logic (`game.py`), configuration (`settings.py`), entities (`player.py`, `enemy.py`), UI panels (`ui.py`), and test environments.
- Avoid circular imports by ensuring modules only import one another in a clean hierarchical path (e.g., `main` imports `game`, `game` imports entities/UI, but avoid cross-referencing testing modules back into `game` in a circular loop).
- Ensure all Python code is clean, utilizes proper syntax, and avoids truncated blocks or literal raw JSON text output.

## Commit Message Guidelines
- Follow conventional commit format rules for version control:
  - `feat: [description]` for adding new features (such as menus, player inventory tabs, or enemy bullet hell mechanics).
  - `fix: [description]` for resolving bugs, path errors, or circular import exceptions.
  - `refactor: [description]` for cleaning up component architectures without altering core behaviors.
  - `chore: [description]` for asset, requirement, or repository adjustments.

## Agent Execution Rules
- Explicitly examine stack traces and terminal error logs when debugging before making direct source code changes.
- Ensure all required project components (such as `settings.py`, `ui.py`, `enemy.py`, and `player.py`) are fully generated and completely usable prior to finalizing edits.
- Test changes locally using `python main.py` to verify that execution runs smoothly without import errors or game crashes[cite: 2].
