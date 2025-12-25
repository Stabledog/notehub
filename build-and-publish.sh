#!/bin/bash
set -e

# Build and publish lm-notehub to PyPI
# Requires: LM_NOTEHUB_PYPI_TOKEN environment variable

if [ -z "$LM_NOTEHUB_PYPI_TOKEN" ]; then
    echo "Error: LM_NOTEHUB_PYPI_TOKEN environment variable not set"
    exit 1
fi

# Check for required Python packages
missing_packages=()

if ! python -c "import build" 2>/dev/null; then
    missing_packages+=("build")
fi

if ! python -c "import twine" 2>/dev/null; then
    missing_packages+=("twine")
fi

# Prompt to install missing packages
if [ ${#missing_packages[@]} -gt 0 ]; then
    echo "Missing required packages: ${missing_packages[*]}"
    echo -n "Install them now? (y/n): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Installing ${missing_packages[*]}..."
        python -m pip install "${missing_packages[@]}"
    else
        echo "Cannot proceed without required packages. Exiting."
        exit 1
    fi
fi

echo "Cleaning old distribution files..."
rm -rf dist/

echo "Building distribution packages..."
python -m build

echo "Uploading to PyPI..."
python -m twine upload dist/* -u __token__ -p "$LM_NOTEHUB_PYPI_TOKEN"

echo "Done! Package published to PyPI"
echo "Install with: pip install lm-notehub"
