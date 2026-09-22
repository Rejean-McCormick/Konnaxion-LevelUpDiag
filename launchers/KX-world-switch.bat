@echo off
setlocal
cd /d "%~dp0.."
python levelupdiag.py run world-switch
exit /b %ERRORLEVEL%
