@echo off
setlocal
cd /d "%~dp0"
set PYTHONDONTWRITEBYTECODE=1
python --version >nul 2>&1
if errorlevel 1 (
  echo Python no esta instalado o no esta agregado al PATH.
  pause
  exit /b 1
)
echo Instalando / actualizando dependencias de Taller OS...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo No se pudieron instalar las dependencias.
  pause
  exit /b 1
)
echo.
echo Abriendo Taller OS...
python -m streamlit run app.py
endlocal
