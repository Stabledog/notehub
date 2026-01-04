# Common Patterns & Best Practices

Proven approaches for integrating and customizing CodeMirror Vim mode.

## Setup Patterns

### Minimal Vim Setup

```typescript
import { EditorView, minimalSetup } from 'codemirror'
import { vim } from '@replit/codemirror-vim'

const view = new EditorView({
  extensions: [
    vim(),
    minimalSetup,
  ],
  parent: element
})
```

### Full-Featured Setup

```typescript
import { EditorView, basicSetup } from 'codemirror'
import { vim } from '@replit/codemirror-vim'
import { javascript } from '@codemirror/lang-javascript'
import { oneDark } from '@codemirror/theme-one-dark'

const view = new EditorView({
  doc: initialContent,
  extensions: [
    vim(),              // 1. Vim (first!)
    basicSetup,         // 2. Basic editor features
    javascript(),       // 3. Language
    oneDark,            // 4. Theme
    // ... other extensions
  ],
  parent: element
})
```

**Rule**: Always place `vim()` before other keymap extensions.

## Language Support & Syntax Highlighting

### Available Language Packages

CodeMirror 6 provides first-party language support packages:

| Language | Package | Import |
|----------|---------|--------|
| JavaScript | `@codemirror/lang-javascript` | `import { javascript } from '@codemirror/lang-javascript'` |
| TypeScript | `@codemirror/lang-javascript` | `javascript({ typescript: true })` |
| JSX/TSX | `@codemirror/lang-javascript` | `javascript({ jsx: true })` |
| Python | `@codemirror/lang-python` | `import { python } from '@codemirror/lang-python'` |
| Markdown | `@codemirror/lang-markdown` | `import { markdown } from '@codemirror/lang-markdown'` |
| HTML | `@codemirror/lang-html` | `import { html } from '@codemirror/lang-html'` |
| CSS | `@codemirror/lang-css` | `import { css } from '@codemirror/lang-css'` |
| JSON | `@codemirror/lang-json` | `import { json } from '@codemirror/lang-json'` |
| XML | `@codemirror/lang-xml` | `import { xml } from '@codemirror/lang-xml'` |
| SQL | `@codemirror/lang-sql` | `import { sql } from '@codemirror/lang-sql'` |

**Complete list**: See https://codemirror.net/6/docs/ref/#language

### Basic Language Setup

```typescript
import { EditorView, basicSetup } from 'codemirror'
import { vim } from '@replit/codemirror-vim'
import { markdown } from '@codemirror/lang-markdown'

const view = new EditorView({
  doc: '# Markdown heading\n\nSome **bold** text',
  extensions: [
    vim(),
    basicSetup,
    markdown(),  // Adds syntax highlighting + language features
  ],
  parent: element
})
```

### Custom Syntax Highlighting Theme

Create custom color schemes for syntax elements:

```typescript
import { syntaxHighlighting, HighlightStyle } from '@codemirror/language'
import { tags } from '@lezer/highlight'

const myHighlight = HighlightStyle.define([
  { tag: tags.heading1, fontSize: "1.6em", fontWeight: "bold", color: "#0969da" },
  { tag: tags.heading2, fontSize: "1.4em", fontWeight: "bold", color: "#0969da" },
  { tag: tags.strong, fontWeight: "bold" },
  { tag: tags.emphasis, fontStyle: "italic" },
  { tag: tags.link, color: "#0969da", textDecoration: "underline" },
  { tag: tags.monospace, 
    fontFamily: "monospace", 
    backgroundColor: "#f6f8fa",
    color: "#cf222e"
  },
  { tag: tags.keyword, color: "#cf222e", fontWeight: "bold" },
  { tag: tags.string, color: "#0a3069" },
  { tag: tags.comment, color: "#6a737d", fontStyle: "italic" },
])

// Use in editor
const view = new EditorView({
  extensions: [
    vim(),
    markdown(),
    syntaxHighlighting(myHighlight),
  ]
})
```

