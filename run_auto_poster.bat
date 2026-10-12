@echo off
chcp 65001 > nul
setlocal

set "PROJECT_DIR=C:\MY PROJECT\2. FACEBOOK AUTO POSTER AGENT (Be Smart With AI)"
set "PYTHON_EXE=C:\Users\ASSDI\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "LOG_FILE=%PROJECT_DIR%\scheduler.log"
set "PATH=%PATH%;C:\Users\ASSDI\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd;C:\Users\ASSDI\AppData\Local\Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin"

cd /d "%PROJECT_DIR%"

echo ============================================================ >> "%LOG_FILE%"
echo [%date% %time%] Auto Poster Scheduled Execution Starting... >> "%LOG_FILE%"

:: 1. Sync latest state from GitHub so we never duplicate a post made by cloud runner
git pull --rebase origin main >> "%LOG_FILE%" 2>&1

if not exist "%PYTHON_EXE%" (
    echo [%date% %time%] [ERROR] Python executable not found at: %PYTHON_EXE% >> "%LOG_FILE%"
    exit /b 1
)

:: 2. Execute poster
"%PYTHON_EXE%" main.py --slot auto >> "%LOG_FILE%" 2>&1
set EXIT_CODE=%ERRORLEVEL%

:: 3. If local posted, sync history to GitHub
git add post_history.json >> "%LOG_FILE%" 2>&1
git diff --cached --quiet
if errorlevel 1 (
    git commit -m "chore(local): update post history [skip ci]" >> "%LOG_FILE%" 2>&1
    git push origin main >> "%LOG_FILE%" 2>&1
)

echo [%date% %time%] Run completed with exit code: %EXIT_CODE% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"

endlocal
exit /b %EXIT_CODE%
