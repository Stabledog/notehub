# Troubleshooting Guide

Quick solutions to common issues when working with CodeMirror Vim mode.

## Setup Issues

### ❌ Vim keys not working at all

**Symptoms**: Pressing `j`, `k`, `:`, etc. just types those characters

**Solutions**:
1. Ensure `vim()` is in extensions array
   ```typescript
   extensions: [vim(), ...]
   ```

2. Check `vim()` comes **before** other keymap extensions
   ```typescript
   // WRONG
   extensions: [basicSetup, vim()]
   
   // CORRECT
   extensions: [vim(), basicSetup]
   ```

3. Verify import is correct
   ```typescript
   import { vim } from '@replit/codemirror-vim'
   ```

---

### ❌ Visual mode cursor not showing

**Symptoms**: Visual mode selection is invisible or looks wrong

**Solution**: Include `drawSelection` plugin (automatic with `basicSetup`)
```typescript
import { drawSelection } from '@codemirror/view'

extensions: [
  vim(),
  drawSelection(),
  // ... other extensions
]
```

---

### ❌ Can't access CM5 API

**Symptoms**: `view.getValue()` doesn't exist, `view` doesn't have CM5 methods

**Solution**: Use `getCM(view)` to get CM5-compatible wrapper
```typescript
import { getCM } from '@replit/codemirror-vim'

const cm = getCM(view)  // Now has CM5 methods
cm.getValue()
cm.setCursor({ line: 0, ch: 0 })
```

---

## Key Mapping Issues

### ❌ Custom map not working

**Symptoms**: Key mapping doesn't trigger

**Checklist**:
1. Context is correct (`"normal"`, `"insert"`, `"visual"`)
   ```typescript
   Vim.map("jj", "<Esc>", "insert")  // Only works in insert mode
   ```

2. Mapping is registered before first use
   ```typescript
   // Register BEFORE creating view
   Vim.map("jj", "<Esc>", "insert")
   
   const view = new EditorView({ extensions: [vim()] })
   ```

3. No conflicting mappings
   ```typescript
   // Check what's mapped
   console.log(Vim._mapCommand)  // Debug only
   ```

---

### ❌ Leader key not working

**Symptoms**: `<Leader>` mappings don't trigger

**Solution**: Map your leader key first
```typescript
// Default leader is backslash, map to Space if desired
Vim.map("<Space>", "<Leader>", "normal")

// Then use <Leader> in other maps
Vim.map("<Leader>w", ":write<CR>", "normal")
```

---

### ❌ Recursive mapping issue

**Symptoms**: Infinite loop or unexpected behavior

**Solution**: Use `noremap` instead of `map`
```typescript
// BAD - can recurse
Vim.map("j", "gj")
Vim.map("gj", "j")  // Infinite loop!

// GOOD - no recursion
Vim.noremap("j", "gj")
```

---

## Ex Command Issues

### ❌ Ex command not recognized

**Symptoms**: `:mycommand` shows "Not an editor command"

**Checklist**:
1. Command is defined
   ```typescript
   Vim.defineEx("mycommand", "mc", (cm, params) => { ... })
   ```

2. Name matches (case-sensitive)
   ```typescript
   Vim.defineEx("write", "w", ...)  // :write or :w
   ```

3. Defined before first use

---

### ❌ Ex command params are undefined

**Symptoms**: `params.args` is empty or wrong

**Solution**: Check how Ex command parses arguments
```typescript
Vim.defineEx("test", "t", (cm, params) => {
  console.log("Full string:", params.argString)  // "arg1 arg2 arg3"
  console.log("Array:", params.args)             // ["arg1", "arg2", "arg3"]
  console.log("Range:", params.line, params.lineEnd)  // If range given
})
```

Usage: `:5,10test arg1 arg2`
- `params.line` = 4 (0-indexed)
- `params.lineEnd` = 9
- `params.argString` = "arg1 arg2"
- `params.args` = ["arg1", "arg2"]

---

### ❌ Async Ex command doesn't work

**Symptoms**: Command completes before async operation finishes

**Solution**: Use `async/await` correctly
```typescript
Vim.defineEx("fetch", "f", async (cm, params) => {
  try {
    const response = await fetch(params.args[0])
    const text = await response.text()
    cm.setValue(text)
  } catch (e) {
    console.error("Fetch failed:", e)
  }
})
```

---

## Custom Operator/Motion Issues

### ❌ Operator doesn't apply to text

**Symptoms**: Operator executes but text unchanged

