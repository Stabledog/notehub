# Notehub: Design Overview

## 1. Module Responsibilities & Public APIs

### 1.1 `__main__.py` - Application Entry Point
**Responsibility**: Bootstrap the application and hand off to CLI parser.

```python
# Public API
def main() -> int:
    """Entry point. Returns exit code."""
    pass
```

### 1.2 `cli.py` - Command-Line Interface Parser
**Responsibility**: Parse command-line arguments and dispatch to appropriate command handlers.

```python
# Public API
def main(argv: list[str]) -> int:
    """Parse args and dispatch to commands. Returns exit code."""
    pass

def create_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all subcommands."""
    pass
```

### 1.3 `context.py` - Store Context Resolution
**Responsibility**: Determine host/org/repo based on flags, git config, environment, and defaults.

```python
# Public API
class StoreContext:
    host: str
    org: str
    repo: str
    
    @classmethod
    def resolve(cls, args: Namespace) -> StoreContext:
        """Resolve context from args, config, env, defaults."""
        pass
    
    def repo_identifier(self) -> str:
        """Return 'org/repo' string."""
        pass
    
    def full_identifier(self) -> str:
        """Return 'host:org/repo' string."""
        pass
    
    def build_issue_url(self, issue_number: int) -> str:
        """
        Build full GitHub issue URL.
        
        Args:
            issue_number: Issue number
            
        Returns:
            str: Full URL like https://github.com/org/repo/issues/123
        """
        return f"https://{self.host}/{self.org}/{self.repo}/issues/{issue_number}"
```

### 1.4 `config.py` - Configuration Management
**Responsibility**: Read/write git config values for notehub settings.

```python
# Public API
def get_git_config(key: str, global_only: bool = False) -> str | None:
    """Retrieve git config value for notehub.{key}."""
    pass

def set_git_config(key: str, value: str, global_scope: bool = False) -> None:
    """Set git config notehub.{key} = value."""
    pass

def get_editor() -> str:
    """Return editor path from $EDITOR or default to 'vi'."""
    pass
```

### 1.5 `gh_wrapper.py` - GitHub CLI Wrapper
**Responsibility**: Execute `gh` commands and manage stdin/stdout/stderr.

```python
# Public API
class GhResult:
    returncode: int
    stdout: str
    stderr: str

def create_issue(context: StoreContext, interactive: bool = True) -> GhResult:
    """Invoke gh issue create."""
    pass

def get_issue(context: StoreContext, issue_number: int) -> dict:
    """Fetch issue JSON via gh api."""
    pass

def update_issue(context: StoreContext, issue_number: int, body: str) -> GhResult:
    """Update issue body via gh issue edit."""
    pass

def list_issues(context: StoreContext, filters: dict = None) -> list[dict]:
    """List issues via gh issue list --json."""
    pass

def search_issues(context: StoreContext, query: str) -> list[dict]:
    """Search issues via gh search issues."""
    pass
```

### 1.6 `commands/status.py` - Status Command
**Responsibility**: Display context, auth state, and user identity.

```python
# Public API
def run(args: Namespace) -> int:
    """Execute status command. Returns exit code."""
    pass
```

### 1.7 `commands/add.py` - Add Command
**Responsibility**: Create new note-issues.

```python
# Public API
def run(args: Namespace) -> int:
    """Execute add command. Returns exit code."""
    pass
```

### 1.8 `commands/show.py` - Show Command
**Responsibility**: Display note-header and URLs for specified note-idents.

```python
# Public API
def run(args: Namespace) -> int:
    """Execute show command. Returns exit code."""
    pass

def resolve_note_ident(context: StoreContext, ident: str) -> int | None:
    """Resolve note-ident to issue number."""
    pass

def format_note_header(issue: dict) -> str:
    """Format issue as [#123] Title."""
    pass
```

### 1.9 `commands/list.py` - List Command
**Responsibility**: List all note-issues.

```python
# Public API
def run(args: Namespace) -> int:
    """Execute list command. Returns exit code."""
    pass
```

### 1.10 `commands/find.py` - Find Command
**Responsibility**: Search note-issue bodies with regex and display matches in context.

```python
# Public API
def run(args: Namespace) -> int:
    """Execute find command. Returns exit code."""
    pass

def highlight_match(text: str, pattern: str) -> str:
    """Return text with ANSI color codes highlighting pattern."""
    pass

def extract_context(body: str, match_line: int, context_lines: int = 1) -> str:
    """Extract lines around match with context."""
    pass
```

