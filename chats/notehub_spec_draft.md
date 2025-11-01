# notehub — CLI-first GitHub/GHES note & issue manager (Draft 0.2)

A thin, opinionated wrapper over `gh` for fast note-taking using Github issues for backing store.  Shell + Python 3.11+. Context-aware (repo vs global).  

---

## Goals
- Treat GitHub issues as personal and team **notes/tasks** with minimal friction.
- Delegate Github operations + authentication to `gh`
- Auto-detect host/org/repo

## Dependencies
- **Hard**: `gh` (GitHub CLI) configured for all relevant hosts.
- **Runtime**: bash/zsh, Python 3.11+, standard Unix tools (`sed`, `awk`, `xargs`).
- **Optional**: `fzf` for interactive pickers; 

## Glossary

- "note-issue":  
    - we're using github issues as notes, but this term removes ambiguity: "an issue which is being treated as a note"
    - implies that there may be only a subset of issues which are "note-issues" (filter criteria TBD)
- "store-context": host+org+repo -- resolved on startup as described in config
- "note-ident": one of (issue number | top match for title regex)
- "note-header": formatted one-line info about a note -- [issue#] [title]

## Context resolution
- Store context resolved as follows:
    - Repo: 
        - --repo|-r [name] is top choice
        - git config (local working copy) 'notehub.repo' , skip if -g|--global
        - Env 'NotehubRepo' 
        - git config (global) 'notehub.repo' 
        - 'notehub.default' (literal repo name) is 4th
    - Org:
        - --org|-o is top choice
        - auto-detect from local working copy unless -g|--global
        - Env 'NotehubOrg' 
        - git config (global) 'notehub.org' 
        - 'github.com' 
    - Host:
        - --host|-h is top choice
        - auto-detect from local working copy unless -g|--global
        - git config (global) 'notehub.host'
        - 'github.com'

---

## Configuration

- User configures host,repo,org manually using `git config` command,
    e.g:
    `git config notehub.host my.enterprise.github.com`
    `git config --global notehub.org notehub.weasel`
- Editor:  respects $EDITOR environ, defaults to vi


## Command structure

```
notehub <command> [<subcommand>] [flags] [args]
```

### 1) Setup, context, status
- `notehub status`  
  - Show detected context (repo path, host, owner/repo, user identity), and `gh` auth state.
  - Show login identity on host

### 2) Quick capture & edit
- `notehub add`
    - Generate note-issue from template, load in editor

### 3) List, search, filter
- `notehub list`
    - Show titles of note-issues
- `notehub find "[full-regex]"`
    - Search note-issues full body, list each match

### 4) Edit/update
- `notehub edit <note-ident>`
    — open in `$EDITOR` for full-body edit.  
- `notehub show <ISSUE|title-regex>`
    - Show note-titles of note-issues
    - Print URL of issue on 2nd line, indented

### 5) Cross-repo or cross-org moves
- `notehub move <issue-ident> <TARGET-REPO>`  
    - Use the “extract and rebuild” flow via `gh api` 

