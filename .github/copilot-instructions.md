# Copilot instructions for Notehub

Purpose
- Short guidance for Copilot/assistant contributions while developing Notehub — a CLI that stores notes as GitHub issues.

Quick context
- Language: Python (3.8+)
- Package: `src/notehub` with CLI entrypoints in `src/notehub/__main__.py` and `src/notehub/cli.py`
- Tests: `tests/unit/` and `tests/integration/`
- GitHub integration: uses the `gh` CLI; default repo name recommended: `notehub.default`

Developer setup
- Install editable dev environment:

```bash
python -m pip install -e .[dev]
```

- Install git hooks:

```bash
pre-commit install
```

- Run tests:

```bash
pytest
pytest tests/unit/
```

- Run CLI locally:

```bash
python -m notehub --help
# or after install: notehub --help
```

Authentication & tokens
- Prefer `gh auth login` for interactive auth.
- Token environment variables (checked in order): `GH_ENTERPRISE_TOKEN_2`, `GH_ENTERPRISE_TOKEN`, `GITHUB_TOKEN`.

Project defaults (git config)
- Configure defaults so the CLI finds the target repo:

```bash
git config --global notehub.host github.com
git config --global notehub.org <your-username>
git config --global notehub.repo notehub.default
```

Windows notes
- Use the Python installer from python.org (avoid MS Store).
- To use VS Code as the editor for `notehub add` / `notehub edit`:

```powershell
[System.Environment]::SetEnvironmentVariable('EDITOR','code --wait','User')
```

Pre-commit & CI expectations
- Pre-commit runs formatting and validation hooks and enforces basic test coverage for commits. Keep tests green and avoid large unreviewed changes.

Common places to edit
- CLI commands: `src/notehub/commands/` (`add.py`, `edit.py`, `list.py`, etc.)
- GitHub wrapper + auth: `src/notehub/gh_wrapper.py`
- Shared logic: `src/notehub/utils.py`, `src/notehub/context.py`

Suggested assistant prompts
- "Add unit tests for `src/notehub/commands/add.py` covering happy path and missing fields."
- "Refactor `src/notehub/gh_wrapper.py` to prefer `GH_ENTERPRISE_TOKEN_2` and allow enterprise hostnames."
- "Improve CLI help text for `notehub add` and include an example usage snippet."
- "Update README with succinct Windows setup steps and editor configuration."

Debugging & local checks
- Ensure editable install and `gh auth login` succeeded, then run targeted tests:

```bash
pytest -k <testname>
python -m notehub <command>
```

Files of interest
- `README.md` — user and developer setup
- `spec/` — feature design and notes
- `src/notehub/` — implementation
- `tests/` — test suites

Next steps
- If you want, I can run tests locally or commit this file. Tell me which you prefer.

— End —
