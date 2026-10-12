@echo off
chcp 65001 > nul
cd /d "C:\test\test-1"

echo [%date% %time%] Auto Poster Scheduled Run Starting... >> "C:\test\test-1\scheduler.log"

:: 1. Sync latest changes from remote
git pull --rebase origin main >> "C:\test\test-1\scheduler.log" 2>&1

:: 2. Run poster for current slot
"C:\test\test-1\.venv\Scripts\python.exe" "C:\test\test-1\main.py" --slot auto >> "C:\test\test-1\scheduler.log" 2>&1

:: 3. Commit and push history if updated
git add post_history.json >> "C:\test\test-1\scheduler.log" 2>&1
git diff --cached --quiet
if errorlevel 1 (
    git commit -m "chore: auto-update post history [skip ci]" >> "C:\test\test-1\scheduler.log" 2>&1
    git push origin main >> "C:\test\test-1\scheduler.log" 2>&1
    echo [%date% %time%] Successfully pushed updated history. >> "C:\test\test-1\scheduler.log"
) else (
    echo [%date% %time%] No history changes to commit. >> "C:\test\test-1\scheduler.log"
)

echo [%date% %time%] Run finished. >> "C:\test\test-1\scheduler.log"
