import argparse
import sys

from .commands import add, edit, list, show, status, sync


def add_store_arguments(parser):
    """Add common store context arguments to a parser."""
    parser.add_argument("--host", "-H", help="GitHub host (for GHES)")
    parser.add_argument("--org", "-o", help="Organization/owner name")
    parser.add_argument("--repo", "-r", help="Repository name")
    parser.add_argument(
        "--global",
        "-g",
        dest="global_scope",
        action="store_true",
        help="Use global config only (ignore local git repo)",
    )


def create_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="notehub",
        epilog="For comprehensive help, see: https://github.com/Stabledog/notehub/blob/main/notehub-help.md",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add command
    add_parser = subparsers.add_parser(
        "add",
        help="Create a new note-issue",
        epilog="For details, see: https://github.com/Stabledog/notehub/blob/main/notehub-help.md#command-add",
    )
    add_store_arguments(add_parser)
    add_parser.set_defaults(handler=add.run)

    # Show command
    show_parser = subparsers.add_parser(
        "show",
        help="Display note-header and URL for specified issues",
        epilog="For details, see: https://github.com/Stabledog/notehub/blob/main/notehub-help.md#command-show",
    )
    show_parser.add_argument(
        "note_idents",
        nargs="+",
        metavar="NOTE-IDENT",
        help="Issue number or title regex (one or more required)",
    )
    add_store_arguments(show_parser)
    show_parser.set_defaults(handler=show.run)

    # Status command
    status_parser = subparsers.add_parser(
        "status",
        help="Show context, authentication status, and user identity",
        epilog="For details, see: https://github.com/Stabledog/notehub/blob/main/notehub-help.md#command-status",
    )
    add_store_arguments(status_parser)
    status_parser.set_defaults(handler=status.run)

    # Edit command
    edit_parser = subparsers.add_parser(
        "edit",
        help="Edit note-issue body in $EDITOR",
        epilog="For details, see: https://github.com/Stabledog/notehub/blob/main/notehub-help.md#command-edit",
    )
    edit_parser.add_argument(
        "note_ident", metavar="NOTE-IDENT", help="Issue number or title regex"
    )
    add_store_arguments(edit_parser)
    edit_parser.set_defaults(handler=edit.run)

    # List command
    list_parser = subparsers.add_parser(
        "list",
        help="List all note-issues",
        epilog="For details, see: https://github.com/Stabledog/notehub/blob/main/notehub-help.md#command-list",
    )
    add_store_arguments(list_parser)
    list_parser.set_defaults(handler=list.run)

    # Sync command
    sync_parser = subparsers.add_parser(
        "sync",
        help="Commit and push cache changes to GitHub",
        epilog="For details, see: https://github.com/Stabledog/notehub/blob/main/notehub-help.md#command-sync",
    )
    sync_parser.add_argument(
        "note_ident", metavar="NOTE-IDENT", help="Issue number or title regex"
    )
    add_store_arguments(sync_parser)
    sync_parser.set_defaults(handler=sync.run)

    return parser


def main(args=None):
    """Parse arguments and dispatch to appropriate command."""
    args = sys.argv[1:] if not args else args
    parser = create_parser()
    parsed = parser.parse_args(args)

    return parsed.handler(parsed)
