@echo off
REM Script to build and publish scopemate package to PyPI

REM Clean up previous builds
if exist build\ rmdir /s /q build
if exist dist\ rmdir /s /q dist
for /d %%G in ("src\*.egg-info") do rmdir /s /q "%%G"

REM Build the package
python -m build

REM Check the package
python -m twine check dist\*

REM Upload to PyPI (uncomment when ready)
REM python -m twine upload dist\*

echo Build complete. To upload to PyPI, run: python -m twine upload dist\* 