@echo off
setlocal
cd /d "%~dp0.."
python levelupdiag.py run i18n-validation
exit /b %ERRORLEVEL%
