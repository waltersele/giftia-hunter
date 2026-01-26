# Instrucciones para Copilot - Giftia Hunter

**Versión:** 11.0 (Gold Master v51)  
**Última actualización:** 19 Enero 2026

## REGLAS OBLIGATORIAS

### 1. INVESTIGAR ANTES DE ESCRIBIR
- Leer `process_queue.py` completo antes de modificar
- El prompt de Gemini ya tiene todos los campos SEO v51
- No añadir campos nuevos sin verificar el schema

### 2. FUENTE ÚNICA DE VERDAD
- `giftia_schema.json` define categorías, edades, géneros, etc.
- NO hardcodear valores, leer del schema
- Si algo no está en el schema, no inventarlo

### 3. NO DUPLICAR LÓGICA
- `classify_batch_with_gemini()` ya genera todos los campos SEO
- `process_product()` es legacy, el flujo principal usa batches
- No crear funciones nuevas para lo mismo

## ARQUITECTURA

### Flujo Principal
```
hunter.py → pending_products.json → process_queue.py → Gemini → api-ingest.php
```

### Archivos Clave

| Archivo | Función |
|---------|---------|
| `hunter.py` | Scraper de Amazon con Selenium |
| `process_queue.py` | Procesador batch + Gemini + envío a WP |
| `giftia_schema.json` | Schema centralizado (17 categorías, 6 edades, etc.) |

### Configuración

```python
WP_API_URL = "https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php"
WP_TOKEN = "LEER_DESDE_ENV_FILE"
BATCH_SIZE = 3
GEMINI_PACING_SECONDS = 1
```

### Campos SEO que Gemini Genera

```python
seo_title           # Meta title 50-60 chars
meta_description    # Snippet 150-160 chars
h1_title            # H1 persuasivo 40-70 chars
short_description   # Above the fold 80-120 palabras
expert_opinion      # E-E-A-T 100-150 palabras
pros                # 5-6 bullets emocionales
cons                # 2-3 bullets honestos
full_description    # SEO 600-800 palabras con H2s
who_is_for          # Buyer persona 80-100 palabras
faqs                # 4-5 Q&A para Featured Snippets
verdict             # Conclusión 50-80 palabras
seo_slug            # URL amigable max 5 palabras
```

### NO TOCAR

- El prompt de Gemini en `classify_batch_with_gemini()` ya está completo
- La lógica de verificación de respuesta (`"success":true`) ya maneja el 500 de WP
- Los filtros de calidad (4 filtros de excelencia) están calibrados
