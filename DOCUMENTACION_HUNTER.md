# 🏹 GIFTIA HUNTER v10.0 - DOCUMENTACIÓN TÉCNICA

> **Versión:** 10.0 (Gemini Judge Edition)  
> **Fecha:** 17 Enero 2026  
> **Lenguaje:** Python 3.10+

---

## 🎯 PROPÓSITO

El Hunter es un **scraper inteligente** que:

1. **Busca** productos en Amazon España por categorías
2. **Filtra** basura (recambios, consumibles, productos baratos)
3. **Clasifica** con AI (Gemini) para determinar categoría y demografía
4. **Envía** productos de calidad a WordPress para el catálogo de Giftia

---

## 🏗️ ARQUITECTURA

```
┌─────────────────────────────────────────────────────────────────┐
│                        GIFTIA HUNTER v10.0                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │   SCHEMA    │───►│   CONFIG    │───►│    SMART_SEARCHES   │ │
│  │   .json     │    │   .env      │    │    (Búsquedas)      │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
│         │                                        │              │
│         ▼                                        ▼              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    SELENIUM DRIVER                          ││
│  │              (Chrome headless + WebDriver)                  ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    FILTROS PYTHON                           ││
│  │  • Killer keywords (basura, recambio, repuesto)            ││
│  │  • Precio válido (12€ - 9999€)                             ││
│  │  • Rating mínimo (4.0★)                                    ││
│  │  • Reviews mínimas (50+ general, 20+ premium)              ││
│  │  • Título válido (15-200 chars)                            ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    GEMINI JUDGE AI                          ││
│  │  • is_good_gift: ¿Es buen regalo?                          ││
│  │  • target_gender: male/female/kids/unisex                  ││
│  │  • category: Tech/Gamer/Gourmet/etc.                       ││
│  │  • gift_quality: 1-10                                      ││
│  │  • is_duplicate: ¿Ya tenemos similar?                      ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    WORDPRESS API                            ││
│  │              POST /giftia/v1/ingest                         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 ARCHIVOS

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `hunter.py` | 1821 | Script principal de scraping |
| `giftia_schema.json` | ~200 | Categorías/edades/géneros centralizados |
| `requirements.txt` | 4 | Dependencias Python |
| `hunter.log` | Variable | Log de ejecución |
| `.env` | ~10 | Variables de entorno (no en repo) |

---

## ⚙️ CONFIGURACIÓN

### Variables de Entorno

```bash
# API de Gemini (clasificación AI)
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# WordPress API
WP_API_TOKEN=nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5
WP_API_URL=https://giftia.es/wp-json/giftia/v1/ingest

# Amazon Affiliates
AMAZON_TAG=GIFTIA-21

# Debug mode (0 o 1)
DEBUG=0
```

### Constantes del Hunter

```python
# Gemini
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_TIMEOUT_SECONDS = 8
GEMINI_RETRY_WAIT = 60      # Segundos entre reintentos
GEMINI_MAX_RETRIES = 3      # Máximo intentos antes de fallback

# Calidad
BLACKLIST = {
    "min_price_eur": 12.0,
    "max_price_eur": 9999.0,
    "min_rating": 4.0,
    "min_reviews": 50,
    "min_reviews_niche": 20,
    "niche_price_threshold": 100,
    "min_title_length": 15,
    "max_title_length": 200,
}

