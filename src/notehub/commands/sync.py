"""Sync command - push cache changes to GitHub."""

import sys
from argparse import Namespace

from .. import cache
from ..context import StoreContext
from ..gh_wrapper import GhError, get_issue_metadata, update_issue
from ..utils import resolve_note_ident


def sync_all_dirty() -> int:
    """
    Sync all dirty cached notes across all repos/orgs/hosts.

    Discovers all cached notes with uncommitted changes and pushes them
    to GitHub, continuing on individual failures.

    Returns:
        0 if all succeeded, 1 if any errors occurred
    """
    dirty_notes = cache.find_dirty_cached_notes()

    if not dirty_notes:
        print("No dirty cached notes found.")
        return 0

    print(f"Found {len(dirty_notes)} dirty cached note(s). Syncing...")
    errors = []
    synced_count = 0

    for host, org, repo, issue_num, cache_path in dirty_notes:
        try:
            # Commit if dirty
            if cache.commit_if_dirty(cache_path):
                pass  # Committed, continue with sync

            # Read content
            content = cache.get_note_content(cache_path)

            # Push to GitHub
            update_issue(host, org, repo, issue_num, content)

            # Update timestamp
            metadata = get_issue_metadata(host, org, repo, issue_num)
            updated_at = metadata.get("updated_at")
            if updated_at:
                cache.set_last_known_updated_at(cache_path, updated_at)

            print(f"  {org}/{repo}#{issue_num}: Synced")
            synced_count += 1

        except GhError as e:
            # Check if issue was deleted (404)
            if "Not Found" in e.stderr or "404" in e.stderr:
                print(f"  {org}/{repo}#{issue_num}: Skipped - issue deleted on GitHub")
            else:
                error_msg = f"  {org}/{repo}#{issue_num}: Failed - {e.stderr.strip()}"
                print(error_msg, file=sys.stderr)
                errors.append(error_msg)

        except Exception as e:
            error_msg = f"  {org}/{repo}#{issue_num}: Failed - {str(e)}"
            print(error_msg, file=sys.stderr)
            errors.append(error_msg)

    # Print summary
    print(f"\nSynced {synced_count} note(s).")
    if errors:
        print(f"{len(errors)} error(s) occurred.", file=sys.stderr)
        return 1

    return 0


def run(args: Namespace) -> int:
    """
    Execute sync command.

    Workflow (single note mode):
    1. Resolve note-ident to issue number
    2. Find cache directory
    3. Commit if dirty
    4. Push content to GitHub
    5. Update timestamp

    Workflow (--cached mode):
    1. Find all dirty cached notes
    2. For each: commit, push, update timestamp

    Returns:
        0 if successful, 1 if error
    """
    # Handle --cached flag
    if getattr(args, "cached", False):
        return sync_all_dirty()

    # Validate note_ident is provided for single-note sync
    if not args.note_ident:
        print("Error: NOTE-IDENT is required unless --cached is used.", file=sys.stderr)
        return 1

    # Original single-note sync
    context = StoreContext.resolve(args)

    try:
        # Resolve note-ident
        issue_num, error = resolve_note_ident(context, args.note_ident)
        if error:
            print(f"Error: {error}", file=sys.stderr)
            return 1

        # Get cache path
        cache_path = cache.get_cache_path(context.host, context.org, context.repo, issue_num)

        # Check if cache exists
        if not cache_path.exists():
            print(
                f"Error: No cache found for issue #{issue_num}. Use 'notehub edit {issue_num}' first.",
                file=sys.stderr,
            )
            return 1

        # Commit if dirty
        if cache.commit_if_dirty(cache_path):
            print("Committed local changes")

        # Read content
        content = cache.get_note_content(cache_path)

        # Push to GitHub
        print("Pushing to GitHub...")
        update_issue(context.host, context.org, context.repo, issue_num, content)

        # Fetch updated metadata to get new timestamp
        metadata = get_issue_metadata(context.host, context.org, context.repo, issue_num)
        updated_at = metadata.get("updated_at")

        if updated_at:
            cache.set_last_known_updated_at(cache_path, updated_at)

        print(f"Synced issue #{issue_num}")
        print(f"URL: https://{context.host}/{context.org}/{context.repo}/issues/{issue_num}")

        return 0

    except GhError:
        # Error already printed to stderr by gh_wrapper
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 1
