import { EditorView, keymap } from "@codemirror/view";
import { EditorState } from "@codemirror/state";
import { defaultKeymap, indentWithTab } from "@codemirror/commands";
import { markdown } from "@codemirror/lang-markdown";
import { Vim, vim } from "@replit/codemirror-vim";

// Enhanced theme for better visual mode visibility
const vimTheme = EditorView.theme({
  ".cm-selectionMatch": {
    backgroundColor: "#99ccff !important"
  },
  ".cm-line ::selection": {
    backgroundColor: "#4a90e2 !important",
    color: "inherit !important"
  },
  ".cm-line::selection": {
    backgroundColor: "#4a90e2 !important",
    color: "inherit !important"
  },
  "::selection": {
    backgroundColor: "#4a90e2 !important",
    color: "inherit !important"
  }
});

// Initial content for testing
const initialContent = `# CodeMirror 6 + Vim Mode Test

## Testing jk → Esc

1. Press 'i' to enter insert mode
2. Type 'j' then 'k' quickly (within ~250ms)
3. You should exit to normal mode
4. If you pause after 'j', it inserts literally

## Vim Commands to Test

- hjkl navigation (normal mode)
- w, b, e word motions
- dd, yy, p delete/yank/paste
- / search
- Visual mode with v

Try editing this text!
`;

// Set up the jk → Esc mapping
// This needs to be done via Vim.map() which handles timing
Vim.map("jk", "<Esc>", "insert");

// Create the editor
const state = EditorState.create({
  doc: initialContent,
  extensions: [
    vim(),
    vimTheme,
    markdown(),
    keymap.of([...defaultKeymap, indentWithTab]),
    EditorView.lineWrapping,
    // Prevent browser from stealing Tab key
    EditorView.domEventHandlers({
      keydown(event, view) {
        if (event.key === "Tab") {
          event.preventDefault();
          return false; // Let CodeMirror/Vim handle it after preventing browser default
        }
        return false;
      },
    }),
  ],
});

const view = new EditorView({
  state,
  parent: document.getElementById("editor-container"),
});

// Auto-focus the editor
view.focus();

// Expose to window for debugging
window.view = view;
window.Vim = Vim;

// Save button handler
document.getElementById("save-btn").addEventListener("click", () => {
  const content = view.state.doc.toString();
  console.log("Editor content:", content);
  
  // Also save to localStorage for persistence across reloads
  localStorage.setItem("codemirror-content", content);
  console.log("Saved to localStorage");
  
  alert("Content logged to console and saved to localStorage");
});

// Load from localStorage if available
const savedContent = localStorage.getItem("codemirror-content");
if (savedContent) {
  console.log("Found saved content in localStorage");
}

// Log Vim mode changes for debugging
Vim.defineOption("showmode", true, "boolean");
