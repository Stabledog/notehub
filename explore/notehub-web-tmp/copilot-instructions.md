# CodeMirror 6 + Vim Mode Evaluation Brief

## Purpose

Create a **minimal local web playground** to evaluate **CodeMirror 6 with Vim mode** purely for **editor behavior**.

This document is intended to be given to **GitHub Copilot inside VS Code** so it can scaffold and iterate without repeated explanation.

The goal is to validate that the editor experience is viable before building any real application.

---

## Explicit Non‑Goals

Do **not** implement:

* GitHub integration
* OAuth or authentication
* Cloudflare Workers / backend
* Routing or frameworks beyond a simple dev server
* Comments, issues, metadata, or workflows
* Styling beyond basic layout

This is **not an app**. It is an editor test harness.

---

## Primary Requirements (Must‑Have)

1. **CodeMirror 6**

   * Use the modern CM6 packages (not CM5)

2. **Vim mode enabled**

   * Normal / Insert / Visual modes
   * Standard motions and operators

3. **`jk → Escape` mapping**

   * In *insert mode only*
   * `j` followed by `k` within a short timeout (≈200–300ms) exits insert mode
   * If timeout expires, literal `j` is inserted
   * Must work at real typing speed
   * Must not depend on the browser `Esc` key

This requirement is **non‑negotiable**.

---

## Secondary Requirements (Nice‑to‑Have)

* Single large editor pane
* Markdown‑friendly configuration (no rendering needed)
* Optional Save button that logs content or stores to `localStorage`
* Keyboard focus stays in editor (browser shortcuts should not interfere)

---

## Environment Constraints

* Local development only
* npm‑based setup is acceptable
* Vite or similarly minimal dev server is preferred
* Plain HTML + JS/TS is fine
* No frameworks required (React, Vue, etc. not needed)

---

## Expected Deliverable

A minimal runnable setup that:

* Starts a local dev server
* Loads a page with CodeMirror 6
* Enables Vim mode
* Demonstrates reliable `jk → Esc` behavior

This is strictly for **hands‑on evaluation** of editor ergonomics.

---

## Guidance to Copilot

* Favor clarity and minimalism over abstraction
* Inline configuration is acceptable
* Avoid unnecessary indirection
* Assume the user is comfortable editing JS/HTML directly

If tradeoffs exist, prioritize **typing feel and Vim correctness** over elegance.

---

## Success Criteria

This experiment is successful if:

* Vim insert/normal mode transitions feel natural
* `jk → Esc` works consistently at speed
* Browser key handling does not interfere

If these are met, the concept is sound.
