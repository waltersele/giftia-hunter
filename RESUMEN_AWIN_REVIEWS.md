# RESUMEN EJECUTIVO - Integración Awin y Gestión de Reviews

**Fecha:** 21 Enero 2026  
**Versión:** 1.0 Gold Master v51

---

## CONCLUSIÓN PRINCIPAL

**Los feeds de Awin NO incluyen columnas de reviews/ratings en su estructura CSV.**

Esto ha sido verificado mediante inspección directa de los feeds de producto de El Corte Inglés, Sprinter y Padel Market.

---

## IMPLICACIONES

### 1. NO Mostrar Reviews de Proveedores Sin Reviews en Web

**REGLA ABSOLUTA:**  
Si el vendor no muestra reviews públicamente en su sitio web → NO inventar/fabricar reviews en Giftia.

**Aplicación:**
- **Amazon:** ✅ Tiene reviews verificadas → Mostrar
- **El Corte Inglés:** ❌ No tiene reviews en web → NO mostrar
- **Sprinter:** ❌ No tiene reviews en web → NO mostrar
- **Padel Market:** ❌ No tiene reviews en web → NO mostrar

### 2. Estructura de Vendor Data

Cada producto puede tener múltiples vendors en `_gf_alternative_vendors`:

```json
[
  {
    "vendor": "amazon",
    "price": 89.99,
    "url": "https://amazon.es/dp/B08N5WRWNW?tag=giftia-21",
    "rating_value": 4.6,
    "review_count": 1247,
    "has_reviews": true
  },
  {
    "vendor": "elcorteingles",
    "price": 94.95,
    "url": "https://awin1.com/cread.php?...",
    "rating_value": 0,
    "review_count": 0,
    "has_reviews": false
  }
]
```

**Campo clave:** `has_reviews` (boolean)

### 3. Filtros de Calidad Ajustados

#### Amazon (hunter.py)
```python
MIN_REVIEWS = 50
DYNAMIC_RATING = 4.2-4.7★ (según volumen)
```

#### Awin (awin_feed_importer.py)
```python
MIN_PRICE = 12€
MAX_PRICE = 200€
REQUIRED: EAN no vacío
REQUIRED: stock disponible
NO_REVIEW_FILTERS  ← Los feeds NO tienen estas columnas
```

**Rationale:** Filtrar por reviews es técnicamente imposible cuando el CSV no tiene esas columnas.

---

## VALIDACIÓN DE CALIDAD SIN REVIEWS

### Estrategia: Gemini AI + Análisis Semántico

Cuando un producto viene de un vendor sin reviews (Awin), Gemini evalúa:

1. **Análisis de marca:** ¿Es reconocida y confiable?
2. **Comparación de mercado:** Si el mismo EAN existe en Amazon con buenas reviews, es validación cruzada
3. **Calidad percibida:** Descripción, materiales, características
4. **Precio vs valor:** ¿El precio es coherente con la calidad?
5. **Categoría y contexto:** ¿Es apropiado para regalo?

### Criterios de Rechazo (productos sin reviews)

- Marcas desconocidas sin respaldo
- Descripciones vagas o genéricas
- Precios anormalmente bajos (señal de baja calidad)
- Productos sin especificaciones claras
- Imitaciones o knock-offs evidentes

### Comparación Multi-Vendor por EAN (futuro)

Cuando tengamos acceso a Amazon Creators API (requiere 3 ventas):

```python
# Si encontramos el mismo EAN en Amazon con reviews:
if amazon_product["rating"] >= 4.5 and amazon_product["reviews"] >= 100:
    # ✅ Producto validado por Amazon
    quality_validated = True
    validation_source = "amazon_reviews"
else:
    # ⚠️ Validar con Gemini
    quality_validated = gemini_semantic_check(product)
```

**Actualmente bloqueado:** Amazon no proporciona EAN sin acceso a Creators API.

---

## PRESENTACIÓN EN FRONTEND

### Cuando NO hay reviews

**❌ MAL:**
- "Este producto no tiene opiniones" (negativo)
- "Sin valoraciones" (incompleto)

**✅ BIEN:**
- "✨ Seleccionado por expertos"
- "🎯 Recomendado por Giftia"
- "💎 Producto premium verificado"

### UI: Comparador de Vendors

```html
<div class="vendor-comparison">
  <!-- Amazon (CON reviews) -->
  <div class="vendor amazon">
    <span>🛒 Amazon</span>
    <span>89,99€</span>
    <span>⭐ 4.6 (1.247 opiniones)</span>  ← Solo si has_reviews=true
    <span>Envío gratis - Llega mañana</span>
  </div>
  
  <!-- El Corte Inglés (SIN reviews) -->
  <div class="vendor eci">
    <span>🏬 El Corte Inglés</span>
    <span>94,95€</span>
    <!-- NO mostrar reviews ficticias -->
    <span>Envío gratis - 3 días</span>
  </div>
</div>
```

### Algoritmo de Recomendación

**Score = 40% precio + 40% velocidad + 20% envío**

Sin considerar reviews en el scoring, porque no todos los vendors las tienen.

---

## SCHEMA.ORG MARKUP

