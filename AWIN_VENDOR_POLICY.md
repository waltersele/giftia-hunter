# Política de Vendors y Reviews - Awin Integration

**Versión:** 1.0  
**Fecha:** 21 Enero 2026

---

## REGLA FUNDAMENTAL

**NO mostrar reviews/ratings de productos de vendors que NO las tienen en su página web.**

### Principio de Autenticidad
- Si El Corte Inglés no muestra reviews en su web → NO inventar reviews
- Si Sprinter no muestra reviews en su web → NO inventar reviews
- Solo Amazon tiene reviews verificadas → Solo mostrar reviews de Amazon

---

## ARQUITECTURA DE MULTI-VENDOR

### Estructura de Datos

```php
// WordPress meta fields
_gf_ean                     // EAN del producto (clave de matching)
_gf_primary_vendor          // "amazon" | "elcorteingles" | "sprinter" | "padelmarket"
_gf_alternative_vendors     // Array serializado de todos los vendors
```

### Formato de Alternative Vendors

```json
[
  {
    "vendor": "amazon",
    "price": 89.99,
    "url": "https://amazon.es/dp/B08N5WRWNW?tag=giftia-21",
    "availability": "En stock",
    "delivery_days": 1,
    "shipping_cost": 0,
    "rating_value": 4.6,
    "review_count": 1247,
    "has_reviews": true
  },
  {
    "vendor": "elcorteingles",
    "price": 94.95,
    "url": "https://awin1.com/cread.php?...",
    "availability": "En stock",
    "delivery_days": 3,
    "shipping_cost": 0,
    "rating_value": 0,
    "review_count": 0,
    "has_reviews": false
  }
]
```

### Campos por Vendor

| Campo | Amazon | Awin (ECI/Sprinter/etc) |
|-------|---------|------------------------|
| `price` | ✅ Obligatorio | ✅ Obligatorio |
| `url` | ✅ Afiliado Amazon | ✅ Afiliado Awin |
| `availability` | ✅ Scrapeado | ✅ Feed CSV |
| `delivery_days` | ✅ Scrapeado | ✅ Feed CSV |
| `shipping_cost` | ✅ Scrapeado | ✅ Feed CSV |
| `rating_value` | ✅ 0.0-5.0 | ⚠️ 0 (no disponible) |
| `review_count` | ✅ N° real | ⚠️ 0 (no disponible) |
| `has_reviews` | ✅ true | ❌ false |

---

## FILTROS DE CALIDAD

### Amazon (hunter.py)
```python
MIN_PRICE = 12€
MAX_PRICE = 9999€
MIN_REVIEWS = 50
DYNAMIC_RATING:
  - 1000+ reviews → 4.2★ mínimo
  - 500-999 reviews → 4.3★ mínimo
  - 100-499 reviews → 4.5★ mínimo
  - 50-99 reviews → 4.7★ mínimo
```

### Awin (awin_feed_importer.py)
```python
MIN_PRICE = 12€
MAX_PRICE = 200€
REQUIRED: EAN no vacío
REQUIRED: in_stock = "yes"
NO_REVIEW_FILTERS ← ¡IMPORTANTE!
```

**Rationale:** Los feeds de Awin NO incluyen columnas de reviews/ratings en su CSV. Filtrar por reviews es técnicamente imposible a nivel de feed.

---

## EVALUACIÓN DE CALIDAD CON GEMINI

### Problema
Sin reviews de usuarios, ¿cómo garantizar que productos Awin sean buenos regalos?

### Solución: Análisis Semántico con Gemini

