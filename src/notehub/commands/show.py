"""Show command - display note-header and URLs for issues."""

import sys
from argparse import Namespace

from ..context import StoreContext
from ..gh_wrapper import get_issue, GhError


def format_note_header(issue: dict) -> str:
    """
    Format issue as note-header: [#123] Title.
    
    Args:
        issue: Issue dict from GitHub API
        
    Returns:
        str: Formatted note-header
    """
    number = issue["number"]
    title = issue["title"]
    return f"[#{number}] {title}"


def run(args: Namespace) -> int:
    """
    Execute show command.
    
    Args:
        args: Parsed command-line arguments with note_idents attribute
        
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    # Resolve context
    context = StoreContext.resolve(args)
    
    # Track if any errors occurred
    had_error = False
    
    # Process each note-ident
    for ident in args.note_idents:
        # Validate it's numeric
        try:
            issue_number = int(ident)
        except ValueError:
            print(f"Error: '{ident}' is not a valid issue number", file=sys.stderr)
            had_error = True
            continue
        
        # Fetch issue data - pass primitives to gh_wrapper
        try:
            issue = get_issue(context.host, context.org, context.repo, issue_number)
        except GhError as e:
            # Error message already printed to stderr by get_issue
            print(f"Error: Issue #{issue_number} not found in {context.repo_identifier()}", file=sys.stderr)
            had_error = True
            continue
        
        # Format and print output
        note_header = format_note_header(issue)
        issue_url = context.build_issue_url(issue_number)
        
        print(note_header)
        print(f"    {issue_url}")
    
    return 1 if had_error else 0
