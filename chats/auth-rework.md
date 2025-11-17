lmatheson4_bbeng: This project is designed to delegate authentication to `gh`, but it doesn't seem to be working right.   When I manually run `gh_enterprise` (my shell helper), it uses environ vars to setup for our internal GH enterprise or the public service.  That's really the behavior we need from notehub.

Identify areas in the spec that deal with authentication and propose revisions to achieve that

Workspace: Collecting workspace information# Authentication Design Issues & Proposed Fixes

## Current State Analysis

### Problem
The spec delegates authentication to `gh` but doesn't account for:
1. Multiple GitHub hosts (github.com + GHES)
2. Environment-based authentication switching (like your `gh_enterprise` helper)
3. How `gh` knows which credentials to use for which host

### Your Working Pattern
```bash
# Your shell helper sets:
GH_TOKEN=${GH_ENTERPRISE_TOKEN} GH_HOST=${GH_HOST_ENTERPRISE} gh issue list
```

This tells `gh` CLI:
- Which token to use (`GH_TOKEN`)
- Which host to target (via `--hostname` flag, not `GH_HOST` env var)

---

## Spec Sections Requiring Changes

### 1. **Dependencies Section** (Currently Silent on Auth)

**Current:**
```markdown
## Dependencies
- **Hard**: `gh` (GitHub CLI) configured for all relevant hosts.
```

**Proposed Revision:**
```markdown
## Dependencies
- **Hard**: `gh` (GitHub CLI) v2.0+
- **Authentication**: 
  - Use `gh auth login --hostname <host>` for persistent auth, OR
  - Set `GH_TOKEN` environment variable for session-based auth
  - For convenience: set `GH_ENTERPRISE_TOKEN` (notehub auto-maps to `GH_TOKEN`)
  - notehub uses `--hostname` flag to target the correct GitHub instance
  
**Token Requirements:**
- Personal access tokens need `repo` scope for private repositories
- For public repos only: `public_repo` scope is sufficient
- Check token scopes: `gh auth status -t`
```

---

### 2. **Context Resolution** (Doesn't Mention Auth Flow)

**Current:** Only resolves host/org/repo, no auth consideration.

**Proposed Addition After "Context resolution":**
```markdown
## Host Resolution Priority

notehub determines which GitHub host to use:

1. `--host` CLI flag (highest priority)
2. `GH_HOST` environment variable (notehub convention)
3. `git config notehub.host` (repository-level)
4. `git config --global notehub.host` (global)
5. Default to "github.com" (lowest priority)

## Authentication Flow

notehub delegates all authentication to `gh` CLI but provides convenient credential handling:

1. **Token Mapping** (before invoking `gh`):
   - If `GH_ENTERPRISE_TOKEN` set and `GH_TOKEN` not set: copy to `GH_TOKEN`
   - If `GH_TOKEN` already set: use as-is (takes precedence)

2. **Host Targeting**:
   - Always use `--hostname <host>` flag with `gh` commands
   - This tells `gh` which stored credentials to use
   - For github.com: `--hostname github.com` (explicit)

3. **Credential Precedence** (as interpreted by `gh` CLI):
   - `GH_TOKEN` environment variable (highest)
   - `gh auth` stored credentials for specified hostname
   - Interactive prompt (if neither available)

4. **Multi-Host Workflow**:
   ```bash
   # Public GitHub (using stored credentials)
   notehub status
   
   # Enterprise GitHub (using environment token)
   GH_ENTERPRISE_TOKEN=<token> notehub --host my.github.com status
   
   # Or set in shell for session:
   export GH_HOST=my.github.com
   export GH_ENTERPRISE_TOKEN=<token>
   notehub status
   ```
```

---

### 3. **gh_wrapper.py Design** (Missing Env Handling)

**Current in design.md:**
```python
def get_issue(host: str, org: str, repo: str, issue_number: int) -> dict:
    """Fetch issue JSON via gh api."""
    pass
```