### 1.11 `commands/edit.py` - Edit Command
**Responsibility**: Open note-issue in $EDITOR and sync changes.

```python
# Public API
def run(args: Namespace) -> int:
    """Execute edit command. Returns exit code."""
    pass

def open_in_editor(content: str, editor: str) -> str | None:
    """Open temp file in editor, return modified content or None if unchanged."""
    pass
```

### 1.12 `commands/move.py` - Move Command
**Responsibility**: Transfer note-issues across repos/orgs.

```python
# Public API
def run(args: Namespace) -> int:
    """Execute move command. Returns exit code."""
    pass

def extract_issue_data(context: StoreContext, issue_number: int) -> dict:
    """Extract full issue data for recreation."""
    pass

def recreate_issue(target_context: StoreContext, data: dict) -> int:
    """Recreate issue in target repo. Returns new issue number."""
    pass
```

---

## 2. Structural Diagrams

### 2.1 Component Architecture

```mermaid
graph TD
    Main[__main__.py] --> CLI[cli.py]
    CLI --> Ctx[context.py]
    CLI --> Cmd[commands/*]
    
    Cmd --> Status[commands/status.py]
    Cmd --> Add[commands/add.py]
    Cmd --> Show[commands/show.py]
    Cmd --> List[commands/list.py]
    Cmd --> Find[commands/find.py]
    Cmd --> Edit[commands/edit.py]
    Cmd --> Move[commands/move.py]
    
    Status --> Ctx
    Status --> GH[gh_wrapper.py]
    Status --> Cfg[config.py]
    
    Add --> Ctx
    Add --> GH
    
    Show --> Ctx
    Show --> GH
    
    List --> Ctx
    List --> GH
    
    Find --> Ctx
    Find --> GH
    
    Edit --> Ctx
    Edit --> GH
    Edit --> Cfg
    
    Move --> Ctx
    Move --> GH
    
    Ctx --> Cfg
    GH --> External[gh CLI]
    Cfg --> GitCfg[git config]
    
    style External fill:#e1f5ff
    style GitCfg fill:#e1f5ff
```

### 2.2 Data Flow & Dependencies

```mermaid
graph LR
    User[User Input] --> CLI
    CLI --> Args[Parsed Args]
    Args --> Ctx[Context Resolution]
    Ctx --> GitCfg[Git Config]
    Ctx --> Env[Environment]
    Ctx --> Context[StoreContext Object]
    
    Context --> Commands
    Commands --> GH[gh_wrapper]
    GH --> GH_CLI[gh CLI Process]
    GH_CLI --> GitHub[GitHub API]
    
    GitHub --> Response
    Response --> GH
    GH --> Commands
    Commands --> Output[User Output]
    
    style User fill:#ffe1e1
    style Output fill:#e1ffe1
    style GitHub fill:#e1f5ff
```

---

## 3. Sequence Diagrams

### 3.1 `notehub add` Command Flow

```mermaid
sequenceDiagram
    participant User
    participant Main as __main__
    participant CLI as cli.py
    participant Ctx as context.py
    participant Add as commands/add.py
    participant GH as gh_wrapper.py
    participant GH_CLI as gh CLI
    
    User->>Main: notehub add
    Main->>CLI: main(argv)
    CLI->>CLI: parse_args()
    CLI->>Ctx: StoreContext.resolve(args)
    Ctx->>Ctx: check flags/config/env
    Ctx-->>CLI: context
    CLI->>Add: run(args)
    Add->>Ctx: context.full_identifier()
    Ctx-->>Add: "host:org/repo"
    Add->>GH: create_issue(context, interactive=True)
    GH->>GH_CLI: subprocess.run(["gh", "issue", "create", "--repo", ...])
    GH_CLI->>User: [Interactive prompts for title/body]
    User-->>GH_CLI: [User input]
    GH_CLI-->>GH: stdout: issue URL
    GH-->>Add: GhResult(returncode=0, stdout=...)
    Add->>User: "Created issue #123: https://..."
    Add-->>CLI: exit code 0
    CLI-->>Main: exit code 0
    Main-->>User: exit code 0
```

