# GIFTIA - Schema de Campos Completo

**Versión:** Gold Master v51.2  
**Última actualización:** 20 Enero 2026  
**Total de campos:** 30

---

## 📋 RESUMEN RÁPIDO

| Categoría | Campos | Origen | Obligatorios |
|-----------|--------|--------|--------------|
| Datos Básicos | 11 | Hunter/Amazon | ✅ Todos |
| Contenido SEO | 11 | Gemini AI | ✅ Todos |
| Taxonomías | 5 | Gemini AI | ✅ Todos |
| Calidad | 3 | Gemini AI | ✅ Todos |

---

## A. DATOS BÁSICOS (Hunter captura de Amazon)

| # | Campo | Meta Key WordPress | Tipo | Descripción | Ejemplo |
|---|-------|-------------------|------|-------------|---------|
| 1 | **title** | `post_title` | string | Título del producto | "Echo Dot 5ª Generación" |
| 2 | **image** | `_thumbnail_id` | int | ID de imagen en WP | 12345 |
| 3 | **asin** | `_gf_asin` | string(10) | ASIN de Amazon | "B0BT8BHPCQ" |
| 4 | **affiliate_url** | `_gf_affiliate_url` | url | URL con tag afiliado | "https://amazon.es/dp/B0BT8BHPCQ?tag=GIFTIA-21" |
| 5 | **price** | `_gf_current_price` | float | Precio actual en € | 59.99 |
| 6 | **rating** | `_gf_rating` | float(1-5) | Rating promedio Amazon | 4.7 |
| 7 | **reviews_count** | `_gf_reviews` | int | Número de reseñas | 15420 |
| 8 | **is_prime** | `_gf_is_prime` | bool/string | ¿Tiene Prime? | "1" o "yes" |
| 9 | **free_shipping** | `_gf_free_shipping` | bool/string | ¿Envío gratis? | "1" o "yes" |
| 10 | **delivery_time** | `_gf_delivery_time` | string | Tiempo de entrega | "Entrega mañana" |
| 11 | **amazon_reviews** | `_gf_amazon_reviews` | JSON array | Reseñas extraídas | Ver estructura abajo |

### Estructura de `amazon_reviews`:
```json
[
  {
    "author": "Juan M.",
    "rating": 5,
    "title": "Excelente calidad",
    "text": "Llegó antes de lo esperado...",
    "date": "15 enero 2026",
    "verified": true
  }
]
```

---

## B. CONTENIDO SEO (Gemini AI genera)

| # | Campo | Meta Key WordPress | Tipo | Descripción | Longitud Recomendada |
|---|-------|-------------------|------|-------------|---------------------|
| 12 | **seo_title** | `_gf_seo_title` | string | Título SEO optimizado | 50-60 chars |
| 13 | **meta_description** | `_gf_meta_description` | string | Meta description | 150-160 chars |
| 14 | **h1_title** | `_gf_h1_title` | string | H1 de la página | 40-70 chars |
| 15 | **short_description** | `_gf_short_description` | string | Descripción breve/headline | 100-200 chars |
| 16 | **full_description** | `_gf_full_description` | HTML | Descripción completa | 500-1500 chars |
| 17 | **expert_opinion** | `_gf_expert_opinion` | string | Análisis IA (typewriter) | 150-300 chars |
| 18 | **pros** | `_gf_pros` | JSON array | Lista de beneficios | 3-5 items |
| 19 | **cons** | `_gf_cons` | JSON array | Lista de desventajas | 2-3 items |
| 20 | **who_is_for** | `_gf_who_is_for` | string | Para quién es ideal | 100-200 chars |
| 21 | **faqs** | `_gf_faqs` | JSON array | Preguntas frecuentes | 3-5 FAQs |
| 22 | **verdict** | `_gf_verdict` | string | Veredicto final | 100-200 chars |

### Estructura de `pros` y `cons`:
```json
["Excelente sonido", "Diseño compacto", "Fácil configuración"]
```

### Estructura de `faqs`:
```json
[
  {
    "question": "¿Es compatible con Alexa?",
    "answer": "Sí, incluye Alexa integrada..."
  }
]
```

---

## C. TAXONOMÍAS (WordPress Terms)

| # | Campo | Taxonomía WP | Descripción | Valores Válidos |
|---|-------|-------------|-------------|-----------------|
| 23 | **category** | `gf_category` | Categoría principal | tech, gaming, cocina, deporte, outdoor, viajes, hogar, belleza, moda, libros, musica, mascotas, bebes, manualidades, jardineria, original |
| 24 | **ages** | `gf_age` | Edades objetivo | ninos, adolescentes, jovenes, adultos, seniors, abuelos |
| 25 | **occasions** | `gf_occasion` | Ocasiones | cumpleanos, navidad, san-valentin, dia-madre, dia-padre, aniversario, boda, graduacion, jubilacion, nuevo-hogar |
| 26 | **recipients** | `gf_recipient` | Destinatarios | padre, madre, pareja, amigo, hermano, abuelo, hijo, jefe, companero |
| 27 | **budget** | `gf_budget` | Rango presupuesto | bajo (<20€), medio (20-50€), alto (50-100€), premium (>100€) |

