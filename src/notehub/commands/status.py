import subprocess
import sys
from argparse import Namespace

from ..context import StoreContext
from ..gh_wrapper import check_gh_installed, check_gh_auth, get_gh_user


def run(args: Namespace) -> int:
    """
    Execute status command - display context, auth state, and user identity.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        int: Exit code (always 0 - informational only)
    """
    # Resolve store context
    context = StoreContext.resolve(args)
    
    # Detect local repo path (if in a git repository)
    repo_path = get_local_repo_path()
    
    # Display Store Context
    print("Store Context:")
    print(f"  Host:  {context.host}")
    print(f"  Org:   {context.org}")
    print(f"  Repo:  {context.repo}")
    print(f"  Full:  {context.full_identifier()}")
    
    if repo_path:
        print(f"  Path:  {repo_path}")
    else:
        print(f"  Path:  N/A - global context")
    
    print()
    
    # Check if gh is installed
    if not check_gh_installed():
        print("GitHub CLI:")
        print("  Status: ✗ gh CLI not found")
        print("  Info:   Install from https://cli.github.com/")
        return 0
    
    # Display Authentication Status
    print("Authentication:")
    
    is_authenticated = check_gh_auth(context.host)
    
    if is_authenticated:
        user = get_gh_user(context.host)
        print(f"  Status: ✓ Authenticated to {context.host}")
        if user:
            print(f"  User:   {user}")
    else:
        print(f"  Status: ✗ Not authenticated to {context.host}")
        print(f"  Run:    gh auth login --hostname {context.host}")
    
    return 0


def get_local_repo_path() -> str | None:
    """
    Get the root path of the local git repository, if in one.
    
    Returns:
        str: Absolute path to repo root, or None if not in a git repo
    """
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        return result.stdout.strip()
    
    return None
