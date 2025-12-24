#!/bin/bash
set -e

# Build and publish lm-notehub to PyPI
# Requires: LM_NOTEHUB_PYPI_TOKEN environment variable

if [ -z "$LM_NOTEHUB_PYPI_TOKEN" ]; then
    echo "Error: LM_NOTEHUB_PYPI_TOKEN environment variable not set"
    exit 1
fi

echo "Building distribution packages..."
python -m build

echo "Uploading to PyPI..."
python -m twine upload dist/* -u __token__ -p "$LM_NOTEHUB_PYPI_TOKEN"

echo "Done! Package published to PyPI"
echo "Install with: pip install lm-notehub"
