# FAQ - CodeMirror Vim Mode

Common questions and their answers.

## Setup Questions

### Q: Why isn't Vim mode working?

**Check**:
1. `vim()` extension is included
2. `vim()` is placed **before** other keymap extensions
3. `drawSelection` plugin is included (automatic with `basicSetup`)

```typescript
// WRONG
extensions: [basicSetup, vim()]

// CORRECT
extensions: [vim(), basicSetup]
```

### Q: How do I access the CM5 API from CM6?

Use `getCM(view)`:

```typescript
import { getCM } from '@replit/codemirror-vim'

const cm = getCM(view)
cm.getValue()
cm.setCursor({ line: 0, ch: 0 })
```

### Q: Can I use CM5 and CM6 together?

No. They are separate editor implementations. CM6-Vim provides a CM5-compatible **API surface** but runs on CM6 architecture.

## Key Mapping Questions

### Q: How do I remap Esc?

```typescript
Vim.map("jj", "<Esc>", "insert")
Vim.map("jk", "<Esc>", "insert")
```

### Q: What's the difference between `map` and `noremap`?

- `Vim.map("a", "b")` - If `b` is mapped elsewhere, it expands recursively
- `Vim.noremap("a", "b")` - No recursive expansion (safer)

**Example**:
```typescript
Vim.map("a", "b")
Vim.map("b", "c")
// Pressing 'a' eventually triggers 'c'

Vim.noremap("a", "b")
Vim.map("b", "c")
// Pressing 'a' triggers 'b', not 'c'
```

### Q: How do I set a leader key?

```typescript
// Map Space as leader in normal mode
Vim.map("<Space>", "<Leader>", "normal")

// Then use <Leader> in other maps
Vim.map("<Leader>w", ":write<CR>", "normal")
```

**Default leader**: backslash `\`

### Q: Can I map Ctrl/Alt combinations?

Yes:
```typescript
Vim.map("<C-s>", ":write<CR>", "insert")  // Ctrl-s
Vim.map("<A-j>", ":m+<CR>", "normal")     // Alt-j
Vim.map("<C-S-p>", ":command<CR>")        // Ctrl-Shift-p
```

## Ex Command Questions

### Q: How do I create a custom Ex command?

```typescript
Vim.defineEx("mycommand", "mc", (cm, params) => {
  // params.args - array of arguments
  // params.argString - full argument string
  // params.line, params.lineEnd - range if provided
})
```

Usage: `:mycommand arg1 arg2` or `:mc arg1 arg2`

### Q: How do I handle line ranges in Ex commands?

```typescript
Vim.defineEx("uppercase", "up", (cm, params) => {
  const startLine = params.line || 0
  const endLine = params.lineEnd || cm.lastLine()
  
  // Process lines startLine to endLine
})
```

Usage: `:5,10uppercase` (lines 5-10), `:.,+5up` (current + 5 lines)

### Q: Can Ex commands be async?

Yes:
```typescript
Vim.defineEx("fetch", "f", async (cm, params) => {
  const data = await fetch(params.args[0])
  const text = await data.text()
  cm.setValue(text)
})
```

## Operator/Motion Questions

### Q: What's the difference between operator, motion, and action?

- **Motion**: Moves cursor (e.g., `w`, `$`, `gg`)
- **Operator**: Acts on text range (e.g., `d`, `y`, `c`)
- **Action**: Arbitrary command (e.g., `i`, `dd`, `x`)

**Composability**: Operator + Motion (e.g., `dw` = delete word)

### Q: How do I create a custom operator?

```typescript
Vim.defineOperator("uppercase", (cm, operatorArgs, ranges) => {
  ranges.forEach(range => {
    const text = cm.getRange(range.anchor, range.head)
    cm.replaceRange(text.toUpperCase(), range.anchor, range.head)
  })
  // Optionally return new cursor position
})

// Map to keys
Vim.mapCommand("gu", "operator", "uppercase")
```

Usage: `guw` (uppercase word), `gu2j` (uppercase 2 lines)

### Q: How do I create a custom motion?

```typescript
Vim.defineMotion("nextSection", (cm, head, motionArgs) => {
  // Find next section marker
  let line = head.line + 1
  while (line < cm.lastLine()) {
    if (cm.getLine(line).startsWith('##')) {
      return { line, ch: 0 }
    }
    line++
  }
  return head  // No match, stay put
})

Vim.mapCommand("]]", "motion", "nextSection")
```

## Mode Questions

### Q: How do I detect the current Vim mode?

```typescript
const cm = getCM(view)

cm.on("vim-mode-change", (modeObj) => {
  console.log(modeObj.mode)      // "normal", "insert", "visual", "replace"
  console.log(modeObj.subMode)   // "linewise", "blockwise" (for visual)
})

// Or check current state
const mode = cm.state.vim?.mode
```

### Q: How do I programmatically change modes?

```typescript
// Exit insert mode
Vim.exitInsertMode(cm)

// Exit visual mode
Vim.exitVisualMode(cm)

// Enter insert mode (trigger 'i' command)
Vim.handleKey(cm, "i")
```

### Q: Can I disable certain modes?

Not directly, but you can intercept mode changes:

```typescript
cm.on("vim-mode-change", (modeObj) => {
  if (modeObj.mode === "replace") {
    // Force back to normal
    Vim.exitInsertMode(cm)
  }
})
```

## Options Questions

### Q: What Vim options are supported?

Common ones:
- `ignorecase` - Case-insensitive search
- `smartcase` - Override ignorecase if pattern has uppercase
- `hlsearch` - Highlight search matches
- `number` - Show line numbers
- `relativenumber` - Relative line numbers

**Check CM5 docs** for full list: [cm5/doc/manual.html#vimapi](../cm5/doc/manual.html)

### Q: How do I define custom options?

```typescript
let myCustomValue = false

