@echo off
REM ============================================================================
REM GIFTIA - GUIA RÁPIDA EN TERMINAL
REM Muestra dónde están todos los archivos y cómo usarlos
REM ============================================================================

:menu
cls
echo.
echo ======================================================================
echo  GIFTIA - UBICACIÓN DE ARCHIVOS Y PRÓXIMOS PASOS
echo ======================================================================
echo.
echo ESTADO DEL SISTEMA:
echo   ✓ WordPress configurado
echo   ✓ Plugin instalado
echo   ✓ Tablas creadas
echo   ✓ Post type registrado
echo   ✗ TOKENS NO CONFIGURADOS - ESTO ES LO QUE FALTA
echo.
echo ======================================================================
echo.
echo PASO 1: GENERAR TOKEN (2 minutos)
echo -------
echo Ejecuta en PowerShell:
echo   cd D:\HunterScrap
echo   .\config-helper.ps1 generate
echo.
echo Esto te generará un token como:
echo   aB3cD9eF7gH2iJ8kL1mN4oP6qR5sTu0v
echo.
echo ======================================================================
echo.
echo PASO 2: GUARDAR EN WORDPRESS (5 minutos)
echo -------
echo Ve a: https://giftia.es/wp-admin
echo.
echo Menu: Products → ⚙️ Configuración
echo.
echo Rellena estos campos:
echo   - Token de API (WP_API_TOKEN): Pega el token de arriba
echo   - Amazon Tag (AMAZON_TAG): Tu código, ej: giftia0-21
echo   - Gemini API Key (opcional): Para descripciones IA
echo.
echo Haz clic: 💾 Guardar Configuración
echo.
echo ======================================================================
echo.
echo PASO 3: VERIFICAR (2 minutos)
echo -------
echo Abre en navegador:
echo   https://giftia.es/wp-content/plugins/giftfinder-core/verify.php
echo.
echo Deberías ver:
echo   ✓ WP_API_TOKEN: aB3cD9...
echo   ✓ AMAZON_TAG: giftia0-21
echo.
echo ======================================================================
echo.
echo PASO 4: EJECUTAR HUNTER (20-30 minutos)
echo -------
echo Una vez que verify.php muestre ✓ en los tokens:
echo.
echo   cd D:\HunterScrap
echo   python3 hunter.py
echo.
echo Los productos aparecerán automáticamente en WordPress Admin
echo   → Products → All Gifts
echo.
echo ======================================================================
echo.
echo ARCHIVOS ÚTILES DE REFERENCIA:
echo.
echo En c:\webproject\giftia\giftfinder-core\:
echo   - EMPIEZA_AQUI.md ................... Guía rápida (LEER PRIMERO)
echo   - SIGUIENTE_PASO.md ................ Próximos pasos (AHORA)
echo   - CONFIGURAR_TOKENS.md ............ Detalles de cada token
echo   - INSTRUCCIONES_FINALES.md ........ Guía completa
echo   - verify.php ...................... Verificador web
echo   - test.php ........................ Prueba de API
echo.
echo En D:\HunterScrap\:
echo   - config-helper.ps1 .............. Generador de tokens
echo   - troubleshoot.ps1 ............... Menú de diagnóstico
echo   - hunter.py ...................... Script principal
echo   - test_api.py .................... Test API desde Python
echo.
echo ======================================================================
echo.
echo ¿QUE HACER AHORA?
echo.
echo 1. Abre PowerShell
echo 2. Ejecuta: cd D:\HunterScrap
echo 3. Ejecuta: .\config-helper.ps1 generate
echo 4. Copia el token
echo 5. Ve a WordPress y guárdalo
echo 6. Vuelve aquí para verificar
echo.
echo ======================================================================
echo.
pause
goto menu
