#!/bin/bash
# Script to build and publish scopemate package to PyPI

# Clean up previous builds
rm -rf build/ dist/ src/*.egg-info/

# Build the package
python3 -m build

# Check the package
twine check dist/*

# Upload to PyPI (uncomment when ready)
# twine upload dist/*

echo "Build complete. To upload to PyPI, run: twine upload dist/*" 