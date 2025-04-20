#!/bin/bash
# Shell script to install scopemate on Linux/macOS systems

# Check for Python 3.10+
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if (( $(echo "$python_version < 3.10" | bc -l) )); then
    echo "Error: Python 3.10 or higher is required."
    echo "Your version: $python_version"
    exit 1
fi

# Install package
echo "Installing scopemate..."
python3 -m pip install -e .

# Check installation status
if [ $? -eq 0 ]; then
    echo "scopemate installed successfully!"
    echo "You can now run 'scopemate --interactive' to start using it."
else
    echo "Installation failed. Please check the error messages above."
    exit 1
fi 