**Solutions**:
1. Ensure you're modifying via CM API
   ```typescript
   Vim.defineOperator("uppercase", (cm, operatorArgs, ranges) => {
     ranges.forEach(range => {
       const text = cm.getRange(range.anchor, range.head)
       // MUST use replaceRange to update
       cm.replaceRange(text.toUpperCase(), range.anchor, range.head)
     })
   })
   ```

2. Return new cursor position if needed
   ```typescript
   return ranges[0].head  // Position cursor after operation
   ```

---

### ❌ Motion doesn't move cursor

**Symptoms**: Motion command does nothing

**Solution**: Return new position from motion function
```typescript
Vim.defineMotion("nextBlank", (cm, head, motionArgs) => {
  let line = head.line + 1
  while (line < cm.lastLine()) {
    if (cm.getLine(line).trim() === '') {
      return { line, ch: 0 }  // MUST return position
    }
    line++
  }
  return head  // Return original if not found
})
```

---

### ❌ Operator + motion composition fails

**Symptoms**: `dw`, `cw`, etc. don't work with custom motion

**Solution**: Map motion correctly
```typescript
// Define motion
Vim.defineMotion("nextSection", (cm, head, args) => { ... })

// Map to key as motion type
Vim.mapCommand("]]", "motion", "nextSection")

// Now works: d]], y]], v]], etc.
```

---

## Mode Issues

### ❌ Can't exit insert mode

**Symptoms**: Esc doesn't work

**Solutions**:
1. Check for conflicting mappings
   ```typescript
   // If you remapped Esc, add alternative
   Vim.map("jj", "<Esc>", "insert")
   ```

2. Force exit programmatically
   ```typescript
   Vim.exitInsertMode(cm)
   ```

---

### ❌ Mode changes not detected

**Symptoms**: Mode change events don't fire

**Solution**: Ensure event listener is on CM adapter, not view
```typescript
// WRONG
view.on("vim-mode-change", ...)  // Not a method

// CORRECT
const cm = getCM(view)
cm.on("vim-mode-change", (modeObj) => { ... })
```

---

### ❌ Visual mode behaves oddly

**Symptoms**: Selection is wrong after visual mode operations

**Solution**: Check if you need `drawSelection` plugin
```typescript
import { drawSelection } from '@codemirror/view'

extensions: [vim(), drawSelection()]
```

---

## State Management Issues

### ❌ Vim state out of sync

**Symptoms**: Vim thinks cursor is in wrong position

**Solution**: Always use CM adapter for state changes
```typescript
// WRONG - bypasses Vim state
view.dispatch({
  selection: EditorSelection.single(10)
})

// CORRECT - updates Vim state
const cm = getCM(view)
cm.setCursor({ line: 1, ch: 5 })
```

---

### ❌ Registers not working

**Symptoms**: Yank/paste doesn't work with named registers

**Solution**: Use register prefix
```typescript
// In editor:
"ayy    // Yank line to register 'a'
"ap     // Paste from register 'a'

// Programmatically:
const rc = Vim.getRegisterController()
rc.getRegister('a').setText("hello")
```

Note: CM6‑Vim already pre‑defines the `+` and `*` registers with system clipboard integration. Attempting to call `Vim.defineRegister('+', ...)` will throw an error like `Register already defined +` and should be avoided. Use the register prefix `"+` (or `"*`) to interact with the system clipboard.

---

### ❌ Editor completely broken after defining custom register

**Symptoms**: Editor blank/frozen after `Vim.defineRegister()`

**Cause**: Register methods marked as `async` - Vim requires synchronous functions

**Solution**: Remove `async/await`, use fire-and-forget pattern
```typescript
// ❌ WRONG - breaks editor
const badRegister = {
  async setText(text) {
    await navigator.clipboard.writeText(text)
  },
  async toString() {
    return await navigator.clipboard.readText()
  }
}

// ✅ CORRECT - synchronous with background async
const goodRegister = {
  text: '',
  setText(text) {
    this.text = text
    navigator.clipboard.writeText(text).catch(err => {
      console.error('Clipboard error:', err)
    })
  },
  toString() {
    navigator.clipboard.readText().then(clip => {
      this.text = clip
    }).catch(err => {
      console.error('Clipboard error:', err)
    })
    return this.text  // Must return string immediately
  }
}

---

### ❌ Clipboard operations silently fail (NotAllowedError / Document not focused)

**Symptoms**: `navigator.clipboard.readText()` or `writeText()` throws `NotAllowedError` or returns stale data; paste from system clipboard doesn't work.

**Cause**: Browsers often require a user gesture and focused document for clipboard access. Clipboard permissions are granted per origin and may be ephemeral.

**Solutions**:

1. Ensure the page is focused before invoking clipboard APIs (click the page or the editor).
2. Perform reads during a user gesture such as a `keydown` handler (see KB examples). Browsers are more permissive for clipboard actions triggered by explicit user events.
3. Provide an execCommand fallback for writes (textarea + `document.execCommand('copy')`) for older/blocked contexts.
4. Check the Permissions API to inspect current clipboard permission state.

Example: perform paste on user keydown (grants read permission in many browsers)

```javascript
document.addEventListener('keydown', async (e) => {
  if (e.key !== 'p') return
  const text = await navigator.clipboard.readText().catch(() => '')
  if (text) {
    const cm = getCM(view)
    cm.replaceRange(text, cm.getCursor())
  }
}, true)
```
```