### 3.2 `notehub edit <note-ident>` Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI as cli.py
    participant Ctx as context.py
    participant Edit as commands/edit.py
    participant Show as commands/show.py
    participant GH as gh_wrapper.py
    participant Cfg as config.py
    participant Editor as $EDITOR Process
    participant GH_CLI as gh CLI
    
    User->>CLI: notehub edit "bug"
    CLI->>Ctx: StoreContext.resolve(args)
    Ctx-->>CLI: context
    CLI->>Edit: run(args)
    Edit->>Show: resolve_note_ident(context, "bug")
    Show->>GH: search_issues(context, "bug in:title")
    GH->>GH_CLI: gh search issues ...
    GH_CLI-->>GH: JSON results
    GH-->>Show: [{"number": 123, ...}]
    Show-->>Edit: issue_number = 123
    Edit->>GH: get_issue(context, 123)
    GH->>GH_CLI: gh api repos/.../issues/123
    GH_CLI-->>GH: JSON with body
    GH-->>Edit: {"body": "original content"}
    Edit->>Cfg: get_editor()
    Cfg-->>Edit: "vim"
    Edit->>Edit: write to temp file
    Edit->>Editor: subprocess.run(["vim", tmpfile])
    Editor->>User: [Opens editor]
    User-->>Editor: [Edits and saves]
    Editor-->>Edit: exit code 0
    Edit->>Edit: read modified temp file
    Edit->>GH: update_issue(context, 123, new_body)
    GH->>GH_CLI: gh issue edit 123 --body ...
    GH_CLI-->>GH: success
    GH-->>Edit: GhResult(returncode=0)
    Edit->>User: "Updated issue #123"
    Edit-->>CLI: exit code 0
```

### 3.3 `notehub find <regex>` Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI as cli.py
    participant Ctx as context.py
    participant Find as commands/find.py
    participant GH as gh_wrapper.py
    participant GH_CLI as gh CLI
    
    User->>CLI: notehub find "TODO.*urgent"
    CLI->>Ctx: StoreContext.resolve(args)
    Ctx-->>CLI: context
    CLI->>Find: run(args)
    Find->>GH: list_issues(context)
    GH->>GH_CLI: gh issue list --json number,title,body
    GH_CLI-->>GH: JSON array
    GH-->>Find: [{"number": 45, "body": "..."}, ...]
    loop For each issue
        Find->>Find: regex search in body
        alt Match found
            Find->>Find: extract_context(body, match_line)
            Find->>Find: highlight_match(context, pattern)
            Find->>User: [#45] Issue Title<br/>https://...<br/>[highlighted match context]
        end
    end
    Find-->>CLI: exit code 0
```

---

## 4. `gh` CLI Integration Design

### 4.1 Design Principles

1. **Delegation**: All GitHub API interactions delegated to `gh` CLI
2. **No Direct API Calls**: Never call GitHub REST/GraphQL APIs directly
3. **Subprocess Management**: Use Python `subprocess` for `gh` invocations
4. **I/O Modes**: Support both interactive (passthrough) and programmatic (JSON) modes
5. **Error Transparency**: Pass through `gh` stderr to user; check return codes
6. **Authentication**: Rely entirely on `gh auth` status

### 4.2 Interaction Modes

#### Interactive Mode (for `add`, `edit`)
```python
# Pass stdin/stdout/stderr directly to user terminal
result = subprocess.run(
    ["gh", "issue", "create", "--repo", f"{host}:{org}/{repo}"],
    stdin=sys.stdin,
    stdout=sys.stdout,
    stderr=sys.stderr
)
```

**Characteristics**:
- User sees `gh` prompts directly
- User provides input interactively
- ANSI colors and formatting preserved
- No parsing of output needed

#### Programmatic Mode (for `list`, `show`, `find`)
```python
# Capture JSON output for parsing
result = subprocess.run(
    ["gh", "issue", "list", "--repo", f"{host}:{org}/{repo}", "--json", "number,title,body"],
    capture_output=True,
    text=True
)
data = json.loads(result.stdout)
```

**Characteristics**:
- Request JSON output via `--json` flag
- Capture stdout for parsing
- Stderr still goes to user (warnings, errors)
- Structured data for processing

#### Hybrid Mode (for `edit`)
```python
# 1. Fetch data programmatically
issue_json = gh_api_get(f"repos/{org}/{repo}/issues/{num}")

# 2. User edits in $EDITOR (local process)
modified = edit_in_editor(issue_json["body"])

# 3. Update programmatically
gh_issue_edit(num, body=modified)
```

