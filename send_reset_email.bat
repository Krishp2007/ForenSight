@echo off
title ForenSight - Reset Email Trigger
echo ========================================================
echo   ForenSight - Sending Password Reset Email to Brevo
echo ========================================================
echo.

set PYTHONPATH=d:\ForenSight\ForenSight
cd /d d:\ForenSight\ForenSight

backend\.venv\Scripts\python.exe send_reset_direct.py

echo.
echo ========================================================
echo Done! Press any key to close.
pause