# Anti-duplicados
MAX_PER_CATEGORY = 3
```

---

## 🔖 CATEGORÍAS VÁLIDAS

El Hunter carga las categorías desde `giftia_schema.json`:

```python
VALID_CATEGORIES = [
    "Tech",        # Tecnología, gadgets, electrónica
    "Gamer",       # Videojuegos, consolas, gaming
    "Gourmet",     # Cocina, vinos, gastronomía
    "Deporte",     # Fitness, running, gym
    "Outdoor",     # Camping, senderismo, aventura
    "Viajes",      # Maletas, accesorios viaje
    "Moda",        # Ropa, accesorios, joyería
    "Belleza",     # Maquillaje, skincare
    "Decoración",  # Hogar, lámparas, decorativo
    "Zen",         # Bienestar, yoga, meditación
    "Lector",      # Libros, e-readers
    "Música",      # Instrumentos, vinilos, audio
    "Artista",     # Arte, manualidades, craft
    "Fotografía",  # Cámaras, polaroid, álbumes
    "Friki",       # Coleccionismo, Funko, merchandising
    "Mascotas",    # Productos para animales
    "Lujo",        # Premium, alta gama
]
```

### Mapeo de Categorías Legacy

```python
CATEGORY_MAPPING = {
    "Arte": "Artista",
    "Gaming": "Gamer",
    "Wellness": "Zen",
    "Bienestar": "Zen",
    "Hogar": "Decoración",
    "Lectura": "Lector",
    "Libros": "Lector",
    "Cocina": "Gourmet",
    "Fitness": "Deporte",
    "Geek": "Friki",
    # ... etc
}
```

---

## 🔍 SMART_SEARCHES

Diccionario con búsquedas organizadas por categoría:

```python
SMART_SEARCHES = {
    "Tech": [
        "gadgets tecnologicos regalo original",
        "auriculares gaming inalámbricos premium",
        "smartwatch regalo premium",
        "drone DJI Mini regalo",
        # ... más búsquedas
    ],
    "Gourmet": [
        "kit cata vinos regalo premium",
        "cafetera espresso regalo premium",
        "cuchillo chef japonés regalo",
        # ... más búsquedas
    ],
    "Zen": [
        "difusor aceites esenciales regalo",
        "cuenco tibetano regalo",
        "esterilla yoga premium regalo",
        # ... más búsquedas
    ],
    # ... más categorías
}
```

---

## 🧠 GEMINI JUDGE

### Función: `ask_gemini_judge()`

```python
def ask_gemini_judge(title, price, category_hint="", already_sent_categories=None):
    """
    Consulta a Gemini para clasificar el producto de forma inteligente.
    
    Parámetros:
    - title: Título del producto
    - price: Precio en euros
    - category_hint: Pista de categoría (opcional)
    - already_sent_categories: Dict con conteo de categorías ya enviadas
    
    Retorna dict con:
    - is_good_gift: bool
    - reject_reason: str o None
    - target_gender: 'male', 'female', 'kids', 'unisex'
    - category: Una de VALID_CATEGORIES
    - gift_quality: 1-10
    - is_duplicate: bool
    """
```

### Prompt de Gemini

```
Eres un experto en regalos. Analiza este producto de Amazon España:

PRODUCTO: {title}
PRECIO: {price}€
{sent_context}

CATEGORÍAS DISPONIBLES (usar EXACTAMENTE una de estas):
Tech, Gamer, Gourmet, Deporte, Outdoor, Viajes, Moda, Belleza, 
Decoración, Zen, Lector, Música, Artista, Fotografía, Friki, 
Mascotas, Lujo

Responde SOLO con un JSON válido...
```

### Manejo de Errores

```python
# Retry automático en quota exceeded (429)
for attempt in range(GEMINI_MAX_RETRIES):
    response = requests.post(url, json=payload, timeout=GEMINI_TIMEOUT_SECONDS)
    
    if response.status_code == 429:
        wait_time = GEMINI_RETRY_WAIT * (attempt + 1)  # Backoff
        time.sleep(wait_time)
        continue
    
    if response.status_code != 200:
        return None  # Usar fallback
```

### Fallback Regex

Si Gemini falla, usa clasificación local:

```python
def classify_with_gemini_or_fallback(title, price, description=""):
    gemini_result = ask_gemini_judge(title, price, ...)
    
    if gemini_result:
        return {"source": "gemini", ...}
    
    # Fallback al sistema regex
    return {
        "source": "fallback",
        "target_gender": detect_target_gender(title, description),
        "category": classify_product_vibes(title, description, price)[0],
        ...
    }