**Proposed Revision:**
```python
def get_issue(host: str, org: str, repo: str, issue_number: int) -> dict:
    """
    Fetch issue JSON via gh api.
    
    Args:
        host: GitHub hostname (e.g., "github.com" or "my.github.com")
        org: Organization name
        repo: Repository name
        issue_number: Issue number
    
    Environment variables:
        GH_TOKEN: Used by gh CLI for auth (set externally)
        GH_ENTERPRISE_TOKEN: Mapped to GH_TOKEN if GH_TOKEN not set
    
    Returns:
        dict: Issue data from GitHub API
    """
    pass

def _prepare_gh_cmd(host: str, base_cmd: list[str]) -> tuple[list[str], dict]:
    """
    Prepare gh command with proper hostname and auth environment.
    
    Args:
        host: GitHub hostname to target
        base_cmd: Base gh command (e.g., ["gh", "api", "..."])
    
    Returns:
        tuple: (modified command with --hostname, environment dict)
    """
    env = os.environ.copy()
    
    # Map enterprise token to standard token
    if 'GH_ENTERPRISE_TOKEN' in env and 'GH_TOKEN' not in env:
        env['GH_TOKEN'] = env['GH_ENTERPRISE_TOKEN']
    
    # Add --hostname flag (always explicit)
    cmd = base_cmd.copy()
    cmd.extend(["--hostname", host])
    
    return cmd, env
```

---

### 4. **Subprocess Invocation Pattern** (No Env Passing)

**Current in design.md:**
```python
result = subprocess.run(
    ["gh", "api", "repos/{org}/{repo}/issues/{num}"],
    capture_output=True,
    text=True
)
```

**Proposed Revision:**
```python
def run_gh_api(host: str, endpoint: str) -> dict:
    """
    Run gh api command with proper auth environment.
    
    Args:
        host: GitHub hostname
        endpoint: API endpoint path (e.g., "repos/org/repo/issues/123")
    
    Returns:
        dict: Parsed JSON response
    
    Raises:
        RuntimeError: If gh command fails
    """
    base_cmd = ["gh", "api", endpoint]
    cmd, env = _prepare_gh_cmd(host, base_cmd)
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode != 0:
        _handle_gh_error(result, host)
        raise RuntimeError(f"gh command failed with exit code {result.returncode}")
    
    return json.loads(result.stdout)

def _handle_gh_error(result: subprocess.CompletedProcess, host: str) -> None:
    """Print helpful error messages based on gh CLI stderr output."""
    stderr_lower = result.stderr.lower()
    
    # Always print original error first
    print(result.stderr, file=sys.stderr, end="")
    
    # Add helpful guidance for auth failures
    if any(keyword in stderr_lower for keyword in ['authentication', 'credentials', 'token', '401', '403']):
        print(f"\n❌ Authentication failed for {host}", file=sys.stderr)
        print(f"   Try: gh auth login --hostname {host}", file=sys.stderr)
        print(f"   Or:  export GH_ENTERPRISE_TOKEN=<token>", file=sys.stderr)
        if host != "github.com":
            print(f"   Or:  export GH_TOKEN=<token>", file=sys.stderr)

def check_gh_auth(host: str) -> bool:
    """Check if authenticated to specified host."""
    base_cmd = ["gh", "auth", "status"]
    cmd, env = _prepare_gh_cmd(host, base_cmd)
    
    result = subprocess.run(cmd, capture_output=True, env=env)
    return result.returncode == 0

def get_gh_user(host: str) -> Optional[str]:
    """Get authenticated username for specified host."""
    try:
        base_cmd = ["gh", "api", "user", "--jq", ".login"]
        cmd, env = _prepare_gh_cmd(host, base_cmd)
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None
```

---

### 5. **Status Command** (Should Show Effective Auth)

