# Contributing

## Workflow

1. Create a focused branch for a coherent change.
2. Add acceptance tests for new domain behavior before implementation where practical.
3. Run `ruff check .`, `mypy app`, `python -m compileall -q app tests`, and `pytest -q`.
4. Review the complete diff for security, correctness, unnecessary complexity, and backwards compatibility.
5. Open a pull request with the problem, approach, verification, and known limitations.

## Design principles

Prefer deterministic domain rules, explicit state transitions, small modules, bounded resources, and explainable behavior. Do not weaken tests or static checks just to make CI green.
