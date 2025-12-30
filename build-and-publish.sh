#!/bin/bash
set -e

# Build and publish lm-notehub to PyPI
# Requires: LM_NOTEHUB_PYPI_TOKEN environment variable

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Build and publish lm-notehub to PyPI.

OPTIONS:
    -h, --help              Show this help message and exit
    -b, --build-only        Build distribution packages only (skip publishing)
    -p, --publish-only      Skip the build step and only publish existing dist/ files
                           Useful for retrying after a failed publish

ENVIRONMENT:
    LM_NOTEHUB_PYPI_TOKEN  Required. Your PyPI API token

EXAMPLES:
    # Normal build and publish
    ./$(basename "$0")

    # Build only (skip publishing)
    ./$(basename "$0") --build-only

    # Retry publish after network failure (skips rebuild)
    ./$(basename "$0") --publish-only

NOTES:
    Publishing from within a corporate network with Python 3.13 may fail due to
    SSL certificate validation issues. If you encounter SSL errors, try:
    - Publishing from outside the corporate network (home/mobile hotspot)
    - Using Python 3.11 or earlier (more lenient SSL validation)

EOF
    exit 0
}

PUBLISH_ONLY=false
BUILD_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        -b|--build-only)
            BUILD_ONLY=true
            shift
            ;;
        -p|--publish-only)
            PUBLISH_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run '$(basename "$0") --help' for usage information."
            exit 1
            ;;
    esac
done

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

if [ "$PUBLISH_ONLY" = false ]; then
    echo "Cleaning old distribution files..."
    rm -rf dist/

    echo "Building distribution packages..."
    python -m build
else
    echo "Skipping build (publish-only mode)..."
    if [ ! -d "dist" ] || [ -z "$(ls -A dist 2>/dev/null)" ]; then
        echo "Error: No distribution files found in dist/ directory"
        echo "Run without --publish-only to build first"
        exit 1
    fi
fi

if [ "$BUILD_ONLY" = false ]; then
    echo "Uploading to PyPI..."
    python -m twine upload dist/* -u __token__ -p "$LM_NOTEHUB_PYPI_TOKEN"

    echo "Done! Package published to PyPI"
    echo "Install with: pip install lm-notehub"
else
    echo "Build complete (skipping publish)."
    echo "Distribution files are in dist/"
fi
