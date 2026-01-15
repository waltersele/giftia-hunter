#!/usr/bin/env pwsh
<#
.SYNOPSIS
    GIFTIA Troubleshooting Script - PowerShell Edition
.DESCRIPTION
    Herramientas para diagnóstico y ejecución de Hunter.py
.EXAMPLE
    .\troubleshoot.ps1
.AUTHOR
    GIFTIA Team
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('check', 'hunter', 'test', 'logs', 'verify', 'full')]
    [string]$Action = 'menu'
)

# Colors
$colors = @{
    'Info'    = 'Cyan'
    'Success' = 'Green'
    'Error'   = 'Red'
    'Warning' = 'Yellow'
}

function Show-Banner {
    Clear-Host
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host "  GIFTIA TROUBLESHOOTING" -ForegroundColor Cyan
    Write-Host "  PowerShell Edition v1.0" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""
}

function Show-Menu {
    Show-Banner
    Write-Host "Opciones disponibles:" -ForegroundColor Green
    Write-Host ""
    Write-Host "  1. [CHECK]  - Verificar estado del sistema" -ForegroundColor Cyan
    Write-Host "  2. [HUNTER] - Ejecutar Hunter.py" -ForegroundColor Cyan
    Write-Host "  3. [TEST]   - Enviar producto de prueba" -ForegroundColor Cyan
    Write-Host "  4. [LOGS]   - Ver logs recientes" -ForegroundColor Cyan
    Write-Host "  5. [VERIFY] - Abrir verificador en navegador" -ForegroundColor Cyan
    Write-Host "  6. [FULL]   - Diagnóstico completo" -ForegroundColor Cyan
    Write-Host "  7. [EXIT]   - Salir" -ForegroundColor Cyan
    Write-Host ""
}

function Test-WordPress {
    Write-Host "[*] Verificando WordPress..." -ForegroundColor $colors['Info']
    
    $wp_url = "https://giftia.es/wp-content/plugins/giftfinder-core/verify.php"
    try {
        $response = Invoke-WebRequest -Uri $wp_url -TimeoutSec 5 -UseBasicParsing
        Write-Host "[✓] WordPress responde (HTTP $($response.StatusCode))" -ForegroundColor $colors['Success']
        return $true
    }
    catch {
        Write-Host "[✗] WordPress NO responde: $($_.Exception.Message)" -ForegroundColor $colors['Error']
        return $false
    }
}

function Run-HunterTest {
    Write-Host ""
    Write-Host "[*] Enviando producto de prueba..." -ForegroundColor $colors['Info']
    Write-Host ""
    
    $token = Read-Host "Pega tu API Token"
    if ([string]::IsNullOrWhiteSpace($token)) {
        Write-Host "[!] Token requerido" -ForegroundColor $colors['Error']
        return
    }
    
    Write-Host ""
    Write-Host "[*] Ejecutando test_api.py..." -ForegroundColor $colors['Info']
    python3 test_api.py --token=$token
    
    Write-Host ""
    Read-Host "Presiona ENTER para continuar"
}

function Show-Logs {
    Write-Host ""
    Write-Host "[*] Últimas 30 líneas de hunter.log:" -ForegroundColor $colors['Info']
    Write-Host ""
    
    if (Test-Path "hunter.log") {
        Get-Content "hunter.log" -Tail 30
    }
    else {
        Write-Host "[!] hunter.log no encontrado" -ForegroundColor $colors['Warning']
    }
    
    Write-Host ""
    Write-Host "[*] Últimas 30 líneas de WordPress debug.log:" -ForegroundColor $colors['Info']
    Write-Host ""
    
    $wp_log = "C:\webproject\giftia\wp-content\debug.log"
    if (Test-Path $wp_log) {
        Get-Content $wp_log -Tail 30 | ForEach-Object {
            if ($_ -match "ERROR|GIFTIA") {
                Write-Host $_ -ForegroundColor $colors['Error']
            }
            else {
                Write-Host $_
            }
        }
    }
    else {
        Write-Host "[!] debug.log no encontrado en: $wp_log" -ForegroundColor $colors['Warning']
    }
    
    Write-Host ""
    Read-Host "Presiona ENTER para continuar"
}

