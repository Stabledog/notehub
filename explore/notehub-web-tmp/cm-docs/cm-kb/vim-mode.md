# Vim Mode API Reference

Complete reference for CodeMirror Vim mode. API is defined in CM5, implemented in CM6-Vim.

## Setup (CM6)

```typescript
import { vim, getCM, Vim } from '@replit/codemirror-vim'
import { EditorView, basicSetup } from 'codemirror'

const view = new EditorView({
  extensions: [
    vim(),           // MUST be before other keymaps
    basicSetup,      // includes default keymaps for insert mode
  ]
})

// Access CM5-compatible API
const cm = getCM(view)
```

**Source**: [cm6-vim/README.md](../cm6-vim/README.md), [cm6-vim/src/index.ts](../cm6-vim/src/index.ts)

## Configuration API

### `Vim.setOption(name, value, ?cm, ?cfg)`
Set a Vim option (like `:set` in Vim).

```typescript
Vim.setOption("hlsearch", true)  // Enable search highlighting
```

**Source**: [cm5/doc/manual.html#vimapi_setOption](../cm5/doc/manual.html) (line 3550)

### `Vim.getOption(name, ?cm, ?cfg)`
Get current value of a Vim option.

```typescript
const isEnabled = Vim.getOption("hlsearch")
```

**Source**: [cm5/doc/manual.html#vimapi_getOption](../cm5/doc/manual.html) (line 3558)

## Key Mapping API

### `Vim.map(lhs, rhs, ?context)`
Map key sequence `lhs` to `rhs` in specified context.

```typescript
Vim.map("jj", "<Esc>", "insert")  // jj exits insert mode
Vim.map("Y", "y$")                 // Y yanks to end of line (normal)
```

**Contexts**: `"normal"`, `"insert"`, `"visual"`

**Source**: [cm5/doc/manual.html#vimapi_map](../cm5/doc/manual.html) (line 3565)

### `Vim.noremap(lhs, rhs, context)`
Non-recursive mapping (prevents recursive expansion).

```typescript
Vim.noremap("Y", "y$", "normal")
```

**Source**: [cm5/doc/manual.html#vimapi_noremap](../cm5/doc/manual.html) (line 3600)

### `Vim.unmap(lhs, context)`
Remove a key mapping.

```typescript
Vim.unmap("jj", "insert")
```

**Source**: [cm5/doc/manual.html#vimapi_unmap](../cm5/doc/manual.html) (line 3588)

### `Vim.mapclear(context)`
Clear all mappings in context.

```typescript
Vim.mapclear("insert")
```

**Source**: [cm5/doc/manual.html#vimapi_mapclear](../cm5/doc/manual.html) (line 3595)

### `Vim.mapCommand(keys, type, name, ?args, ?extra)`
Map keys to a named command with specific type.

```typescript
Vim.mapCommand("gq", "operator", "hardWrap", {}, {})
```

**Types**: `"motion"`, `"operator"`, `"action"`

**Source**: [cm5/doc/manual.html#vimapi_mapCommand](../cm5/doc/manual.html) (line 3576)

## Extension API

### `Vim.defineMotion(name, fn)`
Define a custom motion command.

```typescript
Vim.defineMotion("nextParagraph", (cm, head, motionArgs) => {
  // Return new cursor position
  return { line: head.line + 1, ch: 0 }
})
```

**Signature**: `fn(cm: CodeMirror, head: Pos, motionArgs: object) → Pos`

**Source**: [cm5/doc/manual.html#vimapi_defineMotion](../cm5/doc/manual.html) (line 3654)

### `Vim.defineOperator(name, fn)`
Define a custom operator command.

```typescript
Vim.defineOperator("uppercase", (cm, operatorArgs, ranges) => {
  // Operate on ranges
  ranges.forEach(range => {
    const text = cm.getRange(range.anchor, range.head)
    cm.replaceRange(text.toUpperCase(), range.anchor, range.head)
  })
  return ranges[0].head  // New cursor position
})
```

**Signature**: `fn(cm: CodeMirror, operatorArgs: object, ranges: Array<{anchor, head}>) → ?Pos`

**Source**: [cm5/doc/manual.html#vimapi_defineOperator](../cm5/doc/manual.html) (line 3662)

### `Vim.defineAction(name, fn)`
Define an action command (arbitrary behavior).

```typescript
Vim.defineAction("saveFile", (cm, actionArgs) => {
  // Perform action
  saveToServer(cm.getValue())
})
```

**Signature**: `fn(cm: CodeMirror, actionArgs: object)`

**Source**: [cm5/doc/manual.html#vimapi_defineActon](../cm5/doc/manual.html) (line 3673)

### `Vim.defineEx(name, ?prefix, fn)`
Define an Ex command (`:name`).

```typescript
Vim.defineEx("write", "w", (cm, params) => {
  // params.argString - full args
  // params.args - args split by whitespace
  // params.line, params.lineEnd - range if provided
  saveFile(cm.getValue())
})
```

**Usage**: `:w`, `:write` (both work if prefix is "w")

**Source**: [cm5/doc/manual.html#vimapi_defineEx](../cm5/doc/manual.html) (line 3679)

### `Vim.defineOption(name, default, type, ?aliases, ?callback)`
Define a custom Vim option.

```typescript
Vim.defineOption("myoption", false, "boolean", ["mo"], (value, cm) => {
  if (value === undefined) {
    return myOptionValue  // getter
  }
  myOptionValue = value   // setter
})
```

**Types**: `"boolean"`, `"string"`

**Source**: [cm5/doc/manual.html#vimapi_defineOption](../cm5/doc/manual.html) (line 3634)

## Events

Listen via `cm.on(eventName, handler)`.

### `"vim-mode-change"`
Fired when Vim mode changes.

```typescript
cm.on("vim-mode-change", (modeObj) => {
  // modeObj: { mode: string, subMode?: string }
  // modes: "insert", "normal", "replace", "visual"
  // visual subModes: "linewise", "blockwise"
})
```

**Source**: [cm5/doc/manual.html#vimapi_modechange](../cm5/doc/manual.html) (line 3620)

### `"vim-command-done"`
Fired after a Vim command completes.

```typescript
cm.on("vim-command-done", (reason) => {
  // Command finished
})
```

**Source**: [cm5/doc/manual.html#vimapi_commanddone](../cm5/doc/manual.html) (line 3614)

### `"vim-keypress"`
Fired on each Vim key press.

```typescript
cm.on("vim-keypress", (vimKey) => {
  // vimKey: string representation of key
})
```

**Source**: [cm5/doc/manual.html#vimapi_keypress](../cm5/doc/manual.html) (line 3617)

## Utility Methods

### `Vim.handleKey(cm, key, origin)`
Manually trigger a key in Vim mode.

```typescript
Vim.handleKey(cm, "<Esc>", "user")
```

**Source**: [cm5/doc/manual.html#vimapi_handleKey](../cm5/doc/manual.html) (line 3728)

### `Vim.exitInsertMode(cm)`
Programmatically exit insert mode.

```typescript
Vim.exitInsertMode(cm)
```

**Source**: [cm5/doc/manual.html#vimapi_exitInsertMode](../cm5/doc/manual.html) (line 3756)

### `Vim.exitVisualMode(cm, ?moveHead)`
Exit visual mode. If `moveHead` is false, cursor stays in place.

```typescript
Vim.exitVisualMode(cm, true)
```

**Source**: [cm5/doc/manual.html#vimapi_exitVisualMode](../cm5/doc/manual.html) (line 3749)

### `Vim.getRegisterController()`
Access the register system.

```typescript
const rc = Vim.getRegisterController()
// Use rc.getRegister(name), rc.setRegister(name, text), etc.
```

**Source**: [cm5/doc/manual.html#vimapi_getRegisterController](../cm5/doc/manual.html) (line 3693)

### `Vim.defineRegister(name, register)`
Define a custom register.

Register object must implement:
- `setText(text)` - **must be synchronous**
- `pushText(text)` - **must be synchronous**
- `clear()` - **must be synchronous**
- `toString() → string` - **must be synchronous, must return string**

**⚠️ Critical**: All methods must be synchronous. Do not use `async/await` or return Promises. For async operations (like clipboard access), use fire-and-forget pattern with `.catch()` for error handling.

**Source**: [cm5/doc/manual.html#vimapi_defineRegister](../cm5/doc/manual.html) (line 3701)

## Implementation Files

| Component | File |
|-----------|------|
| Plugin entry | [cm6-vim/src/index.ts](../cm6-vim/src/index.ts) |
| CM5 adapter | [cm6-vim/src/cm_adapter.ts](../cm6-vim/src/cm_adapter.ts) |
| Vim logic | [cm6-vim/src/vim.js](../cm6-vim/src/vim.js) |
| Type definitions | [cm6-vim/src/types.ts](../cm6-vim/src/types.ts) |

## Common Patterns

### Custom Ex Command
```typescript
Vim.defineEx("format", "fmt", (cm, params) => {
  const code = cm.getValue()
  const formatted = prettier.format(code)
  cm.setValue(formatted)
})
```

### Custom Operator
```typescript
Vim.defineOperator("comment", (cm, args, ranges) => {
  ranges.forEach(r => {
    const lines = cm.getRange(r.anchor, r.head).split('\n')
    const commented = lines.map(l => '// ' + l).join('\n')
    cm.replaceRange(commented, r.anchor, r.head)
  })
})
Vim.mapCommand("gc", "operator", "comment")
```

### Mode-specific Mapping
```typescript
// Quick save in normal mode
Vim.map("<Leader>w", ":w<CR>", "normal")

// Exit insert with jk
Vim.map("jk", "<Esc>", "insert")
```
