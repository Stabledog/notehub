lmatheson4_bbeng: Review this spec for internal inconsistencies and conceptual clarity.

GitHub Copilot: # Review of notehub_spec_draft.md

## Internal Inconsistencies

### 1. **Context Resolution Conflicts**
- The resolution order lists `'notehub.default' (literal repo name)` as 4th choice for Repo, but this contradicts the earlier statement about `'notehub.default'` being a *literal repo name*. The naming is confusing—should this be `notehub.repo` instead?
- **Org resolution**: Falls back to `'github.com'` but that's a host, not an org. This seems incorrect.

### 2. **Glossary vs. Commands Mismatch**
- **Glossary** defines `note-ident` as "(issue number | top match for title regex)"
- **Commands** use inconsistent parameter names:
  - `edit <note-ident>` (correct)
  - `show <ISSUE|title-regex>` (different terminology)
  - `move <issue-ident>` (yet another variant)

**Recommendation**: Standardize on `<note-ident>` everywhere.

### 3. **Missing "note-issue" Filter Criteria**
- Glossary states: "implies that there may be only a subset of issues which are 'note-issues' (filter criteria TBD)"
- No specification of what distinguishes a note-issue from a regular issue (labels? naming convention? all issues?)

### 4. **Command Return Values Unclear**
- `list` says "Show titles" but doesn't specify format (is this same as "note-header"?)
- `show` says "Show note-titles" (plural?) but takes a single `<note-ident>`—should this be singular?

## Conceptual Clarity Issues

### 1. **Auto-detection Logic Incomplete**
```
- auto-detect from local working copy unless -g|--global
```
What does "auto-detect" mean here? Via `git remote`? This needs explicit specification.

### 2. **"note-header" Definition vs. Usage**
- Defined as `[issue#] [title]` but never referenced in commands section
- Should `list` output use this format? Make it explicit.

### 3. **Editor Flow for `add` Unclear**
- "Generate note-issue from template, load in editor"
- Is the issue created *before* or *after* the user saves/exits the editor?
- What happens if they exit without saving?

### 4. **Missing Commands**
- No `delete` or `close` command (common for note management)
- No `tag`/`label` command (would help define note-issues vs regular issues)

### 5. **`find` vs `list` Distinction**
- `list` → "Show titles of note-issues"
- `find` → "Search note-issues full body, list each match"
- Should `find` show full note-headers or just titles? What's "each match"—per line, per issue?

## Recommended Fixes

````markdown
1. **Standardize terminology**:
   - Use `<note-ident>` consistently in all commands
   - Replace "Show note-titles" with "Show note-header"

2. **Clarify context resolution**:
   ```
   - Org:
       - --org|-o is top choice
       - auto-detect via `git remote get-url origin` unless -g|--global
       - Env 'NotehubOrg'
       - git config (global) 'notehub.org'
       - (no default - error if unresolved)
   ```

3. **Define note-issue filter**:
   Add to spec: "All issues in the configured repo are treated as note-issues"
   OR: "Issues with label `note` are note-issues"

4. **Clarify command outputs**:
   - `list` → "Show note-header for each note-issue"
   - `show <note-ident>` → "Display full body of single note-issue, followed by issue URL"
   - `find` → "Show note-header for each note-issue containing regex match"
````

## Missing Specifications
- Error handling (what if `gh` isn't installed? auth fails?)
- Concurrency (what if issue changes between fetch and edit?)
- Template format for `add` command
