#!/bin/bash
# Shell script to install ScopeMate on Linux/macOS systems

# Check for Python 3.10+
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python $required_version or higher is required. You have Python $python_version."
    exit 1
fi

# Install package
echo "Installing ScopeMate..."
pip3 install -e .

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo "ScopeMate installed successfully!"
    echo "You can now run 'scopemate --interactive' to start using it."
else
    echo "Installation failed. Please check the error messages above."
    exit 1
fi 