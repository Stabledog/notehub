# scheme-linking-plan.md

## Goal
Enable stable, clickable cross-references between “task notes” managed by **notehub** by introducing a Windows custom URL scheme (e.g., `notehub://...`). The OS launches **notehub** with the full URI; notehub resolves the URI to a cached issue repo + file (and optionally line/section), refreshes cache, then opens VS Code on the resolved local artifact.

This plan is written to be dropped into the notehub dev environment so GitHub Copilot can implement it without rediscovering the design.

---

## Non-Goals
- Not asking VS Code to understand `notehub://`.
- Not adding network access requirements beyond existing notehub behavior.
- Not changing the cache/repo model (one local repo per issue, upstream enterprise GitHub).

---

## Background / Problem
- notehub maintains a **home-dir cache** of issues; each issue corresponds to a local git repo tracking enterprise GitHub.
- notehub can already refresh the cache and open VS Code locally for an issue file.
- Current pain: task notes cannot easily reference other task notes with **stable, clickable links** (paths are machine-specific; no URL scheme exists).

---

## Proposed Solution (High-Level)
1. Register a **Windows custom URI scheme**: `notehub://`.
2. The protocol handler launches a small bootstrapper (preferred: `notehub.exe` or `notehub-uri.exe`) with `"%1"` (the full URI) as an argument.
3. notehub parses the URI, resolves it to:
   - issue identity (repo key)
   - target file within cache
   - optional navigation (line, fragment, “view”)
4. notehub ensures the cache is present and up-to-date (existing refresh logic).
5. notehub launches VS Code with the resolved local path (and optionally `--goto file:line`).
6. Provide Markdown-friendly link forms so cross-links “just work” in editors, browsers, and wikis.

---

## URI Design

### Canonical forms
Pick one canonical pattern and support a couple of convenient aliases.

**Recommended canonical** (hierarchical, easy to read):
- `notehub://issue/<ISSUE_KEY>`
- `notehub://issue/<ISSUE_KEY>/file/<PATH_IN_ISSUE_REPO>`

**Optional query parameters**:
- `line=<N>` (1-based) – open file at line
- `rev=<branch|sha|tag>` – optional, if you support per-issue refs
- `view=<name>` – optional, e.g., `content|history|diff|comments` if notehub supports views

**Examples**:
- `notehub://issue/ENG-1234`  → open the default issue content file
- `notehub://issue/ENG-1234?line=20` → open default issue file at line 20
- `notehub://issue/ENG-1234/file/notes.md#acceptance` → open specific file; fragment may map to search

### Encoding rules
- Percent-decode path segments and query values.
- Treat `+` as literal plus in path segments (do not convert to space unless you intentionally adopt `application/x-www-form-urlencoded` semantics).
- Normalize ISSUE_KEY (trim, optionally uppercase) but preserve raw for display.

### Back-compat / aliases
Support:
- `notehub://open?issue=ENG-1234&file=notes.md&line=20`
- `notehub://ENG-1234` (shorthand) if desired.

---

## Windows Protocol Handler Registration

### Registry keys
Register `notehub` as a URL protocol handler so `notehub://...` invokes the program.

**Required structure**:
- `HKEY_CLASSES_ROOT\notehub`
  - `(Default)` = `URL:notehub Protocol`
  - `URL Protocol` = `` (empty string)
  - `shell\open\command` default = `"<path-to-launcher>" "%1"`

**Per-user install** (no admin):
- `HKEY_CURRENT_USER\Software\Classes\notehub` with the same subkeys.

### Preferred launcher
- If notehub is a script (PowerShell/Python), create a small **native** launcher EXE that:
  - accepts `%1`
  - calls the script with `%1`
  - ensures working directory and environment
  - logs failures

Reasons:
- avoids script execution-policy issues
- reduces quoting problems
- works consistently from browsers

### Security prompts / browser behavior
- Browsers may prompt the user the first time a custom protocol is launched.
- Non-user-initiated navigation (e.g., auto-redirect) may be blocked; rely on explicit clicks.

---

## notehub CLI / Entry Point

