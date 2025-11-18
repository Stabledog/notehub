import json
import subprocess
import sys
import os
from typing import Optional
from dataclasses import dataclass


class GhError(Exception):
    """gh CLI invocation failed."""
    def __init__(self, returncode: int, stderr: str):
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"gh CLI failed with exit code {returncode}")


@dataclass
class GhResult:
    """Result from gh CLI invocation."""
    returncode: int
    stdout: str
    stderr: str


def _prepare_gh_cmd(host: str, base_cmd: list[str]) -> tuple[list[str], dict]:
    """
    Prepare gh command with proper hostname and auth environment.
    
    Mimics the gh_enterprise wrapper pattern:
    - Checks GH_ENTERPRISE_TOKEN_2 → GH_ENTERPRISE_TOKEN → GH_TOKEN
    - Sets both GH_TOKEN and GH_ENTERPRISE_TOKEN in subprocess env
    - Sets GH_HOST to target correct GitHub instance
    
    Args:
        host: GitHub hostname (e.g., 'github.com' or 'my.github.com')
        base_cmd: Base gh command (e.g., ["gh", "api", "..."])
        
    Returns:
        tuple: (command, environment dict)
    """
    env = os.environ.copy()
    
    # Token priority: GH_ENTERPRISE_TOKEN_2 > GH_ENTERPRISE_TOKEN > GH_TOKEN
    token = None
    if 'GH_ENTERPRISE_TOKEN_2' in env:
        token = env['GH_ENTERPRISE_TOKEN_2']
    elif 'GH_ENTERPRISE_TOKEN' in env:
        token = env['GH_ENTERPRISE_TOKEN']
    elif 'GH_TOKEN' in env:
        token = env['GH_TOKEN']
    
    # If we found a token, set both GH_TOKEN and GH_ENTERPRISE_TOKEN
    if token:
        env['GH_TOKEN'] = token
        env['GH_ENTERPRISE_TOKEN'] = token
    
    # Set GH_HOST to target the correct GitHub instance
    env['GH_HOST'] = host
    
    # Return command as-is (no --hostname flag needed)
    cmd = base_cmd.copy()
    
    return cmd, env


def _handle_gh_error(result: subprocess.CompletedProcess, host: str) -> None:
    """
    Print helpful error messages based on gh CLI stderr output.
    
    Args:
        result: Completed subprocess result
        host: GitHub hostname that was targeted
    """
    stderr_lower = result.stderr.lower() if result.stderr else ""
    
    # Check for authentication-related errors
    if any(keyword in stderr_lower for keyword in ['authentication', 'credentials', 'token', '401', '403']):
        print(f"\n❌ Authentication failed for {host}", file=sys.stderr)
        print(f"   Try: gh auth login --hostname {host}", file=sys.stderr)
        print(f"   Or:  export GH_ENTERPRISE_TOKEN=<token>", file=sys.stderr)
        print(f"   Or:  export GH_ENTERPRISE_TOKEN_2=<token>", file=sys.stderr)
        if host != "github.com":
            print(f"   Or:  export GH_TOKEN=<token>", file=sys.stderr)


def build_repo_arg(host: str, org: str, repo: str) -> str:
    """
    Build --repo argument value for gh commands.
    
    Since we set GH_HOST in the environment, we always use the simple org/repo format.
    The GH_HOST environment variable handles routing to the correct GitHub instance.
    
    Args:
        host: GitHub host (e.g., 'github.com' or 'github.enterprise.com')
        org: Organization/owner name
        repo: Repository name
        
    Returns:
        str: Formatted repo argument as 'org/repo'
    """
    return f"{org}/{repo}"


def create_issue(host: str, org: str, repo: str, interactive: bool = True, labels: list[str] | None = None) -> GhResult:
    """
    Invoke gh issue create in interactive mode.
    
    Args:
        host: GitHub host
        org: Organization/owner name
        repo: Repository name
        interactive: If True, pass stdin/stdout/stderr to user terminal
        labels: List of label names to apply to the issue
        
    Returns:
        GhResult: Result (stdout/stderr will be empty in interactive mode)
        
    Raises:
        GhError: If gh command fails
    """
    repo_arg = build_repo_arg(host, org, repo)
    base_cmd = ["gh", "issue", "create", "--repo", repo_arg]
    
    # Add labels if provided
    if labels:
        for label in labels:
            base_cmd.extend(["--label", label])
    
    cmd, env = _prepare_gh_cmd(host, base_cmd)
    
    if interactive:
        # Pure passthrough - let gh handle all I/O and print URL directly
        result = subprocess.run(
            cmd,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            env=env
        )
    else:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode != 0:
        raise GhError(result.returncode, "")
    
    return GhResult(
        returncode=result.returncode,
        stdout="",  # Empty in interactive mode
        stderr=""
    )


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
    
    # Build command with proper auth environment
    base_cmd = ["gh", "api", api_path]
    cmd, env = _prepare_gh_cmd(host, base_cmd)
    
    # Execute command
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode != 0:
        # Pass through stderr to user
        print(result.stderr, file=sys.stderr, end="")
        _handle_gh_error(result, host)
        raise RuntimeError(f"gh command failed with exit code {result.returncode}")
    
    # Parse and return JSON
    return json.loads(result.stdout)

def check_gh_auth(host: str = "github.com") -> bool:
    """
    Check if gh is authenticated for the specified host by attempting a real operation.
    
    Uses 'gh repo list --limit 1' as a lightweight test that requires authentication.
    
    Args:
        host: GitHub host (e.g., 'github.com' or 'github.enterprise.com')
        
    Returns:
        bool: True if authenticated, False otherwise
    """
    base_cmd = ["gh", "repo", "list", "--limit", "1"]
    cmd, env = _prepare_gh_cmd(host, base_cmd)
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode != 0:
        # Pass through any errors to console
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        return False
    
    return True


def get_gh_user(host: str = "github.com") -> str | None:
    """
    Get the authenticated username for the specified host.
    
    Args:
        host: GitHub host (e.g., 'github.com' or 'github.enterprise.com')
        
    Returns:
        str: Username if authenticated, None otherwise
    """
    try:
        base_cmd = ["gh", "api", "user", "--jq", ".login"]
        cmd, env = _prepare_gh_cmd(host, base_cmd)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
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


def ensure_label_exists(host: str, org: str, repo: str, label_name: str, color: str, description: str = "") -> bool:
    """
    Ensure a label exists in the repository, creating it if necessary.
    
    Args:
        host: GitHub host
        org: Organization/owner name
        repo: Repository name
        label_name: Label name to ensure exists
        color: Hex color code (without #), e.g., "FFC107" for yellow
        description: Label description
        
    Returns:
        bool: True if label exists or was created, False on error
    """
    api_path = f"repos/{org}/{repo}/labels"
    base_cmd = ["gh", "api", api_path, "-X", "POST",
                "-f", f"name={label_name}",
                "-f", f"color={color}",
                "-f", f"description={description}"]
    cmd, env = _prepare_gh_cmd(host, base_cmd)
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode == 0:
        return True
    
    # Check if failure was due to label already existing
    # GitHub returns HTTP 422 with "already_exists" in the JSON response
    if result.returncode != 0:
        # Try parsing stdout as JSON to check for already_exists error
        try:
            error_data = json.loads(result.stdout)
            if "errors" in error_data:
                for error in error_data["errors"]:
                    if error.get("code") == "already_exists":
                        return True
        except (json.JSONDecodeError, KeyError):
            pass
    
    # Real error - print it and return False
    if result.stdout:
        print(result.stdout, file=sys.stderr, end="")
    return False
