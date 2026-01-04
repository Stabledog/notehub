# Examples Index

Locate working code examples across the documentation.

## CM6-Vim Examples

### Basic Setup
**File**: [cm6-vim/README.md](../cm6-vim/README.md)

```typescript
import { EditorView, basicSetup } from 'codemirror'
import { vim } from "@replit/codemirror-vim"

let view = new EditorView({
  doc: "",
  extensions: [
    vim(),        // Include before other keymaps
    basicSetup,   // Default keymaps for insert mode
  ],
  parent: document.querySelector('#editor'),
})
```

### Using CM5 Vim API
**File**: [cm6-vim/README.md](../cm6-vim/README.md)

```typescript
import { Vim, getCM } from "@replit/codemirror-vim"

let cm = getCM(view)
Vim.exitInsertMode(cm)
Vim.handleKey(cm, "<Esc>")
```

### Custom Ex Commands
**File**: [cm6-vim/README.md](../cm6-vim/README.md)

```typescript
Vim.defineEx('write', 'w', function() {
  // save the file
})
```

### Key Mapping
**File**: [cm6-vim/README.md](../cm6-vim/README.md)

```typescript
// Insert mode
Vim.map("jj", "<Esc>", "insert")

// Normal mode
Vim.map("Y", "y$")
```

### Custom Operators
**File**: [cm6-vim/README.md](../cm6-vim/README.md)

```typescript
Vim.defineOperator("hardWrap", function(cm, operatorArgs, ranges, oldAnchor, newHead) {
  // make changes and return new cursor position
})

// Map to keys
defaultKeymap.push({ keys: 'gq', type: 'operator', operator: 'hardWrap' })
```

## CM5 Demo Files

Located in [cm5/demo/](../cm5/demo/)

### Vim Demo
**File**: [cm5/demo/vim.html](../cm5/demo/vim.html)

Shows classic CM5 Vim integration. **Note**: CM5 demo uses old API, but Vim behavior is authoritative.

### Other Useful Demos

| Feature | File |
|---------|------|
| Key mapping | [cm5/demo/emacs.html](../cm5/demo/emacs.html) |
| Search | [cm5/demo/search.html](../cm5/demo/search.html) |
| Completion | [cm5/demo/complete.html](../cm5/demo/complete.html) |
| Markers | [cm5/demo/marker.html](../cm5/demo/marker.html) |

## CM6 Demo Files

Located in [cm6/demo/](../cm6/demo/)

**Note**: CM6 folder appears to mirror CM5 structure. Check online CM6 docs at codemirror.net/6 for canonical examples.

## Common Patterns

### Pattern: Initialize CM6 with Vim

```typescript
import { EditorView, basicSetup } from 'codemirror'
import { vim } from '@replit/codemirror-vim'
import { javascript } from '@codemirror/lang-javascript'

const view = new EditorView({
  doc: 'const x = 1',
  extensions: [
    vim(),          // First
    basicSetup,     // Then base functionality
    javascript(),   // Language support
  ],
  parent: element
})
```

### Pattern: Access Vim API

```typescript
import { getCM, Vim } from '@replit/codemirror-vim'

const cm = getCM(view)

// Now use CM5-style API
cm.getValue()
cm.setCursor({ line: 0, ch: 0 })
```

### Pattern: Define Custom Ex Command

```typescript
Vim.defineEx("save", "s", (cm, params) => {
  const content = cm.getValue()
  // params.args - array of arguments
  // params.argString - full argument string
  // params.line, params.lineEnd - range if specified
  saveToBackend(content, params.args[0])
})
```

Usage: `:save myfile.txt` or `:s myfile.txt`

### Pattern: Custom Motion

```typescript
Vim.defineMotion("nextFunction", (cm, head, motionArgs) => {
  const doc = cm.getDoc()
  let line = head.line
  
  // Search for next function definition
  while (line < doc.lineCount()) {
    if (/^function/.test(doc.getLine(line))) {
      return { line: line, ch: 0 }
    }
    line++
  }
  
  return head // No match, stay in place
})

// Map to ]f
Vim.mapCommand("]f", "motion", "nextFunction")
```

### Pattern: Custom Operator with Range

