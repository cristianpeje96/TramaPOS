@echo off
REM =====================================================================
REM TramaPos · Empaqueta hardware_agent.py como un .exe standalone
REM Correr desde esta misma carpeta (hardware-agent), con el venv
REM activado y las dependencias instaladas (pip install -r requirements.txt)
REM =====================================================================

pyinstaller --onefile --console --name TramaPos-Agente hardware_agent.py

echo.
echo =====================================================================
echo  Listo. El ejecutable quedo en: dist\TramaPos-Agente.exe
echo  Copia ese archivo a la carpeta que quieras en el PC de la caja
echo  (ej: C:\TramaPos\), y correlo una vez para que genere config.json
echo  al lado. Edita config.json con el vendor_id/product_id reales de
echo  tu ticketera antes de usarlo en produccion.
echo =====================================================================
pause