```python
# process_queue.py - classify_batch_with_gemini()

prompt_awin = """
CONTEXTO: Este producto viene de {vendor} (NO tiene reviews de usuarios).

EVALUACIÓN ALTERNATIVA:
1. **Análisis de marca**: ¿Es una marca reconocida y confiable?
2. **Comparación de mercado**: Si el mismo EAN existe en Amazon con buenas reviews, es señal positiva
3. **Calidad percibida**: Descripción, materiales, características
4. **Precio vs valor**: ¿El precio es coherente con la calidad esperada?
5. **Categoría y contexto**: ¿Es apropiado para la ocasión/destinatario?

CRITERIOS DE RECHAZO (sin reviews):
- Marcas desconocidas sin respaldo
- Descripciones vagas o genéricas
- Precios anormalmente bajos (señal de baja calidad)
- Productos sin especificaciones técnicas claras
- Imitaciones o knock-offs evidentes

COMPARACIÓN MULTI-VENDOR:
Si encuentras el mismo EAN en Amazon con reviews:
- Rating Amazon ≥4.5★ + 100+ reviews → Producto validado para cualquier vendor
- Rating Amazon 4.0-4.4★ → Revisar descripción y precio en vendor alternativo
- Rating Amazon <4.0★ → Rechazar incluso si está en otro vendor

ACCIÓN: ¿Este producto pasa el filtro de calidad para Giftia?
"""
```

### Lógica de Comparación

```python
# 1. Buscar mismo EAN en Amazon (inventory check)
amazon_product = find_by_ean_in_amazon_inventory(ean)

if amazon_product and amazon_product["rating_value"] >= 4.5 and amazon_product["review_count"] >= 100:
    # ✅ Producto validado por Amazon
    quality_validated = True
    validation_source = "amazon_reviews"
else:
    # ⚠️ Validar con Gemini usando análisis semántico
    quality_validated = gemini_semantic_quality_check(product_data)
    validation_source = "gemini_semantic"
```

---

## COMPARACIÓN EN FRONTEND

### UI Component: Selector de Vendor

```html
<div class="vendor-comparison">
  <h3>📦 Dónde comprarlo</h3>
  
  <!-- Amazon (CON reviews) -->
  <div class="vendor-option amazon">
    <span class="vendor-logo">🛒 Amazon</span>
    <span class="price">89,99€</span>
    <span class="rating">⭐ 4.6 (1.247 opiniones)</span>
    <span class="delivery">Envío gratis - Llega mañana</span>
    <button>Ver en Amazon</button>
  </div>
  
  <!-- El Corte Inglés (SIN reviews) -->
  <div class="vendor-option eci">
    <span class="vendor-logo">🏬 El Corte Inglés</span>
    <span class="price">94,95€</span>
    <span class="delivery">Envío gratis - Llega en 3 días</span>
    <button>Ver en El Corte Inglés</button>
  </div>
  
  <!-- Sprinter (SIN reviews) -->
  <div class="vendor-option sprinter">
    <span class="vendor-logo">👟 Sprinter</span>
    <span class="price">92,00€</span>
    <span class="delivery">Recogida en tienda - Hoy mismo</span>
    <button>Ver en Sprinter</button>
  </div>
</div>

<div class="recommendation-badge">
  ✅ Recomendado: Amazon (mejor precio + envío rápido)
</div>
```

### Algoritmo de Recomendación

```python
def calculate_vendor_score(vendor_data):
    """
    Scoring: 40% precio + 40% velocidad entrega + 20% coste envío
    """
    # Normalizar precio (más bajo = mejor)
    min_price = min(v["price"] for v in all_vendors)
    price_score = (min_price / vendor_data["price"]) * 40
    
    # Normalizar entrega (más rápido = mejor)
    max_days = max(v["delivery_days"] for v in all_vendors)
    if max_days > 0:
        delivery_score = ((max_days - vendor_data["delivery_days"]) / max_days) * 40
    else:
        delivery_score = 40
    
    # Coste envío (gratis = mejor)
    if vendor_data["shipping_cost"] == 0:
        shipping_score = 20
    else:
        shipping_score = max(0, 20 - (vendor_data["shipping_cost"] * 2))
    
    total_score = price_score + delivery_score + shipping_score
    return round(total_score, 1)

# Ordenar vendors por score
vendors_sorted = sorted(all_vendors, key=calculate_vendor_score, reverse=True)
recommended_vendor = vendors_sorted[0]
```

