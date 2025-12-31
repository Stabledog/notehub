import os
import subprocess
from argparse import Namespace

from ..context import StoreContext
from ..gh_wrapper import check_gh_auth, check_gh_installed, get_gh_user
from ..utils import HELP_URL


def get_env_auth_source(host: str = "github.com") -> str | None:
    """
    Return which environment variable provides authentication, if any.
    Token priority depends on the host being accessed.

    Args:
        host: GitHub hostname (e.g., 'github.com' or enterprise host)

    Returns:
        str: Name of the environment variable, or None if using gh auth
    """
    if host == "github.com":
        # For public GitHub, only report token if it's appropriate for public GitHub
        if os.environ.get("GITHUB_TOKEN"):
            return "GITHUB_TOKEN"
        # GH_TOKEN only if no enterprise tokens (they would conflict)
        if (
            os.environ.get("GH_TOKEN")
            and not os.environ.get("GH_ENTERPRISE_TOKEN_2")
            and not os.environ.get("GH_ENTERPRISE_TOKEN")
        ):
            return "GH_TOKEN"
        # If enterprise tokens are set, we're NOT using them for github.com
        # (let gh auth take over)
        return None
    else:
        # For enterprise hosts, check enterprise tokens
        if os.environ.get("GH_ENTERPRISE_TOKEN_2"):
            return "GH_ENTERPRISE_TOKEN_2"
        if os.environ.get("GH_ENTERPRISE_TOKEN"):
            return "GH_ENTERPRISE_TOKEN"
        # GH_TOKEN only if GITHUB_TOKEN isn't set (they would conflict)
        if os.environ.get("GH_TOKEN") and not os.environ.get("GITHUB_TOKEN"):
            return "GH_TOKEN"
        return None


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
        print("  Path:  N/A - global context")

    print()

    # Check if gh is installed
    if not check_gh_installed():
        print("GitHub CLI:")
        print("  Status: ✗ gh CLI not found")
        print("  Info:   Install from https://cli.github.com/")
        return 0

    # Display Authentication Status
    print("Authentication:")

    # Show environment-based auth if present
    env_auth = get_env_auth_source(context.host)
    if env_auth:
        print(f"  Source: Environment variable ({env_auth})")
    else:
        print("  Source: gh auth (stored credentials)")

    is_authenticated = check_gh_auth(context.host)

    if is_authenticated:
        user = get_gh_user(context.host)
        print(f"  Status: ✓ Authenticated to {context.host}")
        if user:
            print(f"  User:   {user}")
    else:
        print(f"  Status: ✗ Not authenticated to {context.host}")
        print()
        print("  Setup options:")
        print(f"    1. gh auth login --hostname {context.host}")
        if context.host == "github.com":
            print("    2. export GITHUB_TOKEN=<token>")
            print("    3. export GH_TOKEN=<token>")
        else:
            print("    2. export GH_ENTERPRISE_TOKEN=<token>")
            print("    3. export GH_ENTERPRISE_TOKEN_2=<token>")

    print()
    print(f"For help: {HELP_URL}")

    return 0


def get_local_repo_path() -> str | None:
    """
    Get the root path of the local git repository, if in one.

    Returns:
        str: Absolute path to repo root, or None if not in a git repo
    """
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)

    if result.returncode == 0:
        return result.stdout.strip()

    return None
