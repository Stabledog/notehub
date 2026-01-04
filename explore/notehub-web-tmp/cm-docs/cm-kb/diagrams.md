# Vim API Flow Diagrams

Visual reference for understanding how Vim mode processes commands and interacts with CM6.

## Command Processing Flow

```mermaid
graph TD
    A[User Presses Key] --> B[CM6 Key Handler]
    B --> C{Vim Mode Active?}
    C -->|No| D[Default CM6 Handler]
    C -->|Yes| E[Vim Plugin]
    E --> F[Get Vim State]
    F --> G{Current Mode?}
    
    G -->|Insert| H[Pass to CM6 or Map]
    G -->|Normal| I[Vim Command Parser]
    G -->|Visual| I
    
    I --> J{Command Type?}
    J -->|Motion| K[Execute Motion]
    J -->|Operator| L[Execute Operator]
    J -->|Action| M[Execute Action]
    J -->|Ex| N[Execute Ex Command]
    
    K --> O[Update Cursor]
    L --> P[Modify Text]
    M --> Q[Arbitrary Action]
    N --> R[Ex Command Logic]
    
    O --> S[Update Vim State]
    P --> S
    Q --> S
    R --> S
    
    S --> T[Dispatch CM6 Transaction]
    T --> U[Re-render View]
    U --> V[Emit vim-command-done]
```

## Mode Transitions

```mermaid
stateDiagram-v2
    [*] --> Normal
    
    Normal --> Insert: i, a, o, O, I, A, etc.
    Normal --> Visual: v, V, Ctrl-v
    Normal --> Replace: R
    Normal --> CmdLine: :, /, ?
    
    Insert --> Normal: Esc, Ctrl-c, Ctrl-[
    Visual --> Normal: Esc, v
    Replace --> Normal: Esc
    CmdLine --> Normal: Enter, Esc
    
    Visual --> Insert: i, a, etc. (after operation)
    
    note right of Normal
        Default mode
        Most commands available
    end note
    
    note right of Insert
        Text entry mode
        Limited Vim commands
    end note
    
    note right of Visual
        Text selection
        Can apply operators
    end note
```

## Operator + Motion Composition

```mermaid
graph LR
    A[Operator Key] --> B[Vim State: Pending]
    B --> C[Motion Key]
    C --> D[Calculate Range]
    D --> E[Apply Operator to Range]
    E --> F[Update Document]
    F --> G[Update Cursor]
    G --> H[Clear Pending State]
    
    style B fill:#fff3cd
    style E fill:#d4edda
```

**Examples**:
- `d` (operator) + `w` (motion) → delete word
- `c` (operator) + `2j` (motion) → change 2 lines down
- `y` (operator) + `$` (motion) → yank to end of line

## Ex Command Lifecycle

```mermaid
sequenceDiagram
    participant User
    participant Vim
    participant Parser
    participant Handler
    participant CM6
    
    User->>Vim: Press :
    Vim->>Vim: Enter CmdLine mode
    Vim->>User: Show : prompt
    User->>Vim: Type command + Enter
    Vim->>Parser: Parse "write myfile.txt"
    Parser->>Parser: Extract name, args, range
    Parser->>Handler: Call defineEx handler
    Handler->>CM6: Read/modify document
    Handler-->>Vim: Complete
    Vim->>Vim: Exit CmdLine mode
    Vim->>User: Back to Normal mode
```

## Custom Command Integration

```mermaid
graph TB
    subgraph "Your Code"
        A[Define Ex Command]
        B[Define Operator]
        C[Define Motion]
        D[Define Action]
    end
    
    subgraph "Vim Registry"
        E[Ex Commands Map]
        F[Operators Map]
        G[Motions Map]
        H[Actions Map]
    end
    
    subgraph "Runtime"
        I[Command Parser]
        J[Execute Logic]
    end
    
    A --> E
    B --> F
    C --> G
    D --> H
    
    E --> I
    F --> I
    G --> I
    H --> I
    
    I --> J
    
    J --> K[CM6 Transaction]
    K --> L[Updated View]
    
    style A fill:#e3f2fd
    style B fill:#e3f2fd
    style C fill:#e3f2fd
    style D fill:#e3f2fd
```

## Key Mapping Resolution

```mermaid
graph TD
    A[Key Pressed] --> B{In Map Context?}
    B -->|Yes| C[Get Current Mode]
    C --> D{Mode-Specific Map?}
    D -->|Yes| E[Check Mode Maps]
    D -->|No| F[Check Global Maps]
    
    E --> G{Found?}
    F --> G
    
    G -->|Yes| H{Recursive?}
    G -->|No| I[Default Handling]
    
    H -->|Yes noremap| J[Execute Directly]
    H -->|No map| K[Expand and Re-parse]
    
    K --> A
    J --> L[Execute Command]
    
    style E fill:#d1ecf1
    style F fill:#d1ecf1
    style J fill:#d4edda
    style K fill:#fff3cd
```

