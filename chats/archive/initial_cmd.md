# Implementation Plan: Bare-bones `notehub add` command

## Goal
Create a minimally functional `notehub add` command that creates a GitHub issue via `gh issue create`.

## Scope
- No error handling
- No context resolution (hardcode or use simplest fallback)
- No configuration system
- Direct `gh` invocation only
- Interactive mode only (let `gh` prompt for title/body)

## Implementation Steps

### 1. Entry Point (`__main__.py`)
- Import and call `cli.main()`
- Pass `sys.argv[1:]` to CLI parser

### 2. CLI Parser (`cli.py`)
- Use `argparse` to create parser
- Add single subcommand: `add`
- Parse arguments and dispatch to `commands.add.run()`

### 3. Add Command (`commands/add.py`)
- Define `run()` function (takes parsed args)
- Call `gh_wrapper.create_issue()`
- Print success message with issue number/URL

### 4. GH Wrapper (`gh_wrapper.py`)
- Define `create_issue()` function
- Use `subprocess.run()` to invoke `gh issue create --web` or interactive mode
- No repo/host specification (rely on `gh` defaults from current directory)
- Return stdout or nothing

### 5. Package Init (`__init__.py`)
- Can be empty for now

### 6. Commands Init (`commands/__init__.py`)
- Can be empty for now

## Minimal Test
```bash
cd /some/git/repo
python -m notehub add
# Should launch gh issue create interactively
```

## Files Not Needed Yet
- `context.py` - skip context resolution
- `config.py` - skip configuration
- `utils.py` - no utilities needed yet
- All other command files
- All test files

## Notes
- Assume user is in a git repo where `gh` works
- Assume `gh` is installed and authenticated
- Let `gh` handle all prompts and errors
- Focus on plumbing: main → cli → command → gh_wrapper
