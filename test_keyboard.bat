@echo off
cd /d "%~dp0"
echo Running keyboard test...
echo (You may need to run as Administrator)
echo.
python test_keyboard.py
pause
