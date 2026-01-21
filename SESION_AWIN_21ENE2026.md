# SESIÓN AWIN - 21 Enero 2026

## ESTADO ACTUAL

### Objetivo
Integrar productos de Awin (El Corte Inglés, Sprinter, Padel Market) como **vendors alternativos** en productos Amazon existentes, para ofrecer comparación multi-vendor.

### Descubrimiento Clave
- **607 productos WordPress publicados**
- **0 productos tienen EAN** (0%)
- **532 productos tienen ASIN** (87.6%)
- **Awin feeds SÍ incluyen EAN** en CSV
- **Problema**: No podemos hacer matching EAN directo porque Amazon no lo tiene

---

## DECISIONES TOMADAS

### 1. NO Crear Páginas Nuevas de Awin
❌ **Rechazado**: Importar 100k productos Awin y procesar todos con Gemini
✅ **Aprobado**: Awin como **vendor alternativo** en productos existentes

**Razón**: "No vamos a posicionar por producto en la vida" si creamos 10k páginas sin contenido SEO trabajado.

### 2. Estrategia de Matching
**Nivel 1**: Match por EAN → ❌ Bloqueado (Amazon no tiene EAN)
**Nivel 2**: Match por título original + marca → ❌ Bloqueado (Gemini cambia títulos SEO)
**Nivel 3**: **Scraping Amazon → Extraer EAN** ✅ SOLUCIÓN

### 3. Filtrado Categorial Estricto
- Antes de importar 100k productos Awin, filtrar por categorías que SÍ sean regalos
- Script `analyze_awin_categories.py` analiza categorías reales de feeds
- Blacklist automática de: electrodomésticos grandes, muebles, alimentación granel, ropa con tallas, limpieza

### 4. Flujo Dual (después de tener EANs)
**A) Producto Awin CON match EAN en WordPress:**
- NO procesar con Gemini (ahorro masivo)
- Añadir como `_gf_alternative_vendors`
- Heredar clasificación existente
- Solo actualizar precio/stock

**B) Producto Awin SIN match:**
- SÍ pasa a `pending_products.json`
- SÍ procesado por Gemini (genera SEO v51)
- Crea página nueva (pero solo ~20% tras filtros)

---

## ARCHIVOS CREADOS

### 1. `analyze_awin_categories.py`
- **Estado**: ⏳ Ejecutando (descargando El Corte Inglés 69k productos)
- **Función**: Analiza categorías reales de feeds Awin
- **Output**: `awin_categories_13075.json`, `awin_blacklist_13075.json`

### 2. `fetch_wp_inventory.py`
- **Estado**: ✅ Ejecutado completamente
- **Función**: Obtiene inventario completo de WordPress
- **Output**: 
  - `wp_inventory.json` (607 productos completos)
  - `wp_products_no_ean.json` (607 productos sin EAN)

### 3. `awin_feed_importer.py`
- **Estado**: ⏸️ Pausado (esperando estrategia EAN)
- **Función**: Descarga feeds Awin, filtra, transforma a formato Giftia
- **Modificaciones pendientes**: Añadir filtro categorial tras análisis

### 4. `inspect_feed_columns.py`
- **Estado**: ❓ Estado desconocido (script de verificación CSV)
- **Función**: Verificar columnas exactas de feeds Awin

---

## PRÓXIMOS PASOS (SESIÓN CASA)

### FASE 1: Enriquecimiento de EAN (URGENTE)
```bash
# Opción recomendada: Scraping Amazon
python enrich_ean_from_amazon.py
# Input: wp_products_no_ean.json (532 con ASIN)
# Output: wp_inventory_enriched.json (con EANs extraídos)
# Duración estimada: 2-3 horas (532 productos, 15seg/producto)
```

**Crear script**: `enrich_ean_from_amazon.py`
- Leer `wp_products_no_ean.json`
- Para cada producto con ASIN:
  - Scrape `https://www.amazon.es/dp/{ASIN}`
  - Extraer EAN de tabla "Detalles del producto"
  - Actualizar WordPress con `_gf_ean` vía API
- Rate limiting: 15 segundos entre requests

### FASE 2: Análisis Categorías Awin (EN PROGRESO)
```bash
# Esperar a que termine analyze_awin_categories.py
# Revisar output: awin_categories_13075.json
# Ajustar blacklist si es necesario
# Repetir para Sprinter (27904) y Padel Market (24562)
```

### FASE 3: Importación Awin con Matching
```bash
# Modificar awin_feed_importer.py con:
# 1. Filtro categorial (blacklist)
# 2. Match EAN con wp_inventory_enriched.json
# 3. Si match → Actualizar vendor, NO Gemini
# 4. Si no match → pending_products.json → Gemini

python awin_feed_importer.py
```

### FASE 4: Actualización WordPress
```bash
# Enviar vendors alternativos a WordPress
python update_alternative_vendors.py
# Input: awin_matched_products.json
# Action: POST a api-ingest.php con _gf_alternative_vendors
```