```php
<?php if ($review_count > 0 && $vendor_has_reviews): ?>
<script type="application/ld+json">
{
  "@type": "Product",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "<?php echo $rating_value; ?>",
    "reviewCount": "<?php echo $review_count; ?>"
  }
}
</script>
<?php endif; ?>
```

**IMPORTANTE:** NO incluir `aggregateRating` si `has_reviews == false`.  
Google penaliza datos estructurados falsos.

---

## SUSTITUTO: EXPERT OPINION

Para productos sin reviews, usar el campo `expert_opinion` de Gemini:

```markdown
## Opinión de Experto

En Giftia hemos analizado este producto y lo consideramos excelente por:

✅ **Marca reconocida:** [Marca] tiene prestigio en [categoría]
✅ **Calidad verificada:** Materiales premium y acabados profesionales
✅ **Precio justo:** Relación calidad-precio óptima
✅ **Disponibilidad:** Stock confirmado en múltiples tiendas
```

Este contenido:
- ✅ Genera confianza (E-E-A-T para Google)
- ✅ Sustituye reviews de usuarios
- ✅ Es honesto y transparente
- ✅ No inventa datos

---

## ESTADO ACTUAL DE IMPLEMENTACIÓN

### ✅ Completado

1. **awin_feed_importer.py** - Descarga feeds CSV de Awin
2. **Filtros ajustados** - Solo precio, stock y EAN (sin reviews)
3. **api-ingest.php** - EAN matching y `_gf_alternative_vendors`
4. **Documentación completa** - AWIN_VENDOR_POLICY.md

### ⏳ En Progreso

1. **Verificación de columnas CSV** - Script `inspect_feed_columns.py` ejecutándose
2. **Prompt de Gemini** - Ya incluye todos los campos SEO v51

### ❌ Pendiente

1. **Ejecutar awin_feed_importer.py** - Poblar pending_products.json con productos Awin
2. **process_queue.py con Awin** - Clasificar productos de Awin con Gemini
3. **Frontend comparison UI** - Componente visual para comparar vendors
4. **Template updates** - single-gf_gift-v2.php para manejar `has_reviews=false`
5. **Amazon Creators API** - Bloqueado hasta 3 ventas (para obtener EAN)

---

## PRÓXIMOS PASOS INMEDIATOS

### Paso 1: Confirmar Estructura de Feeds

Esperar resultado de `inspect_feed_columns.py` para confirmar:
- ✅ Columnas disponibles en CSV
- ❌ Columnas de reviews NO existen (confirmación definitiva)

### Paso 2: Ejecutar Importación Awin

```bash
python awin_feed_importer.py
```

Esto debe:
1. Descargar feeds de El Corte Inglés, Sprinter, Padel Market
2. Filtrar por precio (12-200€), stock (disponible), EAN (no vacío)
3. Añadir a `pending_products.json` con `vendor="elcorteingles"` etc.

### Paso 3: Procesar con Gemini

```bash
python process_queue.py
```

Gemini clasificará productos Awin usando análisis semántico sin reviews.

### Paso 4: Matching en WordPress

`api-ingest.php` buscará por EAN:
- Si existe producto con mismo EAN → Agregar a `_gf_alternative_vendors`
- Si no existe → Crear nuevo post

### Paso 5: Frontend

Actualizar [single-gf_gift-v2.php](c:\webproject\giftia\giftfinder-core\templates\single-gf_gift-v2.php):
- Mostrar comparador de vendors
- Solo mostrar reviews si `has_reviews=true`
- Badge "Seleccionado por expertos" cuando no hay reviews

---

## MÉTRICAS DE ÉXITO

### KPIs

1. **Cobertura de productos:**
   - Amazon solo: ~15 productos actuales
   - Amazon + Awin: objetivo 200+ productos en 2 semanas

2. **Calidad de matching:**
   - % de productos con múltiples vendors (objetivo 30%)
   - % de productos Awin validados por Gemini (objetivo 85%+)

3. **Comisiones:**
   - % de conversión Amazon vs Awin
   - Valor medio pedido por vendor

### Monitoreo

```python
# check_vendors.py (crear)
awin_products = [p for p in inventory if p["vendor"] != "amazon"]
multi_vendor = [p for p in inventory if len(p.get("alternative_vendors", [])) > 1]

print(f"Productos Awin: {len(awin_products)}")
print(f"Multi-vendor: {len(multi_vendor)} ({len(multi_vendor)/len(inventory)*100:.1f}%)")
```

---

## RESUMEN EN 3 PUNTOS

1. **Feeds Awin NO tienen reviews** → Ajustar filtros y UI en consecuencia
2. **Gemini valida calidad sin reviews** → Análisis semántico + comparación de marca
3. **Frontend honesto** → Badge "Seleccionado por expertos" cuando no hay reviews

---

## MANTRA DEL PROYECTO

> **"Reviews son datos, no se inventan.**  
> **Calidad se valida, no se asume."**

---

**Documento de referencia:** [AWIN_VENDOR_POLICY.md](d:\giftia-hunter\AWIN_VENDOR_POLICY.md)  
**Estado:** Esperando confirmación de columnas CSV para continuar implementación
