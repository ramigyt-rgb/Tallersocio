@echo off
set PYTHONDONTWRITEBYTECODE=1
cd /d "%~dp0"
title Taller OS
python -m streamlit run app.py --server.headless true --browser.gatherUsageStats false
if errorlevel 1 (
    echo.
    echo Si es la primera vez, ejecuta INSTALAR_Y_ABRIR.bat
    pause
)
