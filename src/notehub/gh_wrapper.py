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
