import json
import os
import subprocess
import sys
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
    Prepare gh command using gh.sh or ghe.sh wrapper (from gh-doctor dotkit).

    Delegates ALL auth/token/host logic to gh.sh/ghe.sh scripts.
    These scripts handle everything - we just call them.

    Args:
        host: GitHub hostname (e.g., 'github.com' or 'github.enterprise.com')
        base_cmd: Base gh command (e.g., ["gh", "api", "..."])

    Returns:
        tuple: (command as list, environment dict)
    """
    env = os.environ.copy()

    # Set GH_HOST to target the correct GitHub instance
    env["GH_HOST"] = host

    # Replace 'gh' with appropriate wrapper:
    # - gh.sh for github.com
    # - ghe.sh for enterprise hosts
    cmd = base_cmd.copy()
    if cmd[0] == "gh":
        if host == "github.com":
            cmd[0] = "gh.sh"
        else:
            cmd[0] = "ghe.sh"

    return cmd, env


def _run_gh_command(
    cmd: list[str],
    env: dict,
    host: str,
    capture_output: bool = True,
    stdin=None,
    stdout=None,
    stderr=None,
) -> subprocess.CompletedProcess:
    """
    Execute gh command through shell (delegates to gh() function from gh-doctor dotkit).

    Fail fast - no error recovery, no fallbacks.
    The gh() function handles all auth and provides its own error messages.

    Args:
        cmd: Shell command to execute (already prepared by _prepare_gh_cmd)
        env: Environment variables
        host: GitHub hostname (unused, kept for API compatibility)
        capture_output: Whether to capture stdout/stderr
        stdin/stdout/stderr: Optional I/O redirection

    Returns:
        subprocess.CompletedProcess result
    """
    if capture_output:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, errors="replace")
    else:
        result = subprocess.run(cmd, stdin=stdin, stdout=stdout, stderr=stderr, env=env)
    return result


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


def create_issue(
    host: str,
    org: str,
    repo: str,
    interactive: bool = True,
    labels: list[str] | None = None,
) -> GhResult:
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
        result = _run_gh_command(
            cmd,
            env,
            host,
            capture_output=False,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
    else:
        result = _run_gh_command(cmd, env, host)

    if result.returncode != 0:
        raise GhError(result.returncode, "")

    return GhResult(
        returncode=result.returncode,
        stdout="",  # Empty in interactive mode
        stderr="",
    )


def get_issue(host: str, org: str, repo: str, issue_number: int) -> dict:
    """
    Fetch issue JSON via gh api.

    Args:
        host: GitHub host (e.g., 'github.com')
        org: Organization or user name
        repo: Repository name
        issue_number: Issue number

    Returns:
        Issue dict with: number, title, html_url, body

    Raises:
        GhError: If gh command fails
    """
    # Use --jq to filter to only the fields we need
    jq_filter = "{number: .number, title: .title, html_url: .html_url, body: .body}"
    base_cmd = [
        "gh",
        "api",
        f"repos/{org}/{repo}/issues/{issue_number}",
        "--jq",
        jq_filter,
    ]

    cmd, env = _prepare_gh_cmd(host, base_cmd)
    result = _run_gh_command(cmd, env, host)

    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise GhError(result.returncode, result.stderr)

    if not result.stdout:
        error_msg = f"No response from GitHub server at {host}. Check your network connection."
        print(error_msg, file=sys.stderr)
        raise GhError(1, error_msg)

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid response from GitHub server at {host}: {str(e)}"
        print(error_msg, file=sys.stderr)
        raise GhError(1, error_msg) from e


def get_issue_metadata(host: str, org: str, repo: str, issue_number: int) -> dict:
    """
    Fetch issue metadata (updated_at, title) without full body.

    Args:
        host: GitHub host (e.g., 'github.com')
        org: Organization or user name
        repo: Repository name
        issue_number: Issue number

    Returns:
        Issue dict with: number, title, html_url, updated_at

    Raises:
        GhError: If gh command fails
    """
    # Fetch only metadata fields
    jq_filter = "{number: .number, title: .title, html_url: .html_url, updated_at: .updated_at}"

    base_cmd = [
        "gh",
        "api",
        f"repos/{org}/{repo}/issues/{issue_number}",
        "--jq",
        jq_filter,
    ]

    cmd, env = _prepare_gh_cmd(host, base_cmd)
    result = _run_gh_command(cmd, env, host)

    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise GhError(result.returncode, result.stderr)

    if not result.stdout:
        error_msg = f"No response from GitHub server at {host}. Check your network connection."
        print(error_msg, file=sys.stderr)
        raise GhError(1, error_msg)

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid response from GitHub server at {host}: {str(e)}"
        print(error_msg, file=sys.stderr)
        raise GhError(1, error_msg) from e


def list_issues(
    host: str,
    org: str,
    repo: str,
    fields: str = "number,title,url,labels",
    limit: int = 1000,
) -> list[dict]:
    """
    List all issues with 'notehub' label via gh issue list.

    Args:
        host: GitHub host
        org: Organization or user name
        repo: Repository name
        fields: Comma-separated list of fields to fetch
               (e.g., "number,title,body,url,labels")
        limit: Maximum number of issues to return (default 1000)

    Returns:
        List of issue dicts with requested fields

    Raises:
        GhError: If gh command fails
    """
    repo_arg = build_repo_arg(host, org, repo)

    base_cmd = [
        "gh",
        "issue",
        "list",
        "--repo",
        repo_arg,
        "--label",
        "notehub",
        "--limit",
        str(limit),
        "--json",
        fields,
    ]

    cmd, env = _prepare_gh_cmd(host, base_cmd)
    result = _run_gh_command(cmd, env, host)

    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise GhError(result.returncode, result.stderr)

    # Ensure we have valid output before parsing
    if not result.stdout:
        error_msg = f"No response from GitHub server at {host}. Check your network connection."
        print(error_msg, file=sys.stderr)
        raise GhError(1, error_msg)

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid response from GitHub server at {host}: {str(e)}"
        print(error_msg, file=sys.stderr)
        raise GhError(1, error_msg) from e


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

    try:
        result = _run_gh_command(cmd, env, host)
    except GhError:
        return False

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

        result = _run_gh_command(cmd, env, host)

        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    return None


def check_gh_installed() -> bool:
    """
    Check if gh.sh wrapper is available (provided by gh-doctor dotkit).

    Assumes dotkit setup via ~/.local/bin is already done.
    Always returns True - if gh.sh is missing, commands will fail fast.

    Returns:
        bool: Always True
    """
    return True


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
    base_cmd = [
        "gh",
        "api",
        api_path,
        "-X",
        "POST",
        "-f",
        f"name={label_name}",
        "-f",
        f"color={color}",
        "-f",
        f"description={description}",
    ]
    cmd, env = _prepare_gh_cmd(host, base_cmd)

    try:
        result = _run_gh_command(cmd, env, host)
    except GhError:
        return False

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


def update_issue(host: str, org: str, repo: str, issue_number: int, body: str) -> GhResult:
    """
    Update issue body via gh issue edit.

    Args:
        host: GitHub host
        org: Organization/owner name
        repo: Repository name
        issue_number: Issue number
        body: New body content

    Returns:
        GhResult

    Raises:
        GhError: If gh command fails
    """
    repo_arg = build_repo_arg(host, org, repo)
    base_cmd = [
        "gh",
        "issue",
        "edit",
        str(issue_number),
        "--repo",
        repo_arg,
        "--body",
        body,
    ]

    cmd, env = _prepare_gh_cmd(host, base_cmd)
    result = _run_gh_command(cmd, env, host)

    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise GhError(result.returncode, result.stderr)

    return GhResult(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
