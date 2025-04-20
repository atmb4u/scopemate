@echo off
SETLOCAL

REM Script to build and publish scopemate package to PyPI

REM Clean up previous builds
echo Cleaning up previous builds...
if exist dist rmdir /S /Q dist
if exist build rmdir /S /Q build
if exist *.egg-info rmdir /S /Q *.egg-info

REM Build the package
echo Building package...
python -m build

REM Check the package
python -m twine check dist\*

REM Upload to PyPI (uncomment when ready)
REM python -m twine upload dist\*

echo Package built. To publish:
echo twine upload dist/*

ENDLOCAL 