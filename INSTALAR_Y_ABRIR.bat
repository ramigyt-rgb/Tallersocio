@echo off
set PYTHONDONTWRITEBYTECODE=1
cd /d "%~dp0"
title Taller OS - Instalacion

echo ========================================
echo          TALLER OS - INSTALACION
echo ========================================
echo.
python -m pip install --upgrade --user pip
python -m pip install --user -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: No se pudieron instalar las dependencias.
    echo Verifica que Python este instalado y agregado al PATH.
    pause
    exit /b 1
)
echo.
echo Abriendo Taller OS...
python -m streamlit run app.py --server.headless true --browser.gatherUsageStats false
pause
