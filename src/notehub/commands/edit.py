"""Edit command - edit note-issue body in cached git repo."""

import os
import shlex
import shutil
import subprocess
import sys
from argparse import Namespace

from .. import cache
from ..config import get_editor
from ..context import StoreContext
from ..gh_wrapper import GhError, get_issue, get_issue_metadata, update_issue
from ..utils import resolve_note_ident


def _prepare_editor_command(editor: str) -> list[str] | None:
    """
    Prepare editor command, adding --wait flag for VS Code if needed.

    VS Code requires the --wait flag to wait for the file to be closed before
    continuing, otherwise the script will immediately proceed without user input.

    On Windows, automatically searches for .exe or .cmd versions of executables
    if the base command is not found in PATH.

    Args:
        editor: Editor command (e.g., 'vim', 'code', 'code --wait')

    Returns:
        List of command arguments, or None if editor executable not found
    """
    # Split editor command into parts (handles both 'code' and 'code --wait')
    editor_parts = shlex.split(editor)
    if not editor_parts:
        return None

    # Find the actual executable in PATH
    editor_exe = editor_parts[0]

    # If it's not an absolute path, search PATH for the executable
    if not os.path.isabs(editor_exe):
        found_exe = shutil.which(editor_exe)
        if found_exe:
            editor_parts[0] = found_exe
        else:
            # Not found - return None to signal error
            return None

    # Check if editor is VS Code (code, code.cmd, code.exe, or path containing 'code')
    if "code" in os.path.basename(editor_parts[0]).lower():
        # Add --wait flag if not already present
        if "--wait" not in editor_parts and "-w" not in editor_parts:
            editor_parts.append("--wait")

    return editor_parts


def _launch_editor_blocking(editor_cmd: list[str], file_path: str) -> int:
    """
    Launch editor and wait for it to close.

    Args:
        editor_cmd: Editor command parts (e.g., ['code', '--wait'])
        file_path: Path to file to edit

    Returns:
        0 if editor exited successfully, non-zero if error
    """
    # Print helpful message
    if "--wait" in editor_cmd or "-w" in editor_cmd:
        print(f"Opening {file_path} in editor...")
        print("Close the editor when done to continue.")
    else:
        print(f"Opening {file_path} in editor...")

    # Launch and wait for editor to close
    try:
        result = subprocess.run([*editor_cmd, file_path], shell=False)
        return result.returncode
    except (FileNotFoundError, OSError) as e:
        print(f"Error: Failed to launch editor: {e}", file=sys.stderr)
        print(f"Edit manually: {file_path}", file=sys.stderr)
        return 1


def _ensure_cache_current(context: StoreContext, cache_path, issue_number: int) -> None:
    """
    Ensure cache is synced with GitHub (fetch if stale).

    Args:
        context: Store context with host/org/repo
        cache_path: Path to cache directory
        issue_number: Issue number
    """
    # Commit any dirty state first
    cache.commit_if_dirty(cache_path, "Auto-commit before sync check")

    # Get last known timestamp
    last_known = cache.get_last_known_updated_at(cache_path)

    # Fetch metadata from GitHub
    try:
        metadata = get_issue_metadata(context.host, context.org, context.repo, issue_number)
    except GhError:
        # If issue doesn't exist, delete cache
        print(
            f"Warning: Issue #{issue_number} no longer exists on GitHub. Removing cache.",
            file=sys.stderr,
        )
        import shutil

        shutil.rmtree(cache_path)
        raise

    github_updated = metadata.get("updated_at")

    # Check if GitHub is newer
    if last_known is None or (github_updated and github_updated > last_known):
        # Fetch full issue and merge
        print("Fetching updates from GitHub...")
        issue = get_issue(context.host, context.org, context.repo, issue_number)
        new_content = issue.get("body") or ""

        cache.merge_from_github(cache_path, new_content, issue_number)
        cache.set_last_known_updated_at(cache_path, github_updated)

        print(f"Merged changes from GitHub (updated at {github_updated})")


