# Notehub

Using GitHub issues as general notes.

## Quick Start

1. **Install prerequisites:**
   - Python 3.8+
   - GitHub CLI (`gh`) - https://cli.github.com/

2. **Install notehub:**
   ```bash
   pip install lm-notehub
   ```

3. **Authenticate:**
   ```bash
   gh auth login
   ```

4. **Configure:**
   ```bash
   git config --global notehub.org <your-github-username>
   git config --global notehub.repo notehub.default
   ```

5. **Create your notes repo** at https://github.com/new (name it `notehub.default`)

6. **Verify:**
   ```bash
   notehub status
   ```

## Documentation

**For complete usage, commands, configuration, and troubleshooting:**

👉 **[notehub-help.md](https://github.com/Stabledog/notehub/blob/main/notehub-help.md)**

Or run: `notehub --help`

## Development Setup

For contributors and developers:

### 1. Clone and Install

```bash
git clone https://github.com/Stabledog/notehub.git
cd notehub
python -m pip install -e .[dev]
```

### 2. Set Up Pre-commit Hooks

```bash
pre-commit install
```

### 3. Run Tests

```bash
pytest                    # All tests
pytest tests/unit/        # Unit tests only
```

### 4. Publishing (Maintainers Only)

Set `LM_NOTEHUB_PYPI_TOKEN` environment variable, then:
```bash
bash build-and-publish.sh
```

For detailed development guidance, see [.github/copilot-instructions.md](.github/copilot-instructions.md).

## Virtual Environments (Optional)

Many developers recommend using virtual environments (venv, conda, etc.) to isolate project dependencies. While this is a best practice for production and complex projects with conflicting dependencies, it adds complexity and can be skipped for simpler projects or solo development. If you want to use one:

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix/macOS
```

Then proceed with the installation steps above.
