# Syntax Highlighting Guide

Complete guide to adding language support and syntax highlighting to CodeMirror 6 + Vim.

## Quick Start

```typescript
import { EditorView, basicSetup } from 'codemirror'
import { vim } from '@replit/codemirror-vim'
import { markdown } from '@codemirror/lang-markdown'

const view = new EditorView({
  extensions: [
    vim(),
    basicSetup,
    markdown(),  // Language support includes syntax highlighting
  ],
  parent: element
})
```

## Overview

CodeMirror 6 separates **language support** (parsing, highlighting structure) from **styling** (colors, fonts). This allows:
- Using any language with any theme
- Creating custom color schemes without touching parsing
- Mixing languages in the same document

## Language Packages

### Official CodeMirror Languages

Install from npm and import:

| Language | Package | Import Statement |
|----------|---------|------------------|
| JavaScript | `@codemirror/lang-javascript` | `import { javascript } from '@codemirror/lang-javascript'` |
| TypeScript | Same as JS | `javascript({ typescript: true })` |
| JSX/TSX | Same as JS | `javascript({ jsx: true, typescript: true })` |
| Python | `@codemirror/lang-python` | `import { python } from '@codemirror/lang-python'` |
| Markdown | `@codemirror/lang-markdown` | `import { markdown } from '@codemirror/lang-markdown'` |
| HTML | `@codemirror/lang-html` | `import { html } from '@codemirror/lang-html'` |
| CSS | `@codemirror/lang-css` | `import { css } from '@codemirror/lang-css'` |
| JSON | `@codemirror/lang-json` | `import { json } from '@codemirror/lang-json'` |
| XML | `@codemirror/lang-xml` | `import { xml } from '@codemirror/lang-xml'` |
| SQL | `@codemirror/lang-sql` | `import { sql } from '@codemirror/lang-sql'` |
| Rust | `@codemirror/lang-rust` | `import { rust } from '@codemirror/lang-rust'` |
| C++ | `@codemirror/lang-cpp` | `import { cpp } from '@codemirror/lang-cpp'` |
| Java | `@codemirror/lang-java` | `import { java } from '@codemirror/lang-java'` |
| PHP | `@codemirror/lang-php` | `import { php } from '@codemirror/lang-php'` |

**Full list**: https://codemirror.net/6/docs/ref/#language

### Installation

```bash
npm install @codemirror/lang-markdown
npm install @codemirror/lang-javascript
# etc.
```

## Custom Syntax Highlighting

### Basic Custom Theme

Define colors for syntax elements:

```typescript
import { syntaxHighlighting, HighlightStyle } from '@codemirror/language'
import { tags } from '@lezer/highlight'

const myHighlight = HighlightStyle.define([
  { tag: tags.keyword, color: "#cf222e", fontWeight: "bold" },
  { tag: tags.string, color: "#0a3069" },
  { tag: tags.comment, color: "#6a737d", fontStyle: "italic" },
  { tag: tags.variableName, color: "#953800" },
  { tag: tags.function(tags.variableName), color: "#8250df" },
])

const view = new EditorView({
  extensions: [
    vim(),
    javascript(),
    syntaxHighlighting(myHighlight),
  ]
})
```

### Common Syntax Tags

From `@lezer/highlight`:

```typescript
import { tags } from '@lezer/highlight'

// Programming languages
tags.keyword        // if, for, class, def, etc.
tags.string         // "strings"
tags.comment        // // comments
tags.variableName   // variable names
tags.function       // function names
tags.typeName       // type names
tags.operator       // +, -, *, etc.
tags.number         // 123, 4.56
tags.bool           // true, false

// Markdown-specific
tags.heading1       // # H1
tags.heading2       // ## H2
tags.heading3       // ### H3
tags.strong         // **bold**
tags.emphasis       // *italic*
tags.link           // [link](url)
tags.monospace      // `code`
tags.strikethrough  // ~~strikethrough~~
tags.quote          // > blockquote
tags.list           // - list items
```

**Complete tag list**: https://lezer.codemirror.net/docs/ref/#highlight.tags

## Markdown Highlighting Patterns

### GitHub-Style Markdown

Perfect for editing GitHub issues, PRs, or wikis:

