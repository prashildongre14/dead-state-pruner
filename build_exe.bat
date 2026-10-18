@echo off
title Build Standalone Windows Executable (.exe)
echo ========================================================
echo Compiling Dead-State Pruner into a Standalone .EXE
echo ========================================================
cd /d "%~dp0"

echo Cleaning previous builds...
rmdir /s /q build dist 2>nul
del /q *.spec 2>nul

echo Running PyInstaller...
pyinstaller --name "DeadStatePruner" ^
  --noconsole ^
  --onefile ^
  --add-data "templates;templates" ^
  --add-data "static;static" ^
  desktop.py

echo ========================================================
if exist "dist\DeadStatePruner.exe" (
  echo [SUCCESS] Executable generated successfully at:
  echo dist\DeadStatePruner.exe
  echo.
  echo You can copy this .exe to any Windows laptop and run it
  echo without needing Python or any dependencies installed!
) else (
  echo [ERROR] Build failed. Please check the output above.
)
echo ========================================================
pause
