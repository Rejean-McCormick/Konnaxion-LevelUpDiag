@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_CMD="
where py >nul 2>nul && set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
  where python >nul 2>nul && set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo [LevelUpDiag] Python 3 introuvable dans PATH.
  pause
  exit /b 30
)

echo [LevelUpDiag] Konnaxion Worlds - world-switch...
%PYTHON_CMD% levelupdiag.py run world-switch
set "RC=%ERRORLEVEL%"
echo.
echo [LevelUpDiag] Resultat: .levelupdiag\current\summary.txt
pause
exit /b %RC%
