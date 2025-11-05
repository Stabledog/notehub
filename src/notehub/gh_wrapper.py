import json
import subprocess
import sys

def create_issue():
    """Create a new issue interactively using gh CLI."""
    subprocess.run(["gh", "issue", "create"])

def get_issue(host: str, org: str, repo: str, issue_number: int) -> dict:
    """
    Fetch issue JSON via gh api.
    
    Args:
        host: GitHub host (e.g., 'github.com' or 'github.enterprise.com')
        org: Organization/owner name
        repo: Repository name
        issue_number: Issue number to fetch
        
    Returns:
        dict: Parsed JSON response from GitHub API
        
    Raises:
        RuntimeError: If gh command fails (issue not found, auth error, etc.)
    """
    # Build API path
    api_path = f"repos/{org}/{repo}/issues/{issue_number}"
    
    # Build command
    cmd = ["gh", "api", api_path]
    
    # Add hostname if not github.com
    if host != "github.com":
        cmd.extend(["--hostname", host])
    
    # Execute command
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        # Pass through stderr to user
        print(result.stderr, file=sys.stderr, end="")
        raise RuntimeError(f"gh command failed with exit code {result.returncode}")
    
    # Parse and return JSON
    return json.loads(result.stdout)
    return json.loads(result.stdout)

def check_gh_auth(host: str = "github.com") -> bool:
    """
    Check if gh is authenticated for the specified host.
    
    Args:
        host: GitHub host (e.g., 'github.com' or 'github.enterprise.com')
        
    Returns:
        bool: True if authenticated, False otherwise
    """
    result = subprocess.run(
        ["gh", "auth", "status", "--hostname", host],
        capture_output=True
    )
    return result.returncode == 0


def get_gh_user(host: str = "github.com") -> str | None:
    """
    Get the authenticated username for the specified host.
    
    Args:
        host: GitHub host (e.g., 'github.com' or 'github.enterprise.com')
        
    Returns:
        str: Username if authenticated, None otherwise
    """
    # gh auth status outputs to stderr, format: "Logged in to <host> as <user> (...)"
    result = subprocess.run(
        ["gh", "auth", "status", "--hostname", host],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return None
    
    # Parse stderr for username
    # Expected format: "✓ Logged in to github.com as username (/path/to/config)"
    for line in result.stderr.split('\n'):
        if 'Logged in to' in line and host in line:
            parts = line.split()
            try:
                # Find "as" and get the next word
                as_index = parts.index('as')
                return parts[as_index + 1]
            except (ValueError, IndexError):
                pass
    
    return None


def check_gh_installed() -> bool:
    """
    Check if gh CLI is installed and available.
    
    Returns:
        bool: True if gh is found, False otherwise
    """
    result = subprocess.run(
        ["which", "gh"],
        capture_output=True
    )
    return result.returncode == 0