---

## CONFIGURACIÓN NECESARIA

### .env (Ya configurado)
```env
AWIN_FEEDLIST_URL=https://...
AWIN_PUBLISHER_ID=...
AWIN_API_KEY=...
AWIN_MERCHANTS=13075,27904,24562
WP_API_TOKEN=nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5
```

### Merchants
- **13075**: El Corte Inglés (69,606 productos)
- **27904**: Sprinter (118,288 productos estimados)
- **24562**: Padel Market

---

## DUDAS/DECISIONES PENDIENTES

### 1. Scraping Amazon
- ¿Usar Selenium (como hunter.py) o requests simple?
- ¿Qué hacer si Amazon no muestra EAN en algunos productos?
- ¿Proxy/rotación IP necesario para 532 requests?

### 2. Categorías Awin
- ¿Revisar manualmente las categorías top antes de blacklist?
- ¿Importar TODAS las categorías gift-worthy o limitar a top 20?

### 3. Precio/Competitividad
- ¿Solo importar Awin si precio es 5% menor que Amazon?
- ¿O importar siempre para dar opciones al usuario?

### 4. Frontend
- ¿Diseño de UI multi-vendor lo hacemos después de importación?
- ¿Scoring: 40% precio + 40% delivery + 20% shipping? (ya definido)

---

## COMANDOS RÁPIDOS (CASA)

### Ver estado de análisis categorías
```bash
cd d:\giftia-hunter
Get-Process | Where-Object {$_.Name -like '*python*'}
```

### Continuar desde donde dejamos
```bash
# 1. Revisar inventario
cat wp_inventory.json | jq '.[] | select(.has_asin == true) | .post_id' | wc -l

# 2. Crear script enriquecimiento EAN
code enrich_ean_from_amazon.py

# 3. Ejecutar enriquecimiento (¡largo!)
python enrich_ean_from_amazon.py

# 4. Verificar categorías Awin
cat awin_categories_13075.json | jq '.categories | to_entries | sort_by(-.value) | .[0:20]'
```

---

## CITAS IMPORTANTES DEL USUARIO

> "No vamos a poner reseñas de proveedores que no tengan en su página"

> "Primero deberás preguntarme, no? La primera haremos una búsqueda grande para llenar stock, luego solo analizaremos si han cambiado o bajado de precio"

> "No vamos a posicionar por producto en la vida" (si creamos 10k páginas sin SEO)

> "Título + marca no va a funcionar, porque los genera Gemini para el SEO"

> "Primero, deberemos tener EAN de los productos en stock"

---

## REFERENCIAS TÉCNICAS

### Estructura WordPress Meta Fields
```php
_gf_ean              // EAN del producto (vacío actualmente)
_gf_asin             // ASIN de Amazon (87.6% tienen)
_gf_brand            // Marca (mayoría vacío)
_gf_original_title   // Título scrapeado original (NO existe, pendiente añadir)
_gf_alternative_vendors  // Array de vendors alternativos (estructura v51)
```

### Estructura `_gf_alternative_vendors`
```json
[
  {
    "vendor": "El Corte Inglés",
    "price": 249.99,
    "affiliate_url": "https://...",
    "delivery_time": "24-48h",
    "free_shipping": true,
    "has_reviews": false,
    "in_stock": true
  }
]
```

### API WordPress para actualizar
```bash
POST https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php
Header: X-GIFTIA-TOKEN: nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5
Body: {
  "post_id": 3155,
  "ean": "194253398707",
  "alternative_vendors": [...]
}
```

---

## ESTIMACIONES TIEMPO

| Tarea | Tiempo Estimado |
|-------|----------------|
| Enriquecimiento EAN (532 productos) | 2-3 horas |
| Análisis categorías Awin (3 merchants) | 30 min (automático) |
| Modificación awin_feed_importer.py | 1 hora |
| Importación Awin con matching | 1-2 horas |
| Testing multi-vendor en WordPress | 30 min |
| **TOTAL FASE 1** | **5-7 horas** |

---

## FECHA/HORA SESIÓN
- **Inicio**: 21 Enero 2026, ~10:00 (estimado)
- **Pausa**: 21 Enero 2026, ~12:30 (estimado)
- **Reanudar**: Casa (pendiente)

---

## NOTAS FINALES

1. **CRÍTICO**: Sin EANs no podemos hacer matching Awin-WordPress
2. **Prioridad 1**: Script `enrich_ean_from_amazon.py` es el bloqueador principal
3. **Gemini ahorro**: Con matching EAN correcto, ahorramos ~80% procesamiento Gemini
4. **SEO intacto**: Multi-vendor no crea páginas nuevas, enriquece existentes
5. **Categorías**: Blacklist automática evita basura (electrodomésticos, muebles, etc)

---

**CONTINUAR EN CASA**: Ejecutar `python enrich_ean_from_amazon.py` primero.
