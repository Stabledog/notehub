import { EditorView, keymap, drawSelection } from "@codemirror/view";
import { EditorState } from "@codemirror/state";
import { defaultKeymap, indentWithTab } from "@codemirror/commands";
import { markdown } from "@codemirror/lang-markdown";
import { Vim, vim, getCM } from "@replit/codemirror-vim";

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

// Make plain p/P use the system clipboard (+ register) so external
// copies paste into the editor without needing the register prefix
Vim.map('p', '+p', 'normal');
Vim.map('P', '+P', 'normal');
Vim.map('p', '+p', 'visual');
Vim.map('P', '+P', 'visual');
// Create the editor first, then set up clipboard after we have the cm instance
const state = EditorState.create({
  doc: initialContent,
  extensions: [
    vim(),
    drawSelection(),
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

// Set up clipboard sync using Vim events
const cm = getCM(view);

// Better approach: Intercept the register controller's pushText method
// This is called every time text is yanked/deleted
const registerController = Vim.getRegisterController();
const originalPushText = registerController.pushText.bind(registerController);

registerController.pushText = function(registerName, operator, text, linewise, blockwise) {
  console.log('📋 Register pushText called:', {
    registerName,
    operator,
    text: text?.substring(0, 50),
    linewise,
    blockwise
  });
  
  // Call the original method first
  const result = originalPushText(registerName, operator, text, linewise, blockwise);
  
  // If it's a yank operation (not delete), sync to clipboard
  if (operator === 'yank') {
    console.log('📋 Yank detected, syncing to clipboard');
    
    // Use execCommand fallback since clipboard API has focus issues
    fallbackCopyToClipboard(text);
  }
  
  return result;
};

// Fallback clipboard method using textarea + execCommand
function fallbackCopyToClipboard(text) {
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.select();
  try {
    const success = document.execCommand('copy');
    console.log(success ? '✓ Fallback copy successful' : '❌ Fallback copy failed');
  } catch (err) {
    console.error('❌ Fallback copy error:', err);
  }
  document.body.removeChild(textarea);
}

console.log('✓ Clipboard event listener registered');

// Handle physical keypresses for paste (read from system clipboard)
// Browsers only allow clipboard.readText() during a user gesture (keydown),
// so intercept real keydown events and perform the paste ourselves when
// the editor is in normal mode and the user pressed 'p' or 'P'.
document.addEventListener('keydown', async (e) => {
  try {
    // Only consider lower/upper p keys
    if (e.key !== 'p' && e.key !== 'P') return;

    // Ensure the event target is inside the editor DOM
    if (!view.dom.contains(document.activeElement)) return;

    // Only when Vim is in normal mode
    const cmState = cm.state.vim || {};
    if (cmState.mode !== 'normal') return;

    // Prevent default handling and handle as a genuine user gesture
    e.preventDefault();
    const text = await navigator.clipboard.readText();
    if (!text) return;

    // Insert at cursor (p) or before cursor (P)
    const cur = cm.getCursor();
    if (e.key === 'p') {
      cm.replaceRange(text, cur);
    } else {
      // For 'P' insert before the cursor position
      cm.replaceRange(text, { line: cur.line, ch: cur.ch });
    }

    // Update unnamed register so subsequent vim operations see the text
    try {
      const rc = Vim.getRegisterController();
      rc.getRegister('"').setText(text);
    } catch (err) {
      // Non-fatal if register update fails
      console.warn('Failed to update unnamed register:', err);
    }
  } catch (err) {
    console.error('Paste from clipboard failed:', err);
  }
}, true);
