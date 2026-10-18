@echo off
title Dead-State Pruner
cd /d "%~dp0"
where python >nul 2>nul || (echo Python is not installed. Get it from https://www.python.org/downloads/ and tick "Add Python to PATH". & pause & exit /b)
python -c "import flask" 2>nul || (echo Installing Flask, first run only... & python -m pip install flask)
python -c "import webview" 2>nul && (python desktop.py & exit /b)
echo Desktop window package not found, trying to install pywebview...
python -m pip install pywebview >nul 2>nul
python -c "import webview" 2>nul && (python desktop.py & exit /b)
echo Opening in browser mode instead...
start "" http://127.0.0.1:5000
python app.py