def run(args: Namespace) -> int:
    """
    Execute edit command.

    Workflow:
    1. Resolve note-ident to issue number
    2. Get or create cache directory
    3. Ensure cache is current (fetch from GitHub if needed)
    4. Print guidance about sync
    5. Launch editor on note.md (block until closed)
    6. Auto-sync changes to GitHub

    Returns:
        0 if successful, 1 if error
    """
    context = StoreContext.resolve(args)

    try:
        # Resolve note-ident
        issue_num, error = resolve_note_ident(context, args.note_ident)
        if error:
            print(f"Error: {error}", file=sys.stderr)
            return 1

        # Get cache path
        cache_path = cache.get_cache_path(context.host, context.org, context.repo, issue_num)

        # Initialize cache if it doesn't exist
        if not cache_path.exists():
            print(f"Creating cache for issue #{issue_num}...")
            issue = get_issue(context.host, context.org, context.repo, issue_num)
            content = issue.get("body") or ""
            updated_at = issue.get("updated_at")

            cache.init_cache(cache_path, issue_num, content)

            # Store initial timestamp if available
            if updated_at:
                cache.set_last_known_updated_at(cache_path, updated_at)
        else:
            # Ensure cache is up to date
            _ensure_cache_current(context, cache_path, issue_num)

        # Get editor
        editor = get_editor()
        editor_cmd = _prepare_editor_command(editor)

        if editor_cmd is None:
            print(f"Error: Editor '{editor}' not found in PATH.", file=sys.stderr)
            if sys.platform == "win32":
                print(
                    "On Windows, common editors: 'code', 'notepad', 'vim'",
                    file=sys.stderr,
                )
            return 1

        # Get note path
        note_path = cache.get_note_path(cache_path)

        # Print info before launching editor
        print(f"Editing: {note_path}")
        print(f"URL: https://{context.host}/{context.org}/{context.repo}/issues/{issue_num}")
        print("Changes will be automatically synced to GitHub when you close the editor.")
        print()

        # Launch editor and block until it closes
        exit_code = _launch_editor_blocking(editor_cmd, str(note_path))

        if exit_code != 0:
            print(
                f"\nWarning: Editor exited with code {exit_code}. "
                f"Use 'notehub sync {issue_num}' to sync changes manually.",
                file=sys.stderr,
            )
            return exit_code

        print("\nEditor closed. Syncing changes...")

        # Auto-sync: commit if dirty and push to GitHub
        if cache.commit_if_dirty(cache_path):
            print("Committed local changes")

        # Read content
        content = cache.get_note_content(cache_path)

        # Push to GitHub
        update_issue(context.host, context.org, context.repo, issue_num, content)

        # Fetch updated metadata to get new timestamp
        metadata = get_issue_metadata(context.host, context.org, context.repo, issue_num)
        updated_at = metadata.get("updated_at")

        if updated_at:
            cache.set_last_known_updated_at(cache_path, updated_at)

        print(f"Synced issue #{issue_num}")

        return 0

    except GhError:
        # Error already printed to stderr by gh_wrapper
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 1


def edit_in_temp_file(content: str, editor: str) -> str | None:
    """
    Open content in temporary file using editor.

    Args:
        content: Original content to edit
        editor: Editor command (e.g., 'vim', 'nano')

    Returns:
        Modified content if file was changed, None if unchanged or editor failed
    """
    import tempfile

    # Create temp file with .md suffix for syntax highlighting
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Get original modification time
        original_mtime = os.path.getmtime(tmp_path)

        # Prepare editor command (add --wait for VS Code if needed)
        editor_cmd = _prepare_editor_command(editor)

        # Check if editor was found
        if editor_cmd is None:
            print(f"Error: Editor '{editor}' not found in PATH.", file=sys.stderr)
            if sys.platform == "win32":
                print(
                    "On Windows, common editors: 'code', 'notepad', 'vim' (try with .exe extension)",
                    file=sys.stderr,
                )
            return None

        # Print helpful message for VS Code users
        if "--wait" in editor_cmd or "-w" in editor_cmd:
            print("Opening in VS Code... Close the editor tab when done to continue.")

        # Open in editor (shell=False to avoid quoting issues on Windows)
        try:
            result = subprocess.run([*editor_cmd, tmp_path], shell=False)
        except (FileNotFoundError, OSError) as e:
            print(f"Error: Failed to run editor: {e}", file=sys.stderr)
            return None

        # Check if editor failed
        if result.returncode != 0:
            return None

        # Check if file was modified
        new_mtime = os.path.getmtime(tmp_path)
        if new_mtime == original_mtime:
            return None

        # Read modified content
        with open(tmp_path) as f:
            return f.read()

    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
