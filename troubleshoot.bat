@echo off
REM ============================================================================
REM GIFTIA - BATCH UTILITIES PARA TROUBLESHOOTING
REM Ejecuta desde: D:\HunterScrap\
REM ============================================================================

setlocal enabledelayedexpansion

:menu
cls
echo.
echo ======================================================================
echo  GIFTIA TROUBLESHOOTING UTILITIES v1.0
echo ======================================================================
echo.
echo Elige una opcion:
echo.
echo   1. Ver ultimas lineas de Hunter.log
echo   2. Ver ultimas lineas de debug.log de WordPress
echo   3. Ejecutar Hunter.py con debug activo
echo   4. Enviar producto de prueba (test_api.py)
echo   5. Verificar estado del sistema (verify.php en navegador)
echo   6. Limpiar logs
echo   7. Salir
echo.
set /p option="Tu opcion (1-7): "

if "%option%"=="1" goto hunter_log
if "%option%"=="2" goto wordpress_log
if "%option%"=="3" goto hunter_debug
if "%option%"=="4" goto test_api
if "%option%"=="5" goto verify_php
if "%option%"=="6" goto clear_logs
if "%option%"=="7" goto end

goto menu

:hunter_log
echo.
echo === HUNTER.LOG (Ultimas 50 lineas) ===
echo.
if exist hunter.log (
    powershell -Command "Get-Content hunter.log -Tail 50"
) else (
    echo ERROR: hunter.log no encontrado
)
echo.
pause
goto menu

:wordpress_log
echo.
echo === DEBUG.LOG DE WORDPRESS (Ultimas 50 lineas) ===
echo.
set wp_log=C:\webproject\giftia\wp-content\debug.log
if exist "%wp_log%" (
    powershell -Command "Get-Content '%wp_log%' -Tail 50"
) else (
    echo ERROR: %wp_log% no encontrado
    echo Verifica la ruta de tu WordPress
)
echo.
pause
goto menu

:hunter_debug
echo.
echo === EJECUTANDO HUNTER.PY CON DEBUG ===
echo.
python3 hunter.py
echo.
pause
goto menu

:test_api
echo.
echo === ENVIAR PRODUCTO DE PRUEBA ===
echo.
set /p token="Pega tu API Token (copia de WordPress Admin): "
echo.
python3 test_api.py --token=%token%
echo.
pause
goto menu

:verify_php
echo.
echo === VERIFICADOR DE ESTADO ===
echo.
echo Abriendo navegador...
start https://giftia.es/wp-content/plugins/giftfinder-core/verify.php
echo.
echo Espera a que se abra el navegador con el estado completo.
echo.
pause
goto menu

:clear_logs
echo.
echo === LIMPIAR LOGS ===
echo.
if exist hunter.log (
    del hunter.log
    echo hunter.log limpiado
)
echo.
pause
goto menu

:end
echo.
echo Saliendo...
echo.