---

## TRATAMIENTO DE REVIEWS EN FICHAS

### Regla de Oro
**Solo mostrar reviews si `has_reviews == true`**

### Template Logic (single-gf_gift-v2.php)

```php
<?php
$primary_vendor = get_post_meta($post->ID, '_gf_primary_vendor', true);
$rating_value = get_post_meta($post->ID, '_gf_rating_value', true);
$review_count = get_post_meta($post->ID, '_gf_review_count', true);

// Solo mostrar reviews si el vendor principal las tiene
if ($primary_vendor === 'amazon' && $review_count > 0) {
    ?>
    <div class="product-reviews">
        <div class="rating-stars">
            <?php echo render_stars($rating_value); ?>
        </div>
        <span class="rating-value"><?php echo number_format($rating_value, 1); ?></span>
        <span class="review-count">(<?php echo number_format($review_count); ?> opiniones)</span>
    </div>
    <?php
} else {
    ?>
    <div class="product-no-reviews">
        <span class="badge">✨ Seleccionado por expertos</span>
        <span class="note">Sin opiniones públicas disponibles</span>
    </div>
    <?php
}
?>
```

### Schema.org Markup

```php
<?php if ($review_count > 0 && $primary_vendor === 'amazon'): ?>
<script type="application/ld+json">
{
  "@context": "https://schema.org/",
  "@type": "Product",
  "name": "<?php echo esc_js($product_name); ?>",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "<?php echo $rating_value; ?>",
    "reviewCount": "<?php echo $review_count; ?>"
  }
}
</script>
<?php endif; ?>
```

**IMPORTANTE:** NO incluir `aggregateRating` en el schema si no hay reviews reales.

---

## MESSAGING AL USUARIO

### Cuando NO hay reviews

```
❌ MAL:
"Este producto no tiene opiniones" (negativo)
"Sin valoraciones disponibles" (suena incompleto)

✅ BIEN:
"✨ Seleccionado por nuestros expertos"
"🎯 Recomendado por Giftia"
"💎 Producto premium verificado"
```

### Expert Opinion como Sustituto

```markdown
## Opinión de Experto

En Giftia hemos analizado este producto y lo consideramos una **excelente opción** 
por las siguientes razones:

✅ **Marca reconocida**: [Marca] tiene prestigio en [categoría]
✅ **Calidad verificada**: Materiales premium y acabados profesionales
✅ **Precio justo**: Relación calidad-precio óptima en su rango
✅ **Disponibilidad**: Stock confirmado en múltiples tiendas
```

---

## RESUMEN EJECUTIVO

| Aspecto | Política |
|---------|----------|
| **Reviews en feeds Awin** | NO existen en CSV |
| **Mostrar reviews ficticias** | ❌ PROHIBIDO |
| **Validación de calidad** | Gemini + Comparación EAN con Amazon |
| **UI sin reviews** | Badge "Seleccionado por expertos" |
| **Schema.org** | Solo si has_reviews=true |
| **Comparación multi-vendor** | Precio + Entrega + Envío (sin reviews) |
| **Recomendación vendor** | Score automático 40-40-20 |

---

## PRÓXIMOS PASOS

1. ✅ Confirmar columnas reales de feeds Awin (script inspect_feed_columns.py)
2. ⏳ Actualizar awin_feed_importer.py según resultado
3. ⏳ Añadir lógica de comparación EAN en process_queue.py
4. ⏳ Implementar vendor_comparison UI component
5. ⏳ Actualizar template single-gf_gift-v2.php para manejar productos sin reviews

---

**Mantra:** *"Reviews son datos, no se inventan. Calidad se valida, no se asume."*
