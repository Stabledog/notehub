# notehub — CLI-first GitHub/GHES note & issue manager (Draft 0.1)

> A thin, opinionated wrapper over `gh` for fast note-taking and issue workflow across GitHub **and** GitHub Enterprise.  
> Shell + Python 3.11+. Respects `$EDITOR` (including `code`). Context-aware (repo vs global).

---

## Goals
- Treat GitHub issues as personal and team **notes/tasks** with minimal friction.
- Work **anywhere**: single repo context or global multi-org view.
- Delegate authentication to `gh`

## Non-goals
- GUI. (TUI later is optional.)
- Replacing `gh` – notehub is a higher-level workflow layer.

## Dependencies
- **Hard**: `gh` (GitHub CLI) configured for all relevant hosts.
- **Runtime**: bash/zsh, Python 3.11+, `jq` (for JSON shaping), standard Unix tools (`sed`, `awk`, `xargs`).
- **Optional**: `fzf` for interactive pickers; 

## Context model
- **Repo context (default):** running inside a Git working copy.
  - Detect via `git rev-parse --show-toplevel`.
  - Discover interesting remotes via `git remote -v` → host(s) → owner/repo.
  - Operations default to *the primary detected repo*.
- **Global context:** when outside a repo **or** `-g/--global` is set.
  - Commands may require `--host`, `--org`, or `--repo` selectors.

### Host discovery
- Enumerate authenticated hosts via `gh auth status --show-token=false`.
- Each command may accept `--host <hostname>` to pin to `github.com` or a GHES like `ghe.example.com`.

---

## Configuration
Search order: env vars -> `./.notehub.yml`

```yaml
# Example ~/.notehub.yml
default_host: ghe.example.com
views:
  - name: "Today"
    query: "is:issue is:open assignee:@me sort:updated-desc"
  - name: "My Notes"
    query: "is:issue is:open author:@me label:notes sort:updated-desc"
label_aliases:
  todo: ["todo","to-do","next"]
assignee_map:
  lmatheson4: lmatheson4   # identity mapping across orgs/hosts
```

Env vars:
- `NOTEHUB_HOST` (overrides default_host)
- `NOTEHUB_EDITOR` (overrides default_editor)
- `NOTEHUB_FZF` (`1` enables interactive pickers)

---

## High-level commands (proposed)

```
notehub <command> [flags] [args]
```

### 1) Bootstrap & context
- `notehub status`  
  Show detected context (repo path, host, owner/repo, user identity), and `gh` auth state.
- `notehub whoami [--host HOST]`  
  Print current identity per host via `gh api user`.

### 2) Quick capture & edit
- `notehub new [TITLE] [--label L...] [--assignee U...] [--milestone M] [--body FILE|'-'] [--repo OWNER/REPO] [--host HOST]`  
  Create an issue in the current repo (repo context) or in a chosen repo (global).  
  Opens `$EDITOR` for body if `--body` is not provided.

### 3) List, search, filter
- `notehub list [QUERY|VIEW] [--host HOST] [--json|--table]`  
  Run a saved view (`Today`, `My Notes`, etc.) or an ad‑hoc GitHub search query.

### 4) Edit/update
- `notehub edit <ISSUE>` — open in `$EDITOR` for full-body edit.  
- `notehub label <ISSUE> +L1 -L2` — add/remove labels.  
- `notehub close <ISSUE>` — close issue.  
- `notehub reopen <ISSUE>` — reopen.  
- `notehub comment <ISSUE> [--body FILE|'-']` — add comment.

### 5) Cross-repo or cross-org moves
- `notehub move <ISSUE> <TARGET-REPO>`  
  Use the “extract and rebuild” flow via `gh api` (reusing your `gh` auth).

### 6) Views and dashboards
- `notehub view [NAME] [--json|--table]`  
  Lists issues using configured saved searches.

### 7) Sync/backup
- `notehub export [--host HOST] [--org ORG] [--out FILE]`  
  Dump issues/notes as structured JSON or Markdown for offline use.

### 8) Utilities
- `notehub browse <ISSUE>` — open in browser.
- `notehub open` — open current repo’s issues page.
- `notehub config edit` — open config in `$EDITOR`.

---

## Example flows

### Capture a quick note while coding
```bash
notehub new "Investigate flaky tests" -l todo
```

### Review all notes across both hosts
```bash
notehub list -g "label:notes is:open author:@me"
```

### Move an issue between orgs
```bash
notehub move myorg/app#42 otherorg/app
```

### Global dashboard
```bash
notehub view Today
```

---

## Future ideas
- Optional TUI (`notehub dash`) using `fzf`/`textual`.
- Bi-directional link between local markdown files and issues.
- Pluggable “storage providers” (e.g., GitLab, Gitea) behind a unified interface.
