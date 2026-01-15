# Setup Remoto - Giftia Hunter

Guía para clonar y ejecutar Hunter desde casa.

## 1. Clonar el Repositorio

```bash
git clone https://github.com/waltersele/giftia-hunter.git
cd giftia-hunter
```

## 2. Instalar Dependencias

```bash
# Python 3.8+ requerido
pip install -r requirements.txt
```

**Paquetes principales:**
- `selenium==4.39.0` - Navegación web automatizada
- `requests==2.32.5` - HTTP requests
- `webdriver-manager==4.0.2` - Gestión de ChromeDriver
- `beautifulsoup4==4.14.3` - Parsing HTML

## 3. Configurar Variables de Entorno

Crea un archivo `.env` en la carpeta del proyecto:

```env
# API Endpoint
WP_API_URL=https://giftia.es/wp-json/giftia/v1/ingest

# Token de autenticación (obtén del WordPress admin)
WP_API_TOKEN=nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5

# Amazon Affiliate Tag (obtén de tu cuenta Amazon Associates)
AMAZON_TAG=your-amazon-tag-here

# Google Gemini API Key (para análisis de productos)
GEMINI_API_KEY=your-gemini-api-key-here

# Navegador (chrome o firefox)
BROWSER=chrome

# Debug mode (True/False)
DEBUG=False
```

**⚠️ IMPORTANTE:** No commits .env a GitHub (está en .gitignore)

## 4. Verificar Configuración

```bash
python hunter.py --test
```

Esto ejecutará:
- ✓ Prueba de conexión a API
- ✓ Validación de tokens
- ✓ Test de Selenium/ChromeDriver

## 5. Ejecutar Hunter

### Scraping Completo (Todas las Categorías)
```bash
python hunter.py
```

### Scraping de Categoría Específica
```bash
python hunter.py --category Tech
python hunter.py --category Gourmet
python hunter.py --category Friki
python hunter.py --category Zen
python hunter.py --category Viajes
python hunter.py --category Deporte
python hunter.py --category Moda
```

### Con Cantidad Específica de Productos
```bash
python hunter.py --max-products 50
```

### Combinado
```bash
python hunter.py --category Tech --max-products 25
```

## 6. Verificar Resultados

Después de ejecutar, deberías ver output como:

```
[INFO] Starting Hunter v8.0
[INFO] Scraping category: Tech
[INFO] Found 12 products on Amazon
[INFO] Sending to API: https://giftia.es/wp-json/giftia/v1/ingest
[SUCCESS] Sent: 10, Discarded: 2
```

Luego verifica en WordPress:
```
https://giftia.es/wp-admin/edit.php?post_type=gf_gift
```

Deberías ver productos nuevos en la tabla.

## 7. Troubleshooting

### Error: "ChromeDriver not found"
```bash
# Webdriver-manager descarga automáticamente, pero si falla:
python -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"
```

### Error: "API returned 403"
- Verifica que `WP_API_TOKEN` es correcto
- Ve a WordPress admin y busca el token en Giftia Settings

### Error: "SSL Certificate Verification Failed"
```bash
# Temporal (desarrollo):
export PYTHONHTTPSVERIFY=0
python hunter.py
```

### No encuentra productos en Amazon
- Amazon cambió selectores CSS frecuentemente
- Abre issue en GitHub o actualiza los selectores en `hunter.py` líneas 480-510

## 8. Logs y Debugging

```bash
# Ver log en tiempo real
tail -f hunter.log

# Ejecutar con debug verbose
python hunter.py --debug
```

El log se guarda en `hunter.log`

## 9. Automatización (Opcional)

### Windows - Task Scheduler
```powershell
# Crear tarea que ejecuta cada día a las 8 AM
$trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM
$action = New-ScheduledTaskAction -Execute "C:\path\to\python.exe" -Argument "C:\path\to\hunter.py"
Register-ScheduledTask -TaskName "Giftia Hunter" -Trigger $trigger -Action $action
```

### macOS/Linux - Cron
```bash
# Editar crontab
crontab -e

# Ejecutar cada día a las 8 AM
0 8 * * * cd /path/to/giftia-hunter && python hunter.py >> hunter.log 2>&1
```

## 10. Estructura del Proyecto

```
giftia-hunter/
├── hunter.py              # Script principal
├── requirements.txt       # Dependencias Python
├── README.md             # Documentación
├── .gitignore            # Excluir .env y logs
├── .env                  # Variables de entorno (LOCAL)
└── hunter.log            # Log de ejecución (LOCAL)
```

## 11. Contacto / Soporte

- **Repo Hunter:** https://github.com/waltersele/giftia-hunter
- **Repo Plugin:** https://github.com/waltersele/giftfinder-core
- **Website:** https://giftia.es

## Checklist Inicial

- [ ] Clone el repo
- [ ] Instale dependencias (`pip install -r requirements.txt`)
- [ ] Cree `.env` con credenciales
- [ ] Ejecute `python hunter.py --test`
- [ ] Ejecute `python hunter.py` para scraping inicial
- [ ] Verifique productos en WordPress admin
- [ ] Suba cambios a GitHub si modifica algo

---

**Versión:** 1.0  
**Última actualización:** 15 de Enero 2026
