#!/usr/bin/env pwsh
<#
.SYNOPSIS
    GIFTIA Configuration Helper - Generar tokens y configuración
.DESCRIPTION
    Script para generar tokens de API automáticamente
    y guiar al usuario en la configuración de WordPress
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('generate', 'help', 'config')]
    [string]$Action = 'help'
)

# Colors
$colors = @{
    'Info'    = 'Cyan'
    'Success' = 'Green'
    'Error'   = 'Red'
    'Warning' = 'Yellow'
    'Title'   = 'Magenta'
}

function Show-Banner {
    Clear-Host
    Write-Host "================================" -ForegroundColor $colors['Title']
    Write-Host "  GIFTIA CONFIG HELPER" -ForegroundColor $colors['Title']
    Write-Host "  Token & Setup Generator" -ForegroundColor $colors['Title']
    Write-Host "================================" -ForegroundColor $colors['Title']
    Write-Host ""
}

function Show-Help {
    Show-Banner
    Write-Host "USO:" -ForegroundColor $colors['Title']
    Write-Host "  .\config-helper.ps1 [action]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "ACCIONES DISPONIBLES:" -ForegroundColor $colors['Title']
    Write-Host "  generate  - Generar nuevo token de API" -ForegroundColor $colors['Info']
    Write-Host "  config    - Mostrar instrucciones de configuración" -ForegroundColor $colors['Info']
    Write-Host "  help      - Mostrar esta ayuda" -ForegroundColor $colors['Info']
    Write-Host ""
    Write-Host "EJEMPLOS:" -ForegroundColor $colors['Title']
    Write-Host "  .\config-helper.ps1 generate" -ForegroundColor Cyan
    Write-Host "  .\config-helper.ps1 config" -ForegroundColor Cyan
    Write-Host ""
}

function Generate-Token {
    Show-Banner
    
    Write-Host "GENERADOR DE TOKENS DE API" -ForegroundColor $colors['Title']
    Write-Host ""
    
    # Generar token de 32 caracteres
    $characters = ([char[]]@(48..57 + 65..90 + 97..122))
    $token = -join ($characters | Get-Random -Count 32)
    
    Write-Host "✓ Token generado exitosamente:" -ForegroundColor $colors['Success']
    Write-Host ""
    Write-Host $token -ForegroundColor $colors['Success'] -BackgroundColor Black
    Write-Host ""
    
    # Copiar al clipboard
    $token | Set-Clipboard
    Write-Host "✓ Token copiado al clipboard" -ForegroundColor $colors['Success']
    Write-Host ""
    
    Write-Host "PRÓXIMOS PASOS:" -ForegroundColor $colors['Title']
    Write-Host "1. Ve a: https://giftia.es/wp-admin/" -ForegroundColor $colors['Info']
    Write-Host "2. Menú izquierdo → Products → ⚙️ Configuración" -ForegroundColor $colors['Info']
    Write-Host "3. En el campo 'Token de API (WP_API_TOKEN)' pega:" -ForegroundColor $colors['Info']
    Write-Host "   $token" -ForegroundColor $colors['Success']
    Write-Host "4. Rellena los otros campos (Gemini, Amazon Tag)" -ForegroundColor $colors['Info']
    Write-Host "5. Haz clic en '💾 Guardar Configuración'" -ForegroundColor $colors['Info']
    Write-Host ""
    
    Write-Host "VERIFICAR QUE FUNCIONÓ:" -ForegroundColor $colors['Title']
    Write-Host "Abre en navegador:" -ForegroundColor $colors['Info']
    Write-Host "https://giftia.es/wp-content/plugins/giftfinder-core/verify.php" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Deberías ver:" -ForegroundColor $colors['Info']
    Write-Host "✓ WP_API_TOKEN: " + $token.Substring(0, 10) + "..." -ForegroundColor $colors['Success']
    Write-Host ""
}

