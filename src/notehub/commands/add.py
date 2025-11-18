from argparse import Namespace

from ..context import StoreContext
from ..gh_wrapper import create_issue, GhError


def run(args: Namespace) -> int:
    """
    Execute add command - create a new note-issue.

    Args:
        args: Parsed command-line arguments

    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    context = StoreContext.resolve(args)

    try:
        # Pure passthrough - gh will prompt user and print URL
        create_issue(context.host, context.org, context.repo, interactive=True)
        return 0

    except GhError as e:
        # gh's error message already shown to user via stderr passthrough
        return e.returncode
