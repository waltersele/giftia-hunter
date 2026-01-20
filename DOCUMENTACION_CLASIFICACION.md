# Documentación del Sistema de Clasificación Giftia

**Versión:** 2.0  
**Última actualización:** 20 Enero 2026

---

## 1. Resumen del Sistema

El sistema de clasificación de Giftia utiliza **Gemini AI** para categorizar productos de Amazon en 18 categorías de regalo. Esta documentación detalla las reglas de clasificación, errores comunes y herramientas de corrección.

---

## 2. Categorías Válidas (18 total)

| Categoría | Slug | Descripción | Ejemplos |
|-----------|------|-------------|----------|
| **Tech** | tech | Gadgets y electrónica para adultos | Smart home, drones, tablets, smart trackers |
| **Gamer** | gamer | Videojuegos y accesorios gaming | Consolas, mandos, teclados gaming, sillas gaming |
| **Gourmet** | cocina | Cocina y gastronomía | Barbacoas, utensilios, vino, whisky, café |
| **Deporte** | deporte | Fitness y ejercicio físico | Electroestimuladores, foam roller, pádel, running |
| **Outdoor** | outdoor | Actividades al aire libre | Tiendas campaña, senderismo, camping, linternas |
| **Viajes** | viajes | Accesorios y experiencias viaje | Maletas, mapas rascar, Smartbox, Wonderbox |
| **Moda** | moda | Ropa y accesorios adultos | Bolsos, carteras, joyería, cinturones |
| **Belleza** | belleza | Cosmética y bienestar personal | Skincare, perfumes, gua sha, rodillo jade |
| **Decoración** | decoracion | Hogar y decoración adultos | Lámparas, arte, globos terráqueos, mantas adulto |
| **Zen** | zen | Relajación y mindfulness | Yoga, meditación, velas, incienso, difusores |
| **Lector** | lector | Lectura y escritura | Kindle, libros, cuadernos premium |
| **Música** | musica | Música y audio | Auriculares, vinilos, tocadiscos, instrumentos |
| **Artista** | artista | Arte y manualidades adultos | Rotuladores, pintura, craft DIY |
| **Fotografía** | fotografia | Fotografía adulta | Cámaras, objetivos, marcos digitales, drones |
| **Friki** | friki | Merchandising y coleccionismo | Funko Pop, Harry Potter, Star Wars, Marvel, anime |
| **Mascotas** | mascotas | Productos SOLO para animales | Comederos, camas, juguetes mascota |
| **Lujo** | lujo | Productos premium +200€ | Whisky premium, relojes, joyería fina |
| **Infantil** | infantil | TODO para bebés/niños 0-10 | Biberones, Montessori, mantas bebé, juguetes |

---

## 3. Reglas de Clasificación Críticas

### 3.1 INFANTIL (Prioridad Máxima)

> **Si el producto es para bebé o niño (0-10 años), ES INFANTIL. Sin excepciones.**

| Producto | ❌ Error Común | ✅ Correcto |
|----------|---------------|-------------|
| Biberones Philips Avent | Belleza | **Infantil** |
| Termómetro bebé | Tech | **Infantil** |
| Mantas bebé | Decoración/Moda | **Infantil** |
| Juguetes Montessori | Tech | **Infantil** |
| Cubos actividades | Tech | **Infantil** |
| Set regalo nacimiento | Zen/Decoración | **Infantil** |
| Colonia bebé | Belleza | **Infantil** |
| Cámara instantánea niños | Fotografía | **Infantil** |
| Kit costura niños | Artista | **Infantil** |
| Peluches infantiles | Decoración | **Infantil** |

### 3.2 GOURMET (Todo lo de cocina)

| Producto | ❌ Error Común | ✅ Correcto |
|----------|---------------|-------------|
| Set barbacoa | Fandom/Outdoor | **Gourmet** |
| Utensilios parrilla | Outdoor | **Gourmet** |
| Delantal cocina | Moda | **Gourmet** |
| Set té/café portátil | Viajes | **Gourmet** |
| Kit cerveza artesanal | Outdoor | **Gourmet** |

### 3.3 DEPORTE (Ejercicio físico)

| Producto | ❌ Error Común | ✅ Correcto |
|----------|---------------|-------------|
| Electroestimulador TENS/EMS | Fandom/Tech/Belleza | **Deporte** |
| Foam roller | Zen | **Deporte** |
| Paletero pádel | Viajes/Mascotas | **Deporte** |
| Bandas elásticas | Zen | **Deporte** |

### 3.4 FRIKI (Solo merchandising franquicias)

| Producto | ❌ Error Común | ✅ Correcto |
|----------|---------------|-------------|
| Funko Pop | Música/Decoración | **Friki** |
| Varitas Harry Potter | Decoración | **Friki** |
| LEGO Star Wars | Tech | **Friki** |
| Juegos de mesa temáticos | Gamer | **Friki** |

> ⚠️ **"Fandom" NO EXISTE como categoría.** Gemini a veces lo inventa. Usar siempre "Friki".

### 3.5 OUTDOOR vs DEPORTE

