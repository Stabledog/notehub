"""Sync command - push cache changes to GitHub."""

import sys
from argparse import Namespace

from .. import cache
from ..context import StoreContext
from ..gh_wrapper import GhError, get_issue_metadata, update_issue
from ..utils import resolve_note_ident


def run(args: Namespace) -> int:
    """
    Execute sync command.

    Workflow:
    1. Resolve note-ident to issue number
    2. Find cache directory
    3. Commit if dirty
    4. Push content to GitHub
    5. Update timestamp

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
        cache_path = cache.get_cache_path(
            context.host, context.org, context.repo, issue_num
        )

        # Check if cache exists
        if not cache_path.exists():
            print(
                f"Error: No cache found for issue #{issue_num}. "
                f"Use 'notehub edit {issue_num}' first.",
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
        metadata = get_issue_metadata(
            context.host, context.org, context.repo, issue_num
        )
        updated_at = metadata.get("updated_at")

        if updated_at:
            cache.set_last_known_updated_at(cache_path, updated_at)

        print(f"Synced issue #{issue_num}")
        print(
            f"URL: https://{context.host}/{context.org}/{context.repo}/issues/{issue_num}"
        )

        return 0

    except GhError:
        # Error already printed to stderr by gh_wrapper
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 1
