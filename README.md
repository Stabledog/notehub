# Notehub

Using Github issues as general notes.

## Requirements

- Python 3.8 or higher
- Git
- GitHub personal access token (for API access)

## Development Setup

### 1. Install Python (Windows)

- Install the python.org edition of Python3.x, stay away from MS Store
- Installer should add to the PATH:
```
C:\Users\<username>\AppData\Local\Programs\Python\Python313\Scripts
C:\Users\<username>\AppData\Local\Programs\Python\Python313
C:\Users\<username>\AppData\Local\Programs\Python\Launcher
```

### 2. Install in Development Mode

Install notehub with development dependencies:
```bash
python -m pip install -e .[dev]
```

This installs:
- `pytest` - Testing framework
- `pytest-cov` - Code coverage
- `pytest-mock` - Mocking utilities
- `pre-commit` - Git hooks framework

**Note**: Don't use `--user` flag. On Windows, `--user` puts packages in AppData\Roaming instead of AppData\Local, but since you own the latter there's no reason to use `--user`.

### 3. Set Up Pre-commit Hooks

Install the git hooks:
```bash
pre-commit install
```

This will automatically run on every commit:
- Trailing whitespace removal
- End-of-file fixes
- YAML validation
- Large file checks
- Merge conflict detection
- Unit tests with 20% minimum coverage

### 4. Configure GitHub Token

**For public GitHub:**
Set `GITHUB_TOKEN` environment variable with a personal access token.

**Within the corp wall:**
Set `GH_ENTERPRISE_TOKEN_2` environment variable (add to Windows environment variables).

### 5. Running Tests

Run all tests:
```bash
pytest
```

Run only unit tests:
```bash
pytest tests/unit/
```

Run with coverage report:
```bash
pytest --cov=src/notehub --cov-report=term-missing
```

## Usage

After installation, the `notehub` command will be available:
```bash
notehub --help
```

## Virtual Environments (Optional)

Many developers recommend using virtual environments (venv, conda, etc.) to isolate project dependencies. While this is a best practice for production and complex projects with conflicting dependencies, it adds complexity and can be skipped for simpler projects or solo development. If you want to use one:

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix/macOS
```

Then proceed with the installation steps above.
