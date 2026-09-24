@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -B exprscope_web.py
    goto done
)
where python >nul 2>nul
if not errorlevel 1 (
    python -B exprscope_web.py
    goto done
)
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B exprscope_web.py
    goto done
)
echo Python 3.10 or newer is required. Install Python and rerun this launcher.
pause
exit /b 1
:done
if errorlevel 1 pause