**Current in design.md:**
```python
def run(args):
    context = StoreContext.resolve(args)
    if check_gh_auth(context.host):
        print(f"✓ Authenticated to {context.host}")
```

**Proposed Enhancement:**
```python
def run(args):
    context = StoreContext.resolve(args)
    
    # Show environment-based auth if present
    env_auth = get_env_auth_source()
    if env_auth:
        print(f"  Auth:   Environment variable ({env_auth})")
    
    # Check authentication status
    auth_status = check_gh_auth(context.host)
    if auth_status:
        user = get_gh_user(context.host)
        print(f"  Status: ✓ Authenticated to {context.host}")
        if user:
            print(f"  User:   {user}")
    else:
        print(f"  Status: ✗ Not authenticated to {context.host}")
        print(f"\n  Setup options:")
        print(f"    1. gh auth login --hostname {context.host}")
        print(f"    2. export GH_ENTERPRISE_TOKEN=<token>")
        print(f"    3. export GH_TOKEN=<token>")

def get_env_auth_source() -> str | None:
    """Return which env var provides auth, if any."""
    if os.environ.get('GH_TOKEN'):
        return 'GH_TOKEN'
    if os.environ.get('GH_ENTERPRISE_TOKEN'):
        return 'GH_ENTERPRISE_TOKEN'
    return None

def check_gh_auth(host: str) -> bool:
    """
    Check if authenticated to specified host.
    
    Args:
        host: GitHub hostname to check
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    base_cmd = ["gh", "auth", "status"]
    cmd, env = _prepare_gh_cmd(host, base_cmd)
    
    result = subprocess.run(cmd, capture_output=True, env=env)
    return result.returncode == 0
```

---

### 6. **Configuration Section** (Add Auth Guidance)

**Current:**
```markdown
## Configuration
- User configures host,repo,org manually using `git config` command
```

**Proposed Addition:**
```markdown
## Configuration

### Store Context
User configures host, repo, org manually using `git config` command:
```bash
git config notehub.host my.enterprise.github.com
git config notehub.repo myrepo
git config --global notehub.org myorg
```

### Authentication Setup

**Option 1: Persistent (via gh auth)**
```bash
# Public GitHub
gh auth login

# Enterprise GitHub
gh auth login --hostname my.github.com

# Verify
gh auth status --hostname my.github.com
```

**Option 2: Session-based (via environment)**
```bash
# Set in ~/.bashrc or per-session:
export GH_ENTERPRISE_TOKEN=ghp_xxxxxxxxxxxx
export GH_HOST=my.github.com

# notehub will use these automatically
notehub status
```

**Option 3: Hybrid (both hosts)**
```bash
# Public via gh auth
gh auth login

# Enterprise via env var
export GH_ENTERPRISE_TOKEN=ghp_xxxxxxxxxxxx
export GH_HOST=my.github.com

# Switch contexts:
notehub status                              # Uses gh auth for github.com
notehub --host my.github.com status         # Uses GH_ENTERPRISE_TOKEN
```

### Token Scope Requirements
- **Private repositories**: Token needs `repo` scope
- **Public repositories only**: `public_repo` scope sufficient
- **Check your token**: `gh auth status -t` or view at GitHub Settings → Developer settings → Personal access tokens
```

---

### 7. **Error Handling** (Add Auth-Specific Errors)

