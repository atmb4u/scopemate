@echo off
REM Windows installer script for scopemate

SETLOCAL

python -c "import sys; assert sys.version_info >= (3, 10), 'Python 3.10 or higher is required'" || (
    echo Python 3.10 or higher is required.
    exit /b 1
)

echo Installing scopemate...

python -m pip install -e .

echo scopemate installed successfully!
echo You can now run 'scopemate --interactive' to start using it.

ENDLOCAL 