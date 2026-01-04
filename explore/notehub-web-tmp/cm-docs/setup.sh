#!/usr/bin/env bash
set -e


# 2. Clone canonical CodeMirror + Vim reference sources
git clone https://github.com/codemirror/codemirror5.git cm5
git clone https://github.com/codemirror/codemirror.git cm6
git clone https://github.com/replit/codemirror-vim.git cm6-vim

# 4. Create .gitignore masking upstream sources
cat >> .gitignore <<'EOF'
/cm5/
/cm6/
/cm6-vim/
EOF
