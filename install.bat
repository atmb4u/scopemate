@echo off
REM Windows installer script for ScopeMate

REM Check for Python 3.10+
for /f "tokens=2 delims=." %%G in ('python -c "import sys; print(sys.version.split()[0])"') do set PYTHON_VER=%%G
if %PYTHON_VER% LSS 10 (
    echo Error: Python 3.10 or higher is required.
    exit /b 1
)

REM Install package
echo Installing ScopeMate...
pip install -e .

if %ERRORLEVEL% EQU 0 (
    echo ScopeMate installed successfully!
    echo You can now run 'scopemate --interactive' to start using it.
) else (
    echo Installation failed. Please check the error messages above.
    exit /b 1
) 