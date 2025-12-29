lmatheson4_bbeng: Ingest #file:notehub_spec_toplevel.md and #file:design.md -- the design was generated from the toplevel spec.  Now i would like you to review the spec in light of the design -- where are there inconsistencies, such that the design fails to fully or correctly implement the spec.  Then consider where the spec should be improved, bearing in mind that we want it to stay relatively thin and defer to the design on details that don't affect user workflows.

GitHub Copilot: # Spec vs Design Review

## 1. Inconsistencies & Implementation Gaps

### 1.1 `notehub show` Argument Handling

**Spec says:**
```
notehub show <note-ident> ...
```
- Iterates `<note-ident>` list

**Design implements:**
- Only shows single resolution in sequence diagram
- API signature unclear if it handles multiple idents

**Fix needed:** Design should clarify that `run(args)` loops over `args.idents` list.

---

### 1.2 `notehub list` vs `notehub show` Relationship

**Spec says:**
```
notehub list
    - Same as calling `notehub show` on all note-issues
```

**Design shows:**
- `list.py` as separate command calling `gh_wrapper.list_issues()`
- No mention of reusing `show.py` logic

**Recommendation:** Spec language is imprecise. Should say:
```
notehub list
    - Display note-header and URL for all note-issues
    - Similar output format to `show`
```

---

### 1.3 `notehub find` Match Display

**Spec says:**
```
For each match:
    - invoke 'show'
    - print match in context, highlighted (max 3 line context: before,matching,after)
```

**Design shows:**
- `find.py` directly formats output
- No call to `show.py` or `format_note_header()`

**Inconsistency:** Spec says "invoke show" but design doesn't reuse `show` module.

**Fix needed:** Spec should say:
```
For each match:
    - Display note-header (using same format as `show`)
    - Print match in context with highlighting
```

---

### 1.4 `notehub move` Error Handling

**Spec says:**
```
notehub move <note-ident> <TARGET-REPO>
    - Use the "extract and rebuild" flow via `gh api`
```

**Design provides:**
- `extract_issue_data()` and `recreate_issue()` functions
- No mention of what happens to original issue (close? leave open? add comment?)

**Gap:** Spec doesn't define:
- Should original issue be closed?
- Should we add a comment linking to new location?
- What if recreation fails?

**Fix needed:** Add to spec:
```
- After successful recreation, close original issue with comment: "Moved to [new-location]"
- If recreation fails, leave original issue untouched
- Print both old and new URLs on success
```

---

### 1.5 Context Resolution: Missing Git Detection

**Spec says:**
```
Repo:
    - git config custom key 'notehub.repo' (skip if -g|--global)
    - ...
Org:
    - auto-detect from local working copy unless -g|--global
    - ...
Host:
    - auto-detect from local working copy unless -g|--global
    - ...
```

**Design shows:**
- `StoreContext.resolve()` but no detail on git remote detection

**Gap:** Spec says "auto-detect from local working copy" but doesn't explain HOW.

**Fix needed:** Add subsection to spec:
```
### Auto-detection from Git Remote
When in a git repository and not using `-g|--global`:
- Parse `git remote get-url origin`
- Extract host/org/repo from URL patterns:
  - https://[host]/[org]/[repo].git
  - git@[host]:[org]/[repo].git
- If parsing fails, fall back to next resolution method
```

---

### 1.6 `notehub status` Output Format

**Spec says:**
```
notehub status
  - Show detected context (repo path, host, owner/repo, user identity), and `gh` auth state.
  - Show login identity on host
```

**Design shows:**
- Example of auth check output
- No specification of full output format

**Gap:** User-facing command needs output format defined.

**Fix needed:** Add example to spec:
```
Example output:
  Context:
    Host:       github.com
    Org/Repo:   myorg/myrepo
    Repo Path:  /home/user/projects/myrepo (or "global mode")

  Authentication:
    ✓ Authenticated to github.com as username

  Or:
    ✗ Not authenticated. Run: gh auth login
```

---

### 1.7 `notehub add` Output

**Spec says:**
- (No specification of what happens after `gh issue create`)

**Design shows:**
```python
Add->>User: "Created issue #123: https://..."
```

**Gap:** Spec doesn't define success message format.

**Fix needed:** Add to spec:
```
notehub add
    - Generate note-issue by invoking `gh issue create`
    - On success, print: "Created issue #[number]: [URL]"
```

---

### 1.8 Note-Ident Resolution Ambiguity

**Spec says:**
```
"note-ident": one of (issue number | top match for title regex)
```

**Design shows:**
- `resolve_note_ident()` searches with `"ident in:title"`

**Ambiguity:** What if:
- String is numeric but not valid issue number?
- Multiple title matches found?

