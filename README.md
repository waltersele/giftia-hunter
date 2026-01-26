# 🎯 GIFTIA HUNTER v11.0 - Motor de Descubrimiento de Regalos

**Versión:** 11.0 (Gold Master v51)  
**Última actualización:** 19 Enero 2026  
**Estado:** ✅ Producción

> **Ver también:** [GOLD_MASTER_V50_IMPLEMENTACION.md](../giftfinder-core/GOLD_MASTER_V50_IMPLEMENTACION.md) para la arquitectura completa del sistema.

---

## 🏗️ ARQUITECTURA DEL SISTEMA

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GIFTIA HUNTER v11                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────────┐   │
│  │  hunter.py  │───▶│pending_queue │───▶│  process_queue.py   │   │
│  │  (Scraper)  │    │    .json     │    │  (Gemini + WordPress)│   │
│  └─────────────┘    └──────────────┘    └─────────────────────┘   │
│        │                                          │                │
│        ▼                                          ▼                │
│  ┌─────────────┐                        ┌─────────────────────┐   │
│  │   Amazon    │                        │   Gemini API        │   │
│  │   (Chrome)  │                        │   (2 keys rotación) │   │
│  └─────────────┘                        └─────────────────────┘   │
│                                                   │                │
│                                                   ▼                │
│                                         ┌─────────────────────┐   │
│                                         │   api-ingest.php    │   │
│                                         │   (WordPress)       │   │
│                                         └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📋 ÍNDICE

