@echo off
REM Doble clic en este archivo para abrir el Editor de EntityScript en Windows.
REM Requiere Python 3.10+ instalado (con tkinter, que viene incluido por defecto).

cd /d "%~dp0"
python Editor\desktop_app.py
if errorlevel 1 (
    echo.
    echo Hubo un problema al abrir el editor. Verifica que Python este instalado
    echo y disponible como 'python' en la linea de comandos.
    pause
)
