# notehub — CLI-first GitHub/GHES note & issue manager (Draft 0.3)

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
    - implies that there may be only a subset of issues which are "note-issues" (filter criteria TBD version 2, v1 will not filter at all)
- "store-context": host+org+repo -- resolved on startup as described in config
- "note-ident": one of (issue number | top match for title regex)
- "note-header": formatted one-line info about a note -- [issue#] [title]

## Context resolution
- Store context resolved as follows:
    - Host:
        - --host|-h is top choice
        - GH_HOST environment variable
        - auto-detect from local working copy unless -g|--global
        - git config (global) custom key 'notehub.host'
        - 'github.com'
        
    - Org:
        - --org|-o [name] is top choice
        - auto-detect from local working copy unless -g|--global
        - Env 'NotehubOrg' 
        - git config (global) 'notehub.org' 
        - notehub.$USER ($USER being the user's shell environment value)
    
    - Repo: 
        - --repo|-r [name] is top choice
            - If name is '.', it will be parsed from the local git remote spec
        - git config custom key 'notehub.repo' ( skip if -g|--global)
        - Env 'NotehubRepo' 
        - git config (global) key 'notehub.repo' 
        - 'notehub.default' (literal repo name) 


---

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
    - Generate note-issue by invoking `gh issue create`

### 3) List, search, filter
- `notehub show <note-ident> ...`
    - Iterates <note-ident> list, and shows note-header then issue URL (latter is indented) for each
- `notehub list`
    - Same as calling `notehub show` on all note-issues
- `notehub find "[full-regex]"`
    - Search note-issues full body
        For each match:
            - invoke 'show' 
            - print match in context, highlighted (max 3 line context: before,matching,after)
            - Highlight matching text

### 4) Edit/update
- `notehub edit <note-ident>`
    - open in `$EDITOR` for full-body edit.  
    - send update to host when edit quit (i.e. child process exit)

### 5) Cross-repo or cross-org moves
- `notehub move <note-ident> <TARGET-REPO>`  
    - Use the “extract and rebuild” flow via `gh api` 

### Misc
- Failure to invoke of `gh` fails with `gh not found` 
- `gh` stderr ouput is passed through to parent stderr


# File tree layout

## /
- `pyproject.toml` - Modern Python package metadata (PEP 517/518)
- `requirements.txt` - Python dependencies

## /src/notehub
Main application source code.
- `__main__.py` - Entry point for `python -m notehub`
- `cli.py` - Command-line argument parsing and dispatch
- `context.py` - Store-context resolution (host/org/repo detection)
- `config.py` - Configuration management (git config integration)
- `gh_wrapper.py` - Wrapper functions for `gh` CLI invocations

## /src/notehub/commands
Command implementations (one file per command).
- `status.py` - Context and auth status display
- `add.py` - Create new note-issues
- `show.py` - Display note-header and URLs
- `list.py` - List all note-issues
- `find.py` - Search note-issue bodies with regex
- `edit.py` - Edit note-issues in $EDITOR
- `move.py` - Cross-repo/org note transfers

Test suite.
- `/tests/unit` - Unit tests for individual modules
- `/tests/integration` - Integration tests with `gh` CLI

## /scripts
- `install.sh` - Installation script

## /spec
- `notehub_spec_toplevel.md` - This specification document
- `filetree.txt` - Directory structure reference

