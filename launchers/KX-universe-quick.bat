@echo off
cd /d "%~dp0\.."
python levelupdiag.py run universe-quick
exit /b %ERRORLEVEL%