1. [Descripción General](#descripción-general)
2. [Arquitectura](#arquitectura)
3. [Configuración](#configuración)
4. [Estructura del Código](#estructura-del-código)
5. [Categorías y Búsquedas](#categorías-y-búsquedas)
6. [Sistema de Filtrado](#sistema-de-filtrado)
7. [Sistema de Scoring](#sistema-de-scoring)
8. [API de Ingesta](#api-de-ingesta)
9. [Ejecución](#ejecución)
10. [Logs y Debugging](#logs-y-debugging)
11. [Problemas Conocidos](#problemas-conocidos)
12. [Multi-Vendor Awin](./DOCUMENTACION_MULTIVENDOR_AWIN.md) 🆕

---

## 🎯 DESCRIPCIÓN GENERAL

Hunter es un scraper inteligente de Amazon que:

1. **Busca productos** relevantes para regalos en Amazon.es
2. **Filtra basura** (productos genéricos, recambios, cargadores, etc.)
3. **Puntúa calidad** (rating, reviews, keywords premium)
4. **Envía a Giftia** los productos que pasan los filtros

### Flujo de trabajo:
```
[Búsquedas Smart] → [Selenium/Chrome] → [Extracción] → [Filtrado] → [Scoring] → [API Giftia]
```

---

## 🏗️ ARQUITECTURA

```
┌─────────────────────────────────────────────────────────────────┐
│                      GIFTIA HUNTER v8.0                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐                                               │
│  │ SMART_SEARCHES│  Dict con categorías y términos de búsqueda │
│  │ - Digital     │                                              │
│  │ - Tech        │                                              │
│  │ - Gourmet     │                                              │
│  │ - Zen         │                                              │
│  │ - Deporte     │                                              │
│  │ - Viajes      │                                              │
│  │ - Moda        │                                              │
│  │ - Friki       │                                              │
│  └──────┬───────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│  │   SELENIUM   │────▶│  EXTRACCIÓN  │────▶│  FILTRADO    │   │
│  │   Chrome     │     │  - ASIN      │     │  - Blacklist │   │
│  │   Headless   │     │  - Precio    │     │  - Rating    │   │
│  │              │     │  - Rating    │     │  - Reviews   │   │
│  │              │     │  - Reviews   │     │  - Precio    │   │
│  │              │     │  - Imagen    │     │              │   │
│  └──────────────┘     └──────────────┘     └──────┬───────┘   │
│                                                    │            │
│                                                    ▼            │
│                       ┌──────────────┐     ┌──────────────┐   │
│                       │   SCORING    │────▶│  API GIFTIA  │   │
│                       │  0-100 pts   │     │  /ingest     │   │
│                       │  Keywords    │     │              │   │
│                       │  Premium     │     │              │   │
│                       └──────────────┘     └──────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ CONFIGURACIÓN

### Variables de Entorno (.env)

```bash
# Token de autenticación para API Giftia
WP_API_TOKEN=nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5

# URL del endpoint de ingesta
WP_API_URL=https://giftia.es/wp-json/giftia/v1/ingest

# Tag de afiliado Amazon
AMAZON_TAG=GIFTIA-21

# Modo debug (0=off, 1=on)
DEBUG=0
```

### Instalación

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Copiar y configurar .env
cp .env.example .env
# Editar .env con tus credenciales

# 3. Ejecutar
python hunter.py
```

### requirements.txt

```
selenium>=4.0.0
webdriver-manager>=3.8.0
requests>=2.28.0
python-dotenv>=1.0.0
```

---

## 📂 ESTRUCTURA DEL CÓDIGO

### Archivos

| Archivo | Descripción |
|---------|-------------|
| `hunter.py` | Script principal (943 líneas) |
| `.env` | Variables de entorno (no en Git) |
| `.env.example` | Plantilla de configuración |
| `requirements.txt` | Dependencias Python |
| `hunter.log` | Log de ejecución |

### Secciones principales de hunter.py

```python
# Líneas 1-50:     Imports y configuración
# Líneas 50-350:   SMART_SEARCHES - Diccionario de búsquedas por categoría
# Líneas 350-450:  BLACKLIST - Filtros anti-basura
# Líneas 450-550:  GIFT_KEYWORDS - Keywords para scoring
# Líneas 550-650:  calculate_gift_score() - Algoritmo de puntuación
# Líneas 650-750:  send_to_giftia() - Envío a API
# Líneas 750-850:  Funciones de extracción (parse_price, extract_asin, etc.)
# Líneas 850-943:  Bucle principal de scraping
```

---

## 🔍 CATEGORÍAS Y BÚSQUEDAS

### SMART_SEARCHES

Diccionario con 8 categorías, cada una con 20-40 términos de búsqueda optimizados:

| Categoría | Ejemplos de búsquedas | Cantidad |
|-----------|----------------------|----------|
| **Digital** | tarjeta regalo Netflix, suscripción Spotify | ~20 |
| **Tech** | auriculares gaming, drone DJI Mini, Alexa Echo | ~35 |
| **Gourmet** | kit cata vinos, cafetera espresso, cuchillo japonés | ~30 |
| **Zen** | difusor aceites, cuenco tibetano, masajeador | ~25 |
| **Deporte** | mancuernas, reloj GPS Garmin, raqueta padel | ~25 |
| **Viajes** | maleta cabina, powerbank, hamaca camping | ~25 |
| **Moda** | reloj automático, bolso piel, perfume nicho | ~30 |
| **Friki** | Funko Pop, LEGO Star Wars, figura anime | ~35 |

### Mapeo a Frontend

| Hunter Category | Frontend Vibe |
|----------------|---------------|
| Tech | Tecnología |
| Gourmet | Gourmet |
| Zen | Bienestar |
| Deporte | Deporte |
| Viajes | Viajes |
| Moda | Moda |
| Friki | Gaming / Juguetes |
| Digital | (transversal) |

---

## 🚫 SISTEMA DE FILTRADO

### BLACKLIST

#### Palabras Prohibidas (`banned_keywords`)
Productos que contienen estas palabras son **rechazados automáticamente**:

```python
"calentador agua", "tendedero", "grifo", "recambio", "batería", "pila",
"fregona", "detergente", "papel higienico", "filtro aire", "bombilla",
"cable usb", "adaptador", "tornillo", "destornillador", "funda teléfono",
"protector pantalla", "enchufe", "regleta", "bolsa plástico", "molde horno",
"tinta cartucho", "spray", "limpiador", "cepillo dientes", ...
```

#### Palabras Sospechosas (`suspicious_keywords`)
Disminuyen el score pero no rechazan:

```python
"fake", "réplica", "genérico", "pack ahorro", "lote", "outlet",
"defectuoso", "reparado", "reacondicionado", "imitación", "copia"
```

### Filtros de Precio

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `min_price_eur` | 12€ | Nada por debajo (basura) |
| `max_price_eur` | 9999€ | Nada absurdamente caro |
| `preferred_price_range` | 20-500€ | Rango ideal para regalos |

### Filtros de Calidad

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `min_rating` | 4.0⭐ | Mínimo rating de Amazon |
| `min_reviews` | 50 | Mínimo reseñas (mainstream) |
| `min_reviews_niche` | 20 | Mínimo reseñas (productos +100€) |
| `min_title_length` | 15 chars | Títulos muy cortos = basura |
| `max_title_length` | 200 chars | Títulos muy largos = spam |

---

## ⭐ SISTEMA DE SCORING

### calculate_gift_score(title, price, description)

Retorna puntuación de 0-100. Solo productos con **score >= 60** se envían.

### Keywords Premium (`GIFT_KEYWORDS`)

```python
"premium": +10 pts
"exclusivo": +10 pts
"edición especial": +9 pts
"limitado": +9 pts
"oficial": +8 pts
"auténtico": +8 pts
"licenciado": +8 pts
"handmade": +9 pts
"artesanal": +8 pts
"ecológico": +7 pts
"original": +7 pts
"profesional": +6 pts
```

### Bonificaciones

| Condición | Puntos |
|-----------|--------|
| Precio en rango ideal (20-500€) | +20 |
| Contiene ⭐ o ✓ en título | +5 |
| Rating >= 4.5 | +10 |
| Reviews >= 100 | +5 |
| Reviews >= 500 | +10 |

### Penalizaciones

| Condición | Puntos |
|-----------|--------|
| Palabra sospechosa | -10 |
| Título muy corto | -20 |
| Título muy largo | -15 |
| Precio > 500€ | -5 |

---

## 🌐 API DE INGESTA

### Endpoint
`POST https://giftia.es/wp-json/giftia/v1/ingest`

### Headers
```
Content-Type: application/json
X-GIFTIA-TOKEN: <WP_API_TOKEN>
```

### Body (JSON)
```json
{
    "asin": "B0XXXXXXXX",
    "title": "Auriculares Sony WH-1000XM5 Premium Noise Cancelling",
    "price": "349.99",
    "description": "Auriculares inalámbricos con cancelación de ruido...",
    "image_url": "https://m.media-amazon.com/images/I/...",
    "affiliate_url": "https://www.amazon.es/dp/B0XXXXXXXX?tag=GIFTIA-21",
    "vendor": "amazon",
    "rating_value": 4.7,
    "review_count": 1523,
    "category": "Tech"
}
```

### Response
```json
{
    "success": true,
    "post_id": 456,
    "title": "Auriculares Sony WH-1000XM5...",
    "price": 349.99
}
```

---

## 🚀 EJECUCIÓN

### Modo Normal
```bash
python hunter.py
```

### Modo Debug (muestra navegador)
```bash
set DEBUG=1
python hunter.py
```

### Flujo de Ejecución

1. **Inicialización**: Carga Chrome driver (headless por defecto)
2. **Loop por categorías**: Itera `SMART_SEARCHES`
3. **Loop por búsquedas**: Cada término de búsqueda en Amazon
4. **Paginación**: Procesa múltiples páginas por búsqueda
5. **Extracción**: Obtiene ASIN, título, precio, rating de cada producto
6. **Filtrado**: Aplica BLACKLIST
7. **Scoring**: Calcula `gift_score`
8. **Envío**: Si score >= 60, envía a API Giftia
9. **Delay**: Pausa aleatoria entre peticiones (anti-bot)

### Tiempo de Ejecución
- **Por búsqueda**: ~30-60 segundos
- **Por categoría**: ~15-30 minutos
- **Ejecución completa**: ~2-4 horas

---

## 📊 LOGS Y DEBUGGING

### Archivo de Log
`hunter.log` - Rotación automática, encoding UTF-8

### Niveles de Log
```
[INFO]  - Operaciones normales
[DEBUG] - Detalles (solo con DEBUG=1)
[WARNING] - Productos rechazados
[ERROR] - Errores de conexión/parsing
```

### Ejemplo de Log
```
2026-01-16 10:30:15 [INFO] [HUNTER] INICIANDO v8.0
2026-01-16 10:30:16 [INFO] [HUNTER] API Endpoint: https://giftia.es/wp-json/giftia/v1/ingest
2026-01-16 10:30:20 [INFO] [OK] Chrome driver initialized
2026-01-16 10:30:25 [INFO] [SEARCH] Categoría: Tech, Búsqueda: "auriculares gaming"
2026-01-16 10:30:35 [INFO] [FOUND] ASIN: B0XXXXX - Sony WH-1000XM5 - 349.99€ - Score: 85
2026-01-16 10:30:36 [INFO] [SENT] Producto enviado a Giftia: post_id=456
2026-01-16 10:30:40 [WARNING] [SKIP] Rating bajo: 3.2 < 4.0
2026-01-16 10:30:45 [WARNING] [SKIP] Blacklisted: "cable usb" en título
```

---

## ⚠️ PROBLEMAS CONOCIDOS

### 1. Captcha de Amazon
**Síntoma**: Chrome se bloquea pidiendo captcha  
**Solución**: Ejecutar con `DEBUG=1` y resolver manualmente, o esperar y reintentar

### 2. Rate Limiting
**Síntoma**: Amazon devuelve páginas vacías  
**Solución**: Aumentar delays entre peticiones

### 3. Productos sin precio
**Síntoma**: Precio extrae como "0" o vacío  
**Causa**: Amazon muestra precios diferentes según ubicación  
**Solución**: Verificar User-Agent y cookies

### 4. WebDriver no encontrado
**Síntoma**: `ChromeDriver executable needs to be in PATH`  
**Solución**: `webdriver-manager` lo descarga automáticamente, pero a veces falla. Instalar Chrome actualizado.

---

## 🔧 COMANDOS ÚTILES

```bash
# Verificar instalación
python -c "from selenium import webdriver; print('OK')"

# Ver logs en tiempo real
Get-Content hunter.log -Wait -Tail 20

# Limpiar logs
Remove-Item hunter.log

# Ejecutar solo una categoría (editar código)
# Cambiar: for category in SMART_SEARCHES:
# Por: for category in ["Tech"]:
```

---

## 📞 CONEXIÓN CON PLUGIN

El Hunter envía productos al plugin WordPress Giftia. Ver documentación del plugin en:
`c:\webproject\giftia\giftfinder-core\README.md`

### Token de Autenticación
El token `WP_API_TOKEN` debe coincidir con el configurado en:
**WP Admin → Ajustes → Giftia → Token API**

---

## 🚀 DESARROLLO FUTURO

1. **Multi-vendor**: Agregar Awin, TradeDoubler, PCComponentes
2. **Programación**: Ejecutar automáticamente cada X horas
3. **Métricas**: Dashboard de productos ingestionados
4. **IA**: Usar Gemini para validar calidad de productos
