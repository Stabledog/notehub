# LLM Quick Start Guide

**For AI assistants**: Start here to quickly navigate this knowledgebase.

## What This Repo Contains

Three upstream documentation trees for CodeMirror:
- **cm5/** - Legacy CodeMirror 5 (reference only)
- **cm6/** - Modern CodeMirror 6 (active framework)  
- **cm6-vim/** - Vim mode for CM6 (@replit/codemirror-vim)

## The Key Insight

```
CM6 (editor framework)
  ↓ uses
CM6-Vim (vim extension)
  ↓ exposes
CM5 Vim API (for compatibility)
```

**Rule**: CM6-Vim implements Vim for CM6 but exposes the CM5 Vim API surface.

## Answering Questions - Decision Tree

```
User asks about...

├─ "How do I add Vim to CM6?"
│  → [examples.md](./examples.md#basic-setup)
│
├─ "How do I map keys / create ex commands?"
│  → [vim-mode.md](./vim-mode.md) for API
│  → [examples.md](./examples.md) for code samples
│
├─ "How does Vim mode work internally?"
│  → [architecture.md](./architecture.md)
│  → [diagrams.md](./diagrams.md)
│
├─ "My Vim setup isn't working"
│  → [troubleshooting.md](./troubleshooting.md)
│
├─ "What Vim features are supported?"
│  → [vim-mode.md](./vim-mode.md) for API list
│  → [faq.md](./faq.md#q-are-all-cm5-vim-features-supported)
│
├─ "How do I add syntax highlighting / language support?"
│  → [SYNTAX-HIGHLIGHTING.md](./SYNTAX-HIGHLIGHTING.md) for complete guide
│  → [patterns.md](./patterns.md#language-support--syntax-highlighting) for quick patterns
│
└─ "Show me examples of X"
   → [examples.md](./examples.md)
   → [patterns.md](./patterns.md)
```

## Most Important Files

| File | When to Use |
|------|-------------|
| [vim-mode.md](./vim-mode.md) | Complete Vim API reference |
| [examples.md](./examples.md) | Need working code |
| [SYNTAX-HIGHLIGHTING.md](./SYNTAX-HIGHLIGHTING.md) | Language support & syntax highlighting |
| [architecture.md](./architecture.md) | Understanding relationships |
| [troubleshooting.md](./troubleshooting.md) | Something's broken |
| [faq.md](./faq.md) | Quick questions |

## Upstream Source Locations

| Info Needed | File Path |
|-------------|-----------|
| CM5 Vim API docs | `cm5/doc/manual.html` lines 3532-3762 |
| CM5 full manual | `cm5/doc/manual.html` |
| CM6 manual | `cm6/doc/manual.html` |
| CM6-Vim README | `cm6-vim/README.md` |
| CM6-Vim implementation | `cm6-vim/src/index.ts` |
| CM5 adapter | `cm6-vim/src/cm_adapter.ts` |
| Vim logic | `cm6-vim/src/vim.js` |

## Common Patterns to Reference

### Basic Setup
```typescript
import { EditorView, basicSetup } from 'codemirror'
import { vim } from '@replit/codemirror-vim'

const view = new EditorView({
  extensions: [vim(), basicSetup]  // vim() FIRST
})
```

### Access CM5 API
```typescript
import { getCM } from '@replit/codemirror-vim'
const cm = getCM(view)
```

### Custom Ex Command
```typescript
Vim.defineEx("name", "n", (cm, params) => { ... })
```

### Key Mapping
```typescript
Vim.map("jj", "<Esc>", "insert")
```

## Answering Strategy

1. **Identify the layer**: Is this CM6, CM6-Vim, or Vim API question?
2. **Find the pattern**: Check [patterns.md](./patterns.md) or [examples.md](./examples.md)
3. **Reference the source**: Point to specific files and line numbers
4. **Provide context**: Explain why it works this way (using [architecture.md](./architecture.md))

## Quick Checks

Before answering, verify:
- ✓ Am I confusing CM5 and CM6? (They're different editors)
- ✓ Am I using CM5 Vim docs correctly? (They're the API reference)
- ✓ Did I mention `getCM(view)` when needed? (Bridge to CM5 API)
- ✓ Is `vim()` extension placed first? (Common setup issue)

## Response Templates

### For "How do I..." questions:
1. Quick answer with code
2. Link to relevant section in [vim-mode.md](./vim-mode.md)
3. Point to full example in [examples.md](./examples.md)
4. Note any gotchas from [troubleshooting.md](./troubleshooting.md)

### For "Why doesn't..." questions:
1. Check [troubleshooting.md](./troubleshooting.md) first
2. Verify setup pattern from [examples.md](./examples.md)
3. Explain architecture if needed from [architecture.md](./architecture.md)

### For "What's the difference..." questions:
1. Use [architecture.md](./architecture.md) for layer differences
2. Use [api-reference.md](./api-reference.md) for API comparison
3. Show decision tree from [diagrams.md](./diagrams.md)

## File Priority by Question Type

| Question Type | Primary File | Secondary Files |
|---------------|--------------|-----------------|
| API reference | vim-mode.md | api-reference.md |
| How-to | examples.md | patterns.md |
| Debugging | troubleshooting.md | faq.md |
| Architecture | architecture.md | diagrams.md |
| Best practices | patterns.md | examples.md |

## Key Concepts to Emphasize

1. **CM6 vs CM5**: Different editors, don't mix APIs
2. **Vim API compatibility**: CM5 API is the reference
3. **Extension ordering**: `vim()` must be first
4. **Two APIs**: Use CM6 API for editor, CM5 API (via getCM) for Vim
5. **Adapter pattern**: CM6-Vim bridges CM6 and CM5 Vim API

## Markdown Link Conventions

When referencing files:
- Within kb: `[vim-mode.md](./vim-mode.md)`
- To upstream: `[cm5/doc/manual.html](../cm5/doc/manual.html)`
- To sections: `[API](./vim-mode.md#vim-api)`
- To lines: `[cm5 vim api](../cm5/doc/manual.html)` (line 3532)

## Brevity Tips

- Users want answers, not prose
- Code > explanation (when possible)
- Link to full docs rather than repeating them
- Use tables and lists over paragraphs
- Mermaid diagrams for complex relationships

## This Knowledgebase Is For

✅ Helping users integrate and customize CM6 Vim mode
✅ Debugging Vim-related issues
✅ Understanding architecture and relationships
✅ Finding API documentation and examples

❌ Teaching basic Vim usage (assume user knows Vim)
❌ Rewriting upstream documentation
❌ Non-Vim CodeMirror questions (point to CM6 docs)