**Add to spec after "Misc" section:**
```markdown
### Authentication Errors

**Detection Strategy:**
- Check stderr output for keywords: "authentication", "credentials", "token"
- Exit code `1` from `gh` CLI (general failure)
- Exit code `4` from `gh auth` commands (authentication failure)

**Error Messages:**
- Print original `gh` error first (preserve context)
- Add helpful guidance based on current host
- Show all available authentication methods
- For enterprise hosts: mention both `GH_TOKEN` and `GH_ENTERPRISE_TOKEN`

**Example Output:**
```
ERROR: HTTP 401: Bad credentials (https://api.github.com/)

❌ Authentication failed for my.github.com
   Try: gh auth login --hostname my.github.com
   Or:  export GH_ENTERPRISE_TOKEN=<token>
   Or:  export GH_TOKEN=<token>
```
```

---

## Implementation Summary for gh_wrapper.py

```python
import os
import subprocess
import json
import sys
from typing import Optional

def _prepare_gh_cmd(host: str, base_cmd: list[str]) -> tuple[list[str], dict]:
    """
    Prepare gh command with proper hostname and auth environment.
    
    The gh CLI uses --hostname flag to determine which stored credentials
    to use. We explicitly add this flag for every command.
    """
    env = os.environ.copy()
    
    # Map enterprise token to standard token (if not already set)
    if 'GH_ENTERPRISE_TOKEN' in env and 'GH_TOKEN' not in env:
        env['GH_TOKEN'] = env['GH_ENTERPRISE_TOKEN']
    
    # Add --hostname flag (always explicit, even for github.com)
    cmd = base_cmd.copy()
    cmd.extend(["--hostname", host])
    
    return cmd, env

def get_issue(host: str, org: str, repo: str, issue_number: int) -> dict:
    """Fetch issue with proper auth environment and hostname targeting."""
    endpoint = f"repos/{org}/{repo}/issues/{issue_number}"
    base_cmd = ["gh", "api", endpoint]
    cmd, env = _prepare_gh_cmd(host, base_cmd)
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode != 0:
        _handle_gh_error(result, host)
        raise RuntimeError(f"gh command failed with exit code {result.returncode}")
    
    return json.loads(result.stdout)

def _handle_gh_error(result: subprocess.CompletedProcess, host: str) -> None:
    """Print helpful error messages based on gh CLI stderr output."""
    stderr_lower = result.stderr.lower()
    
    # Always print original error first
    print(result.stderr, file=sys.stderr, end="")
    
    # Add helpful guidance for auth failures
    if any(keyword in stderr_lower for keyword in ['authentication', 'credentials', 'token', '401', '403']):
        print(f"\n❌ Authentication failed for {host}", file=sys.stderr)
        print(f"   Try: gh auth login --hostname {host}", file=sys.stderr)
        print(f"   Or:  export GH_ENTERPRISE_TOKEN=<token>", file=sys.stderr)
        if host != "github.com":
            print(f"   Or:  export GH_TOKEN=<token>", file=sys.stderr)

def check_gh_auth(host: str) -> bool:
    """Check if authenticated to specified host."""
    base_cmd = ["gh", "auth", "status"]
    cmd, env = _prepare_gh_cmd(host, base_cmd)
    
    result = subprocess.run(cmd, capture_output=True, env=env)
    return result.returncode == 0

def get_gh_user(host: str) -> Optional[str]:
    """Get authenticated username for specified host."""
    try:
        base_cmd = ["gh", "api", "user", "--jq", ".login"]
        cmd, env = _prepare_gh_cmd(host, base_cmd)
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None
```

---

## Testing Checklist

After implementing these changes, verify:

- ✅ `notehub status` works with `gh auth login` credentials for github.com
- ✅ `notehub status` works with `GH_TOKEN` env var
- ✅ `notehub status` works with `GH_ENTERPRISE_TOKEN` env var
- ✅ `GH_TOKEN` takes precedence over `GH_ENTERPRISE_TOKEN` when both set
- ✅ `notehub --host enterprise.com show 123` uses enterprise credentials
- ✅ Switching between github.com and GHES in same session works
- ✅ Error messages guide user to correct auth method for the target host
- ✅ Error messages show original `gh` CLI error first
- ✅ `status` command shows which auth source is active (env var vs gh auth)
- ✅ `--hostname` flag is used for all `gh` commands, not `GH_HOST` env var
- ✅ Authentication with token lacking proper scopes shows helpful error
