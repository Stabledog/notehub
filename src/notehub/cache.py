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
    try:
        subprocess.run(["git", "init"], cwd=cache_path, capture_output=True, check=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to initialize git repo in cache: {e.stderr}") from e

    # Create .gitignore
    gitignore_content = "*\n!note.md\n!.gitignore\n"
    (cache_path / ".gitignore").write_text(gitignore_content, encoding="utf-8")

    # Write note.md
    (cache_path / "note.md").write_text(content, encoding="utf-8")

    # Initial commit
    try:
        subprocess.run(
            ["git", "add", ".gitignore", "note.md"],
            cwd=cache_path,
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to add files to git in cache: {e.stderr}") from e

    try:
        subprocess.run(
            ["git", "commit", "-m", f"Cache created for issue {issue_number}"],
            cwd=cache_path,
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create initial commit in cache: {e.stderr}") from e


def is_dirty(cache_path: Path) -> bool:
    """
    Check if working directory has uncommitted changes.

    Args:
        cache_path: Path to cache directory

    Returns:
        bool: True if there are uncommitted changes
    """
    result = subprocess.run(["git", "status", "--porcelain"], cwd=cache_path, capture_output=True, text=True)
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

    try:
        subprocess.run(["git", "add", "note.md"], cwd=cache_path, capture_output=True, check=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to add note.md to git in cache: {e.stderr}") from e

    try:
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=cache_path,
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to commit changes in cache: {e.stderr}") from e

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
    try:
        subprocess.run(["git", "add", "note.md"], cwd=cache_path, capture_output=True, check=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to add note.md to git in cache: {e.stderr}") from e

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


def find_all_cached_notes() -> list[tuple[str, str, str, int, Path]]:
    """
    Find all cached notes across all repos/orgs/hosts.

    Walks the cache directory tree looking for issue cache directories.
    Structure: {cache_root}/{host}/{org}/{repo}/{issue_number}/

    Returns:
        list: Tuples of (host, org, repo, issue_number, cache_path)
    """
    cache_root = get_cache_root()
    results = []

    if not cache_root.exists():
        return results

    # Use glob to find all .git directories matching our structure: host/org/repo/issue_number/.git
    # This replaces 4 nested loops with a single glob pattern
    for git_dir in cache_root.glob("*/*/*/*/.git"):
        if not git_dir.is_dir():
            continue

        issue_dir = git_dir.parent
        repo_dir = issue_dir.parent
        org_dir = repo_dir.parent
        host_dir = org_dir.parent

        # Verify issue_number is actually a number
        if not issue_dir.name.isdigit():
            continue

        results.append(
            (
                host_dir.name,
                org_dir.name,
                repo_dir.name,
                int(issue_dir.name),
                issue_dir,
            )
        )

    return results


def find_dirty_cached_notes() -> list[tuple[str, str, str, int, Path]]:
    """
    Find all cached notes with uncommitted changes.

    Returns:
        list: Tuples of (host, org, repo, issue_number, cache_path) for dirty notes only
    """
    all_notes = find_all_cached_notes()
    return [note for note in all_notes if is_dirty(note[4])]
