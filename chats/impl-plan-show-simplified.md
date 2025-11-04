lmatheson4_bbeng: I need you to plan a simplified implementation of the 'show' command.  It should just handle explicitly-specified issue ID (numeric) and print the output specified in the spec. 

Identify the components that will need to change and the work to be performed.  Don't actually write the code, we will review and iterate

GitHub Copilot: # Implementation Plan: Simplified `show` Command

## Overview
Implement a minimal version of `notehub show <issue-number>` that accepts only numeric issue IDs and displays the note-header and URL.

---

## Components to Create/Modify

### 1. **show.py** (NEW)
**Work Required:**
- Create new command module
- Implement `run(args: Namespace) -> int` function
- Implement `format_note_header(issue: dict) -> str` helper
- **Simplified scope:** Skip `resolve_note_ident()` - just parse integer directly
- Error handling for invalid/non-numeric input

**Core Logic:**
```
1. Extract issue number from args (args.note_idents[0])
2. Validate it's a numeric string
3. Convert to int
4. Call gh_wrapper.get_issue(context, issue_number)
5. Format and print note-header
6. Print issue URL (indented)
7. Return 0 on success, 1 on errors
```

**Dependencies:**
- Needs `context.StoreContext` for repo context
- Needs `gh_wrapper.get_issue()` to fetch issue data
- Needs access to parsed args with `.note_idents` attribute

---

### 2. **gh_wrapper.py** (MODIFY/EXTEND)
**Work Required:**
- Implement `get_issue(context: StoreContext, issue_number: int) -> dict`
- Use `gh api` to fetch issue JSON
- Build API path: `repos/{org}/{repo}/issues/{issue_number}`
- Handle host specification for non-github.com
- Return parsed JSON dict

**Example gh command:**
```bash
gh api repos/{org}/{repo}/issues/{num} --hostname {host}
```

**Error Cases:**
- Issue not found (404)
- Network errors
- Authentication errors (403)
- Invalid repo context

---

### 3. **cli.py** (MODIFY)
**Work Required:**
- Add `show` subcommand to argument parser
- Define positional argument: `note_idents` (nargs='+' for multiple IDs)
- Add common flags: `--repo`, `--org`, `--host`, `--global`
- Wire up to `commands.show.run()`

**Argument Definition:**
```python
show_parser = subparsers.add_parser('show', help='Display note details')
show_parser.add_argument('note_idents', nargs='+', help='Issue numbers to show')
# ... add --repo, --org, --host, --global flags
show_parser.set_defaults(func=commands.show.run)
```

---

### 4. **context.py** (VERIFY EXISTS)
**Work Required:**
- **No changes needed** - should already exist per design
- Verify `StoreContext.resolve(args)` works as designed
- Verify `full_identifier()` method exists for URL construction

**Usage in show command:**
```python
context = StoreContext.resolve(args)
# context.org, context.repo, context.host available
```

---

### 5. **gh_wrapper.py** (VERIFY INFRASTRUCTURE)
**Work Required:**
- Verify `GhResult` dataclass exists
- Verify `run_gh()` or similar helper exists for subprocess execution
- May need to implement `build_repo_arg()` if not already present
- Implement JSON parsing from `gh api` output

**Key Helper:**
```python
def get_issue(context: StoreContext, issue_number: int) -> dict:
    # Build: gh api repos/{org}/{repo}/issues/{num}
    # Add --hostname if not github.com
    # Parse JSON response
    # Return dict
```

---

## Output Format Specification

Based on spec requirements:

**For each issue:**
```
[#123] Issue Title Here
    https://github.com/org/repo/issues/123
```

**Format Details:**
- Note-header: `[#{number}] {title}`
- URL line indented with 4 spaces
- URL constructed from context + issue number
- Handle GHES URLs: `https://{host}/{org}/{repo}/issues/{num}`

---

## Error Handling Requirements

### Input Validation
- Check `note_idents` list is not empty
- Validate each ident is numeric (can convert to int)
- Return exit code 1 with error message if invalid

### GitHub API Errors
- Issue not found: "Error: Issue #{num} not found in {org}/{repo}"
- Auth errors: Pass through gh stderr
- Network errors: Pass through gh stderr
- Return exit code 1 on any failure

### Edge Cases
- Multiple issue numbers (iterate and show all)
- Issue exists but user has no access (403)
- Repo doesn't exist

---

## Dependencies Required

**Must already exist:**
- `context.py` with `StoreContext` class
- `gh_wrapper.py` with basic subprocess infrastructure
- `cli.py` with argument parser framework

**External dependencies:**
- `gh` CLI installed and in PATH
- User authenticated to appropriate host

---

## Testing Strategy (for later implementation)

### Unit Tests
- `test_format_note_header()` - verify formatting
- `test_invalid_input()` - non-numeric input handling
- Mock `gh_wrapper.get_issue()` for isolation

### Integration Tests
- Test with real `gh` CLI (if available)
- Test multiple issue numbers
- Test issue not found scenario
- Test GHES vs github.com URL formatting

---

## Questions to Resolve

1. **Multi-issue behavior**: Spec says `note_idents` is plural - should simplified version handle multiple IDs or just one?
   - **Recommendation:** Support multiple from start (minimal extra code)

2. **URL construction**: Should this be a helper in `context.py` or `show.py`?
   - **Recommendation:** Add `build_issue_url(issue_number: int)` to `StoreContext`

3. **JSON fields needed**: What fields does `gh api` return that we need?
   - Minimum: `number`, `title`, `html_url`
   - `html_url` would eliminate need to construct URL manually

4. **Error verbosity**: How much detail for failed API calls?
   - **Recommendation:** Just pass through `gh` stderr as per design doc

---

## Implementation Order

1. ✅ Ensure `context.py` exists with `StoreContext`
2. ✅ Ensure `gh_wrapper.py` has basic infrastructure
3. **Implement `gh_wrapper.get_issue()`**
4. **Create `commands/show.py` with basic implementation**
5. **Wire up in `cli.py`**
6. **Manual testing with real repo**
7. **Add unit tests**

---

## Out of Scope (Deferred to Full Implementation)

- ❌ `resolve_note_ident()` - title regex search
- ❌ Fuzzy matching
- ❌ Filtering by labels/milestones
- ❌ Color/formatting options
- ❌ Pagination for large numbers of issues
