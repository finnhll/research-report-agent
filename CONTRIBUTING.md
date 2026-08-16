# Contributing

Thanks for helping improve the Research & Report Agent.

## Development setup

1. Install Python 3.11 or newer.
2. Clone the repository.
3. Create and activate a virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

4. Install the development dependencies:

```bash
python -m pip install -e ".[dev]"
```

## Workflow

1. Create a feature branch from `main`.
2. Make a focused change.
3. Add or update tests.
4. Run all quality checks locally:

```bash
ruff format --check .
ruff check .
pytest
```

5. Push your branch.
6. Open a pull request into `main`.
7. Wait for CI and code review to pass.
8. Use a squash merge so `main` retains linear history.

## Commit message conventions

Use the Conventional Commits format:

```text
type: short imperative description
```

Common types:

- `feat`: new user-facing capability
- `fix`: bug fix
- `docs`: documentation
- `test`: tests only
- `refactor`: behavior-preserving code change
- `chore`: tooling or maintenance
- `ci`: CI changes

## Design changes

Architecture-first changes should update `docs/spec/design.md` before implementation.
Describe:

- The affected component
- New contracts
- Failure states
- Retry and termination behavior
- Tests

## Code review expectations

- Public functions have type hints.
- Models are Pydantic types.
- Agent outputs are validated before use.
- Every loop has a termination condition.
- Factual output is tied to source IDs.
- New behavior has tests.

## Security

Do not commit API keys, browser sessions, logs, or private research data.
Report security vulnerabilities through [SECURITY.md](SECURITY.md) rather than public issues.
