# AGENTS.md - AI Agent Guide for Notehub Development

> **Purpose**: This document provides AI coding agents (like GitHub Copilot, Claude, etc.) with the essential context needed to understand, maintain, and extend the Notehub project effectively.

---

## Quick Start for Agents

**What is Notehub?**
- A CLI tool that uses GitHub issues as a backing store for personal/team notes
- Written in Python 3.8+, delegates all GitHub operations to `gh` CLI
- Designed for minimal friction: context-aware, git-backed local cache, editor integration

**Before You Start:**
1. Read [Context Resolution](#context-resolution) - critical for understanding how host/org/repo are determined
2. Review [Architecture Principles](#architecture-principles) - especially the "fail-fast" philosophy
3. Check [Module Responsibilities](#module-responsibilities) for where to make changes
4. Read [Testing Requirements](#testing-requirements) - all code must have tests

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Architecture Principles](#architecture-principles)
3. [Module Responsibilities](#module-responsibilities)
4. [Context Resolution](#context-resolution)
5. [gh CLI Integration](#gh-cli-integration)
6. [Local Cache System](#local-cache-system)
7. [Testing Requirements](#testing-requirements)
8. [Code Style & Standards](#code-style--standards)
9. [Common Tasks](#common-tasks)
10. [Critical Implementation Details](#critical-implementation-details)
11. [Reference Documentation](#reference-documentation)

---

## Project Structure

```
notehub/
├── src/notehub/              # Main application source
│   ├── __main__.py           # Entry point (bootstraps CLI)
│   ├── cli.py                # Argument parsing & command dispatch
│   ├── context.py            # Store context resolution (host/org/repo)
│   ├── gh_wrapper.py         # GitHub CLI wrapper & auth handling
│   ├── cache.py              # Git-backed local cache management
│   ├── config.py             # Git config integration
│   ├── utils.py              # Shared utilities (note-ident resolution, formatting)
│   └── commands/             # Command implementations
│       ├── add.py            # Create new note-issues
│       ├── edit.py           # Edit note bodies in $EDITOR
│       ├── list.py           # List all note-issues
│       ├── show.py           # Display note-header & URLs
│       ├── status.py         # Show context & auth status
│       ├── sync.py           # Push cache changes to GitHub
│       ├── find.py           # Search note bodies (NOT YET IMPLEMENTED)
│       └── move.py           # Cross-repo transfers (NOT YET IMPLEMENTED)
│
├── tests/
│   ├── conftest.py           # Shared pytest fixtures
│   ├── unit/                 # Unit tests (mocked, no external deps)
│   └── integration/          # Integration tests (requires gh CLI)
│
├── spec/                     # Design documentation
│   ├── notehub_spec_toplevel.md  # Top-level spec
│   ├── design.md                 # Detailed design & diagrams
│   └── general.md                # Policies & guidance
│
├── pyproject.toml            # Modern Python packaging (PEP 517/518)
├── .pre-commit-config.yaml   # Pre-commit hooks (ruff, pytest)
└── notehub-help.md           # User-facing documentation
```

---

## Architecture Principles

### 1. **Delegation to gh CLI**

**Core Philosophy**: Never call GitHub APIs directly. Always use `gh` CLI.

**Why?**
- `gh` handles authentication (OAuth, tokens, multiple hosts, GHES)
- `gh` provides clear, actionable error messages
- `gh` is maintained by GitHub with API compatibility guarantees
- `gh` supports enterprise hosts out-of-the-box

**Implementation**: All GitHub operations go through [gh_wrapper.py](src/notehub/gh_wrapper.py).

### 2. **Fail-Fast Execution**

**Philosophy**: Commands do NOT check prerequisites. Let natural errors surface.

**What commands DON'T check:**
- ✗ `gh` installation
- ✗ Authentication status
- ✗ Network connectivity
- ✗ Repository existence

**Why?**
- Single responsibility: commands focus on their core task
- Natural error flow: `gh` errors are self-explanatory
- Better performance: no redundant validation on every invocation
- User agency: `notehub status` is the diagnostic tool

**Exception**: The `status` command explicitly checks `gh` installation, authentication, and provides setup instructions. It's the diagnostic tool.

**Example Error Flow:**
```
notehub add
  → gh_wrapper.create_issue()
    → subprocess.run(["gh", "issue", "create", ...])
      → gh not found: "sh: gh: command not found"
      → not authenticated: "gh: To use GitHub CLI, run 'gh auth login'"
      → repo not found: "gh: repository not found"
```

### 3. **The 'notehub' Label Convention**

**All notehub-managed issues have a `notehub` label.**

**Why?**
- Separates notehub notes from regular project issues
- Filtering: `list`, `find`, `show` only operate on notehub notes
- Safety: doesn't interfere with regular GitHub issue tracking
- Users can still see everything in GitHub UI

**Implementation:**
- `create_issue()` always includes `--label notehub`
- `list_issues()` filters by `label:notehub`
- Label is auto-created if it doesn't exist

### 4. **Git-Backed Local Cache**

**Each edited note gets a git-backed cache directory.**

**Structure:**
```
~/.cache/notehub/{host}/{org}/{repo}/{issue_number}/
├── .git/           # Git repository for change tracking
├── .gitignore      # Ignores everything except note.md
└── note.md         # Issue body content
```

**Why git?**
- Natural change tracking (commit history)
- Easy dirty detection (`git status --porcelain`)
- Merge capabilities (though not yet used)
- Familiar tooling for developers

**See**: [cache.py](src/notehub/cache.py) for implementation.

---

## Module Responsibilities

### Core Modules

#### [__main__.py](src/notehub/__main__.py)
- **Purpose**: Entry point for `python -m notehub`
- **Exports**: `main() -> int`
- **Edit when**: Never (it just bootstraps to cli.py)

#### [cli.py](src/notehub/cli.py)
- **Purpose**: Command-line argument parsing and dispatch
- **Exports**: `main(argv) -> int`, `create_parser() -> ArgumentParser`
- **Edit when**: Adding new commands or CLI flags
- **Key function**: `add_store_arguments()` - adds common host/org/repo flags to parsers

#### [context.py](src/notehub/context.py)
- **Purpose**: Resolve store context (host/org/repo) from multiple sources
- **Exports**: `StoreContext` class with `resolve(args) -> StoreContext`
- **Edit when**: Changing context resolution priority or adding new sources
- **Critical**: Implements the complex resolution hierarchy (see [Context Resolution](#context-resolution))

#### [gh_wrapper.py](src/notehub/gh_wrapper.py)
- **Purpose**: All `gh` CLI interactions and authentication management
- **Exports**: `create_issue()`, `update_issue()`, `get_issue()`, `list_issues()`, etc.
- **Edit when**: Adding new GitHub operations or fixing auth issues
- **Critical functions**:
  - `_prepare_gh_cmd()`: Sets up auth environment, handles token priority
  - `_handle_gh_error()`: Provides helpful error messages
  - `build_repo_arg()`: Formats repo arguments for `gh` commands

#### [cache.py](src/notehub/cache.py)
- **Purpose**: Git-backed local cache management
- **Exports**: `get_cache_path()`, `init_cache()`, `is_dirty()`, `commit_if_dirty()`, etc.
- **Edit when**: Changing cache storage or adding cache operations

#### [config.py](src/notehub/config.py)
- **Purpose**: Git config integration (placeholder - currently minimal)
- **Exports**: `get_editor()` - returns `$EDITOR` or 'vi'
- **Edit when**: Adding git config read/write operations (currently stubbed)

#### [utils.py](src/notehub/utils.py)
- **Purpose**: Shared utility functions
- **Exports**: `resolve_note_ident()`, `format_note_header()`, `get_version()`
- **Edit when**: Adding cross-command utilities

### Command Modules

All commands implement `run(args: Namespace) -> int` and return 0 for success, non-zero for errors.

#### [commands/status.py](src/notehub/commands/status.py)
- **Purpose**: Display context, auth state, user identity
- **Special**: ONLY command that checks prerequisites
- **Always returns**: 0 (informational, never fails)

#### [commands/add.py](src/notehub/commands/add.py)
- **Purpose**: Create new note-issues interactively
- **Flow**: Ensure label exists → `gh issue create` (interactive)

#### [commands/edit.py](src/notehub/commands/edit.py)
- **Purpose**: Edit note bodies in `$EDITOR`
- **Flow**: Resolve ident → fetch/create cache → ensure current → launch editor → auto-sync
- **Complex**: Handles VS Code `--wait` flag, cache staleness, merge from GitHub

#### [commands/list.py](src/notehub/commands/list.py)
- **Purpose**: List all notehub issues
- **Flow**: Fetch issues (auto-filtered by label) → display note-header + URL

#### [commands/show.py](src/notehub/commands/show.py)
- **Purpose**: Display note-header and URL for specified issues
- **Flow**: Resolve each note-ident → fetch issue → display

#### [commands/sync.py](src/notehub/commands/sync.py)
- **Purpose**: Push cache changes to GitHub
- **Modes**: Single note or `--cached` (all dirty notes)
- **Flow**: Find cache → commit if dirty → push to GitHub → update timestamp

#### [commands/find.py](src/notehub/commands/find.py) ⚠️
- **Status**: NOT YET IMPLEMENTED (empty file)
- **Planned**: Search note bodies with regex, show matches in context

#### [commands/move.py](src/notehub/commands/move.py) ⚠️
- **Status**: NOT YET IMPLEMENTED (empty file)
- **Planned**: Transfer notes across repos/orgs (extract & recreate pattern)

---

## Context Resolution

**The most complex part of notehub**: determining `host`, `org`, `repo` from multiple sources.

### Host Aliases

**Built-in host aliases** for convenience (defined in `HOST_ALIASES` constant in [context.py](src/notehub/context.py)):
- `gh` or `github` → `github.com`
- `bbgh` or `bbgithub` → `bbgithub.dev.bloomberg.com`

Aliases are:
- **Case-insensitive**: `GH`, `Gh`, and `gh` all work
- **Expanded automatically** at all resolution sources (CLI flags, env vars, git config)
- **Not configurable**: hardcoded in the source (by design)
- **Pass-through**: non-alias values are unchanged

Example: `notehub status -H bbgh` expands to `notehub status -H bbgithub.dev.bloomberg.com`

### Resolution Hierarchy (Priority Order)

Each component (host/org/repo) is resolved independently using this priority:

1. **CLI flags**: `--host`, `--org`, `--repo`
   - Special: `--repo .` or `-r .` auto-detects from git remote
   - **Host aliases expanded here**
2. **Environment variables**: `GH_HOST`, `NotehubOrg`, `NotehubRepo`
   - **Host aliases expanded here**
3. **Local git config** (skipped with `--global` flag):
   - `git config notehub.host` (**host aliases expanded here**)
   - `git config notehub.org`
   - `git config notehub.repo`
4. **Auto-detect from git remote** (current branch's tracking remote, or 'origin')
5. **Global git config**:
   - `git config --global notehub.host` (**host aliases expanded here**)
   - `git config --global notehub.org`
   - `git config --global notehub.repo`
6. **Defaults**:
   - Host: `github.com`
   - Org: `notehub.$USER` (where `$USER` is the shell environment variable)
   - Repo: `notehub.default`

### Important Edge Cases

**Global-only mode (`--global` flag):**
- Skips local git config and auto-detection
- Only uses: CLI flags → env vars → global git config → defaults

**Auto-detection from git remote:**
- Parses URLs like:
  - `https://github.com/org/repo.git`
  - `git@github.com:org/repo.git`
  - `https://github.enterprise.com/org/repo.git`
- Extracts host, org, repo from the URL
- Handles both HTTPS and SSH formats

**See**: [context.py](src/notehub/context.py) lines 1-457 for full implementation.

---

## gh CLI Integration

### Authentication Token Priority

**CRITICAL**: Token precedence depends on the target host.

#### For `github.com`:
1. `GITHUB_TOKEN` (recommended for public GitHub)
2. `GH_TOKEN` (if no enterprise tokens set)
3. `gh auth` stored credentials (fallback)

#### For GitHub Enterprise hosts:
1. `GH_ENTERPRISE_TOKEN_2` (recommended)
2. `GH_ENTERPRISE_TOKEN`
3. `GH_TOKEN` (if `GITHUB_TOKEN` not set)
4. `gh auth` stored credentials (fallback)

**Why this complexity?**
- Prevents cross-contamination between public GitHub and enterprise
- Follows `gh` CLI conventions
- Supports users with multiple GitHub accounts

**Implementation**: See `_prepare_gh_cmd()` in [gh_wrapper.py](src/notehub/gh_wrapper.py) lines 27-93.

### DO NOT Modify gh Authentication Logic

**⚠️ WARNING**: The authentication logic in `gh_wrapper.py` works, but is tricky.

**From [spec/general.md](spec/general.md):**
> Working with the `gh` authentication is tricky. `gh_wrapper.py` does what works, and that may not agree with public sources about best-practices or the recommendations of the `gh` owners.
>
> Do not vary from using `_prepare_gh_cmd`, `_handle_gh_error`, etc. We want all commands to use consistent interaction patterns with `gh` to avoid chaos.

**Rules:**
- Always use `_prepare_gh_cmd()` to prepare commands
- Always use `_run_gh_command()` for execution
- Always use `_handle_gh_error()` for error messages
- Never call `subprocess.run(["gh", ...])` directly in command code

### Interaction Modes

#### Interactive Mode (for `add`, `edit`)
```python
# Pass stdin/stdout/stderr directly to user
result = _run_gh_command(
    cmd, env, host,
    capture_output=False,
    stdin=sys.stdin,
    stdout=sys.stdout,
    stderr=sys.stderr
)
```

#### Programmatic Mode (for `list`, `show`, `find`)
```python
# Capture JSON output
result = _run_gh_command(cmd, env, host, capture_output=True)
data = json.loads(result.stdout)
```

---

## Local Cache System

### Cache Structure

```
~/.cache/notehub/{host}/{org}/{repo}/{issue_number}/
├── .git/               # Git repo for change tracking
├── .gitignore          # Tracks: note.md, .gitignore (ignores rest)
├── note.md             # Issue body content
└── .last-known-updated-at  # Timestamp for staleness detection
```

### Key Cache Operations

#### `init_cache(cache_path, issue_number, content)`
- Creates directory structure
- Initializes git repo
- Writes `.gitignore` and `note.md`
- Makes initial commit

#### `is_dirty(cache_path) -> bool`
- Checks `git status --porcelain`
- Returns True if uncommitted changes

#### `commit_if_dirty(cache_path, message=None) -> bool`
- Commits if changes present
- Returns True if commit made

#### `get_last_known_updated_at(cache_path) -> str | None`
- Reads `.last-known-updated-at` file
- Returns ISO timestamp or None

#### `set_last_known_updated_at(cache_path, timestamp)`
- Writes timestamp to `.last-known-updated-at`
- Used for staleness detection

### Staleness Detection

**Problem**: User edits note in cache, but someone else updates it on GitHub.

**Solution**: Compare timestamps before editing.

**Flow** (in `edit.py`):
1. Check local timestamp (`.last-known-updated-at`)
2. Fetch GitHub metadata (`updated_at` field)
3. If GitHub is newer: fetch full issue, merge into cache
4. Proceed with edit

**Future**: Could implement 3-way merge for conflicting edits.

---

## Testing Requirements

### Testing Philosophy

**ALL code must have tests.**

- **Unit tests**: Mocked external dependencies, fast, isolated
- **Integration tests**: Require `gh` CLI, test real GitHub interaction (minimal, currently empty)

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_commands.py     # Command implementations
│   ├── test_context.py      # Context resolution
│   ├── test_gh_wrapper.py   # GitHub CLI wrapper
│   ├── test_cache.py        # Cache operations
│   └── ...
└── integration/             # Minimal - requires gh auth
```

### Pre-commit Enforcement

Pre-commit hooks run:
- **Ruff**: Linting & formatting
- **pytest**: Unit tests with coverage
  - Minimum coverage: 20% (enforced)
  - Target: Higher coverage for new code

**Install hooks:**
```bash
pre-commit install
```

### Common Test Fixtures (from conftest.py)

- `mock_env(env_dict)`: Mock os.environ
- `mock_subprocess(returncode, stdout, stderr)`: Mock subprocess.run
- `sample_gh_issue`: Sample GitHub issue JSON
- `sample_gh_issue_list`: List of issues
- `git_remote_urls`: Common git remote URL patterns
- `mock_git_commands`: Mock git command responses

### Writing Tests

**For new commands:**
```python
def test_my_command_happy_path(mocker):
    """Test successful execution."""
    # Mock context resolution
    mock_context = mocker.Mock()
    mocker.patch("notehub.commands.my_cmd.StoreContext.resolve", return_value=mock_context)

    # Mock gh operations
    mocker.patch("notehub.commands.my_cmd.list_issues", return_value=[...])

    # Mock args
    args = argparse.Namespace(host=None, org=None, repo=None)

    # Execute
    result = my_cmd.run(args)

    # Assert
    assert result == 0
```

**For gh_wrapper functions:**
- Mock `subprocess.run`
- Test both success and failure paths
- Test error handling and helpful messages

**For context resolution:**
- Mock git config, git remote, environment variables
- Test each priority level independently
- Test `--global` flag behavior

---

## Code Style & Standards

### Python Version & Typing

- **Target**: Python 3.8+ (for broad compatibility)
- **Type hints**: Use `str | None` (PEP 604 union syntax) instead of `Optional[str]`
- **Returns**: Explicit return types on functions

### Code Organization

**Imports:**
```python
import os
import sys
from argparse import Namespace

from ..context import StoreContext
from ..gh_wrapper import GhError, list_issues
```

**Order**: stdlib → local relative imports

### Comments

**From [spec/general.md](spec/general.md):**

**BAD (restating the obvious):**
```python
# Open the file
with open("myfile", "r") as file:
```

**GOOD (explaining non-obvious reasoning):**
```python
# We need a union of filtered traits because zfiltsvc only accepts unions
# and performs poorly on non-resolved traits in current context
forward_traits = [tx for tx in filter_chain(aggr_traits(...))]
```

**GOOD (documenting known issues):**
```python
# TODO: 'filename' needs to be abstracted for all use cases
filename = '/tmp/instream.json'
```

### Formatting

**Enforced by Ruff:**
- Line length: 120 characters
- Double quotes for strings
- 4-space indentation

### Error Handling

**Commands return int exit codes:**
```python
def run(args: Namespace) -> int:
    try:
        # ... do work ...
        return 0
    except GhError as e:
        # Error already printed to stderr by gh_wrapper
        return e.returncode
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
```

**Don't print errors twice**: `gh_wrapper` already prints to stderr.

---

## Common Tasks

### Adding a New Command

**1. Create command file:**
```bash
touch src/notehub/commands/my_command.py
```

**2. Implement `run()` function:**
```python
from argparse import Namespace
from ..context import StoreContext
from ..gh_wrapper import GhError, list_issues

def run(args: Namespace) -> int:
    """Execute my_command."""
    context = StoreContext.resolve(args)

    try:
        # ... implementation ...
        return 0
    except GhError as e:
        return e.returncode
```

**3. Register in [cli.py](src/notehub/cli.py):**
```python
from .commands import add, edit, list, show, status, sync, my_command

# In create_parser():
my_cmd_parser = subparsers.add_parser(
    "my-command",
    help="Description of my command",
    epilog=f"For details, see: {HELP_URL}#command-my-command"
)
add_store_arguments(my_cmd_parser)
my_cmd_parser.set_defaults(handler=my_command.run)
```

**4. Write tests:**
```python
# tests/unit/test_my_command.py
def test_my_command_success(mocker):
    # ... test implementation ...
```

**5. Update documentation:**
- Add section to [notehub-help.md](notehub-help.md)
- Update [spec/design.md](spec/design.md) if architecture changes

### Adding a New gh Wrapper Function

**1. Add to [gh_wrapper.py](src/notehub/gh_wrapper.py):**
```python
def my_operation(host: str, org: str, repo: str, ...) -> GhResult:
    """
    Do something with gh CLI.

    Args:
        host: GitHub host
        org: Organization/owner
        repo: Repository name

    Returns:
        GhResult with stdout/stderr

    Raises:
        GhError: If gh command fails
    """
    repo_arg = build_repo_arg(host, org, repo)
    base_cmd = ["gh", "api", f"/repos/{org}/{repo}/..."]
    cmd, env = _prepare_gh_cmd(host, base_cmd)

    result = _run_gh_command(cmd, env, host, capture_output=True)

    if result.returncode != 0:
        _handle_gh_error(result, host)
        raise GhError(result.returncode, result.stderr)

    return GhResult(result.returncode, result.stdout, result.stderr)
```

**2. Write tests:**
```python
# tests/unit/test_gh_wrapper.py
def test_my_operation_success(mocker):
    mocker.patch("subprocess.run", return_value=mocker.Mock(
        returncode=0,
        stdout='{"result": "success"}',
        stderr=""
    ))

    result = my_operation("github.com", "org", "repo")
    assert result.returncode == 0
```

### Modifying Context Resolution

**⚠️ Be extremely careful**: This is complex and well-tested.

**1. Understand current behavior:**
- Read [context.py](src/notehub/context.py) completely
- Review tests in [tests/unit/test_context.py](tests/unit/test_context.py)
- Check priority tests in [tests/unit/test_context_priority.py](tests/unit/test_context_priority.py)

**2. Make minimal changes:**
- Modify only one priority level at a time
- Preserve existing behavior for other levels

**3. Update tests extensively:**
- Test new priority behavior
- Verify existing priorities still work
- Test `--global` flag interactions

### Adding Cache Features

**Examples**: merge strategies, conflict detection, cleanup operations

**1. Add to [cache.py](src/notehub/cache.py):**
```python
def my_cache_operation(cache_path: Path, ...) -> ...:
    """Do something with cache."""
    # ... implementation ...
```

**2. Update [edit.py](src/notehub/commands/edit.py) or [sync.py](src/notehub/commands/sync.py) to use it**

**3. Test with mocked filesystem and git operations**

---

## Critical Implementation Details

### 1. VS Code Editor Integration

**Problem**: VS Code returns immediately unless `--wait` flag is used.

**Solution** (in [edit.py](src/notehub/commands/edit.py)):
```python
def _prepare_editor_command(editor: str) -> list[str] | None:
    # ... parse editor command ...

    # Detect VS Code and add --wait
    if "code" in os.path.basename(editor_parts[0]).lower():
        if "--wait" not in editor_parts and "-w" not in editor_parts:
            editor_parts.append("--wait")

    return editor_parts
```

**Handles**:
- `code`, `code.exe`, `code.cmd`
- Editor already has `--wait` (don't duplicate)
- Editor has `-w` (short form)

### 2. Windows Path Handling

**Problem**: Windows paths, executable extensions (.exe, .cmd), path separators.

**Solutions**:
- Use `Path` from `pathlib` for all path operations
- Use `shutil.which()` to find executables (handles .exe/.cmd automatically)
- `subprocess.run()` handles path separators correctly

**Example**:
```python
# Cross-platform executable search
editor_exe = shutil.which("code")  # Finds code.exe on Windows
```

### 3. Unicode & Network Error Handling

**Problem**: `gh` output can have encoding issues or network failures.

**Solution** (in [gh_wrapper.py](src/notehub/gh_wrapper.py)):
```python
result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    env=env,
    errors='replace'  # Critical: replaces bad unicode with �
)
```

**Also handles**:
```python
except (UnicodeDecodeError, OSError) as e:
    error_msg = f"Cannot reach GitHub server at {host}..."
    raise GhError(1, error_msg) from e
```

### 4. Label Auto-Creation

**Problem**: `notehub` label might not exist on first use.

**Solution**: `ensure_label_exists()` in [gh_wrapper.py](src/notehub/gh_wrapper.py) creates it if needed.

**Called by**: [add.py](src/notehub/commands/add.py) before creating issues.

**Label details**:
- Name: `notehub`
- Color: `FFC107` (yellow)
- Description: "Issues created by notehub CLI"

### 5. Timestamp-Based Staleness Detection

**Problem**: Detect if GitHub issue is newer than local cache.

**Solution**:
1. Store GitHub's `updated_at` timestamp in `.last-known-updated-at` file
2. Before editing, fetch metadata from GitHub
3. Compare timestamps
4. If GitHub newer: fetch full issue, merge into cache

**See**: `_ensure_cache_current()` in [edit.py](src/notehub/commands/edit.py) lines 88-124.

---

## Reference Documentation

### For Users
- **[notehub-help.md](notehub-help.md)**: Complete user guide (commands, config, troubleshooting)
- **[README.md](README.md)**: Quick start, installation, development setup

### For Developers
- **[spec/notehub_spec_toplevel.md](spec/notehub_spec_toplevel.md)**: Top-level specification
- **[spec/design.md](spec/design.md)**: Detailed design, architecture diagrams, sequence diagrams
- **[spec/general.md](spec/general.md)**: Coding policies (comments, auth handling)
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)**: Short guidance for AI assistants

### Source Files to Read First

**Understanding the project:**
1. [cli.py](src/notehub/cli.py) - Command dispatch
2. [context.py](src/notehub/context.py) - Context resolution (complex!)
3. [gh_wrapper.py](src/notehub/gh_wrapper.py) - GitHub operations
4. [commands/status.py](src/notehub/commands/status.py) - Simple command example
5. [commands/edit.py](src/notehub/commands/edit.py) - Complex command example

**Testing patterns:**
1. [tests/conftest.py](tests/conftest.py) - Fixtures
2. [tests/unit/test_commands.py](tests/unit/test_commands.py) - Command tests
3. [tests/unit/test_context_priority.py](tests/unit/test_context_priority.py) - Context resolution tests

### Build & Publish

**Build script**: [build-and-publish.sh](build-and-publish.sh)

**Publishing**:
- Requires `LM_NOTEHUB_PYPI_TOKEN` environment variable
- Builds with `python -m build`
- Publishes with `twine`
- Note: SSL issues from corporate networks (use Python 3.11 or publish from home network)

**Version bump**: Edit `version` in [pyproject.toml](pyproject.toml).

---

## FAQ for Agents

**Q: Why doesn't `notehub list` check if `gh` is installed?**
A: Fail-fast philosophy. Let `gh` command fail naturally with clear error. Only `status` command checks prerequisites.

**Q: Why not use PyGitHub or similar library for GitHub API?**
A: Delegating to `gh` CLI handles auth, GHES, multiple accounts, and error messages. Simpler, more maintainable.

**Q: Why git for local cache instead of plain files?**
A: Git provides change tracking, dirty detection, and merge capabilities out-of-the-box. Familiar to developers.

**Q: Why is context resolution so complex?**
A: Supports diverse workflows: global notes, per-repo notes, enterprise hosts, environment overrides. Each source has its use case.

**Q: Can I add dependency on a Python library?**
A: Minimize dependencies. Currently only `requests>=2.32.3` (and dev dependencies). New dependencies must have strong justification.

**Q: What if I need to call `gh` in a way not covered by `gh_wrapper`?**
A: Add a new function to `gh_wrapper.py`. Always use `_prepare_gh_cmd()`, `_run_gh_command()`, `_handle_gh_error()`. Never call `subprocess.run(["gh", ...])` directly.

**Q: How do I debug context resolution?**
A: Run `notehub status` - it shows exactly what context was resolved and from which sources.

**Q: Why are `find.py` and `move.py` empty?**
A: Not yet implemented. Spec exists in [design.md](spec/design.md), but implementation is TODO.

**Q: How do I add a new CLI flag?**
A: Modify `create_parser()` in [cli.py](src/notehub/cli.py). Use `add_store_arguments()` helper for common flags (host/org/repo/global).

**Q: What Python versions are supported?**
A: Python 3.8+ (defined in [pyproject.toml](pyproject.toml)). Avoid using features from 3.9+ without a good reason.

---

## Conclusion

**Key Takeaways for Agents:**

1. **Read [design.md](spec/design.md) for architecture** - especially fail-fast philosophy and `gh` delegation
2. **Understand context resolution** - it's the most complex part
3. **Don't mess with auth logic** - it's tricky and works; use the helpers
4. **All code must have tests** - pre-commit enforces this
5. **Commands don't check prerequisites** - except `status`
6. **Use `gh_wrapper` helpers** - never call `subprocess.run(["gh"])` directly

**When in doubt:**
- Check existing command implementations for patterns
- Look at tests for examples
- Refer to [spec/design.md](spec/design.md) for design decisions
- Ask user to clarify requirements

**Happy coding! 🚀**
