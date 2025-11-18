"""Show command - display note-header and URLs for specified issues."""

import re
import sys
from argparse import Namespace

from ..context import StoreContext
from ..gh_wrapper import GhError, get_issue, list_issues


def resolve_note_ident(context: StoreContext, ident: str) -> tuple[int | None, str | None]:
    """
    Resolve note-ident to issue number.
    
    Args:
        context: Store context (host/org/repo)
        ident: Issue number (e.g., "123") or title regex (e.g., "bug.*login")
    
    Returns:
        Tuple of (issue_number, error_message)
        On success: (123, None)
        On failure: (None, "error description")
    """
    if ident.isdigit():
        # Direct issue number - return as-is
        return (int(ident), None)
    else:
        # Title regex - fetch only number and title for matching
        try:
            all_issues = list_issues(
                context.host, 
                context.org, 
                context.repo, 
                fields="number,title"
            )
            
            # Apply regex to titles (case-insensitive)
            pattern = re.compile(ident, re.IGNORECASE)
            matches = [issue for issue in all_issues if pattern.search(issue['title'])]
            
            if len(matches) == 0:
                return (None, f"No issues found matching '{ident}'")
            
            if len(matches) > 1:
                print(
                    f"Warning: '{ident}' matched {len(matches)} issues, using first match",
                    file=sys.stderr
                )
            
            return (matches[0]["number"], None)
            
        except GhError as e:
            return (None, f"Failed to list issues: {e.stderr.strip()}")


def format_note_header(issue: dict) -> str:
    """
    Format issue as note-header: [#123] Title
    
    Args:
        issue: Issue dict with 'number' and 'title' keys
    
    Returns:
        Formatted string
    """
    return f"[#{issue['number']}] {issue['title']}"


def run(args: Namespace) -> int:
    """
    Execute show command.
    
    Displays note-header and URL for each specified note-ident.
    Continues processing all idents even if some fail.
    
    Returns:
        0 if all successful, 1 if any errors occurred
    """
    context = StoreContext.resolve(args)
    any_errors = False
    
    for i, ident in enumerate(args.note_idents):
        # Add blank line between issues (except before first)
        if i > 0:
            print()
        
        try:
            issue_num, error = resolve_note_ident(context, ident)
            
            if error:
                print(f"Error: {error}", file=sys.stderr)
                any_errors = True
                continue
            
            # Fetch full issue data (includes html_url which list_issues uses 'url')
            issue = get_issue(context.host, context.org, context.repo, issue_num)
            
            # Display note-header
            print(format_note_header(issue))
            
            # Display URL (indented with 2 spaces)
            url = issue["html_url"]
            print(f"  {url}")
            
        except GhError as e:
            print(f"Error processing '{ident}': {e.stderr.strip()}", file=sys.stderr)
            any_errors = True
    
    return 1 if any_errors else 0