### Markdown with GitHub-Style Highlighting

For GitHub issue editing or similar use cases:

```typescript
import { EditorView, basicSetup } from 'codemirror'
import { vim } from '@replit/codemirror-vim'
import { markdown } from '@codemirror/lang-markdown'
import { syntaxHighlighting, HighlightStyle } from '@codemirror/language'
import { tags } from '@lezer/highlight'

// GitHub-inspired color palette
const githubMarkdown = HighlightStyle.define([
  { tag: tags.heading1, fontSize: "1.6em", fontWeight: "bold", color: "#0969da" },
  { tag: tags.heading2, fontSize: "1.4em", fontWeight: "bold", color: "#0969da" },
  { tag: tags.heading3, fontSize: "1.2em", fontWeight: "bold", color: "#0969da" },
  { tag: tags.strong, fontWeight: "bold", color: "#24292f" },
  { tag: tags.emphasis, fontStyle: "italic", color: "#24292f" },
  { tag: tags.link, color: "#0969da", textDecoration: "underline" },
  { tag: tags.monospace, 
    fontFamily: "'Consolas', 'Monaco', monospace", 
    backgroundColor: "#f6f8fa",
    padding: "2px 4px",
    borderRadius: "3px",
    color: "#cf222e"
  },
  { tag: tags.strikethrough, textDecoration: "line-through", color: "#656d76" },
  { tag: tags.quote, color: "#656d76", fontStyle: "italic" },
  { tag: tags.list, color: "#24292f" },
])

const view = new EditorView({
  doc: '# Issue Title\n\n## Description\n\nDetails here...',
  extensions: [
    vim(),
    basicSetup,
    markdown(),
    syntaxHighlighting(githubMarkdown),
    EditorView.lineWrapping,  // Recommended for prose
  ],
  parent: element
})
```

**Note**: The `markdown()` extension provides:
- Syntax parsing and highlighting structure
- Code block language detection
- Proper tokenization for formatting

**Nested Code Block Highlighting**: Add `{ codeLanguages: languages }` to enable syntax highlighting inside fenced code blocks:

```typescript
import { markdown } from '@codemirror/lang-markdown'
import { languages } from '@codemirror/language-data'

const view = new EditorView({
  extensions: [
    vim(),
    markdown({ codeLanguages: languages }),  // Syntax highlighting in code blocks
    syntaxHighlighting(githubMarkdown),
  ]
})
```

### Language-Specific Configuration

Some languages accept configuration options:

```typescript
// TypeScript
javascript({ typescript: true })

// JSX
javascript({ jsx: true })

// Both TypeScript + JSX
javascript({ typescript: true, jsx: true })

// Python with specific dialect
python()  // No special config needed
```

### With Status Bar

```typescript
import { getCM, Vim } from '@replit/codemirror-vim'

const statusBar = document.querySelector('#status')
const cm = getCM(view)

cm.on("vim-mode-change", ({ mode, subMode }) => {
  const modeText = {
    insert: "-- INSERT --",
    normal: "",
    visual: "-- VISUAL --",
    replace: "-- REPLACE --"
  }[mode] || ""
  
  statusBar.textContent = modeText
})
```

## Key Mapping Patterns

### Escape Alternatives

```typescript
// Classic alternatives
Vim.map("jj", "<Esc>", "insert")
Vim.map("jk", "<Esc>", "insert")
Vim.map("<C-c>", "<Esc>", "insert")
```

### Leader Key Patterns

```typescript
// Set leader (defaults to \)
Vim.map("<Space>", "<Leader>", "normal")

// Leader mappings
Vim.map("<Leader>w", ":write<CR>", "normal")
Vim.map("<Leader>q", ":quit<CR>", "normal")
Vim.map("<Leader>f", ":format<CR>", "normal")
```

### Consistent Y Behavior

```typescript
// Make Y consistent with C and D (yank to end of line)
Vim.map("Y", "y$", "normal")
```

### Quick Window Navigation