**Example**:
1. User presses `Y`
2. Check normal mode maps
3. Find `Y` → `y$` mapping
4. If `noremap`: execute `y$` directly
5. If `map`: expand to `y$` and re-parse (could map further)

## CM5 Adapter Bridge

```mermaid
graph LR
    subgraph "CM6 World"
        A[EditorView]
        B[EditorState]
        C[Transaction]
    end
    
    subgraph "Adapter Layer"
        D[CodeMirror Class]
        E[getCM function]
    end
    
    subgraph "CM5-Style API"
        F[getValue]
        G[setValue]
        H[getCursor]
        I[setCursor]
        J[getRange]
        K[replaceRange]
    end
    
    subgraph "Vim Logic"
        L[vim.js]
    end
    
    A --> E
    E --> D
    D --> F
    D --> G
    D --> H
    D --> I
    D --> J
    D --> K
    
    F --> B
    G --> C
    H --> B
    I --> C
    J --> B
    K --> C
    
    L --> F
    L --> G
    L --> H
    L --> I
    L --> J
    L --> K
    
    style D fill:#fff3e1
    style L fill:#f0f0f0
```

## Event Flow

```mermaid
sequenceDiagram
    participant User
    participant CM6
    participant VimPlugin
    participant YourCode
    
    User->>CM6: Press 'i'
    CM6->>VimPlugin: Key event
    VimPlugin->>VimPlugin: Enter insert mode
    VimPlugin->>YourCode: Emit "vim-mode-change"
    YourCode->>YourCode: Update UI
    
    User->>CM6: Type text
    CM6->>CM6: Handle normally
    
    User->>CM6: Press Esc
    CM6->>VimPlugin: Key event
    VimPlugin->>VimPlugin: Exit insert mode
    VimPlugin->>YourCode: Emit "vim-mode-change"
    VimPlugin->>YourCode: Emit "vim-command-done"
    YourCode->>YourCode: Update UI
```

## Register System

```mermaid
graph TB
    subgraph "Register Types"
        A[Named Registers a-z]
        B[Numbered Registers 0-9]
        C[Special Registers]
        D[Clipboard +/*]
    end
    
    subgraph "Operations"
        E[Yank]
        F[Delete]
        G[Change]
    end
    
    subgraph "Register Controller"
        H[Store]
        I[Retrieve]
        J[Push]
    end
    
    E --> H
    F --> H
    G --> H
    
    H --> A
    H --> B
    H --> C
    H --> D
    
    A --> I
    B --> I
    C --> I
    D --> I
    
    I --> K[Paste]
    
    style H fill:#d4edda
    style I fill:#d4edda
```

## Visual Mode Range Selection

```mermaid
graph TD
    A[Press v/V/Ctrl-v] --> B[Enter Visual Mode]
    B --> C[Mark Anchor Point]
    C --> D[Move Cursor with Motions]
    D --> E{Apply Operator?}
    
    E -->|Yes| F[Calculate Range]
    E -->|No| D
    
    F --> G[anchor to head]
    G --> H[Execute Operator on Range]
    H --> I[Exit Visual Mode]
    
    E -->|Esc| J[Exit Without Operation]
    
    style C fill:#fff3cd
    style F fill:#d1ecf1
    style H fill:#d4edda
```

## Plugin Initialization

```mermaid
sequenceDiagram
    participant App
    participant CM6
    participant VimPlugin
    participant VimLogic
    participant Adapter
    
    App->>CM6: new EditorView({ extensions: [vim()] })
    CM6->>VimPlugin: Initialize plugin
    VimPlugin->>Adapter: new CodeMirror(view)
    Adapter->>Adapter: Wrap EditorView
    VimPlugin->>VimLogic: initVim(CodeMirror)
    VimLogic-->>VimPlugin: Vim object
    VimPlugin->>VimLogic: Vim.enterVimMode(cm)
    VimLogic->>Adapter: Initialize vim state
    Adapter-->>VimPlugin: Ready
    VimPlugin->>CM6: Attach event handlers
    CM6-->>App: EditorView ready
```

## Decision Tree: Which API to Use

```mermaid
graph TD
    A{What are you doing?} --> B[Vim-specific customization]
    A --> C[Editor features]
    
    B --> D{What kind?}
    D --> E[Key mapping] --> F[Vim.map/noremap]
    D --> G[Ex command] --> H[Vim.defineEx]
    D --> I[Operator] --> J[Vim.defineOperator]
    D --> K[Motion] --> L[Vim.defineMotion]
    D --> M[Mode control] --> N[Vim.exitInsertMode, etc.]
    
    C --> O{Need Vim state?}
    O -->|Yes| P[getCM then use CM5 API]
    O -->|No| Q[Use CM6 API directly]
    
    P --> R[cm.getValue, cm.setCursor, etc.]
    Q --> S[view.state, view.dispatch, etc.]
    
    style F fill:#e8f5e9
    style H fill:#e8f5e9
    style J fill:#e8f5e9
    style L fill:#e8f5e9
    style N fill:#e8f5e9
    style R fill:#fff3e1
    style S fill:#e1f5ff
```
