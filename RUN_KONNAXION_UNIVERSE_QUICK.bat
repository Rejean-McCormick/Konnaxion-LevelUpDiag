@echo off
setlocal
cd /d "%~dp0"
echo [LevelUpDiag] KX-UNIVERSES-1 quick boundary check...
python levelupdiag.py run universe-quick
set RC=%ERRORLEVEL%
echo.
echo [LevelUpDiag] Termine avec code %RC%.
exit /b %RC%