```

---

## 🛡️ FILTROS DE CALIDAD

### Killer Keywords

Palabras que rechazan el producto inmediatamente:

```python
killer_words = [
    "recambio", "repuesto", "cartucho", "toner", "recarga",
    "mantenimiento", "limpieza", "funda protectora", "cable carga",
    "pilas", "batería", "adaptador cargador", "pantalla protector",
    ...
]
```

### Validación de Precio

```python
price = parse_price(price_str)
if price <= 0 or price < 12.0 or price > 9999.0:
    return False  # Rechazar
```

### Validación de Rating/Reviews

```python
# Mainstream (< 100€)
if price < 100 and (rating < 4.0 or reviews < 50):
    return False

# Nicho/Premium (>= 100€)
if price >= 100 and (rating < 4.0 or reviews < 20):
    return False
```

### Detección de Duplicados

```python
SENT_PRODUCTS_CACHE = set()      # ASINs ya enviados
SENT_CATEGORIES_CACHE = {}       # Conteo por tipo de producto

def is_duplicate_category(title):
    category = get_product_category(title)  # "auriculares", "smartwatch", etc.
    return SENT_CATEGORIES_CACHE.get(category, 0) >= MAX_PER_CATEGORY
```

---

## 📤 ENVÍO A WORDPRESS

### Función: `send_to_giftia()`

```python
def send_to_giftia(datos):
    """
    Envía producto validado a WordPress.
    
    datos = {
        "asin": "B0XXXXXXXX",
        "title": "Nombre del producto",
        "price": "49.99",
        "description": "...",
        "image_url": "https://...",
        "affiliate_url": "https://...",
        "vendor": "amazon",
        "vibes": ["Tech"],
        "target_gender": "unisex",
        "gemini_category": "Tech",
        "gift_score": 75,
        "gift_quality": 8,
        "classification_source": "gemini"
    }
    """
    
    headers = {
        'Content-Type': 'application/json',
        'X-GIFTIA-TOKEN': WP_TOKEN,
        'User-Agent': 'GiftiaHunter/10.0'
    }
    
    response = requests.post(WP_API_URL, json=datos, headers=headers, timeout=10)
```

---

## 🔄 BUCLE PRINCIPAL

```python
# 1. Seleccionar categorías aleatorias
selected_vibes = random.sample(list(SMART_SEARCHES.keys()), k=6)

# 2. Por cada categoría
for vibe in selected_vibes:
    searches = SMART_SEARCHES[vibe]
    selected_searches = random.sample(searches, k=5)
    
    # 3. Por cada búsqueda
    for query in selected_searches:
        # Añadir modificador temporal
        modifiers = ["", " 2026", " novedades", " bestseller"]
        final_query = query + random.choice(modifiers)
        
        # 4. Scrape Amazon
        amazon_url = f"https://www.amazon.es/s?k={final_query}"
        driver.get(amazon_url)
        
        # 5. Procesar resultados (máx 5 por búsqueda)
        items = driver.find_elements(By.CSS_SELECTOR, 'div[data-component-type="s-search-result"]')
        
        for item in items[:5]:
            # Extraer datos
            asin = item.get_attribute("data-asin")
            title = extract_title(item)
            price = extract_price(item)
            rating = extract_rating(item)
            reviews = extract_reviews(item)
            image = extract_image(item)
            
            # Filtrar
            if is_garbage(title, price, rating, reviews):
                continue
            
            # Clasificar con Gemini
            classification = classify_with_gemini_or_fallback(title, price)
            
            # Enviar si es válido
            if classification["is_good_gift"]:
                send_to_giftia({
                    "asin": asin,
                    "title": title,
                    "price": price,
                    ...
                })
```

---

## 🖥️ SELENIUM SETUP

```python
options = Options()
if not DEBUG:
    options.add_argument("--headless")
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 ...")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
```

### Extracción de Elementos

```python
# Múltiples selectores por si Amazon cambia
title_selectors = [
    "h2 a span",
    "h2 span",
    ".a-size-medium.a-color-base.a-text-normal",
    "[data-cy='title-recipe'] h2 span",
    ...
]

