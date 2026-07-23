@echo off
REM =====================================================================
REM TramaPos · Levanta el backend en modo producción.
REM Como el backend ahora sirve tambien el frontend ya compilado
REM (ver main.py), este es el UNICO programa que hay que mantener
REM corriendo para que el POS funcione.
REM =====================================================================

cd /d "%~dp0backend"
call venv\Scripts\activate.bat
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