```typescript
Vim.defineOperator("indent", (cm, operatorArgs, ranges) => {
  ranges.forEach(range => {
    const from = range.anchor
    const to = range.head
    
    // Indent each line in range
    for (let line = from.line; line <= to.line; line++) {
      const lineText = cm.getLine(line)
      cm.replaceRange('  ' + lineText, 
        { line, ch: 0 }, 
        { line, ch: lineText.length }
      )
    }
  })
  
  // Return cursor position
  return ranges[0].head
})

// Use as: 2>j (indent 2 lines down)
```

### Pattern: React to Mode Changes

```typescript
const cm = getCM(view)

cm.on("vim-mode-change", (modeObj) => {
  const { mode, subMode } = modeObj
  
  if (mode === "insert") {
    statusBar.textContent = "-- INSERT --"
  } else if (mode === "visual") {
    const modifier = subMode === "linewise" ? " LINE" : 
                     subMode === "blockwise" ? " BLOCK" : ""
    statusBar.textContent = "-- VISUAL" + modifier + " --"
  } else {
    statusBar.textContent = ""
  }
})
```

### Pattern: Conditional Key Mapping

```typescript
// Map <Leader>g to different actions based on mode
Vim.map("<Leader>g", ":Git status<CR>", "normal")
Vim.map("<Leader>g", "<Esc>:Git status<CR>", "insert")
```

### Pattern: Markdown Editor with Syntax Highlighting

```typescript
import { EditorView, basicSetup } from 'codemirror'
import { vim, getCM } from '@replit/codemirror-vim'
import { markdown } from '@codemirror/lang-markdown'
import { syntaxHighlighting, HighlightStyle } from '@codemirror/language'
import { tags } from '@lezer/highlight'

// GitHub-style markdown highlighting
const markdownHighlight = HighlightStyle.define([
  { tag: tags.heading1, fontSize: "1.6em", fontWeight: "bold", color: "#0969da" },
  { tag: tags.heading2, fontSize: "1.4em", fontWeight: "bold", color: "#0969da" },
  { tag: tags.heading3, fontSize: "1.2em", fontWeight: "bold", color: "#0969da" },
  { tag: tags.strong, fontWeight: "bold" },
  { tag: tags.emphasis, fontStyle: "italic" },
  { tag: tags.link, color: "#0969da", textDecoration: "underline" },
  { tag: tags.monospace, 
    fontFamily: "monospace", 
    backgroundColor: "#f6f8fa",
    color: "#cf222e"
  },
])

const view = new EditorView({
  doc: '# GitHub Issue\n\n## Description\n\nEdit with **Vim** commands!',
  extensions: [
    vim(),
    basicSetup,
    markdown(),
    syntaxHighlighting(markdownHighlight),
    EditorView.lineWrapping,
  ],
  parent: document.getElementById('editor')
})

// Set up mode indicator
const statusBar = document.getElementById('status')
const cm = getCM(view)
cm.on("vim-mode-change", ({ mode }) => {
  statusBar.textContent = mode === "insert" ? "-- INSERT --" : ""
})
```

### Pattern: Option Toggle

```typescript
Vim.defineEx("togglenumber", "tn", (cm) => {
  const current = Vim.getOption("number", cm)
  Vim.setOption("number", !current, cm)
})
```

## Integration Checklist

When integrating Vim mode:

1. ✓ Import `vim` extension
2. ✓ Place `vim()` before other keymap extensions
3. ✓ Include `basicSetup` or equivalent for insert mode
4. ✓ Use `getCM(view)` to access CM5 API
5. ✓ Define custom commands/operators as needed
6. ✓ Set up event listeners for mode changes
7. ✓ Consider adding visual mode cursor styling

## Testing Snippets

### Test Vim is Working
```typescript
const cm = getCM(view)
Vim.handleKey(cm, "i")  // Enter insert mode
Vim.handleKey(cm, "H")
Vim.handleKey(cm, "i")
Vim.handleKey(cm, "<Esc>")  // Back to normal
```

### Test Custom Command
```typescript
Vim.defineEx("test", "t", (cm) => {
  console.log("Test command executed!")
})

// Then in editor: :test or :t
```

## Dev Environment

**File**: [cm6-vim/dev/](../cm6-vim/dev/)

Check this directory for development/testing setups used by the CM6-Vim maintainers.