for selector in title_selectors:
    try:
        title_elem = item.find_element(By.CSS_SELECTOR, selector)
        if title_elem and title_elem.text.strip():
            title = title_elem.text.strip()
            break
    except:
        continue
```

---

## 📊 LOGGING

```python
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('hunter.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Ejemplos de logs
logger.info("🧠 ENVIANDO [Score:75|Q:8] 👥 [Tech] Auriculares Sony...")
logger.info("🔄 DUPLICADO (categoría 'auriculares'): ...")
logger.info("⏳ Gemini quota excedida. Esperando 60s...")
```

---

## 🚀 EJECUCIÓN

### Requisitos

```bash
pip install -r requirements.txt
```

### Ejecutar

```bash
# Normal (headless)
python hunter.py

# Con debug (ventana Chrome visible)
DEBUG=1 python hunter.py
```

### Ver logs en tiempo real

```bash
tail -f hunter.log
```

---

## 🐛 TROUBLESHOOTING

### Error: "Chrome driver not found"

```bash
pip install --upgrade webdriver-manager
```

### Error: Gemini quota exceeded

- El Hunter hace retry automático (60s, 120s, 180s)
- Si persiste, usa fallback regex
- Para más quota: usar API key de pago

### Error: "Token inválido" de WordPress

- Verificar `WP_API_TOKEN` en `.env`
- Verificar que coincide con `gf_wp_api_token` en WordPress

### Productos no aparecen en WordPress

1. Verificar logs del Hunter (¿envío exitoso?)
2. Verificar logs de WordPress (`error_log`)
3. Verificar estado del post (`publish` vs `draft`)

---

## 📈 MÉTRICAS

El Hunter registra:

- **total_sent**: Productos enviados exitosamente
- **total_discarded**: Productos rechazados
- **SENT_PRODUCTS_CACHE**: ASINs enviados (evita duplicados)
- **SENT_CATEGORIES_CACHE**: Conteo por tipo (limita diversidad)

---

## MULTI-VENDOR SUPPORT (AWIN)

El soporte para Awin (`hunter_awin.py`) permite ingerir feeds CSV de múltiples vendedores (El Corte Inglés, Fnac, etc.) integrándolos en el flujo unificado V52.

### 1. Uso
```bash
python hunter_awin.py <archivo_csv> [--limit N]
```

### 2. Procesamiento de CSV
El script mapea dinámicamente las columnas del CSV buscando patrones en las cabeceras:
- **Nombre**: `product_name`, `name`
- **Precio**: `search_price`, `price`
- **Imagen**: `merchant_image_url`, `large_image`
- **Link**: `merchant_deep_link`, `aw_deep_link`
- **Categoría**: `merchant_category`, `category`
- **Envío**: `delivery_time`, `shipping`, `delivery`

### 3. Lógica de Entrega Unificada (V52)
Clasifica el envío en 5 niveles de prioridad (de mayor a menor) basándose en palabras clave del texto de envío o título:

1. **`instant_digital`**: Entrega inmediata (códigos, entradas).
2. **`store_pickup_today`**: Recogida en tienda en 1-2h.
3. **`same_day`**: Entrega en el mismo día.
4. **`express_24h`**: Entrega al día siguiente.
5. **`standard`**: Envío convencional.

Además, establece flags de compatibilidad legacy:
- **`is_prime`**: Si detecta "prime" en el texto de envío.
- **`free_shipping`**: Si detecta "gratis", "gratuito" o "0€".

### 4. Referencia al Schema
Las palabras clave para cada tipo de entrega se gestionan centralizadamente en `giftia_schema.json` bajo la clave `delivery_types`, permitiendo ajustes sin tocar código.

---

*Documentación del Hunter generada el 17 de Enero de 2026*
