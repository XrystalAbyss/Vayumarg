@echo off
setlocal
title VAYUMARG - Cyclone Intelligence Studio

REM ==============================================================================
REM VAYUMARG -- CYCLONE INTELLIGENCE STUDIO (NOOR 2K26)
REM Official Windows One-Click Double-Click Launcher
REM ==============================================================================

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%start_vayumarg.ps1" %*
set LAUNCH_EXIT_CODE=%ERRORLEVEL%

if %LAUNCH_EXIT_CODE% equ 0 goto :success

echo.
echo ========================================================================
echo [ERROR] Vayumarg launcher encountered an error (Code: %LAUNCH_EXIT_CODE%).
echo Review runtime logs at: logs\runtime\launcher.log
echo ========================================================================
echo.
pause
goto :done

:success

:done
endlocal
exit /b %LAUNCH_EXIT_CODE%
