# Notehub CLI Help

Notehub is a command-line tool for managing notes as GitHub issues.

## Table of Contents

- [General](#general)
  - [Installation](#installation)
  - [Authentication](#authentication)
  - [Store Context Resolution](#store-context-resolution)
  - [Note Identifiers (note-ident)](#note-identifiers-note-ident)
  - [Editor Configuration](#editor-configuration)
  - [Troubleshooting](#troubleshooting)
- [Commands](#commands)
  - [notehub status](#command-status)
  - [notehub add](#command-add)
  - [notehub show](#command-show)
  - [notehub list](#command-list)
  - [notehub edit](#command-edit)
  - [notehub sync](#command-sync)

---

## General

### Installation

**Prerequisites:**
- Python 3.8+
- Git
- GitHub CLI (`gh`) - [Installation](https://cli.github.com/)

**Install Notehub:**
```bash
pip install lm-notehub
```

**Verify installation:**
```bash
notehub status
```

### Authentication

Notehub uses the GitHub CLI (`gh`) for all GitHub API operations. You must authenticate with `gh` before using notehub.

**For public GitHub:**
```bash
gh auth login
```

**For GitHub Enterprise:**
```bash
gh auth login --hostname <your-enterprise-github-hostname>
```

**Token Environment Variables:**
Notehub checks these environment variables in a host-aware order:

**For github.com:**
1. `GITHUB_TOKEN` (recommended for public GitHub)
2. `GH_TOKEN`
3. `GH_ENTERPRISE_TOKEN_2` (fallback)
4. `GH_ENTERPRISE_TOKEN` (fallback)

**For GitHub Enterprise hosts:**
1. `GH_ENTERPRISE_TOKEN_2` (recommended for enterprise)
2. `GH_ENTERPRISE_TOKEN`
3. `GH_TOKEN` (fallback)

**Verify authentication:**
```bash
notehub status
```

### Store Context Resolution

Every notehub command requires a "store context" consisting of:
- **Host**: GitHub hostname (default: `github.com`)
- **Org**: Organization or user account name
- **Repo**: Repository name

**Resolution hierarchy (in order):**

1. **CLI flags**: `--host`, `--org`, `--repo`
   - Special: `--repo .` or `-r .` auto-detects repo from current git remote
2. **Environment variables**: `GH_HOST`, `NotehubOrg`, `NotehubRepo`
3. **Local git config** (repository-specific `.git/config`, skipped with `--global` flag):
   ```bash
   git config notehub.host github.example.com
   git config notehub.org myteam
   git config notehub.repo project-notes
   ```
4. **Auto-detect from git remote** (uses current branch's tracking remote, or 'origin')
5. **Global git config** (user-wide `~/.gitconfig`):
   ```bash
   git config --global notehub.host github.com
   git config --global notehub.org <your-username>
   git config --global notehub.repo notehub.default
   ```
6. **Defaults**: Host defaults to `github.com`, Org defaults to `$USER`, Repo defaults to `notehub.default`

**Using current git repository:**
```bash
# Auto-detect repo from current git remote
cd /path/to/my-project
notehub list -r .
notehub add -r .
```

**Setting up defaults (recommended):**
```bash
git config --global notehub.host github.com
git config --global notehub.org <your-username>
git config --global notehub.repo notehub.default
```

**Override for specific repo:**
```bash
cd /path/to/my-project
git config notehub.repo my-project-notes

# Or use auto-detection without configuring
notehub list -r .
```

**Global-only mode:**
Use `--global` flag to ignore local git config and use only global config:
```bash
notehub list --global
```

### Note Identifiers (note-ident)

Many commands accept a `NOTE-IDENT` argument to identify issues. A note-ident can be:

1. **Issue number**: `123`
2. **Title regex**: `"bug.*login"` (matches issue titles, case-insensitive)

**Examples:**
```bash
# By issue number
notehub show 42

# By title regex (quotes recommended)
notehub show "implement.*cache"
notehub edit "bug.*authentication"
```

**Multiple matches:**
If a regex matches multiple issues, notehub will warn and use the first match.

### Editor Configuration

Notehub respects the `EDITOR` environment variable for interactive editing commands (`notehub add`, `notehub edit`).

**Default behavior:**
- Uses `$EDITOR` if set
- Falls back to system defaults

**Setting your editor:**

**Linux/macOS:**
```bash
export EDITOR=vim
# or
export EDITOR="code --wait"
```

**Windows (PowerShell):**
```powershell
[System.Environment]::SetEnvironmentVariable('EDITOR','code --wait','User')
```

**Windows (Command Prompt):**
```cmd
setx EDITOR "code --wait"
```

**For VS Code:**
The `--wait` flag is important - it tells VS Code to block until the file is closed.

### Troubleshooting

#### "gh: command not found"
Install the GitHub CLI: https://cli.github.com/

#### "Error: Not authenticated"
Run `gh auth login` and follow the prompts. Verify with `gh auth status`.

#### "Error: Could not determine store context"
Set your defaults:
```bash
git config --global notehub.org <your-username>
git config --global notehub.repo notehub.default
```

#### "Error: Repository not found"
1. Verify the repository exists: `gh repo view <org>/<repo>`
2. Check you have access to it
3. Create it if needed:
   ```bash
   gh repo create <org>/<repo> --private
   ```

#### Context resolution not working as expected
Check what context is being used:
```bash
notehub status
```
This shows the resolved host/org/repo and your authentication status.

#### Editor not launching (Windows)
Make sure `EDITOR` includes `--wait` flag for GUI editors:
```powershell
[System.Environment]::SetEnvironmentVariable('EDITOR','code --wait','User')
```
Then restart your terminal.

#### Authentication tokens on Windows
If using environment variables for authentication, set them at User level:
```powershell
[System.Environment]::SetEnvironmentVariable('GITHUB_TOKEN','<your-token>','User')
```

---

## Commands

### Command: status

**Usage:**
```bash
notehub status [--host HOST] [--org ORG] [--repo REPO] [--global]
```

**Description:**
Display the resolved store context (host/org/repo) and authentication status.

**Options:**
- `--host`, `-H`: Override GitHub host
- `--org`, `-o`: Override organization/owner
- `--repo`, `-r`: Override repository
- `--global`, `-g`: Use global config only (ignore local git config)

**Examples:**
```bash
# Show current context and auth status
notehub status

# Check status for a different repo
notehub status --repo my-other-notes

# Check global config only
notehub status --global
```

**Output example:**
```
Store context:
  Host: github.com
  Org: myusername
  Repo: notehub.default

Authentication: ✓ Authenticated as myusername
```

---

### Command: add

**Usage:**
```bash
notehub add [--host HOST] [--org ORG] [--repo REPO] [--global]
```

**Description:**
Create a new note-issue. Opens your `$EDITOR` to compose the note. The first line becomes the issue title, subsequent lines become the body.

**Options:**
- `--host`, `-H`: Override GitHub host
- `--org`, `-o`: Override organization/owner
- `--repo`, `-r`: Override repository
- `--global`, `-g`: Use global config only

**Examples:**
```bash
# Create a new note
notehub add

# Create a note in a specific repo
notehub add --repo project-notes
```

**Workflow:**
1. Command opens your editor with a template
2. First line = issue title
3. Remaining lines = issue body (Markdown supported)
4. Save and close editor
5. Issue is created on GitHub with 'notehub' label
6. Displays created issue number and URL

**Tips:**
- Use Markdown formatting in the body
- Leave the first line blank if you want to cancel
- All issues get a 'notehub' label for filtering

---

### Command: show

**Usage:**
```bash
notehub show NOTE-IDENT [NOTE-IDENT ...] [--host HOST] [--org ORG] [--repo REPO] [--global]
```

**Description:**
Display note-header and URL for one or more specified issues.

**Arguments:**
- `NOTE-IDENT`: Issue number or title regex (one or more required)

**Options:**
- `--host`, `-H`: Override GitHub host
- `--org`, `-o`: Override organization/owner
- `--repo`, `-r`: Override repository
- `--global`, `-g`: Use global config only

**Examples:**
```bash
# Show by issue number
notehub show 42

# Show multiple issues
notehub show 42 43 44

# Show by title regex
notehub show "meeting.*notes"

# Mix numbers and regex
notehub show 42 "bug.*login" 99
```

**Output format:**
```
[#42] Weekly standup notes
  https://github.com/myorg/notehub.default/issues/42

[#43] Bug: Login fails on Firefox
  https://github.com/myorg/notehub.default/issues/43
```

---

### Command: list

**Usage:**
```bash
notehub list [--host HOST] [--org ORG] [--repo REPO] [--global]
```

**Description:**
List all note-issues in the repository (shows issues with 'notehub' label).

**Options:**
- `--host`, `-H`: Override GitHub host
- `--org`, `-o`: Override organization/owner
- `--repo`, `-r`: Override repository
- `--global`, `-g`: Use global config only

**Examples:**
```bash
# List all notes
notehub list

# List notes from a specific repo
notehub list --repo project-notes

# List from global config
notehub list --global
```

**Output format:**
```
[#1] Initial setup notes
  https://github.com/myorg/notehub.default/issues/1

[#2] Todo: Implement caching
  https://github.com/myorg/notehub.default/issues/2

[#5] Meeting notes 2025-12-30
  https://github.com/myorg/notehub.default/issues/5
```

---

### Command: edit

**Usage:**
```bash
notehub edit NOTE-IDENT [--host HOST] [--org ORG] [--repo REPO] [--global]
```

**Description:**
Edit an existing note-issue body in your `$EDITOR`. The editor will block until you close it, then changes are automatically synced to GitHub.

**Arguments:**
- `NOTE-IDENT`: Issue number or title regex

**Options:**
- `--host`, `-H`: Override GitHub host
- `--org`, `-o`: Override organization/owner
- `--repo`, `-r`: Override repository
- `--global`, `-g`: Use global config only

**Examples:**
```bash
# Edit by issue number
notehub edit 42

# Edit by title regex
notehub edit "meeting.*notes"

# Edit in a specific repo
notehub edit 42 --repo project-notes
```

**Workflow:**
1. Fetches current issue body from GitHub to local cache
2. Opens body in your `$EDITOR` (blocks until closed)
3. Edit and save, then close the editor
4. Automatically syncs changes to GitHub
5. Displays success message

**Note:**
- Only the body is editable (not the title)
- To change the title, use the GitHub web interface
- Changes are automatically synced when you close the editor
- If you need manual control, you can still use `notehub sync` after editing

---

### Command: sync

**Usage:**
```bash
notehub sync NOTE-IDENT [--host HOST] [--org ORG] [--repo REPO] [--global]
```

**Description:**
Commit and push cache changes to GitHub for a specific note-issue.

**Arguments:**
- `NOTE-IDENT`: Issue number or title regex

**Options:**
- `--host`, `-H`: Override GitHub host
- `--org`, `-o`: Override organization/owner
- `--repo`, `-r`: Override repository
- `--global`, `-g`: Use global config only

**Examples:**
```bash
# Sync by issue number
notehub sync 42

# Sync by title regex
notehub sync "cache.*implementation"
```

**Note:**
This command is for synchronizing local cache state with GitHub. In typical usage, notehub commands automatically sync, so explicit sync is rarely needed.

---

## Additional Resources

- **Repository**: https://github.com/Stabledog/notehub
- **Issues & Bug Reports**: https://github.com/Stabledog/notehub/issues
- **GitHub CLI Docs**: https://cli.github.com/manual/

## Tips & Best Practices

1. **Set global defaults** to avoid repeating `--org` and `--repo` on every command
2. **Use descriptive titles** - they're searchable via regex
3. **Label convention** - notehub automatically adds 'notehub' label to all issues for filtering
4. **Separate repos** - consider separate repos for different projects/contexts
5. **Check status first** - run `notehub status` when troubleshooting context issues
6. **Editor setup** - configure `$EDITOR` once, works for add and edit commands
