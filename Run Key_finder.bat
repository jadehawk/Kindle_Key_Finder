@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: Kindle Key Finder - Simple Launcher
:: ============================================================================

:: [*] Setup
set "script=%cd%\key_finder.py"

:: ============================================================================
:: [*] Check for Python
:: ============================================================================
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    pause
    goto :eof
)

:: ============================================================================
:: [*] Check for script
:: ============================================================================
if not exist "%script%" (
    echo [ERROR] Script not found: "%script%"
    pause
    goto :eof
)

:: ============================================================================
:: [*] Launch Python script in maximized window
:: ============================================================================
echo [*] Launching Kindle Key Extractor in maximized window...

:: Launch in new maximized CMD window
start "Kindle Key Finder" /MAX cmd /k python "%script%"

endlocal