**Fix needed:** Add to spec glossary:
```
"note-ident": Resolves in order:
  1. If numeric and valid issue exists: use as issue number
  2. Otherwise: search issue titles for substring match
     - If single match: use that issue
     - If multiple matches: error, list matches, ask user to be more specific
     - If no matches: error "No issue found matching '[ident]'"
```

---

## 2. Spec Improvements (Preserving Thinness)

### 2.1 Add "Non-Goals" Section

**Why:** Clarifies scope boundaries.

**Add after Goals:**
```markdown
## Non-Goals
- Issue labels, milestones, assignees (deferred to v2)
- Comments, reactions, PR integration
- Offline mode, local caching
- Custom issue templates
- Bulk operations beyond single `show` iteration
```

---

### 2.2 Clarify "Note-Issue" Filtering

**Current spec:**
```
"note-issue":
    - implies that there may be only a subset of issues which are "note-issues"
      (filter criteria TBD version 2, v1 will not filter at all)
```

**Improvement:**
```
"note-issue":
    - In v1: ALL issues in the target repo are treated as note-issues
    - Future versions may filter by label (e.g., "note") or other criteria
    - Current behavior: no distinction between regular issues and notes
```

---

### 2.3 Add Exit Code Convention

**Add new section:**
```markdown
## Exit Codes
- `0`: Success
- `1`: General error (invalid args, gh command failed)
- `2`: Authentication failure
- `3`: Not in git repo (when repo context required and not using --global)
```

---

### 2.4 Clarify Editor Behavior in `edit` Command

**Current:**
```
notehub edit <note-ident>
    - open in `$EDITOR` for full-body edit.
    - send update to host when edit quit (i.e. child process exit)
```

**Improvement:**
```
notehub edit <note-ident>
    - Fetch issue body, write to temp file
    - Open temp file in $EDITOR (blocks until editor exits)
    - If file modified: update issue body via `gh`
    - If file unchanged: no update, print "No changes"
    - Delete temp file on exit
```

---

### 2.5 Add Error Handling Philosophy

**Add new section before "Command structure":**
```markdown
## Error Handling
- `gh` CLI errors: Pass stderr through to user, exit with gh's exit code
- Invalid note-ident: Print error message, list similar issues if applicable
- Missing dependencies: Check for `gh` on startup, fail fast with helpful message
- Network failures: Rely on `gh` error messages (don't wrap/hide them)
```

---

### 2.6 Clarify Configuration Persistence

**Current:**
```
User configures host,repo,org manually using `git config` command
```

**Improvement:**
```
## Configuration Management
- All settings stored in git config (no separate config file)
- Use `git config [--global] notehub.<key> <value>` to set
- Use `git config --get notehub.<key>` to view
- Available keys: `host`, `org`, `repo`
- Future: May add `notehub config` command as convenience wrapper
```

---

## 3. Summary Recommendations

### Critical Fixes (Spec Must Address)
1. ✅ Define note-ident resolution behavior for edge cases
2. ✅ Specify `notehub move` post-transfer behavior
3. ✅ Document git remote auto-detection algorithm
4. ✅ Add output format example for `notehub status`

### Nice-to-Have (Improves Clarity)
1. ✅ Add "Non-Goals" section
2. ✅ Document exit code conventions
3. ✅ Add error handling philosophy section
4. ✅ Clarify editor temp file handling in `edit`

### Design Clarifications Needed
1. `show` command should document handling multiple idents
2. `find` should call `show.format_note_header()` for consistency
3. `list` language should match actual implementation (doesn't delegate to `show`)

---

## 4. Proposed Spec Patch

Here's a minimal diff-style update to fix critical issues:

````markdown
## Glossary

- "note-ident": Identifier for a note-issue, resolved as follows:
    1. If numeric string and issue exists: use as issue number directly
    2. Otherwise: search issue titles containing the string
       - Single match → use that issue
       - Multiple matches → error, print list of matches
       - No matches → error with helpful message

## Context resolution (APPEND)

### Git Remote Auto-Detection
When in a git repository (unless `-g|--global`):
- Run `git remote get-url origin`
- Parse URL for host/org/repo:
  - HTTPS: `https://[host]/[org]/[repo](.git)?`
  - SSH: `git@[host]:[org]/[repo](.git)?`
- On parse failure: skip to next resolution method

## Command structure (UPDATE)

### 5) Cross-repo or cross-org moves
- `notehub move <note-ident> <TARGET-REPO>`
    - Extract issue data via `gh api`
    - Recreate in target repo
    - On success: close original with comment "Moved to [new-URL]"
    - Print both old and new URLs

## Error Handling (NEW SECTION)
- Exit codes: 0=success, 1=error, 2=auth failure, 3=not in git repo
- `gh` failures: Pass stderr to user unchanged
- Invalid note-ident: Print error + similar matches if available
````

This keeps the spec thin while eliminating ambiguities that would cause implementation confusion.