Vim.defineOption("mycustom", false, "boolean", ["mc"], (value, cm) => {
  if (value === undefined) {
    return myCustomValue  // Getter
  }
  myCustomValue = value   // Setter
  // Perform side effects if needed
})
```

Usage: `:set mycustom` or `:set nomycustom`

## Register Questions

### Q: How do I access Vim registers?

```typescript
const rc = Vim.getRegisterController()

// Get register content
const text = rc.getRegister('a').toString()

// Set register
rc.getRegister('a').setText("hello")

// Common registers:
// " - unnamed (default yank/delete)
// 0-9 - numbered (yank history)
// a-z - named
// + - system clipboard (if defined)
```

### Q: How do I integrate with system clipboard?

```typescript
const clipboardRegister = {
  text: '',
  
  setText(text) {
    this.text = text
    navigator.clipboard.writeText(text).catch(err => {
      console.error('Clipboard write failed:', err)
    })
  },
  
  pushText(text) {
    this.text += text
    navigator.clipboard.writeText(this.text).catch(err => {
      console.error('Clipboard write failed:', err)
    })
  },
  
  clear() {
    this.text = ''
  },
  
  toString() {
    // Must be synchronous - return cached value
    navigator.clipboard.readText().then(clipText => {
      if (clipText) this.text = clipText
    }).catch(err => {
      console.error('Clipboard read failed:', err)
    })
    return this.text
  }
}

Vim.defineRegister('+', clipboardRegister)
Vim.defineRegister('*', clipboardRegister)
```

**⚠️ Note**: Register methods must be synchronous. Do not use `async/await`.

Usage: `"+yy` (yank line to clipboard), `"+p` (paste from clipboard)

## Integration Questions

### Q: How do I integrate with React?

```typescript
function Editor() {
  const editorRef = useRef(null)
  const viewRef = useRef(null)
  
  useEffect(() => {
    const view = new EditorView({
      extensions: [vim(), basicSetup],
      parent: editorRef.current
    })
    viewRef.current = view
    
    return () => view.destroy()
  }, [])
  
  return <div ref={editorRef} />
}
```

### Q: How do I save files with `:w`?

```typescript
Vim.defineEx("write", "w", async (cm, params) => {
  const content = cm.getValue()
  const filename = params.args[0] || currentFilename
  await saveToBackend(filename, content)
})
```

### Q: Can I show a status bar?

Yes, track mode changes:

```typescript
const statusBar = document.querySelector('#status')
const cm = getCM(view)

cm.on("vim-mode-change", ({ mode, subMode }) => {
  if (mode === "insert") {
    statusBar.textContent = "-- INSERT --"
  } else if (mode === "visual") {
    const type = subMode === "linewise" ? " LINE" : 
                 subMode === "blockwise" ? " BLOCK" : ""
    statusBar.textContent = "-- VISUAL" + type + " --"
  } else {
    statusBar.textContent = ""
  }
})
```

## Debugging Questions

### Q: How do I debug Vim commands?

```typescript
const cm = getCM(view)

// Log all keypresses
cm.on("vim-keypress", (key) => {
  console.log("Key:", key)
})

// Log command completions
cm.on("vim-command-done", () => {
  console.log("State:", cm.state.vim)
})

// Manually trigger commands
Vim.handleKey(cm, "dd")
console.log("After dd:", cm.getValue())
```

### Q: Why isn't my custom command working?

**Check**:
1. Command is registered before first use
2. Command name/prefix is correct
3. No conflicting commands with same name
4. Handler function signature is correct

```typescript
// Debug registration
Vim.defineEx("test", "t", (cm, params) => {
  console.log("Test command called!", params)
})

// Test from console
const cm = getCM(view)
Vim.handleKey(cm, ":")
// Then type "test" and Enter
```

### Q: How do I see all registered commands?

```typescript
// Access internal state (undocumented, may change)
console.log(Vim._getVimGlobalState_())

// Or via vim.js internals
const cm = getCM(view)
console.log(cm.state.vim)
```

## Performance Questions

### Q: Does Vim mode affect editor performance?

Minimal impact. Vim mode adds event handlers and state tracking but doesn't significantly affect rendering or large document performance.

### Q: Can I lazy-load Vim mode?

Yes:

```typescript
let vimEnabled = false

async function enableVim() {
  if (vimEnabled) return
  
  const { vim } = await import('@replit/codemirror-vim')
  view.dispatch({
    effects: StateEffect.appendConfig.of(vim())
  })
  vimEnabled = true
}
```

## Migration Questions

### Q: I'm migrating from CM5 Vim. What changed?

**Same**: Vim API surface (map, defineEx, etc.)
**Different**:
- Import from `@replit/codemirror-vim` not `codemirror/keymap/vim`
- Must use `getCM(view)` to access CM5-style API
- Editor setup uses CM6 extension system

### Q: Are all CM5 Vim features supported?

Most are. Check [cm6-vim issues](https://github.com/replit/codemirror-vim/issues) for known gaps.

### Q: Can I use CM5 Vim documentation?

Yes! The CM5 Vim API docs are authoritative. Just access the API via `getCM(view)` in CM6.

**Reference**: [cm5/doc/manual.html#vimapi](../cm5/doc/manual.html) (lines 3532-3762)