### Add a URI entry command
Add a subcommand to the tool:
- `notehub uri <URI>`

The protocol handler should execute:
- `notehub uri "%1"`

### Parsing
Implement robust parsing:
- Validate scheme == `notehub`
- Parse authority/host (often empty) + path
- Parse query params and fragment
- Extract `ISSUE_KEY`, optional `file`, optional `line`

### Resolution
Given extracted info:
1. Map `ISSUE_KEY` → cache directory (existing mapping)
2. Ensure cache exists; if not, clone/init.
3. Refresh cache (pull/rebase/fetch) using existing logic.
4. Determine target file:
   - If `file` present: resolve relative to issue repo root (prevent `..` traversal)
   - Else: open default “issue content file” (existing behavior)

### Launch VS Code
- Use VS Code CLI (`code`) if available.
- Fallback to `Code.exe` path if needed.

Preferred invocation:
- Open folder/repo: `code <repoRoot>` (optional)
- Open file: `code -g <file>:<line>` when `line` provided
- Else: `code <file>`

Consider:
- `--reuse-window` / `-r` if user prefers reuse behavior

### Return codes
- 0 success
- non-zero with meaningful error messages for:
  - invalid URI
  - issue not found
  - sync failure
  - file missing

---

## Linking from Notes

### Markdown patterns
In any Markdown note:
- `[ENG-1234](notehub://issue/ENG-1234)`
- `[notes](notehub://issue/ENG-1234/file/notes.md?line=10)`

### Autolinks
Also allow plain-text:
- `notehub://issue/ENG-1234`

### Optional: link generation helper
Add a command:
- `notehub link ENG-1234 [--file notes.md] [--line 10]`
Outputs the canonical URL for copy/paste.

---

## Logging, Diagnostics, and Observability

- Add `notehub uri` logging to a file in `%LOCALAPPDATA%\notehub\logs\uri-handler.log`.
- Log:
  - raw URI
  - parsed components
  - resolved paths
  - VS Code command line
  - errors and stack traces

- Add a `--dry-run` to print what would happen.

---

## Security Considerations
- Treat the inbound URI as **untrusted input**.
- Prevent path traversal: reject any resolved file path outside the issue repo root.
- Sanitize/validate ISSUE_KEY.
- Never execute arbitrary commands from URI content.
- If URI includes an enterprise GitHub URL, treat it only as an identifier unless your existing code already safely uses it.

---

## Implementation Steps (Suggested Order)
1. **Define URI spec** (canonical + aliases) and unit tests.
2. Implement `notehub uri <URI>` end-to-end using existing cache+open logic.
3. Build/ship launcher:
   - Windows EXE (or a robust `.cmd` wrapper if you must)
   - Handles quoting and passes `%1` correctly
4. Add installer step to register scheme:
   - per-user registry keys
   - uninstall removes keys
5. Add `notehub link` helper and doc snippets.
6. Add logging + troubleshooting doc.
7. QA matrix:
   - Edge/Chrome link click
   - VS Code markdown preview click
   - Windows Run dialog
   - paths with spaces
   - issue keys with punctuation

---

## Test Cases
- `notehub://issue/ENG-1` opens default issue file.
- `notehub://issue/ENG-1?line=5` opens at line 5.
- `notehub://issue/ENG-1/file/notes.md` opens that file.
- Invalid scheme: `foo://issue/ENG-1` rejected.
- Traversal attempt: `notehub://issue/ENG-1/file/../../secret.txt` rejected.
- Missing issue → helpful error.

---

## Troubleshooting Checklist
- Confirm protocol registration exists (HKCU\Software\Classes\notehub or HKCR\notehub).
- Confirm command includes `"%1"`.
- Verify launcher path and quoting.
- Check `uri-handler.log`.
- Ensure VS Code CLI is on PATH or configure fallback.

---

## Notes / Decisions to Make
- Canonical URI format (path-style vs query-style).
- Whether to allow shorthand `notehub://ENG-1234`.
- Reuse-window policy when opening VS Code.
- Whether fragments (`#foo`) map to search-in-file or heading navigation.