```typescript
Vim.map("<C-h>", "<C-w>h", "normal")
Vim.map("<C-j>", "<C-w>j", "normal")
Vim.map("<C-k>", "<C-w>k", "normal")
Vim.map("<C-l>", "<C-w>l", "normal")
```

## Ex Command Patterns

### Save Command

```typescript
let saveCallback = null

export function setSaveHandler(handler) {
  saveCallback = handler
}

Vim.defineEx("write", "w", async (cm, params) => {
  if (!saveCallback) {
    console.error("No save handler registered")
    return
  }
  
  const content = cm.getValue()
  await saveCallback(content, params.args[0])
})
```

### Format Command

```typescript
import prettier from 'prettier'

Vim.defineEx("format", "fmt", (cm, params) => {
  const content = cm.getValue()
  const formatted = prettier.format(content, {
    parser: params.args[0] || 'babel',
    semi: false,
    singleQuote: true,
  })
  cm.setValue(formatted)
})
```

Usage: `:fmt` or `:format typescript`

### Custom Range Command

```typescript
Vim.defineEx("uppercase", "upper", (cm, params) => {
  const from = { line: params.line || 0, ch: 0 }
  const to = { line: params.lineEnd || cm.lastLine(), ch: 0 }
  
  const text = cm.getRange(from, to)
  cm.replaceRange(text.toUpperCase(), from, to)
})
```

Usage: `:5,10upper` (uppercase lines 5-10)

## Operator Patterns

### Comment Operator

```typescript
Vim.defineOperator("toggleComment", (cm, operatorArgs, ranges) => {
  ranges.forEach(range => {
    const lines = []
    for (let i = range.anchor.line; i <= range.head.line; i++) {
      lines.push(cm.getLine(i))
    }
    
    const allCommented = lines.every(l => l.trim().startsWith('//'))
    const newLines = lines.map(line => {
      if (allCommented) {
        return line.replace(/^(\s*)\/\/\s?/, '$1')
      } else {
        return line.replace(/^(\s*)/, '$1// ')
      }
    })
    
    cm.replaceRange(
      newLines.join('\n'),
      range.anchor,
      { line: range.head.line, ch: cm.getLine(range.head.line).length }
    )
  })
})

// Map to gc (e.g., gcc for line, gc2j for 2 lines down)
Vim.mapCommand("gc", "operator", "toggleComment")
```

### Surround Operator

```typescript
Vim.defineOperator("surround", (cm, operatorArgs, ranges) => {
  const char = operatorArgs.selectedCharacter || '"'
  
  ranges.forEach(range => {
    const text = cm.getRange(range.anchor, range.head)
    cm.replaceRange(char + text + char, range.anchor, range.head)
  })
})

// Would need additional logic for selecting character
// This is a simplified example
```

## Motion Patterns

### Next/Previous Function

```typescript
Vim.defineMotion("nextFunction", (cm, head, motionArgs) => {
  const doc = cm.getDoc()
  const dir = motionArgs.forward ? 1 : -1
  let line = head.line + dir
  const regex = /^\s*(?:function|const\s+\w+\s*=|class\s+)/
  
  while (line >= 0 && line < doc.lineCount()) {
    if (regex.test(doc.getLine(line))) {
      return { line, ch: 0 }
    }
    line += dir
  }
  
  return head
})

Vim.mapCommand("]f", "motion", "nextFunction", { forward: true })
Vim.mapCommand("[f", "motion", "nextFunction", { forward: false })
```

### Paragraph with Custom Logic

```typescript
Vim.defineMotion("smartParagraph", (cm, head, motionArgs) => {
  // Custom paragraph detection (e.g., by indentation)
  let line = head.line
  const currentIndent = cm.getLine(line).search(/\S/)
  
  while (line < cm.lastLine()) {
    line++
    const lineText = cm.getLine(line)
    if (lineText.trim() === '') break
    if (lineText.search(/\S/) <= currentIndent) break
  }
  
  return { line, ch: 0 }
})

Vim.mapCommand("}", "motion", "smartParagraph")
```

