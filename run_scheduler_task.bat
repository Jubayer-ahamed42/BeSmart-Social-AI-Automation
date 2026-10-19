@echo off
setlocal
cd /d "%~dp0"
call run_auto_poster.bat
exit /b %ERRORLEVEL%
