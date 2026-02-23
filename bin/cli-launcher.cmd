@echo off
if not "%CLAUDE_PLUGIN_ROOT%"=="" (set "ROOT=%CLAUDE_PLUGIN_ROOT%") else (set "ROOT=%~dp0..")

if exist "%ROOT%\.venv\Scripts\python.exe" (
    set "PYTHON=%ROOT%\.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

cd /d "%ROOT%\scripts"
%PYTHON% %*
