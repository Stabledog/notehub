"""Cache management for notehub - git-backed local issue storage."""

import subprocess
from datetime import datetime
from pathlib import Path


def get_cache_root() -> Path:
    """
    Get platform-appropriate cache root directory.

    Returns:
        Path: ~/.cache/notehub on Unix, %USERPROFILE%/.cache/notehub on Windows
    """
    home = Path.home()
    return home / ".cache" / "notehub"


def get_cache_path(host: str, org: str, repo: str, issue_number: int) -> Path:
    """
    Build cache path for a specific issue.

    Args:
        host: GitHub host (e.g., 'github.com')
        org: Organization/owner name
        repo: Repository name
        issue_number: Issue number

    Returns:
        Path: Cache directory path for this issue
    """
    root = get_cache_root()
    return root / host / org / repo / str(issue_number)


def init_cache(cache_path: Path, issue_number: int, content: str) -> None:
    """
    Initialize a new cache directory with git repo.

    Creates directory structure, initializes git, writes .gitignore and note.md,
    makes initial commit.

    Args:
        cache_path: Path to cache directory
        issue_number: Issue number (for commit message)
        content: Initial note content
    """
    # Create directory
    cache_path.mkdir(parents=True, exist_ok=True)

    # Initialize git
    subprocess.run(["git", "init"], cwd=cache_path, capture_output=True, check=True)

    # Create .gitignore
    gitignore_content = "*\n!note.md\n!.gitignore\n"
    (cache_path / ".gitignore").write_text(gitignore_content, encoding="utf-8")

    # Write note.md
    (cache_path / "note.md").write_text(content, encoding="utf-8")

    # Initial commit
    subprocess.run(
        ["git", "add", ".gitignore", "note.md"],
        cwd=cache_path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", f"Cache created for issue {issue_number}"],
        cwd=cache_path,
        capture_output=True,
        check=True,
    )


def is_dirty(cache_path: Path) -> bool:
    """
    Check if working directory has uncommitted changes.

    Args:
        cache_path: Path to cache directory

    Returns:
        bool: True if there are uncommitted changes
    """
    result = subprocess.run(
        ["git", "status", "--porcelain"], cwd=cache_path, capture_output=True, text=True
    )
    return bool(result.stdout.strip())


def commit_if_dirty(cache_path: Path, message: str | None = None) -> bool:
    """
    Commit working directory if it has changes.

    Args:
        cache_path: Path to cache directory
        message: Commit message (default: timestamp-based)

    Returns:
        bool: True if a commit was made, False if no changes
    """
    if not is_dirty(cache_path):
        return False

    if message is None:
        timestamp = datetime.now().isoformat(timespec="seconds")
        message = f"Auto-commit at {timestamp}"

    subprocess.run(
        ["git", "add", "note.md"], cwd=cache_path, capture_output=True, check=True
    )
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=cache_path,
        capture_output=True,
        check=True,
    )
    return True


def get_last_known_updated_at(cache_path: Path) -> str | None:
    """
    Get last known GitHub updated_at timestamp from git config.

    Args:
        cache_path: Path to cache directory

    Returns:
        str: ISO 8601 timestamp or None if not set
    """
    result = subprocess.run(
        ["git", "config", "--local", "notehub.lastKnownUpdatedAt"],
        cwd=cache_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def set_last_known_updated_at(cache_path: Path, timestamp: str) -> None:
    """
    Store GitHub updated_at timestamp in git config.

    Args:
        cache_path: Path to cache directory
        timestamp: ISO 8601 timestamp from GitHub API
    """
    subprocess.run(
        ["git", "config", "--local", "notehub.lastKnownUpdatedAt", timestamp],
        cwd=cache_path,
        capture_output=True,
        check=True,
    )


def merge_from_github(cache_path: Path, content: str, issue_number: int) -> None:
    """
    Write new content from GitHub and commit (may create conflicts).

    This performs a simple overwrite + commit. If there are local changes,
    they should be committed first. Git will create conflict markers if
    the merge can't be done cleanly.

    Args:
        cache_path: Path to cache directory
        content: New content from GitHub
        issue_number: Issue number (for commit message)
    """
    # Write new content
    (cache_path / "note.md").write_text(content, encoding="utf-8")

    # Add and commit
    subprocess.run(
        ["git", "add", "note.md"], cwd=cache_path, capture_output=True, check=True
    )

    timestamp = datetime.now().isoformat(timespec="seconds")
    subprocess.run(
        ["git", "commit", "-m", f"Fetched from GitHub at {timestamp}"],
        cwd=cache_path,
        capture_output=True,
        check=True,
    )


def get_note_content(cache_path: Path) -> str:
    """
    Read current note.md content.

    Args:
        cache_path: Path to cache directory

    Returns:
        str: Content of note.md
    """
    return (cache_path / "note.md").read_text(encoding="utf-8")


def get_note_path(cache_path: Path) -> Path:
    """
    Get path to note.md file.

    Args:
        cache_path: Path to cache directory

    Returns:
        Path: Full path to note.md
    """
    return cache_path / "note.md"
