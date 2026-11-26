@echo off
setlocal enabledelayedexpansion
title Windows Power Meter - Full Installer

echo ========================================
echo   Windows Power Meter - Full Installer
echo ========================================
echo This will install Python (if needed) and the Power Meter.
echo Requires NVIDIA GPU with driver (for NVML power sensors).
echo Cumulative Wh is an estimate from samples.
echo.

REM Check for real Python
set "PYTHON="
for %%P in (
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python310\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python310\python.exe"
) do (
    if exist "%%~P" (
        set "PYTHON=%%~P"
        goto :havepython
    )
)

echo Python not found. Downloading and installing Python 3.12...
echo.

set "PY_INSTALLER=%TEMP%\python-3.12.7-amd64.exe"
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe' -OutFile '%PY_INSTALLER%'"
if errorlevel 1 (
    echo Download failed. Check your internet connection.
    pause
    exit /b 1
)

echo Installing Python (this may take a minute)...
"%PY_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
if errorlevel 1 (
    echo Python install failed.
    pause
    exit /b 1
)

REM Refresh PATH for this session
for /f "delims=" %%i in ('powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('Path','User')"') do set "PATH=%%i;%PATH%"

set "PYTHON=%LocalAppData%\Programs\Python\Python312\python.exe"
if not exist "%PYTHON%" (
    echo Python installed but not found at expected path.
    echo Please close this window, open a new Command Prompt, and run install.bat again.
    pause
    exit /b 1
)

:havepython
echo Found Python: %PYTHON%
echo.

echo Installing Power Meter dependencies...
"%PYTHON%" -m pip install --upgrade pip -q
"%PYTHON%" -m pip install pystray pillow nvidia-ml-py
if errorlevel 1 (
    echo Failed to install packages.
    pause
    exit /b 1
)

echo.
echo Creating Startup shortcut...
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "PYTHONW=%LocalAppData%\Programs\Python\Python312\pythonw.exe"
if not exist "%PYTHONW%" set "PYTHONW=%PYTHON:python.exe=pythonw.exe%"

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$s = $ws.CreateShortcut([Environment]::GetFolderPath('Startup') + '\Power Meter.lnk'); " ^
  "$s.TargetPath = '%PYTHONW%'; " ^
  "$s.Arguments = '\"%SCRIPT_DIR%\power_meter.py\"'; " ^
  "$s.WorkingDirectory = '%SCRIPT_DIR%'; " ^
  "$s.Save()"

echo.
echo ========================================
echo   Done.
echo ========================================
echo Power Meter is installed and will start on next login.
echo.
echo To run it now, close this window and double-click:
echo   %PYTHONW% "%SCRIPT_DIR%\power_meter.py"
echo.
pause