## State Management Patterns

### Track Vim State in React

```typescript
function VimEditor() {
  const [vimMode, setVimMode] = useState('normal')
  const editorRef = useRef(null)
  
  useEffect(() => {
    const view = new EditorView({
      extensions: [
        vim(),
        basicSetup,
      ],
      parent: editorRef.current
    })
    
    const cm = getCM(view)
    cm.on("vim-mode-change", ({ mode }) => {
      setVimMode(mode)
    })
    
    return () => view.destroy()
  }, [])
  
  return (
    <>
      <div ref={editorRef} />
      <div className="status">{vimMode.toUpperCase()}</div>
    </>
  )
}
```

### Persist Vim Options

```typescript
const VIM_OPTIONS_KEY = 'vim_options'

// Load from localStorage
function loadVimOptions() {
  const saved = localStorage.getItem(VIM_OPTIONS_KEY)
  if (saved) {
    const options = JSON.parse(saved)
    Object.entries(options).forEach(([name, value]) => {
      Vim.setOption(name, value)
    })
  }
}

// Save to localStorage
function saveVimOption(name, value) {
  Vim.setOption(name, value)
  
  const saved = JSON.parse(localStorage.getItem(VIM_OPTIONS_KEY) || '{}')
  saved[name] = value
  localStorage.setItem(VIM_OPTIONS_KEY, JSON.stringify(saved))
}
```

## Custom Register Patterns

### Clipboard Register

```typescript
const clipboardRegister = {
  text: '',
  
  setText(text) {
    this.text = text
    // Fire-and-forget: don't await, handle errors
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
    // MUST return string synchronously
    // Update cache in background for next paste
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

**⚠️ Important**: 
Usage: `"+yy` copies line to system clipboard

Note: CM6‑Vim already provides `+`/`*` clipboard registers backed by the browser clipboard. Prefer using `"+y`/`"+p` rather than redefining these registers. Overriding `+` will fail with "Register already defined +" and is unsupported.

Safe clipboard integration (examples)
-----------------------------------
When integrating with the system clipboard, follow two principles:

1. Keep register methods synchronous (no `async`/`await`).
2. Use user‑gesture handlers for reads, and provide an execCommand fallback for writes.

Example — sync writes by intercepting pushText (yank):

```typescript
// Intercept register controller to mirror yanks to system clipboard
const rc = Vim.getRegisterController()
const origPush = rc.pushText.bind(rc)
rc.pushText = function(name, op, text, linewise, block) {
  const res = origPush(name, op, text, linewise, block)
  if (op === 'yank') {
    // Fire-and-forget write; may fail if document isn't focused
    navigator.clipboard?.writeText(text).catch(() => {
      // Fallback: textarea + execCommand('copy')
      const t = document.createElement('textarea')
      t.value = text
      document.body.appendChild(t)
      t.select()
      document.execCommand('copy')
      document.body.removeChild(t)
    })
  }
  return res
}
```

Example — paste from system clipboard on a real user keypress (keydown handler):

```typescript
// Run during an actual user keydown so clipboard.readText() is allowed
document.addEventListener('keydown', async (e) => {
  if (e.key !== 'p') return
  // ensure editor focused and in normal mode, then read clipboard
  const text = await navigator.clipboard.readText().catch(() => '')
  if (text) {
    const cm = getCM(view)
    const cur = cm.getCursor()
    cm.replaceRange(text, cur)
    // update unnamed register
    Vim.getRegisterController().getRegister('"').setText(text)
  }
}, true)
```

Deprecated pattern — DO NOT make register methods `async`
------------------------------------------------------
Register methods (`setText`, `pushText`, `toString`, `clear`) must be synchronous. Making them `async` (returning Promises) breaks the plugin because CM6‑Vim expects immediate return values from `toString()` and similar methods.

❌ Wrong (breaks editor)
```typescript
const badRegister = {
  async setText(text) {
    await navigator.clipboard.writeText(text)
  },
  async toString() {
    return await navigator.clipboard.readText()
  }
}
Vim.defineRegister('+', badRegister)
```