```typescript
import { EditorView, basicSetup } from 'codemirror'
import { vim } from '@replit/codemirror-vim'
import { markdown } from '@codemirror/lang-markdown'
import { syntaxHighlighting, HighlightStyle } from '@codemirror/language'
import { tags } from '@lezer/highlight'

// GitHub color palette
const githubMarkdown = HighlightStyle.define([
  // Headings (blue, progressively smaller)
  { tag: tags.heading1, 
    fontSize: "1.6em", 
    fontWeight: "bold", 
    color: "#0969da" 
  },
  { tag: tags.heading2, 
    fontSize: "1.4em", 
    fontWeight: "bold", 
    color: "#0969da" 
  },
  { tag: tags.heading3, 
    fontSize: "1.2em", 
    fontWeight: "bold", 
    color: "#0969da" 
  },
  
  // Inline formatting
  { tag: tags.strong, 
    fontWeight: "bold", 
    color: "#24292f" 
  },
  { tag: tags.emphasis, 
    fontStyle: "italic", 
    color: "#24292f" 
  },
  
  // Links (blue, underlined)
  { tag: tags.link, 
    color: "#0969da", 
    textDecoration: "underline" 
  },
  { tag: tags.url, 
    color: "#0969da" 
  },
  
  // Code (red on light gray background)
  { tag: tags.monospace, 
    fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace", 
    backgroundColor: "#f6f8fa",
    padding: "2px 4px",
    borderRadius: "3px",
    color: "#cf222e"
  },
  
  // Strikethrough
  { tag: tags.strikethrough, 
    textDecoration: "line-through", 
    color: "#656d76" 
  },
  
  // Blockquotes
  { tag: tags.quote, 
    color: "#656d76", 
    fontStyle: "italic" 
  },
  
  // Lists
  { tag: tags.list, 
    color: "#24292f" 
  },
  
  // Horizontal rules
  { tag: tags.contentSeparator, 
    color: "#d0d7de", 
    fontWeight: "bold" 
  },
])

const view = new EditorView({
  doc: '# Issue Title\n\n## Description\n\nEdit with **Vim**!',
  extensions: [
    vim(),
    basicSetup,
    markdown(),
    syntaxHighlighting(githubMarkdown),
    EditorView.lineWrapping,  // Important for prose editing
  ],
  parent: document.getElementById('editor')
})
```

### Minimal Markdown Highlighting

For simpler use cases:

```typescript
const simpleMarkdown = HighlightStyle.define([
  { tag: tags.heading1, fontSize: "2em", fontWeight: "bold" },
  { tag: tags.heading2, fontSize: "1.5em", fontWeight: "bold" },
  { tag: tags.strong, fontWeight: "bold" },
  { tag: tags.emphasis, fontStyle: "italic" },
  { tag: tags.monospace, fontFamily: "monospace", backgroundColor: "#eee" },
])
```

## Complete Working Example

Full markdown editor with Vim and syntax highlighting:

```typescript
import { EditorView, basicSetup } from 'codemirror'
import { vim, getCM, Vim } from '@replit/codemirror-vim'
import { markdown } from '@codemirror/lang-markdown'
import { syntaxHighlighting, HighlightStyle } from '@codemirror/language'
import { tags } from '@lezer/highlight'

// Define highlighting
const markdownHighlight = HighlightStyle.define([
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
])

// Vim customizations
Vim.map("jk", "<Esc>", "insert")  // jk to exit insert mode

// Create editor
const view = new EditorView({
  doc: '# My Document\n\nEdit with **Vim** commands!',
  extensions: [
    vim(),                              // Vim bindings (FIRST)
    basicSetup,                         // Editor features
    markdown(),                         // Markdown language support
    syntaxHighlighting(markdownHighlight),  // Custom colors
    EditorView.lineWrapping,            // Wrap long lines
  ],
  parent: document.getElementById('editor')
})

// Optional: Mode indicator
const statusBar = document.getElementById('status')
const cm = getCM(view)
cm.on("vim-mode-change", ({ mode }) => {
  const modeText = {
    insert: "-- INSERT --",
    normal: "",
    visual: "-- VISUAL --",
    replace: "-- REPLACE --"
  }[mode] || ""
  statusBar.textContent = modeText
})

// Auto-focus
view.focus()
```

## Language + Vim Compatibility

All CodeMirror language packages work seamlessly with Vim mode:

```typescript
// JavaScript + Vim
const jsView = new EditorView({
  extensions: [vim(), javascript()],
})

// Python + Vim
const pyView = new EditorView({
  extensions: [vim(), python()],
})

// HTML + Vim
const htmlView = new EditorView({
  extensions: [vim(), html()],
})
```

**Key rule**: Always place `vim()` **before** language extensions in the array.

## GitHub Markdown Specifics

CodeMirror's `@codemirror/lang-markdown` supports:

- ✅ Headings (`#` through `######`)
- ✅ **Bold** and *italic*
- ✅ `Inline code`
- ✅ Code blocks with language hints
- ✅ Links and URLs
- ✅ Lists (ordered and unordered)
- ✅ Blockquotes
- ✅ Horizontal rules (`---`)
- ✅ ~~Strikethrough~~
- ⚠️ Tables (basic support)
- ⚠️ Task lists (requires additional extension)
- ⚠️ Emoji (not parsed by default)

For full GitHub-flavored markdown, consider additional extensions or custom parsing.

## Troubleshooting

### Colors not showing?

Make sure you're applying the highlighting:
```typescript
syntaxHighlighting(myHighlight)  // Don't forget this!
```

### Headings not sizing?

Font sizes in highlight styles only work if your CSS doesn't override them. Use:
```css
.cm-line { font-size: inherit; }
```

### Monospace backgrounds not showing?

Background colors in highlight styles may need `display: inline-block`:
```typescript
{ tag: tags.monospace, 
  backgroundColor: "#f6f8fa",
  display: "inline-block",  // May help
  padding: "2px 4px"
}
```

Or handle in CSS:
```css
.cm-monospace {
  background: #f6f8fa;
  padding: 2px 4px;
  border-radius: 3px;
}
```

## See Also

- [patterns.md](./patterns.md) - Language setup patterns
- [examples.md](./examples.md) - Working code examples
- [CodeMirror Language Reference](https://codemirror.net/6/docs/ref/#language)
- [Lezer Highlight Tags](https://lezer.codemirror.net/docs/ref/#highlight.tags)
