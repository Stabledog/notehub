import argparse
from notehub.commands import add

def main(args):
    parser = argparse.ArgumentParser(prog="notehub")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Create a new note-issue")
    
    parsed = parser.parse_args(args)
    
    if parsed.command == "add":
        add.run(parsed)