function Run-Hunter {
    Show-Banner
    Write-Host "Ejecutando Hunter.py..." -ForegroundColor $colors['Info']
    Write-Host ""
    
    python3 hunter.py
    
    Write-Host ""
    Write-Host "Hunter.py completado" -ForegroundColor $colors['Success']
    Write-Host ""
    Read-Host "Presiona ENTER para continuar"
}

function Open-Verify {
    Show-Banner
    Write-Host "Abriendo verificador del sistema..." -ForegroundColor $colors['Info']
    
    $url = "https://giftia.es/wp-content/plugins/giftfinder-core/verify.php"
    Start-Process $url
    
    Write-Host "Se abrió: $url" -ForegroundColor $colors['Success']
    Write-Host ""
    Read-Host "Presiona ENTER para volver al menú"
}

function Run-FullDiagnostic {
    Show-Banner
    Write-Host "DIAGNÓSTICO COMPLETO" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "[1/4] Verificando WordPress..." -ForegroundColor $colors['Info']
    Test-WordPress
    Write-Host ""
    
    Write-Host "[2/4] Verificando archivos del plugin..." -ForegroundColor $colors['Info']
    $files = @(
        "C:\webproject\giftia\giftfinder-core\api-ingest.php",
        "C:\webproject\giftia\giftfinder-core\verify.php",
        "C:\webproject\giftia\giftfinder-core\test.php"
    )
    foreach ($file in $files) {
        if (Test-Path $file) {
            Write-Host "[✓] $(Split-Path $file -Leaf)" -ForegroundColor $colors['Success']
        }
        else {
            Write-Host "[✗] $(Split-Path $file -Leaf)" -ForegroundColor $colors['Error']
        }
    }
    Write-Host ""
    
    Write-Host "[3/4] Verificando hunter.py..." -ForegroundColor $colors['Info']
    if (Test-Path "hunter.py") {
        Write-Host "[✓] hunter.py encontrado" -ForegroundColor $colors['Success']
    }
    else {
        Write-Host "[✗] hunter.py NO encontrado" -ForegroundColor $colors['Error']
    }
    Write-Host ""
    
    Write-Host "[4/4] Revisando logs recientes..." -ForegroundColor $colors['Info']
    if (Test-Path "hunter.log") {
        $errors = Select-String -Path "hunter.log" -Pattern "ERROR|FAILED" -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count
        Write-Host "[*] Errores en hunter.log: $errors" -ForegroundColor $colors['Warning']
    }
    Write-Host ""
    
    Write-Host "PRÓXIMOS PASOS:" -ForegroundColor Green
    Write-Host "1. Abre verify.php en navegador (opción 5)"
    Write-Host "2. Si todo ✓, usa opción 3 (Test)" -ForegroundColor Green
    Write-Host "3. Si test tiene HTTP 200, ejecuta opción 2 (Hunter)" -ForegroundColor Green
    Write-Host ""
    Read-Host "Presiona ENTER para volver al menú"
}

# Main loop
while ($true) {
    if ($Action -eq 'menu') {
        Show-Menu
        $choice = Read-Host "Elige opción (1-7)"
    }
    else {
        $choice = switch ($Action) {
            'check'  { '1' }
            'hunter' { '2' }
            'test'   { '3' }
            'logs'   { '4' }
            'verify' { '5' }
            'full'   { '6' }
            default  { '7' }
        }
        $Action = 'menu'  # Reset para próxima iteración
    }
    
    switch ($choice) {
        '1' { Run-FullDiagnostic }
        '2' { Run-Hunter }
        '3' { Run-HunterTest }
        '4' { Show-Logs }
        '5' { Open-Verify }
        '6' { Run-FullDiagnostic }
        '7' {
            Show-Banner
            Write-Host "¡Hasta luego!" -ForegroundColor Green
            exit
        }
        default {
            Write-Host "Opción inválida" -ForegroundColor $colors['Error']
            Read-Host "Presiona ENTER para continuar"
        }
    }
}