✅ Right (synchronous methods, background async work)
```typescript
const goodRegister = {
  text: '',
  setText(text) {
    this.text = text
    navigator.clipboard.writeText(text).catch(() => {})
  },
  toString() {
    navigator.clipboard.readText().then(t => { this.text = t }).catch(() => {})
    return this.text
  }
}
Vim.defineRegister('a', goodRegister)
```
- Use `.catch()` for clipboard API errors
- First paste after external copy may require two attempts

Usage: `"+yy` copies line to system clipboard

## Event Handling Patterns

### Command Logging

```typescript
const cm = getCM(view)

cm.on("vim-command-done", () => {
  const state = cm.state.vim
  console.log({
    mode: state.mode,
    lastCommand: state.lastCommand,
    marks: state.marks,
  })
})
```

### Keypress Analytics

```typescript
const keyStats = {}

cm.on("vim-keypress", (key) => {
  keyStats[key] = (keyStats[key] || 0) + 1
  
  // Report most-used keys
  if (Math.random() < 0.01) {
    console.log('Top keys:', 
      Object.entries(keyStats)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
    )
  }
})
```

## Integration Anti-Patterns

### ❌ Wrong: Vim after other keymaps

```typescript
// WRONG - Vim won't intercept keys properly
new EditorView({
  extensions: [
    basicSetup,
    vim(),  // Too late!
  ]
})
```

### ✅ Correct: Vim first

```typescript
// CORRECT
new EditorView({
  extensions: [
    vim(),      // First
    basicSetup,
  ]
})
```

### ❌ Wrong: Direct CM6 API for Vim state

```typescript
// WRONG - Bypasses Vim state
view.dispatch({
  selection: EditorSelection.single(10)
})
```

### ✅ Correct: Use CM adapter

```typescript
// CORRECT - Maintains Vim state
const cm = getCM(view)
cm.setCursor({ line: 1, ch: 5 })
```

### ❌ Wrong: Mutating Vim state directly

```typescript
// WRONG
const cm = getCM(view)
cm.state.vim.insertMode = false
```

### ✅ Correct: Use Vim API

```typescript
// CORRECT
Vim.exitInsertMode(cm)
```

## Performance Patterns

### Lazy Command Registration

```typescript
const commands = {
  format: () => import('./commands/format'),
  lint: () => import('./commands/lint'),
  // ...
}

Object.entries(commands).forEach(([name, loader]) => {
  Vim.defineEx(name, name[0], async (cm, params) => {
    const { default: handler } = await loader()
    handler(cm, params)
  })
})
```

### Debounced Operations

```typescript
import { debounce } from 'lodash'

const autosave = debounce((content) => {
  saveToBackend(content)
}, 1000)

const cm = getCM(view)
cm.on("change", () => {
  autosave(cm.getValue())
})
```

## Testing Patterns

### Test Custom Ex Command

```typescript
describe('custom format command', () => {
  let view, cm
  
  beforeEach(() => {
    view = new EditorView({
      extensions: [vim()]
    })
    cm = getCM(view)
  })
  
  it('formats code', () => {
    cm.setValue('const x=1')
    Vim.handleKey(cm, ':')
    // Simulate typing 'fmt' and Enter
    // Check formatted output
    expect(cm.getValue()).toBe('const x = 1')
  })
})
```

## Documentation Pattern

When defining custom Vim commands, document them:

```typescript
/**
 * Custom Vim Commands
 * 
 * Ex Commands:
 * - :write, :w - Save current file
 * - :format, :fmt [parser] - Format with prettier
 * - :lint - Run linter
 * 
 * Operators:
 * - gc{motion} - Toggle comments
 * 
 * Motions:
 * - ]f, [f - Next/previous function
 * 
 * Mappings:
 * - jj (insert) - Exit insert mode
 * - <Leader>w - Save file
 * - <Leader>f - Format file
 */
```
