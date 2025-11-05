import argparse
from notehub.commands import add, show

def add_store_arguments(parser):
    """Add common store context arguments to a parser."""
    parser.add_argument("--host", "-H", help="GitHub host (for GHES)")
    parser.add_argument("--org", "-o", help="Organization/owner name")
    parser.add_argument("--repo", "-r", help="Repository name")
    parser.add_argument("--global", "-g", dest="global_scope", action="store_true",
                       help="Use global config only (ignore local git repo)")

def main(args):
    parser = argparse.ArgumentParser(prog="notehub")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Create a new note-issue")
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show an issue")
    show_parser.add_argument("note_idents", nargs="+", help="Note identifier(s) (issue numbers or URLs)")
    add_store_arguments(show_parser)
    show_parser.set_defaults(func=show.run)

    parsed = parser.parse_args(args)

    if parsed.command == "add":
        add.run(parsed)
    elif parsed.command == "show":
        show.run(parsed)

