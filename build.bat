@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  where choco >nul 2>nul
  if errorlevel 1 (
    echo Python is missing and Chocolatey is not installed. Install Python 3 and re-run.
    exit /b 1
  )
  echo Python not found. Installing with Chocolatey...
  choco install python -y
  if errorlevel 1 exit /b 1
  call refreshenv >nul 2>nul
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python was installed but is not on PATH yet. Open a new terminal and re-run build.bat.
    exit /b 1
  )
)

python scripts\build_packages.py
if errorlevel 1 exit /b 1
echo Build complete. Packages are in dist\.
exit /b 0
