#!/bin/bash
# Script to build and publish scopemate package to PyPI

# Clean up previous builds
echo "Cleaning up previous builds..."
rm -rf dist build *.egg-info

# Build the package
echo "Building package..."
python -m build

echo "Package built. To publish:"
echo "twine upload dist/*"

# Check the package
twine check dist/*

# Upload to PyPI (uncomment when ready)
# twine upload dist/*

echo "Build complete. To upload to PyPI, run: twine upload dist/*" 