| Outdoor | Deporte |
|---------|---------|
| Tiendas campaña | Foam roller |
| Bastones senderismo | Electroestimuladores |
| Linternas frontales | Equipamiento gym |
| Mochilas trekking | Running/ciclismo |

### 3.6 TECH (Solo electrónica adultos)

| Producto | ❌ Error Común | ✅ Correcto |
|----------|---------------|-------------|
| Robot aspirador | Mascotas | **Tech** |
| Smart tracker | - | **Tech** |
| Tableta gráfica | - | **Tech** o Artista |

---

## 4. Correcciones Automáticas

El sistema aplica correcciones automáticas en `validate_category()`:

```python
CATEGORY_CORRECTIONS = {
    # Categorías inventadas que NO existen
    "fandom": "Friki",
    "coleccionismo": "Friki",
    "geek": "Friki",
    
    # Sinónimos
    "hogar": "Decoración",
    "bienestar": "Zen",
    "fitness": "Deporte",
    "bebés": "Infantil",
    "cocina": "Gourmet",
    "electrónica": "Tech",
    "videojuegos": "Gamer",
    "aire libre": "Outdoor",
    "libros": "Lector",
    "manualidades": "Artista",
    "animales": "Mascotas",
    "premium": "Lujo",
    # ... 50+ correcciones más
}
```

---

## 5. Herramientas

### 5.1 Reclasificador de Productos

**Archivo:** `reclassify_products.py`

```bash
# Modo dry-run (solo muestra cambios sin aplicar)
python reclassify_products.py

# Aplicar cambios a WordPress
python reclassify_products.py --apply

# Solo productos de una categoría específica
python reclassify_products.py --category "Fandom"

# Limitar a N productos
python reclassify_products.py --limit 50

# Cambiar tamaño de batch
python reclassify_products.py --batch-size 5
```

**Flujo:**
1. Obtiene todos los productos de WordPress API
2. Los envía a Gemini en batches para reclasificar
3. Compara categoría actual vs sugerida
4. Muestra resumen de cambios
5. Si `--apply`, actualiza WordPress via `api-ingest.php?action=update_category`

### 5.2 Endpoint WordPress: update_category

**URL:** `https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php?action=update_category`

**Método:** POST

**Headers:**
```
Content-Type: application/json
X-GIFTIA-TOKEN: [token]
```

**Body:**
```json
{
    "post_id": 12345,
    "category": "Infantil"
}
```

**Response:**
```json
{
    "success": true,
    "post_id": 12345,
    "category": "Infantil",
    "slug": "infantil",
    "term_id": 42
}
```

---

## 6. Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `process_queue.py` | Prompt Gemini con 50+ reglas, validate_category mejorado |
| `api-ingest.php` | Nuevo endpoint `update_category` |
| `reclassify_products.py` | **NUEVO** - Script de reclasificación |

---

## 7. Errores Detectados en Catálogo (20 Enero 2026)

### Análisis de 541 productos:

| Categoría Incorrecta | Productos | Errores Principales |
|---------------------|-----------|---------------------|
| **Fandom/Friki** | 124 | Electroestimuladores, Barbacoas, Sets nacimiento |
| **Tech** | 72 | Montessori, Cubos bebé, Termómetros |
| **Belleza** | 31 | Biberones Philips Avent |
| **Música** | 16 | Funko Pop (todos) |
| **Viajes** | 33 | Utensilios barbacoa, Paleteros |
| **Mascotas** | 5 | Robot aspirador, Paleteros pádel |
| **Bienestar** | 17 | Peluches bebé, LEGO |

### Acciones Requeridas:

1. Ejecutar `python reclassify_products.py --category Fandom --apply`
2. Ejecutar `python reclassify_products.py --category Tech --apply`
3. Ejecutar `python reclassify_products.py --category Belleza --apply`
4. Ejecutar `python reclassify_products.py --category Música --apply`

---

## 8. Prevención de Errores Futuros

El prompt de Gemini ahora incluye:

1. **Definiciones expandidas** de cada categoría con 5-8 ejemplos
2. **Tabla de reglas críticas** con prioridades claras
3. **Infantil como prioridad máxima** - si es para bebé/niño, ES Infantil
4. **Lista explícita de errores comunes** a evitar
5. **validate_category()** con 50+ correcciones automáticas

---

## 9. Testing

Para verificar clasificaciones:

```bash
# Analizar productos por categoría
python -c "
import requests
resp = requests.get('https://giftia.es/wp-json/wp/v2/gf_gift?per_page=100')
cats = requests.get('https://giftia.es/wp-json/wp/v2/gf_category?per_page=100').json()
cat_map = {c['id']: c['name'] for c in cats}

by_cat = {}
for p in resp.json():
    title = p['title']['rendered'][:50]
    cat_ids = p.get('gf_category', [])
    cat = cat_map.get(cat_ids[0], 'Sin categoría') if cat_ids else 'Sin categoría'
    if cat not in by_cat:
        by_cat[cat] = []
    by_cat[cat].append(title)

for cat, titles in sorted(by_cat.items()):
    print(f'{cat}: {len(titles)} productos')
"
```

---

**Documentación generada automáticamente - Giftia Hunter v11.0**
