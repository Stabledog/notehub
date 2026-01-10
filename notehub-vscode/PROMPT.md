# Notehub VS Code Extension - Implementation Prompt

## Overview

Build a TypeScript VS Code extension that automates notehub workflow in VS Code by:
1. Making `nh`/`notehub` command strings Ctrl+Click-able (like URLs)
2. Providing a command to sync the active note file via status bar button

## Background

**Notehub** is a personal CLI tool (see `../notehub-help.md`) that manages notes as GitHub issues. Command syntax: `notehub [command] -o ORG -r REPO ISSUE_NUMBER`

**Current Pain Points:**
- Manual copy/paste of `nh edit` commands from notes to open related notes
- Status bar button hardcoded to sync one specific note (#7) instead of syncing whatever note is active

**Note File Structure:**
- Notehub stores notes in: `.cache/notehub/{host}/{org}/{repo}/{issue}/note.md`
- Example: `C:\Users\lmatheson4\.cache\notehub\bbgithub.dev.bloomberg.com\training-lmatheson4\compliance-monitor\8\note.md`
- Notes reference other notes via embedded commands like: `nh edit -o training-materials -r cpp-monitor-project 24`

## Requirements

### 1. DocumentLinkProvider for Clickable Commands

**Pattern to detect:** `(nh|notehub)\s+\w+\s+-o\s+\S+\s+-r\s+\S+\s+\d+`

- Match any notehub command with strict `-o ORG -r REPO ISSUE` ordering
- Make the entire command Ctrl+Click-able in markdown files
- On click:
  - Replace `nh` prefix with `notehub` (if needed)
  - Execute the full command string in a reusable integrated terminal
  - Log the command invocation to "Notehub" output channel

**Example:**
```markdown
See the related issue: nh edit -o trainkit -r gutscore 16
```
Should become clickable and execute: `notehub edit -o trainkit -r gutscore 16`

### 2. Sync Active Note Command

**Command ID:** `notehub.syncActive`

**Behavior:**
- Extract the active editor's file path
- Parse for pattern: `.cache/notehub/{host}/{org}/{repo}/{issue}/note.md`
- If pattern matches:
  - Construct command: `notehub sync -H {host} -o {org} -r {repo} {issue}`
  - Execute in the same reusable integrated terminal
  - Log the command to "Notehub" output channel
- If pattern doesn't match:
  - Log error with the file path to "Notehub" output channel
  - Do not execute anything

**Example:**
- Active file: `C:\Users\lmatheson4\.cache\notehub\bbgithub.dev.bloomberg.com\training-lmatheson4\compliance-monitor\8\note.md`
- Should execute: `notehub sync -H bbgithub.dev.bloomberg.com -o training-lmatheson4 -r compliance-monitor 8`

### 3. Terminal Behavior

- Use VS Code's integrated terminal
- Reuse the same terminal for all notehub commands (similar to tasks.json "panel.shared" mode)
- Terminal should be visible when commands execute (user wants to see output)

### 4. Logging

- Create output channel named "Notehub" via `vscode.window.createOutputChannel('Notehub')`
- Log format: `[datetime] message`
- Log all command invocations (success path)
- Log errors with context (e.g., file path that didn't match pattern)

## Technical Constraints

- **Language:** TypeScript (use `yo code` generator)
- **Activation Events:**
  - `onLanguage:markdown` (for DocumentLinkProvider)
  - File pattern matching `.cache/notehub/**` (for sync-active on notehub files)
- **No argument parsing:** Don't interpret notehub semantics, just extract/construct command strings and execute them
- **Strict ordering:** Command pattern requires `-o ... -r ... N` in that order (don't support other orderings)
- **Environment:** User runs git-bash/WSL, not PowerShell

## Extension Configuration

**package.json contributions:**
```json
{
  "contributes": {
    "commands": [
      {
        "command": "notehub.syncActive",
        "title": "Notehub: Sync Active Note"
      }
    ]
  }
}
```

## User Settings Update

After building the extension, user will update their `~/.vscode/settings.json` (or workspace settings) from:
```json
"actionButtons": {
    "commands": [
        {
            "name": "$(fold-up) nh-sync.7",
            "useVsCodeApi": true,
            "command": "workbench.action.tasks.runTask",
            "args": ["notehub-sync-7"]
        }
    ]
}
```

To:
```json
"actionButtons": {
    "commands": [
        {
            "name": "$(fold-up) nh-sync",
            "useVsCodeApi": true,
            "command": "notehub.syncActive"
        }
    ]
}
```

## Deliverables

1. Complete TypeScript VS Code extension source code
2. `package.json` with proper activation events and command contributions
3. `.vsix` package (via `vsce package`) for local installation
4. Basic README.md explaining installation and usage

## Implementation Notes

- Start with `yo code` TypeScript extension template
- Install dependencies: `@types/vscode`, `@types/node`
- Main implementation files:
  - `src/extension.ts` - Activation, command registration, terminal management
  - `src/notehubLinkProvider.ts` - DocumentLinkProvider implementation
  - `src/pathParser.ts` - Path parsing logic for sync-active
- Test manually with sample note.md files in `.cache/notehub/` structure

## Testing Scenarios

1. **Clickable command test:**
   - Open a note.md file with embedded `nh edit -o org -r repo 123` command
   - Ctrl+Click on the command
   - Verify it executes `notehub edit -o org -r repo 123` in terminal
   - Check "Notehub" output channel for log entry

2. **Sync active note test:**
   - Open a file: `.cache/notehub/bbgithub.dev.bloomberg.com/training-lmatheson4/compliance-monitor/8/note.md`
   - Invoke `notehub.syncActive` command
   - Verify it executes `notehub sync -H bbgithub.dev.bloomberg.com -o training-lmatheson4 -r compliance-monitor 8`
   - Check output channel for log entry

3. **Error handling test:**
   - Open a non-notehub file (e.g., random README.md)
   - Invoke `notehub.syncActive` command
   - Verify error is logged to output channel
   - Verify no command is executed in terminal

## References

- Notehub help: `../notehub-help.md`
- VS Code Extension API: https://code.visualstudio.com/api
- DocumentLinkProvider: https://code.visualstudio.com/api/references/vscode-api#DocumentLinkProvider
- Terminal API: https://code.visualstudio.com/api/references/vscode-api#window.createTerminal