---

## Performance Issues

### ❌ Editor is slow with Vim enabled

**Rare but possible solutions**:

1. Disable unused event listeners
   ```typescript
   // Don't listen to vim-keypress unless needed
   // It fires on EVERY key
   ```

2. Debounce expensive operations
   ```typescript
   import { debounce } from 'lodash'
   
   const autosave = debounce((content) => {
     saveToBackend(content)
   }, 1000)
   
   cm.on("change", () => autosave(cm.getValue()))
   ```

3. Lazy-load Vim mode
   ```typescript
   let vimLoaded = false
   async function enableVim() {
     if (!vimLoaded) {
       const { vim } = await import('@replit/codemirror-vim')
       view.dispatch({
         effects: StateEffect.appendConfig.of(vim())
       })
       vimLoaded = true
     }
   }
   ```

---

## Integration Issues

### ❌ React re-renders break Vim state

**Symptoms**: Vim resets on component re-render

**Solution**: Create view outside render cycle
```typescript
function Editor() {
  const editorRef = useRef(null)
  const viewRef = useRef(null)
  
  useEffect(() => {
    if (!viewRef.current) {
      viewRef.current = new EditorView({
        extensions: [vim(), basicSetup],
        parent: editorRef.current
      })
    }
    
    return () => {
      viewRef.current?.destroy()
      viewRef.current = null
    }
  }, [])  // Empty deps - only run once
  
  return <div ref={editorRef} />
}
```

---

### ❌ TypeScript errors with Vim API

**Symptoms**: TypeScript can't find types for Vim methods

**Solution**: Import types or use type assertions
```typescript
import { Vim } from '@replit/codemirror-vim'

// Types should be included, but if not:
(Vim as any).map("jj", "<Esc>", "insert")

// Or check @types/codemirror is installed
```

---

## Debugging Techniques

### Enable verbose logging

```typescript
const cm = getCM(view)

// Log all keys
cm.on("vim-keypress", (key) => console.log("Key:", key))

// Log commands
cm.on("vim-command-done", () => console.log("Command done"))

// Log mode changes
cm.on("vim-mode-change", (m) => console.log("Mode:", m))
```

### Inspect Vim state

```typescript
const cm = getCM(view)

// Current mode
console.log(cm.state.vim?.mode)

// Full state
console.log(cm.state.vim)

// Global Vim state
console.log(Vim._getVimGlobalState_())  // Undocumented
```

### Test commands manually

```typescript
const cm = getCM(view)

// Simulate key sequence
Vim.handleKey(cm, "d")
Vim.handleKey(cm, "d")

// Check result
console.log(cm.getValue())
```

### Verify registration

```typescript
// After defining ex command
Vim.defineEx("test", "t", (cm) => { console.log("TEST") })

// Test it
const cm = getCM(view)
Vim.handleKey(cm, ":")
// Would need to simulate typing "test<CR>"
// Or test via internal state
```

---

## Getting Help

1. **Check CM5 Vim docs**: [cm5/doc/manual.html#vimapi](../cm5/doc/manual.html) (lines 3532-3762)
2. **Review examples**: [examples.md](./examples.md)
3. **Check FAQ**: [faq.md](./faq.md)
4. **GitHub issues**: [replit/codemirror-vim](https://github.com/replit/codemirror-vim/issues)
5. **CM6 forums**: [discuss.codemirror.net](https://discuss.codemirror.net)

## Quick Reference

| Issue Type | First Thing to Check |
|------------|---------------------|
| Keys not working | `vim()` before other extensions |
| Visual mode cursor | `drawSelection` plugin |
| Can't access CM5 API | Use `getCM(view)` |
| Mapping not working | Context ("insert"/"normal"/"visual") |
| Ex command not found | Command defined + name matches |
| Operator no effect | Using `cm.replaceRange()` |
| Motion no effect | Returning position object |
| Mode stuck | `Vim.exitInsertMode(cm)` |
| State out of sync | Use CM adapter not view.dispatch |
| React re-renders | useRef + useEffect once |