function Show-Config {
    Show-Banner
    
    Write-Host "INSTRUCCIONES DE CONFIGURACIÓN" -ForegroundColor $colors['Title']
    Write-Host ""
    
    Write-Host "PASO 1: Acceder al Panel" -ForegroundColor $colors['Title']
    Write-Host "  1. Ve a: https://giftia.es/wp-admin/" -ForegroundColor $colors['Info']
    Write-Host "  2. Menu izquierdo → Products → ⚙️ Configuración" -ForegroundColor $colors['Info']
    Write-Host ""
    
    Write-Host "PASO 2: Rellenar Campos" -ForegroundColor $colors['Title']
    Write-Host ""
    
    Write-Host "  🔐 Token de API (OBLIGATORIO)" -ForegroundColor $colors['Warning']
    Write-Host "     - Ejecuta: .\config-helper.ps1 generate" -ForegroundColor Cyan
    Write-Host "     - Copia el token generado" -ForegroundColor $colors['Info']
    Write-Host "     - Pégalo en el campo WP_API_TOKEN" -ForegroundColor $colors['Info']
    Write-Host ""
    
    Write-Host "  🤖 Clave API Gemini (OPCIONAL)" -ForegroundColor $colors['Warning']
    Write-Host "     - Ve a: https://ai.google.dev/" -ForegroundColor Cyan
    Write-Host "     - Crea una API key" -ForegroundColor $colors['Info']
    Write-Host "     - Pégala en el campo GEMINI_API_KEY" -ForegroundColor $colors['Info']
    Write-Host "     - Si no lo configuras: descripciones genéricas" -ForegroundColor $colors['Warning']
    Write-Host ""
    
    Write-Host "  🛍️ ID de Afiliado Amazon (RECOMENDADO)" -ForegroundColor $colors['Warning']
    Write-Host "     - Ve a: https://associates.amazon.es/" -ForegroundColor Cyan
    Write-Host "     - Copia tu código (formato: dominio-21)" -ForegroundColor $colors['Info']
    Write-Host "     - Pégalo en el campo AMAZON_TAG" -ForegroundColor $colors['Info']
    Write-Host "     - Ejemplo: giftia0-21" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "  🌐 CORS (Dejar por defecto)" -ForegroundColor $colors['Info']
    Write-Host "     - No cambiar a menos que sepas lo que haces" -ForegroundColor $colors['Warning']
    Write-Host ""
    
    Write-Host "  🐛 Modo Debug (ACTIVAR AHORA)" -ForegroundColor $colors['Warning']
    Write-Host "     - Marca la casilla 'Habilitar modo debug'" -ForegroundColor $colors['Info']
    Write-Host "     - Esto activa logs detallados" -ForegroundColor $colors['Info']
    Write-Host "     - Desmarca después de terminar la configuración" -ForegroundColor $colors['Warning']
    Write-Host ""
    
    Write-Host "PASO 3: Guardar" -ForegroundColor $colors['Title']
    Write-Host "  - Haz clic en el botón azul '💾 Guardar Configuración'" -ForegroundColor $colors['Info']
    Write-Host "  - Espera a ver: ✅ Variables de entorno guardadas correctamente" -ForegroundColor $colors['Success']
    Write-Host ""
    
    Write-Host "PASO 4: Verificar" -ForegroundColor $colors['Title']
    Write-Host "  - Abre en navegador:" -ForegroundColor $colors['Info']
    Write-Host "    https://giftia.es/wp-content/plugins/giftfinder-core/verify.php" -ForegroundColor Cyan
    Write-Host "  - Deberías ver ✓ en los 3 tokens principales" -ForegroundColor $colors['Success']
    Write-Host ""
    
    Write-Host "PASO 5: Ejecutar Hunter.py" -ForegroundColor $colors['Title']
    Write-Host "  - Abre PowerShell y ejecuta:" -ForegroundColor $colors['Info']
    Write-Host "    cd D:\HunterScrap" -ForegroundColor Cyan
    Write-Host "    python3 hunter.py" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "TROUBLESHOOTING:" -ForegroundColor $colors['Title']
    Write-Host "  - ¿No se guardan los cambios?" -ForegroundColor $colors['Warning']
    Write-Host "    → Verifica permisos de escritura en /wp-content/" -ForegroundColor $colors['Info']
    Write-Host "  - ¿verify.php aún muestra ✗?" -ForegroundColor $colors['Warning']
    Write-Host "    → Espera 10 segundos y recarga la página" -ForegroundColor $colors['Info']
    Write-Host "  - ¿Problemas al enviar productos?" -ForegroundColor $colors['Warning']
    Write-Host "    → Ejecuta: .\troubleshoot.ps1" -ForegroundColor Cyan
    Write-Host ""
}

# Main
switch ($Action) {
    'generate' { Generate-Token }
    'config' { Show-Config }
    'help' { Show-Help }
    default { Show-Help }
}

Write-Host ""
Read-Host "Presiona ENTER para salir"
