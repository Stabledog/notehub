import argparse
from notehub.commands import add, show

def main(args):
    parser = argparse.ArgumentParser(prog="notehub")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Create a new note-issue")
    
    # Show command
    show_parser = subparsers.add_parser(
        "show",
        help="Display note-header and URLs for specified issues",
    )
    show_parser.add_argument(
        "note_idents",
        nargs="+",
        help="Issue numbers to display",
    )
    show_parser.add_argument("--repo", "-r", help="Target repository name")
    show_parser.add_argument("--org", "-o", help="Target organization/owner")
    show_parser.add_argument("--host", "-h", help="GitHub host (for GHES)")
    show_parser.add_argument(
        "--global",
        "-g",
        dest="global_scope",
        action="store_true",
        help="Use global config only, ignore local repo",
    )
    show_parser.set_defaults(func=show.run)

    parsed = parser.parse_args(args)

    if parsed.command == "add":
        add.run(parsed)
    elif parsed.command == "show":
        show.run(parsed)