### Mapeo de Categorías (Schema → Slug):
```
Tech → tech
Gamer → gaming
Gourmet → cocina
Deporte → deporte
Outdoor → outdoor
Viajes → viajes
Hogar → hogar
Belleza → belleza
Moda → moda
Libros → libros
Música → musica
Mascotas → mascotas
Bebés → bebes
DIY → manualidades
Jardín → jardineria
Experiencias → original
```

### Mapeo de Edades (Schema → Slug):
```
Niños (0-12) → ninos
Adolescentes (13-17) → adolescentes
Jóvenes (18-30) → jovenes
Adultos (31-50) → adultos
Seniors (51-65) → seniors
Abuelos (65+) → abuelos
```

---

## D. CALIDAD Y SCORING

| # | Campo | Meta Key WordPress | Tipo | Rango | Descripción |
|---|-------|-------------------|------|-------|-------------|
| 28 | **gift_quality** | `_gf_gift_quality` | int | 1-10 | Puntuación calidad regalo |
| 29 | **giftia_score** | `_gf_giftia_score` | float | 1-5 | Score Giftia (mostrado) |
| 30 | **marketing_hook** | `_gf_hook` | string | enum | Hook de marketing |

### Valores de `marketing_hook`:
```
core      → Producto esencial
habitat   → Para el hogar
style     → Estilo/Moda
hedonism  → Placer/Experiencia
wildcard  → Sorpresa/Original
```

---

## E. CAMPOS ADICIONALES (Tracking)

| Campo | Meta Key | Descripción |
|-------|----------|-------------|
| last_update | `_gf_last_update` | Última actualización |
| seo_version | `_gf_seo_version` | Versión del prompt SEO |
| data_source | `_gf_data_source` | Origen (hunter/manual) |
| price_history | `_gf_price_history` | Histórico de precios |
| on_sale | `_gf_on_sale` | ¿Está en oferta? |
| sale_percent | `_gf_sale_percent` | % de descuento |

---

## 🔄 FLUJO DE DATOS

```
┌─────────────────────────────────────────────────────────────────┐
│                        HUNTER (Python)                          │
│  Scrapea Amazon → Extrae campos 1-11 → pending_products.json    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PROCESS_QUEUE (Python)                       │
│  Lee pending → Envía a Gemini → Gemini genera campos 12-30      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API-INGEST (PHP)                            │
│  Recibe JSON → Crea/Actualiza post → Guarda meta fields         │
│  POST https://giftia.es/.../api-ingest.php                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       WORDPRESS (PHP)                            │
│  wp_posts + wp_postmeta + taxonomías                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SINGLE-GF_GIFT (Template)                      │
│  Muestra todos los campos en la ficha de producto               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 VERIFICACIÓN DE COMPLETITUD

### Script: `verify_product_data.py`
```bash
# Ver estado de todos los productos
python verify_product_data.py

# Exportar reporte JSON
python verify_product_data.py --export reporte.json

# Exportar ASINs que necesitan actualización
python verify_product_data.py --export-asins faltantes.txt
```

### Script: `update_shipping_info.py`
```bash
# Actualizar productos sin info de envío
python update_shipping_info.py --limit 100

# Modo prueba (no hace cambios)
python update_shipping_info.py --dry-run
```

---

## 🔌 ENDPOINTS API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `?action=products_without_shipping` | GET | Lista productos sin Prime/envío |
| `?action=update_shipping` | POST | Actualiza solo campos envío |
| `?action=get_all_products_meta` | GET | Exporta todos los productos con meta |
| `?action=update_asin` | POST | Actualiza ASIN de un producto |
| `?action=update_status` | POST | Cambia estado (publish/draft) |
| `?action=update_reviews` | POST | Actualiza reseñas de Amazon |
| (default) | POST | Ingesta completa de producto |

---

## ✅ CHECKLIST PRE-PUBLICACIÓN

Antes de publicar un producto, verificar:

- [ ] **Título** - Claro y descriptivo
- [ ] **Imagen** - Alta calidad, fondo limpio
- [ ] **ASIN** - Válido y activo en Amazon
- [ ] **Precio** - Actualizado
- [ ] **Rating** - Mayor a 3.5
- [ ] **Prime/Envío** - Información correcta
- [ ] **SEO Title** - 50-60 caracteres
- [ ] **Meta Description** - 150-160 caracteres
- [ ] **Expert Opinion** - Para el typewriter IA
- [ ] **Pros** - Mínimo 3
- [ ] **Cons** - Mínimo 2
- [ ] **Categoría** - Asignada
- [ ] **Edad** - Al menos una
- [ ] **Ocasión** - Al menos una
- [ ] **Presupuesto** - Según precio

---

## 📁 ARCHIVOS RELACIONADOS

| Archivo | Ubicación | Función |
|---------|-----------|---------|
| `hunter.py` | D:\giftia-hunter\ | Scraping de Amazon |
| `process_queue.py` | D:\giftia-hunter\ | Procesamiento Gemini |
| `extract_reviews.py` | D:\giftia-hunter\ | Extracción reseñas |
| `update_shipping_info.py` | D:\giftia-hunter\ | Actualiza envío |
| `verify_product_data.py` | D:\giftia-hunter\ | Verifica completitud |
| `api-ingest.php` | giftfinder-core/ | Endpoint ingesta |
| `giftia-templates.php` | templates/ | Carga datos producto |
| `single-gf_gift.php` | templates/ | Template ficha |

---

**Autor:** Giftia Development Team  
**Contacto:** dev@giftia.es
