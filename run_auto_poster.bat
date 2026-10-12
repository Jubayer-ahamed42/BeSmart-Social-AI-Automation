@echo off
chcp 65001 > nul
setlocal

set "PROJECT_DIR=C:\MY PROJECT\2. FACEBOOK AUTO POSTER AGENT (Be Smart With AI)"
set "PYTHON_EXE=C:\Users\ASSDI\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "LOG_FILE=%PROJECT_DIR%\scheduler.log"

cd /d "%PROJECT_DIR%"

echo ============================================================ >> "%LOG_FILE%"
echo [%date% %time%] Auto Poster Scheduled Execution Starting... >> "%LOG_FILE%"

if not exist "%PYTHON_EXE%" (
    echo [%date% %time%] [ERROR] Python executable not found at: %PYTHON_EXE% >> "%LOG_FILE%"
    exit /b 1
)

"%PYTHON_EXE%" main.py --slot auto >> "%LOG_FILE%" 2>&1
set EXIT_CODE=%ERRORLEVEL%

echo [%date% %time%] Run completed with exit code: %EXIT_CODE% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"

endlocal
exit /b %EXIT_CODE%