### 4.3 Argument Construction

#### Repository Specification
```python
def build_repo_arg(context: StoreContext) -> str:
    """Build --repo argument value."""
    if context.host == "github.com":
        return f"{context.org}/{context.repo}"
    else:
        return f"{context.host}:{context.org}/{context.repo}"

# Usage:
["gh", "issue", "list", "--repo", build_repo_arg(context)]
```

#### Common Patterns
```python
# Base command construction
def build_gh_command(
    operation: str,          # "issue", "api", "search"
    subcommand: str,         # "create", "list", "repos/..."
    context: StoreContext,
    extra_args: list[str] = None
) -> list[str]:
    """Build gh command with context."""
    cmd = ["gh", operation, subcommand]
    
    if operation in ["issue", "pr"]:
        cmd.extend(["--repo", build_repo_arg(context)])
    
    if extra_args:
        cmd.extend(extra_args)
    
    return cmd
```

### 4.4 Error Handling Strategy

```python
class GhError(Exception):
    """gh CLI invocation failed."""
    def __init__(self, returncode: int, stderr: str):
        self.returncode = returncode
        self.stderr = stderr

def run_gh(cmd: list[str], capture: bool = True) -> GhResult:
    """Run gh command with error handling."""
    if capture:
        result = subprocess.run(cmd, capture_output=True, text=True)
    else:
        result = subprocess.run(cmd)
    
    if result.returncode != 0:
        if capture:
            # stderr was captured, show it
            print(result.stderr, file=sys.stderr)
        raise GhError(result.returncode, result.stderr if capture else "")
    
    return GhResult(
        returncode=result.returncode,
        stdout=result.stdout if capture else "",
        stderr=result.stderr if capture else ""
    )
```

### 4.5 Authentication Check

```python
def check_gh_auth(host: str = "github.com") -> bool:
    """Verify gh is authenticated for host."""
    result = subprocess.run(
        ["gh", "auth", "status", "--hostname", host],
        capture_output=True
    )
    return result.returncode == 0

# Used in status command:
def run(args):
    context = StoreContext.resolve(args)
    if check_gh_auth(context.host):
        print(f"✓ Authenticated to {context.host}")
    else:
        print(f"✗ Not authenticated. Run: gh auth login --hostname {context.host}")
```

### 4.6 JSON vs. Interactive Decision Tree

```mermaid
graph TD
    Start[Command Invocation] --> Question{Needs User Input?}
    Question -->|Yes| Interactive[Interactive Mode]
    Question -->|No| NeedParse{Need to Parse Output?}
    
    Interactive --> PassThrough[Pass stdin/stdout/stderr]
    PassThrough --> Done
    
    NeedParse -->|Yes| JSON[Request JSON Output]
    NeedParse -->|No| PlainText[Capture Plain Text]
    
    JSON --> Parse[Parse JSON in Python]
    PlainText --> Simple[Simple String Processing]
    
    Parse --> Done[Return to Command]
    Simple --> Done
    
    style Interactive fill:#ffe1e1
    style JSON fill:#e1ffe1
    style PlainText fill:#fff5e1
```

**Examples**:
- `add`: Interactive (user input needed)
- `list`: JSON (need structured data)
- `show`: JSON (need issue details)
- `find`: JSON (need to search bodies)
- `edit`: Hybrid (JSON fetch → local edit → programmatic update)
- `status`: Plain text (just need exit code and simple output)

---

## 5. Design Decisions & Rationale

### 5.1 Why Delegate to `gh`?
- **Authentication**: `gh` handles OAuth, tokens, multiple hosts
- **API Stability**: GitHub maintains `gh` compatibility
- **Enterprise Support**: GHES support built into `gh`
- **Maintenance**: No need to track API changes

### 5.2 Why Context Resolution Layer?
- **Flexibility**: Work in repo, global, or cross-repo contexts
- **Sensible Defaults**: Minimize flags for common cases
- **Consistency**: Same resolution logic across all commands

### 5.3 Why Thin Command Modules?
- **Single Responsibility**: Each command file does one thing
- **Testability**: Easy to test individual commands
- **Maintainability**: Easy to add/modify commands

### 5.4 Future Extension Points
- **Configuration**: Extend `config.py` for per-repo settings
- **Filtering**: Add issue filtering logic in v2 (labels, milestones)
