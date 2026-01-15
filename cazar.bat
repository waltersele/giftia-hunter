@echo off
cd /d D:\HunterScrap
echo ===================================================
echo   INICIANDO PROTOCOLO GIFTIA V3.0 (MULTI-VENDOR)
echo   %date% %time%
echo ===================================================

echo.
echo [1/3] 📦 EJECUTANDO AMAZON HUNTER...
python hunter.py
echo. 

echo [2/3] 🟢 EJECUTANDO AWIN HUNTER (Corte Ingles, Fnac...)...
python hunter_awin.py
echo.

echo [3/3] 🛒 EJECUTANDO TRADEDOUBLER HUNTER (Carrefour, Philips...)...
python hunter_td.py
echo.

echo ===================================================
echo   ✅ MISION CUMPLIDA. TODO ACTUALIZADO.
echo      Cerrando ventana en 15 segundos...
echo ===================================================
timeout /t 15