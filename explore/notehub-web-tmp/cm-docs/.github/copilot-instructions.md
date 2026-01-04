# Copilot Instructions for This Repository

This repo contains canonical reference sources for CodeMirror 6, CodeMirror 5,
and the CM6 Vim mode implementation. Another LLM should follow these rules:

## What These Sources Are For
- **CM6 core docs** (codemirror/codemirror) explain extensions, state, view,
  transactions, and keymaps — the parts required to integrate Vim mode.
- **CM6 Vim mode** (@replit/codemirror-vim) is the actual implementation used
  in modern CodeMirror. It exposes a compatibility layer that mirrors the CM5
  Vim API.
- **CM5 docs** (codemirror/codemirror5) remain authoritative for Vim behavior,
  motions, operators, text objects, and custom command APIs.

## How to Use These Sources
- Treat CM6 as the editor framework.
- Treat @replit/codemirror-vim as the CM6 Vim binding.
- Treat CM5 Vim docs as the behavioral and API reference.
- When answering questions, combine these three layers into a coherent model.

## What Not To Do
- Do not rewrite or duplicate upstream docs.
- Do not assume CM6 Vim mode behaves differently unless explicitly documented.
- Do not mix CM5 editor APIs with CM6 editor APIs; only the Vim API is shared.

