# Giftia Hunter v8.0

## Descripción
Sistema automático de scraping de Amazon para buscar y enviar productos a WordPress vía API REST.

## Historial de Fixes (15 Enero 2026)

### Problemas Resueltos:
1. **HTTP 500 en api-ingest.php**
   - Error: Sintaxis PHP incorrecta (llave de cierre extra en línea 227)
   - Solución: Removida llave duplicada
   - Archivo: `c:\webproject\giftia\giftfinder-core\api-ingest.php`

2. **Endpoint de API incorrecto**
   - Error: Hunter usaba ruta directa a PHP que WordPress interceptaba
   - Solución: Creado endpoint REST API `/wp-json/giftia/v1/ingest`
   - Archivo: `c:\webproject\giftia\giftfinder-core\giftfinder-core.php`
   - URL antigua: `https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php`
   - URL nueva: `https://giftia.es/wp-json/giftia/v1/ingest`

3. **Amazon scraping retorna 0 productos**
   - Error: Selectores CSS desactualizados (`div[data-component-type="s-search-result"]` no encontraba elementos)
   - Solución: Agregado WebDriverWait + JavaScript para esperar carga dinámica
   - Archivos: `hunter.py` (líneas 480-510)

4. **Token no coincide entre Hunter y API**
   - Token verificado: `nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5`
   - Ambos usan el mismo token (correcto)

5. **Error de sintaxis Python en hunter.py**
   - Error: Comillas sin escapar en f-string (línea 498)
   - Solución: Usado comillas simples externas

## Configuración

### Variables de entorno:
```
WP_API_TOKEN=nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5
WP_API_URL=https://giftia.es/wp-json/giftia/v1/ingest
AMAZON_TAG=GIFTIA-21
```

### Instalación:
```bash
pip install -r requirements.txt
python hunter.py
```

## Estado Actual (15 Enero 2026 - 15:10 UTC)

- ✅ API REST: Funcional
- ✅ Token: Verificado
- 🔄 Hunter: En ejecución (buscando productos)
- ❓ Scraping Amazon: Buscando solución (selectores CSS actualizados)

## Próximos Pasos:
1. Esperar que Hunter complete búsquedas
2. Verificar productos en WordPress: `https://giftia.es/wp-admin/edit.php?post_type=gf_gift`
3. Si no se crean productos, revisar logs de API

## Archivo de Tokens (.env) - NO GUARDAR EN GIT
```
WP_API_TOKEN=nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5
GEMINI_API_KEY=<tu_key>
AMAZON_TAG=GIFTIA-21
```
⚠️ Guardar en `.env` local SOLAMENTE - añadido a `.gitignore`

## Contacto
Para continuar en otra PC: clonar repo y instalar `pip install -r requirements.txt`
