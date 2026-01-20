#!/usr/bin/env python3
"""
Procesa la cola de productos pendientes con Gemini AI.
Script independiente que no ejecuta el scraper.
"""

import os
import sys
import json
import time
import re
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

# Configuración
PENDING_QUEUE_FILE = "pending_products.json"
PROCESSED_LOG_FILE = "processed_products.json"
GEMINI_PACING_SECONDS = 1  # Con plan de pago podemos ir RÁPIDO
WP_PACING_SECONDS = 5  # Delay entre envíos a WP para evitar 429
BATCH_SIZE = 3  # Reducido a 3 para evitar respuestas cortadas por Gemini

# APIs - Leer desde .env (NUNCA hardcodear secrets)
WP_API_URL = os.getenv("WP_API_URL", "https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php")
WP_TOKEN = os.getenv("WP_API_TOKEN", "")
GEMINI_API_KEYS = [os.getenv("GEMINI_API_KEY", "")]

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("QueueProcessor")

# ==========================================
# CARGAR SCHEMA DESDE giftia_schema.json - FUENTE ÚNICA DE VERDAD
# ==========================================
SCHEMA = {}

try:
    schema_path = os.path.join(os.path.dirname(__file__), "giftia_schema.json")
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            SCHEMA = json.load(f)
        print(f"✅ Schema giftia_schema.json cargado correctamente")
except Exception as e:
    print(f"⚠️ Error cargando schema: {e}")

# Extraer valores del schema JSON
VALID_CATEGORIES = list(SCHEMA.get('categories', {}).keys()) if SCHEMA.get('categories') else [
    "Tech", "Gamer", "Gourmet", "Deporte", "Outdoor", "Viajes", "Moda", "Belleza",
    "Decoración", "Zen", "Lector", "Música", "Artista", "Fotografía", "Friki", "Mascotas", "Lujo", "Infantil"
]

VALID_AGES = list(SCHEMA.get('ages', {}).keys()) if SCHEMA.get('ages') else [
    "ninos", "adolescentes", "jovenes", "adultos", "seniors", "abuelos"
]

VALID_GENDERS = list(SCHEMA.get('genders', {}).keys()) if SCHEMA.get('genders') else [
    "unisex", "male", "female", "kids"
]

VALID_RECIPIENTS = list(SCHEMA.get('recipients', {}).keys()) if SCHEMA.get('recipients') else [
    "pareja", "padre", "amigo", "hermano", "hijo", "abuelo", "jefe", "colega", "yo"
]
VALID_OCCASIONS = list(SCHEMA.get('occasions', {}).keys()) if SCHEMA.get('occasions') else [
    "cumpleanos", "navidad", "amigo-invisible", "san-valentin", "aniversario",
    "dia-de-la-madre", "dia-del-padre", "graduacion", "bodas", "agradecimiento", "sin-motivo"
]

# Mapeo de category key → slug SEO (del schema)
CATEGORY_TO_SLUG = {}
for key, data in SCHEMA.get('categories', {}).items():
    CATEGORY_TO_SLUG[key] = data.get('slug', key.lower())

print(f"✅ Schema giftia_schema.json cargado:")
print(f"   📦 Categorías: {len(VALID_CATEGORIES)} - {VALID_CATEGORIES[:5]}...")
print(f"   👶 Edades: {len(VALID_AGES)} - {VALID_AGES}")
print(f"   ⚧ Géneros: {len(VALID_GENDERS)} - {VALID_GENDERS}")
print(f"   👥 Destinatarios: {len(VALID_RECIPIENTS)} - {VALID_RECIPIENTS}")
print(f"   🎉 Ocasiones: {len(VALID_OCCASIONS)} - {VALID_OCCASIONS[:5]}...")

# Estado Gemini
current_key_index = 0
gemini_call_count = 0

def generate_seo_slug(title):
    """Genera un slug SEO desde el título si Gemini no lo proporciona."""
    import unicodedata
    # Normalizar unicode y convertir a minúsculas
    slug = unicodedata.normalize('NFKD', title.lower())
    slug = slug.encode('ascii', 'ignore').decode('ascii')
    # Quitar marcas, modelos, códigos
    slug = re.sub(r'\b[A-Z]{2,}[\d\-]+\b', '', slug, flags=re.IGNORECASE)  # Códigos tipo XM5, WH-1000
    slug = re.sub(r'\b\d{4,}\b', '', slug)  # Números largos
    slug = re.sub(r'\b(para|con|de|del|la|el|los|las|un|una|y|o)\b', '', slug)  # Stopwords
    # Limpiar caracteres especiales
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug.strip())
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    # Limitar longitud
    if len(slug) > 60:
        slug = slug[:60].rsplit('-', 1)[0]
    return slug

# Inventario de productos publicados (para deduplicación)
PUBLISHED_INVENTORY_FILE = "published_inventory.json"

def load_published_inventory():
    """Carga el inventario de productos ya publicados, agrupados por categoría."""
    try:
        if os.path.exists(PUBLISHED_INVENTORY_FILE):
            with open(PUBLISHED_INVENTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Error cargando inventario: {e}")
    return {}

def save_published_inventory(inventory):
    """Guarda el inventario de productos publicados."""
    try:
        with open(PUBLISHED_INVENTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(inventory, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error guardando inventario: {e}")

def add_to_inventory(product, classification):
    """Añade un producto publicado al inventario para futura deduplicación."""
    inventory = load_published_inventory()
    category = classification.get("category", "otros")
    
    if category not in inventory:
        inventory[category] = []
    
    # Guardar info resumida para comparación
    price = float(str(product.get("price", "0")).replace(",", ".").replace("€", "").strip() or 0)
    inventory[category].append({
        "title": product.get("title", ""),
        "original_title": product.get("original_title", product.get("title", "")),
        "price": price,
        "gift_quality": classification.get("gift_quality", 5),
        "asin": product.get("asin", ""),
        "added_at": datetime.now().isoformat()
    })
    
    # Mantener máximo 50 productos por categoría (los más recientes)
    if len(inventory[category]) > 50:
        inventory[category] = inventory[category][-50:]
    
    save_published_inventory(inventory)

def get_similar_products_context(products):
    """Genera contexto de productos similares ya publicados para cada producto del batch."""
    inventory = load_published_inventory()
    context_per_product = []
    
    for product in products:
        price = float(str(product.get("price", "0")).replace(",", ".").replace("€", "").strip() or 0)
        title_lower = product.get("title", "").lower()
        
        # Buscar productos similares en todas las categorías
        similar = []
        for category, items in inventory.items():
            for item in items:
                # Mismo rango de precio (±30%)
                item_price = item.get("price", 0)
                if item_price > 0 and abs(price - item_price) / item_price < 0.3:
                    # Podría ser similar
                    similar.append({
                        "title": item.get("title", "")[:60],
                        "price": item_price,
                        "quality": item.get("gift_quality", 5),
                        "category": category
                    })
        
        # Limitar a 5 similares más relevantes
        context_per_product.append(similar[:5])
    
    return context_per_product

def load_pending_queue():
    try:
        if os.path.exists(PENDING_QUEUE_FILE):
            with open(PENDING_QUEUE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Error cargando cola: {e}")
    return []

def save_pending_queue(queue):
    try:
        with open(PENDING_QUEUE_FILE, 'w', encoding='utf-8') as f:
            json.dump(queue, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error guardando cola: {e}")

def get_next_from_queue():
    queue = load_pending_queue()
    if queue:
        product = queue.pop(0)
        save_pending_queue(queue)
        return product
    return None

def get_batch_from_queue(batch_size=BATCH_SIZE):
    """Obtiene un batch de productos de la cola."""
    queue = load_pending_queue()
    if not queue:
        return []
    batch = queue[:batch_size]
    remaining = queue[batch_size:]
    save_pending_queue(remaining)
    return batch

def get_pending_count():
    return len(load_pending_queue())

def log_processed_product(product, result):
    try:
        processed = []
        if os.path.exists(PROCESSED_LOG_FILE):
            with open(PROCESSED_LOG_FILE, 'r', encoding='utf-8') as f:
                processed = json.load(f)
        
        product['processed_at'] = datetime.now().isoformat()
        product['ai_result'] = result
        processed.append(product)
        
        if len(processed) > 500:
            processed = processed[-500:]
        
        with open(PROCESSED_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(processed, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Error logging: {e}")

def validate_category(category):
    if not category:
        return "otros"
    cat_lower = category.lower().strip()
    
    # Correcciones de errores comunes de Gemini
    CATEGORY_CORRECTIONS = {
        # Categorías inventadas que NO existen
        "fandom": "Friki",
        "coleccionismo": "Friki",
        "merchandising": "Friki",
        "geek": "Friki",
        
        # Sinónimos de categorías reales
        "hogar": "Decoración",
        "casa": "Decoración",
        "interiores": "Decoración",
        
        "bienestar": "Zen",
        "relax": "Zen",
        "relajación": "Zen",
        "relajacion": "Zen",
        "wellness": "Zen",
        
        "fitness": "Deporte",
        "gimnasio": "Deporte",
        "gym": "Deporte",
        "ejercicio": "Deporte",
        "sport": "Deporte",
        
        "bebés": "Infantil",
        "bebes": "Infantil",
        "bebé": "Infantil",
        "bebe": "Infantil",
        "niños": "Infantil",
        "ninos": "Infantil",
        "niño": "Infantil",
        "nino": "Infantil",
        "kids": "Infantil",
        "children": "Infantil",
        "puericultura": "Infantil",
        "juguetes": "Infantil",
        
        "cocina": "Gourmet",
        "gastronomía": "Gourmet",
        "gastronomia": "Gourmet",
        "food": "Gourmet",
        "comida": "Gourmet",
        "bebidas": "Gourmet",
        
        "electrónica": "Tech",
        "electronica": "Tech",
        "tecnología": "Tech",
        "tecnologia": "Tech",
        "gadgets": "Tech",
        
        "videojuegos": "Gamer",
        "gaming": "Gamer",
        "games": "Gamer",
        
        "aire libre": "Outdoor",
        "aventura": "Outdoor",
        "naturaleza": "Outdoor",
        "acampada": "Outdoor",
        
        "libros": "Lector",
        "lectura": "Lector",
        "literatura": "Lector",
        
        "manualidades": "Artista",
        "craft": "Artista",
        "diy": "Artista",
        "arte": "Artista",
        
        "animales": "Mascotas",
        "pets": "Mascotas",
        "perros": "Mascotas",
        "gatos": "Mascotas",
        
        "premium": "Lujo",
        "luxury": "Lujo",
        "exclusivo": "Lujo",
    }
    
    if cat_lower in CATEGORY_CORRECTIONS:
        return CATEGORY_CORRECTIONS[cat_lower]
    
    for valid in VALID_CATEGORIES:
        if valid.lower() == cat_lower:
            return valid
    return "otros"

def call_gemini(prompt):
    global current_key_index, gemini_call_count
    
    if not GEMINI_API_KEYS:
        logger.error("❌ No hay API keys configuradas!")
        return None
    
    max_wait_cycles = 10  # Máximo 10 ciclos de espera (10 minutos total)
    wait_cycle = 0
    
    while wait_cycle < max_wait_cycles:
        for key_attempt in range(len(GEMINI_API_KEYS)):
            key = GEMINI_API_KEYS[current_key_index]
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
            
            try:
                response = requests.post(url, json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.4,        # Un poco más creativo
                        "maxOutputTokens": 8192    # Suficiente para ficha completa (600-800 palabras)
                    }
                }, timeout=60)  # Más tiempo para respuestas largas
                
                if response.status_code == 200:
                    data = response.json()
                    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    gemini_call_count += 1
                    return text
                elif response.status_code == 429:
                    logger.warning(f"🔄 Key {current_key_index+1} quota exceeded, probando siguiente...")
                    current_key_index = (current_key_index + 1) % len(GEMINI_API_KEYS)
                else:
                    logger.error(f"Gemini error {response.status_code}: {response.text[:100]}")
                    return None
            except Exception as e:
                logger.error(f"Gemini exception: {e}")
                current_key_index = (current_key_index + 1) % len(GEMINI_API_KEYS)
        
        # Todas las keys agotadas - ESPERAR en vez de fallback
        wait_cycle += 1
        wait_seconds = 60  # Esperar 1 minuto
        logger.info(f"⏳ Todas las keys agotadas. Esperando {wait_seconds}s... (intento {wait_cycle}/{max_wait_cycles})")
        time.sleep(wait_seconds)
    
    logger.error("❌ Tiempo de espera agotado después de 10 minutos. Saltando producto.")
    return None

def classify_with_gemini(title, price, description=""):
    prompt = f"""Analiza este producto de Amazon como regalo:

TÍTULO: {title}
PRECIO: {price}€
DESCRIPCIÓN: {description[:200] if description else 'N/A'}

Responde SOLO en este formato JSON exacto:
{{"is_good_gift": true/false, "category": "categoria", "target_gender": "male/female/kids/unisex", "gift_quality": 1-10, "is_duplicate": false, "reject_reason": "motivo si rechazas"}}

Categorías válidas: {', '.join(VALID_CATEGORIES[:10])}...

CRITERIOS:
- is_good_gift=true si es un regalo genuino y deseable
- gift_quality: 1-10 (calidad como regalo)
- Rechaza: consumibles básicos, repuestos, accesorios genéricos, packs múltiples del mismo producto"""

    response = call_gemini(prompt)
    
    if response:
        try:
            json_match = re.search(r'\{[^{}]+\}', response.replace('\n', ' '))
            if json_match:
                data = json.loads(json_match.group())
                return {
                    "is_good_gift": data.get("is_good_gift", False),
                    "category": validate_category(data.get("category", "otros")),
                    "target_gender": data.get("target_gender", "unisex"),
                    "gift_quality": int(data.get("gift_quality", 5)),
                    "is_duplicate": data.get("is_duplicate", False),
                    "reject_reason": data.get("reject_reason", ""),
                    "source": "gemini"
                }
        except Exception as e:
            logger.warning(f"Error parseando respuesta Gemini: {e}")
    
    # SIN FALLBACK - retorna None para que el producto vuelva a cola
    return None

def classify_batch_with_gemini(products):
    """Clasifica productos según giftia_schema.json - FUENTE ÚNICA DE VERDAD."""
    if not products:
        return []
    
    # Construir lista de productos para el prompt con más contexto
    products_text = ""
    for i, p in enumerate(products):
        title = p.get("title", "Sin título")[:150]
        price = p.get("price", "0")
        rating = p.get("rating", "N/A")
        reviews = p.get("reviews_count", "N/A")
        products_text += f"\n{i+1}. {title}\n   Precio: {price}€ | Rating: {rating} | Reviews: {reviews}"
    
    prompt = f"""Eres el CURADOR JEFE y EXPERTO SEO de Giftia.es. Tu trabajo es:
1. Seleccionar regalos que EMOCIONEN
2. Crear fichas de producto optimizadas para posicionar en Google

PRODUCTOS A EVALUAR:{products_text}

═══════════════════════════════════════════════════════════════════════════════
🎁 FILTROS DE EXCELENCIA (4 filtros para aprobar)
═══════════════════════════════════════════════════════════════════════════════

1. UTILIDAD ELEVADA: ¿Resuelve algo o mejora una rutina?
2. AUTO-BOICOT: ¿Es algo que el destinatario NO se compraría solo?
3. ORIGINALIDAD INTELIGENTE: ¿Tiene factor sorpresa o diseño especial?
4. ORGULLO: ¿Te sentirías orgulloso de regalar esto?

RECHAZA (ok: false):
❌ Recambios, pilas, cables, toner, consumibles básicos
❌ Productos de limpieza o puramente funcionales
❌ Cosas aburridas que nadie regalaría con emoción
❌ Repuestos o accesorios sueltos sin gracia

═══════════════════════════════════════════════════════════════════════════════
📦 CATEGORÍA (category) - USA EXACTAMENTE ESTOS VALORES:
═══════════════════════════════════════════════════════════════════════════════

⚠️ USA SOLO ESTOS 18 VALORES EXACTOS. NO INVENTES OTROS:

- Tech: Gadgets ADULTOS, electrónica, smart home, USB, Bluetooth, móviles, tablets, drones
- Gamer: Videojuegos, consolas, accesorios gaming, sillas gaming, mandos, teclados gaming
- Gourmet: Cocina, BARBACOAS, PARRILLAS, utensilios cocina, vino, café, whisky, cerveza artesanal
- Deporte: Fitness, gym, ELECTROESTIMULADORES, running, ciclismo, pádel, tenis, foam roller
- Outdoor: Camping, TIENDAS CAMPAÑA, senderismo, bastones trekking, linternas frontales
- Viajes: Maletas, MAPAS RASCAR, accesorios viaje, experiencias Smartbox/Wonderbox
- Moda: Ropa ADULTOS, bolsos, accesorios moda, joyería, carteras, cinturones
- Belleza: Cosmética, skincare, perfumes ADULTOS, spa, gua sha, rodillo jade, antifaces seda
- Decoración: Hogar ADULTOS, muebles, lámparas, arte, jardinería, globos terráqueos, mantas ADULTO
- Zen: Yoga, meditación, velas, aromaterapia, incienso, cojines meditación, difusores
- Lector: Libros, Kindle, e-readers, accesorios lectura, cuadernos premium
- Música: Instrumentos, AURICULARES, vinilos, tocadiscos, cajas música, altavoces
- Artista: Arte, pintura, rotuladores, manualidades ADULTO, craft, DIY, origami ADULTO
- Fotografía: Cámaras ADULTO, objetivos, trípodes, marcos digitales, drones foto
- Friki: FUNKO POP, merchandising Star Wars/Marvel/anime/Harry Potter, LEGO adultos, juegos mesa
- Mascotas: Perros, gatos, accesorios SOLO para animales, comederos, camas mascota
- Lujo: Premium +200€, whisky premium, relojes, joyería fina, ediciones especiales
- Infantil: TODO para bebés/niños 0-10: juguetes, Montessori, biberones, mantas bebé, peluches

╔═══════════════════════════════════════════════════════════════════════════════╗
║ 🚨 REGLAS CRÍTICAS - LEER ANTES DE CLASIFICAR:                                ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║ 📌 INFANTIL (prioridad máxima - si es para bebé/niño, ES Infantil):          ║
║   • Biberones, chupetes, termómetros bebé → Infantil (NO Belleza, NO Tech)   ║
║   • Mantas bebé, capas baño bebé → Infantil (NO Moda, NO Decoración)         ║
║   • Juguetes Montessori, cubos actividades → Infantil (NO Tech)              ║
║   • Set regalo nacimiento/parto → Infantil (NO Zen, NO Decoración)           ║
║   • Peluches para niños, nutrias dormir → Infantil (NO Decoración)           ║
║   • Kit costura NIÑOS, origami NIÑOS → Infantil (NO Artista)                 ║
║   • Colonia bebé, cremas bebé → Infantil (NO Belleza)                        ║
║   • Cámara instantánea NIÑOS → Infantil (NO Fotografía)                      ║
║                                                                               ║
║ 📌 GOURMET (todo lo de cocina/gastronomía):                                  ║
║   • Set barbacoa, utensilios parrilla → Gourmet (NO Outdoor, NO Fandom)      ║
║   • Delantal cocina → Gourmet (NO Moda)                                      ║
║   • Set té/café → Gourmet (NO Viajes aunque sea "portátil")                  ║
║                                                                               ║
║ 📌 DEPORTE (ejercicio físico):                                               ║
║   • Electroestimuladores TENS/EMS → Deporte (NO Tech, NO Belleza, NO Fandom) ║
║   • Paletero pádel/tenis → Deporte (NO Viajes, NO Mascotas)                  ║
║   • Foam roller, bandas elásticas → Deporte (NO Zen)                         ║
║                                                                               ║
║ 📌 FRIKI (SOLO merchandising franquicias):                                   ║
║   • Funko Pop → Friki (NO Música, NO Decoración)                             ║
║   • Varitas Harry Potter → Friki                                             ║
║   • LEGO Star Wars/Marvel → Friki                                            ║
║   • Juegos de mesa temáticos → Friki (NO Gamer)                              ║
║   ⚠️ "Fandom" NO EXISTE como categoría - usar "Friki"                        ║
║                                                                               ║
║ 📌 OUTDOOR vs DEPORTE:                                                       ║
║   • Tiendas campaña, bastones senderismo → Outdoor                           ║
║   • Equipamiento gym, fitness casa → Deporte                                 ║
║                                                                               ║
║ 📌 TECH (solo electrónica adultos):                                          ║
║   • Robot aspirador → Tech (NO Mascotas)                                     ║
║   • Smart tracker, AirTag → Tech                                             ║
║   • Tableta gráfica → Tech (o Artista si es para dibujo)                     ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════════════════
👶 EDAD (age) - ¿Quién lo DISFRUTARÍA?
═══════════════════════════════════════════════════════════════════════════════
Valores exactos: {', '.join(VALID_AGES)}
- ninos: 0-12 años | adolescentes: 13-17 años | jovenes: 18-30 años
- adultos: 31-50 años | seniors: 51-70 años | abuelos: 70+ años
Array si aplica a varias: ["jovenes", "adultos"]

═══════════════════════════════════════════════════════════════════════════════
⚧ GÉNERO (gender) | 👥 DESTINATARIOS (recipients) | 🎉 OCASIONES (occasions)
═══════════════════════════════════════════════════════════════════════════════
gender: {', '.join(VALID_GENDERS)}
recipients: {', '.join(VALID_RECIPIENTS)} (elige 1-3)
occasions: {', '.join(VALID_OCCASIONS)} (elige 1-3)

═══════════════════════════════════════════════════════════════════════════════
🎯 MARKETING HOOK (Gancho Psicológico)
═══════════════════════════════════════════════════════════════════════════════
- core: LA PASIÓN - Regalo obvio que define su etiqueta (Gamer→Videojuego)
- habitat: EL HÁBITAT - Mejora su espacio casa/oficina
- style: EL ESTILO - Se lleva puesto o muestra
- hedonism: EL HEDONISMO - Placer sensorial
- wildcard: EL WILDCARD - Descubrimiento inesperado

═══════════════════════════════════════════════════════════════════════════════
✍️ FICHA SEO COMPLETA - GOLD MASTER v51
═══════════════════════════════════════════════════════════════════════════════

GENERA TODOS ESTOS CAMPOS (ignora textos de Amazon, crea contenido original):

──────────────────────────────────────────────────────────────────────────────
📊 METADATOS SEO (para Google SERP)
──────────────────────────────────────────────────────────────────────────────

1. seo_title (50-60 chars): Meta title para Google.
   Formato: "Regalo para [Perfil]: [Producto] | Giftia"
   ✅ "Regalo para Melómanos: Auriculares Sony Premium | Giftia"

2. meta_description (150-160 chars): Snippet que incita al clic.
   Incluye: beneficio principal + llamada a la acción
   ✅ "Descubre los auriculares con mejor cancelación de ruido. El regalo perfecto para amantes de la música. Ver precio y análisis."

──────────────────────────────────────────────────────────────────────────────
🏷️ TÍTULOS Y GANCHO (visible en la ficha)
──────────────────────────────────────────────────────────────────────────────

3. h1_title (40-70 chars): Título H1 persuasivo y emocional.
   ❌ "Sony WH-1000XM5 Auriculares Inalámbricos..."
   ✅ "Auriculares que Silencian el Mundo"

4. short_description (80-120 palabras): Above the fold. Gancho emocional.
   - Qué dolor resuelve o placer otorga
   - Por qué es un regalo especial
   - Sensación que produce usarlo
   ✅ "Imagina regalar la capacidad de desconectar del ruido del mundo. Estos auriculares premium ofrecen la mejor cancelación de ruido del mercado, perfectos para quien ama la música o necesita concentrarse. Un regalo que demuestra que entiendes lo que realmente importa."

──────────────────────────────────────────────────────────────────────────────
⭐ VALORACIONES Y PUNTUACIÓN
──────────────────────────────────────────────────────────────────────────────

5. giftia_score (1-5, decimales ok): Puntuación como regalo.
   Basado en: originalidad, calidad, factor sorpresa, reviews Amazon

6. q (1-10): Calidad interna como regalo.
   9-10: "¡QUIERO UNO!" | 7-8: "Qué buena idea" | 5-6: "Está bien" | 1-4: RECHAZAR

──────────────────────────────────────────────────────────────────────────────
💬 OPINIÓN DEL EXPERTO (E-E-A-T para Google)
──────────────────────────────────────────────────────────────────────────────

7. expert_opinion (100-150 palabras): Opinión del curador Giftia en primera persona.
   - Por qué lo seleccionamos
   - Experiencia personal o insights
   - Para quién NO es adecuado (credibilidad)
   - Veredicto final
   ✅ "Después de probar decenas de auriculares, estos Sony se han ganado un lugar especial en nuestra selección. La cancelación de ruido no es un gimmick—realmente funciona en el metro, avión o una oficina ruidosa. Lo que más nos gusta es que no sacrifican calidad de sonido por silencio. Eso sí, no son para quien busca algo discreto: son grandes y llamativos. Pero si el destinatario valora su espacio sonoro, este es EL regalo."

──────────────────────────────────────────────────────────────────────────────
✅ PROS Y ❌ CONTRAS (credibilidad y escaneo rápido)
──────────────────────────────────────────────────────────────────────────────

8. pros (5-6 bullets): Puntos fuertes EMOCIONALES, no specs técnicos.
   ❌ "Bluetooth 5.2, driver 40mm"
   ✅ ["Cancelación de ruido que te aísla del mundo", "Batería para un vuelo transatlántico", "Comodidad para maratones de música", "Sonido que revela detalles ocultos", "Diseño premium que impresiona"]

9. cons (2-3 bullets): Puntos débiles HONESTOS. Genera confianza.
   ✅ ["Precio elevado, pero justificado por la calidad", "Tamaño grande, no son discretos", "Requieren app para sacar todo el partido"]

──────────────────────────────────────────────────────────────────────────────
📝 DESCRIPCIÓN LARGA SEO (600-800 palabras) - POSICIONA LA URL
──────────────────────────────────────────────────────────────────────────────

10. full_description: Contenido principal para posicionar en Google.
    ESTRUCTURA OBLIGATORIA (usa estos H2 exactos):

    ## Por qué este regalo es especial (100-120 palabras)
    Hook emocional. Keyword principal. Por qué destaca sobre alternativas.
    
    ## Características que enamoran (150 palabras)
    Beneficios traducidos a emociones. No specs, sino experiencias.
    
    ## La experiencia de usarlo (150 palabras)
    Storytelling: escenarios de uso. Cómo mejora el día a día.
    
    ## ¿Por qué elegir este y no otro? (100 palabras)
    Comparativa implícita. Qué lo hace único. Justificación del precio.
    
    ## Detalles técnicos para curiosos (100 palabras)
    Para quien busca specs. Formato lista técnica.
    
    ## Veredicto Giftia (80-100 palabras)
    Conclusión + para quién es perfecto + CTA sutil.

    KEYWORDS a incluir naturalmente:
    - "regalo para [perfil]", "mejor [producto] para regalar"
    - "idea de regalo original", "regalo que sorprende"
    - "[producto] como regalo", "comprar [producto] regalo"

──────────────────────────────────────────────────────────────────────────────
👤 BUYER PERSONA (long tails específicos)
──────────────────────────────────────────────────────────────────────────────

11. who_is_for (80-100 palabras): Perfiles específicos.
    - 3-4 perfiles de persona ideal
    - Situaciones donde brillaría como regalo
    - Ocasiones perfectas
    ✅ "Perfecto para el melómano que disfruta cada matiz de una canción. Ideal para el viajero frecuente que necesita su burbuja de paz en vuelos largos. Excelente para el profesional que trabaja desde casa y necesita concentración. También para quien se lo merece todo pero nunca se lo compra."

──────────────────────────────────────────────────────────────────────────────
❓ FAQS (Featured Snippets en Google)
──────────────────────────────────────────────────────────────────────────────

12. faqs: Array de 4-5 preguntas frecuentes con respuestas concisas.
    Formato: [{{"q": "pregunta", "a": "respuesta 40-60 palabras"}}]
    
    Tipos de preguntas:
    - ¿Es buen regalo para...?
    - ¿Vale la pena el precio?
    - ¿Qué incluye / cómo funciona?
    - ¿Diferencia con alternativas?
    - ¿Para qué edad/perfil es ideal?

──────────────────────────────────────────────────────────────────────────────
🏁 VEREDICTO FINAL
──────────────────────────────────────────────────────────────────────────────

13. verdict (50-80 palabras): Conclusión contundente.
    - Resumen en 1 frase
    - Para quién SÍ y para quién NO
    - Puntuación final
    ✅ "Un regalo de los que se recuerdan. Perfecto para melómanos y viajeros que valoran su tranquilidad. No es para presupuestos ajustados ni para quien busca algo discreto. Pero si quieres acertar seguro con alguien especial, esta es tu apuesta. Puntuación Giftia: 4.7/5"

14. slug: URL amigable. Máximo 5 palabras, sin artículos.
    ✅ "auriculares-sony-cancelacion-ruido"

═══════════════════════════════════════════════════════════════════════════════
📋 RESPUESTA JSON (EXACTAMENTE ESTE FORMATO)
═══════════════════════════════════════════════════════════════════════════════

[
  {{
    "i": 1,
    "ok": true,
    "q": 8,
    "giftia_score": 4.7,
    "category": "Tech",
    "age": ["jovenes", "adultos"],
    "gender": "unisex",
    "recipients": ["amigo", "pareja", "yo"],
    "occasions": ["cumpleanos", "navidad", "aniversario"],
    "marketing_hook": "hedonism",
    "seo_title": "Regalo para Melómanos: Auriculares Sony Premium | Giftia",
    "meta_description": "Los auriculares con mejor cancelación de ruido. El regalo perfecto para amantes de la música. Ver precio y análisis en Giftia.",
    "h1_title": "Auriculares que Silencian el Mundo",
    "short_description": "Imagina regalar la capacidad de desconectar del ruido. Estos auriculares premium ofrecen la mejor cancelación del mercado. Un regalo que demuestra que entiendes lo que realmente importa a esa persona especial.",
    "expert_opinion": "Después de analizar decenas de auriculares, estos Sony destacan por encima del resto. La cancelación de ruido funciona de verdad en el metro o en la oficina. No sacrifican calidad de sonido por silencio. Eso sí, son grandes y llamativos, no para quien busca discreción. Pero si el destinatario valora su espacio sonoro personal, este es EL regalo que recordará.",
    "pros": ["Cancelación de ruido líder que te aísla del mundo", "Batería para un vuelo transatlántico completo", "Comodidad premium para sesiones maratonianas", "Sonido que revela detalles ocultos en tu música", "Diseño elegante que impresiona"],
    "cons": ["Inversión importante, aunque justificada", "Tamaño considerable, no son discretos", "App necesaria para personalización completa"],
    "full_description": "## Por qué este regalo es especial\\n\\nEn un mundo lleno de ruido constante, regalar silencio es regalar paz. Estos auriculares Sony representan lo mejor de la tecnología de audio actual, con una cancelación de ruido que no es marketing—es magia real. El momento en que te los pones y el mundo desaparece es algo que quien lo prueba no olvida.\\n\\n## Características que enamoran\\n\\nLa cancelación de ruido adaptativa aprende tu entorno y ajusta el nivel automáticamente. Puedes estar en el metro más ruidoso y solo escuchar tu música con claridad cristalina. Los drivers de 40mm ofrecen un sonido equilibrado que revela matices que nunca habías notado en tus canciones favoritas. La comodidad está cuidada al detalle: almohadillas de espuma con memoria que no presionan incluso tras horas de uso.\\n\\n## La experiencia de usarlo\\n\\nImagina tu vuelo de 8 horas sin el zumbido del motor. O trabajar desde casa sin escuchar las obras del vecino. O simplemente disfrutar de tu álbum favorito como si estuvieras en un estudio de grabación. Esa es la experiencia diaria con estos auriculares. El Speak-to-Chat pausa automáticamente cuando hablas, y la batería de 30 horas significa que casi nunca verás el indicador en rojo.\\n\\n## ¿Por qué elegir este y no otro?\\n\\nExisten alternativas más baratas, sí. Pero ninguna iguala el equilibrio entre cancelación, calidad de sonido y comodidad. Los Bose son cercanos pero el sonido Sony es superior. Los AirPods Max cuestan más y pesan el doble. Estos Sony son el sweet spot donde todo encaja perfectamente.\\n\\n## Detalles técnicos para curiosos\\n\\n• Procesador V1 + QN1 para cancelación líder\\n• Drivers de 40mm con diafragma de fibra de carbono\\n• Bluetooth 5.2 multipoint (2 dispositivos)\\n• Batería 30h con carga rápida (3h en 3 min)\\n• Peso: 250g con almohadillas premium\\n• Códecs: LDAC, AAC, SBC\\n\\n## Veredicto Giftia\\n\\nUn regalo que transforma el día a día de quien lo recibe. Perfecto para melómanos, viajeros frecuentes, o cualquiera que valore su espacio sonoro. No es para presupuestos muy ajustados, pero la inversión vale cada euro. Quien lo reciba pensará en ti cada vez que se los ponga.",
    "who_is_for": "Perfecto para el melómano que aprecia cada matiz musical. Ideal para viajeros frecuentes que necesitan paz en vuelos largos. Excelente para profesionales remotos que requieren concentración absoluta. Para quien se merece un capricho pero nunca se lo compra solo.",
    "faqs": [
      {{"q": "¿Es buen regalo para alguien que no es audiófilo?", "a": "Absolutamente. La cancelación de ruido beneficia a cualquiera: estudiantes, viajeros, teletrabajadores. No necesitas ser experto en audio para apreciar el silencio y la comodidad premium."}},
      {{"q": "¿Vale la pena el precio frente a auriculares más baratos?", "a": "Si el destinatario valora calidad y usará los auriculares a diario, sí. La diferencia en cancelación de ruido y comodidad es notable. Es una inversión en bienestar diario."}},
      {{"q": "¿Son cómodos para usar muchas horas?", "a": "Muy cómodos. Las almohadillas de espuma con memoria distribuyen el peso sin presionar. Probados en vuelos de 10+ horas sin molestias."}},
      {{"q": "¿Funcionan bien para videollamadas?", "a": "Excelentes. Los micrófonos con cancelación de ruido captan tu voz claramente mientras eliminan ruido de fondo. Ideales para trabajo remoto."}},
      {{"q": "¿Qué incluye la caja?", "a": "Auriculares, estuche rígido de viaje, cable USB-C, cable de audio 3.5mm para uso sin batería, y adaptador de avión. Todo lo necesario."}}
    ],
    "verdict": "Un regalo de los que se recuerdan. Perfecto para amantes de la música y quienes valoran su tranquilidad. No apto para presupuestos muy ajustados. Pero si quieres acertar seguro con alguien especial, esta es la apuesta ganadora. Puntuación Giftia: 4.7/5",
    "slug": "auriculares-sony-cancelacion-ruido"
  }},
  {{
    "i": 2,
    "ok": false,
    "q": 2,
    "giftia_score": 0,
    "category": "",
    "age": [],
    "gender": "",
    "recipients": [],
    "occasions": [],
    "marketing_hook": "",
    "seo_title": "",
    "meta_description": "",
    "h1_title": "",
    "short_description": "",
    "expert_opinion": "",
    "pros": [],
    "cons": [],
    "full_description": "",
    "who_is_for": "",
    "faqs": [],
    "verdict": "",
    "slug": ""
  }}
]

⚠️ RECORDATORIO CRÍTICO DE LONGITUDES MÍNIMAS:
- short_description: MÍNIMO 80 palabras (3-4 frases completas)
- expert_opinion: MÍNIMO 100 palabras (párrafo completo con opinión personal)
- full_description: MÍNIMO 600 palabras (6 secciones con H2, cada una 100+ palabras)
- who_is_for: MÍNIMO 80 palabras (4 perfiles detallados)
- verdict: MÍNIMO 50 palabras (conclusión completa)

Si no cumples estas longitudes, la ficha no posicionará en Google.

SOLO JSON VÁLIDO. Sin explicaciones. Sin markdown. Sin ```json."""

    response = call_gemini(prompt)
    
    if not response:
        return [None] * len(products)  # No se pudo clasificar
    
    try:
        # Buscar array JSON en la respuesta
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            json_str = json_match.group()
            
            # Limpiar JSON problemático
            json_str = re.sub(r',\s*]', ']', json_str)  # Quitar coma trailing
            json_str = re.sub(r',\s*}', '}', json_str)  # Quitar coma trailing en objetos
            json_str = json_str.replace('…', '...')  # Reemplazar elipsis unicode
            json_str = re.sub(r'[\x00-\x1f]', ' ', json_str)  # Quitar caracteres de control
            json_str = json_str.replace('\\"', "'")  # Reemplazar escaped quotes problemáticas
            
            # Debug: guardar respuesta si falla
            try:
                results = json.loads(json_str)
                # DEBUG: Siempre guardar la última respuesta para verificar
                with open('last_gemini_response_ok.txt', 'w', encoding='utf-8') as f:
                    f.write(f"=== RAW RESPONSE ===\n{response}\n\n=== PARSED RESULTS ===\n{json.dumps(results, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError as je:
                logger.warning(f"Error parseando batch Gemini: {je}")
                # Guardar respuesta para debug
                with open('last_gemini_response.txt', 'w', encoding='utf-8') as f:
                    f.write(f"=== RAW RESPONSE ===\n{response}\n\n=== EXTRACTED JSON ===\n{json_str}")
                return [None] * len(products)
            
            # Mapear resultados a productos
            classifications = []
            for i, product in enumerate(products):
                # Buscar resultado correspondiente por índice
                result = None
                for r in results:
                    if r.get("i") == i + 1:
                        result = r
                        break
                
                # Si no encontró por i, usar por posición
                if result is None and i < len(results):
                    result = results[i]
                
                if result:
                    # Obtener título optimizado
                    opt_title = result.get("title", "") or product.get("title", "")
                    # Obtener slug - si no hay, generarlo desde título
                    seo_slug = result.get("slug", "")
                    if not seo_slug and opt_title:
                        seo_slug = generate_seo_slug(opt_title)
                    
                    # Obtener categoría - DEBE coincidir con giftia_schema.json
                    category = result.get("category", "Tech")
                    if category not in VALID_CATEGORIES:
                        category = VALID_CATEGORIES[0] if VALID_CATEGORIES else "Tech"
                    
                    # Obtener edad - array de valores del schema
                    age_raw = result.get("age", [])
                    if isinstance(age_raw, str):
                        age_raw = [age_raw]
                    ages = [a for a in age_raw if a in VALID_AGES]
                    if not ages:
                        ages = ["adultos"]  # Fallback
                    
                    # Obtener género
                    gender = result.get("gender", "unisex")
                    if gender not in VALID_GENDERS:
                        gender = "unisex"
                    
                    # Obtener destinatarios - array del schema
                    recipients_raw = result.get("recipients", [])
                    if isinstance(recipients_raw, str):
                        recipients_raw = [recipients_raw]
                    recipients = [r for r in recipients_raw if r in VALID_RECIPIENTS]
                    if not recipients:
                        recipients = ["amigo"]  # Fallback
                    
                    # Obtener ocasiones - array del schema
                    occasions_raw = result.get("occasions", [])
                    if isinstance(occasions_raw, str):
                        occasions_raw = [occasions_raw]
                    occasions = [o for o in occasions_raw if o in VALID_OCCASIONS]
                    if not occasions:
                        occasions = ["cumpleanos", "navidad"]  # Fallback
                    
                    # Obtener marketing_hook - uno de los 5 ganchos psicológicos
                    VALID_HOOKS = ["core", "habitat", "style", "hedonism", "wildcard"]
                    marketing_hook = result.get("marketing_hook", "").lower()
                    if marketing_hook not in VALID_HOOKS:
                        marketing_hook = "wildcard"  # Fallback
                    
                    # Obtener giftia_score (estrellas 1-5)
                    giftia_score = float(result.get("giftia_score", 0))
                    if giftia_score == 0:
                        # Calcular desde gift_quality (1-10) → (1-5)
                        giftia_score = round(int(result.get("q", 5)) / 2, 1)
                    giftia_score = max(1.0, min(5.0, giftia_score))  # Clamp 1-5
                    
                    classifications.append({
                        # Evaluación
                        "is_good_gift": result.get("ok", False),
                        "gift_quality": int(result.get("q", 5)),
                        "giftia_score": giftia_score,  # Estrellas 1-5 para Schema.org
                        
                        # Taxonomías según giftia_schema.json
                        "category": category,        # Tech, Gamer, Gourmet, etc.
                        "ages": ages,                # ninos, adolescentes, jovenes, adultos, seniors, abuelos
                        "gender": gender,            # unisex, male, female, kids
                        "recipients": recipients,    # pareja, padre, amigo, etc.
                        "occasions": occasions,      # cumpleanos, navidad, etc.
                        "marketing_hook": marketing_hook,  # core, habitat, style, hedonism, wildcard
                        
                        # ═══════════════════════════════════════════════════════
                        # FICHA SEO COMPLETA - GOLD MASTER v51
                        # ═══════════════════════════════════════════════════════
                        
                        # Metadatos SEO (Google SERP)
                        "seo_title": result.get("seo_title", ""),                      # Meta title 50-60 chars
                        "meta_description": result.get("meta_description", ""),        # Snippet 150-160 chars
                        
                        # Títulos y gancho
                        "h1_title": result.get("h1_title", opt_title),                 # H1 persuasivo 40-70 chars
                        "short_description": result.get("short_description", ""),      # Above the fold 80-120 palabras
                        
                        # Opinión experto (E-E-A-T)
                        "expert_opinion": result.get("expert_opinion", ""),            # 100-150 palabras
                        
                        # Pros y Contras
                        "pros": result.get("pros", []),                                # 5-6 bullets emocionales
                        "cons": result.get("cons", []),                                # 2-3 bullets honestos
                        
                        # Descripción larga SEO (posiciona la URL)
                        "full_description": result.get("full_description", ""),        # 600-800 palabras con H2s
                        
                        # Buyer persona
                        "who_is_for": result.get("who_is_for", ""),                    # 80-100 palabras
                        
                        # FAQs (Featured Snippets)
                        "faqs": result.get("faqs", []),                                # 4-5 Q&A
                        
                        # Veredicto final
                        "verdict": result.get("verdict", ""),                          # 50-80 palabras
                        
                        # URL slug
                        "seo_slug": result.get("slug", seo_slug),                      # max 5 palabras
                        
                        # Legacy compatibility (mantener para código existente)
                        "marketing_title": result.get("h1_title", opt_title),
                        "optimized_title": result.get("h1_title", opt_title),
                        "seo_content": result.get("full_description", ""),             # Alias para compatibilidad
                        "why_selected": result.get("expert_opinion", ""),              # Alias
                        "gift_headline": result.get("short_description", ""),
                        "gift_pros": result.get("pros", []),
                        "source": "gemini"
                    })
                else:
                    classifications.append(None)
            
            return classifications
    except Exception as e:
        logger.warning(f"Error parseando batch Gemini: {e}")
        logger.debug(f"Respuesta: {response[:300] if response else 'None'}")
    
    return [None] * len(products)

def add_back_to_queue(product):
    """Devuelve un producto a la cola para procesarlo después."""
    queue = load_pending_queue()
    # Añadir al final de la cola
    product['retry_count'] = product.get('retry_count', 0) + 1
    queue.append(product)
    save_pending_queue(queue)
    logger.info(f"🔄 Devuelto a cola (intento {product['retry_count']}): {product.get('title', '')[:40]}...")

def process_product(product):
    title = product.get("title", "")
    asin = product.get("asin", "")
    price = float(product.get("price", "0").replace(",", ".").replace("€", "").strip() or 0)
    
    # Máximo 3 reintentos
    if product.get('retry_count', 0) >= 3:
        logger.warning(f"⚠️ Máximo reintentos alcanzado, descartando: {title[:40]}...")
        log_processed_product(product, {"status": "max_retries", "reason": "3 intentos fallidos"})
        return False
    
    # Llamar a Gemini - SIN FALLBACK
    classification = classify_with_gemini(title, price, product.get("description", ""))
    
    # Si Gemini no responde, devolver a cola
    if classification is None:
        add_back_to_queue(product)
        return False  # No publicado, pero volverá a intentarse
    
    if not classification["is_good_gift"]:
        reason = classification.get("reject_reason", "no es buen regalo")
        logger.info(f"🧠 RECHAZADO: {reason} - {title[:40]}...")
        log_processed_product(product, {"status": "rejected", "reason": reason})
        return False
    
    if classification["gift_quality"] < 5:
        logger.info(f"🧠 CALIDAD BAJA ({classification['gift_quality']}/10): {title[:40]}...")
        log_processed_product(product, {"status": "rejected", "reason": f"calidad {classification['gift_quality']}"})
        return False
    
    # Enriquecer producto - TODOS LOS DATOS DE GEMINI v51
    # Datos básicos de clasificación
    product["gemini_category"] = classification["category"]
    product["target_gender"] = classification.get("gender", "unisex")
    product["gift_quality"] = classification["gift_quality"]
    product["giftia_score"] = classification.get("giftia_score", 4.0)
    product["classification_source"] = "gemini"
    product["vibes"] = [classification["category"]]
    product["gift_score"] = classification["gift_quality"] * 10
    product["processed_at"] = datetime.now().isoformat()
    
    # Taxonomías enriquecidas
    product["ages"] = classification.get("ages", ["adultos"])
    product["recipients"] = classification.get("recipients", [])
    product["occasions"] = classification.get("occasions", ["cumpleanos", "navidad"])
    product["marketing_hook"] = classification.get("marketing_hook", "wildcard")
    
    # ═══════════════════════════════════════════════════════
    # FICHA SEO COMPLETA - GOLD MASTER v51
    # ═══════════════════════════════════════════════════════
    
    # Metadatos SEO (Google SERP)
    product["seo_title"] = classification.get("seo_title", "")
    product["meta_description"] = classification.get("meta_description", "")
    
    # Títulos y gancho
    product["h1_title"] = classification.get("h1_title", product.get("title", ""))
    product["optimized_title"] = classification.get("h1_title", product.get("title", ""))
    product["marketing_title"] = classification.get("h1_title", product.get("title", ""))
    product["short_description"] = classification.get("short_description", "")
    product["gift_headline"] = classification.get("short_description", "")
    
    # Opinión experto (E-E-A-T)
    product["expert_opinion"] = classification.get("expert_opinion", "")
    product["why_selected"] = classification.get("expert_opinion", "")
    
    # Pros y Contras
    product["pros"] = classification.get("pros", [])
    product["cons"] = classification.get("cons", [])
    product["gift_pros"] = classification.get("pros", [])
    
    # Descripción larga SEO
    product["full_description"] = classification.get("full_description", "")
    product["seo_content"] = classification.get("full_description", "")
    
    # Buyer persona
    product["who_is_for"] = classification.get("who_is_for", "")
    product["perfect_for"] = classification.get("who_is_for", "")
    
    # FAQs (Featured Snippets)
    product["faqs"] = classification.get("faqs", [])
    
    # Veredicto final
    product["verdict"] = classification.get("verdict", "")
    
    # URL slug
    product["seo_slug"] = classification.get("seo_slug", "")
    
    # Rating de Amazon (asegurar que se envía)
    if "rating_value" not in product or not product["rating_value"]:
        product["rating_value"] = product.get("rating", 0)
    if "review_count" not in product or not product["review_count"]:
        product["review_count"] = product.get("reviews_count", 0)
    
    # Enviar a WordPress
    logger.info(f"🧠 ENVIANDO [Q:{classification['gift_quality']}] [{classification['category']}] {title[:40]}...")
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'X-GIFTIA-TOKEN': WP_TOKEN,
            'User-Agent': 'GiftiaQueueProcessor/1.0'
        }
        
        response = requests.post(
            WP_API_URL,
            data=json.dumps(product, ensure_ascii=False).encode('utf-8'),
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            logger.info(f"✅ WordPress OK: {title[:40]}")
            log_processed_product(product, {"status": "published", "quality": classification["gift_quality"]})
            time.sleep(WP_PACING_SECONDS)  # Evitar rate limiting
            return True
        else:
            logger.error(f"❌ Error API {response.status_code}: {response.text[:100]}")
            log_processed_product(product, {"status": "error", "http_code": response.status_code})
            time.sleep(WP_PACING_SECONDS)  # Esperar aunque falle
            return False
    except Exception as e:
        logger.error(f"❌ Excepción: {e}")
        log_processed_product(product, {"status": "error", "exception": str(e)})
        return False

def run_processor():
    queue_size = get_pending_count()
    if queue_size == 0:
        print("📭 Cola vacía, nada que procesar")
        return 0
    
    batches_needed = (queue_size + BATCH_SIZE - 1) // BATCH_SIZE
    
    print(f"")
    print(f"═══════════════════════════════════════════")
    print(f"🚀 PROCESADOR TURBO - BATCH MODE")
    print(f"═══════════════════════════════════════════")
    print(f"📦 Productos en cola: {queue_size}")
    print(f"📦 Batch size: {BATCH_SIZE} productos por petición")
    print(f"📊 Peticiones Gemini: ~{batches_needed}")
    print(f"⏱️ Pacing: {GEMINI_PACING_SECONDS}s entre batches")
    print(f"⏰ Tiempo estimado: {batches_needed * GEMINI_PACING_SECONDS / 60:.1f} minutos")
    print(f"🔑 API Key de PAGO activa")
    print(f"")
    
    total_processed = 0
    total_published = 0
    batch_num = 0
    
    while True:
        batch = get_batch_from_queue()
        if not batch:
            break
        
        batch_num += 1
        remaining = get_pending_count()
        logger.info(f"═══════════════════════════════════════════")
        logger.info(f"📦 BATCH {batch_num}: {len(batch)} productos (quedan {remaining})")
        
        # Clasificar batch completo con UNA petición
        classifications = classify_batch_with_gemini(batch)
        
        # Procesar resultados
        for i, (product, classification) in enumerate(zip(batch, classifications)):
            title = product.get("title", "")[:40]
            
            if classification is None:
                # Gemini no respondió - devolver a cola
                add_back_to_queue(product)
                logger.warning(f"   🔄 Sin respuesta AI: {title}...")
                continue
            
            total_processed += 1
            
            # Rechazar duplicados detectados por Gemini
            if classification.get("is_duplicate", False):
                logger.info(f"   🔄 DUPLICADO (hay mejor alternativa): {title}...")
                log_processed_product(product, {"status": "rejected", "reason": "duplicado inferior"})
                continue
            
            if not classification["is_good_gift"]:
                logger.info(f"   ❌ NO ES BUEN REGALO - {title}...")
                log_processed_product(product, {"status": "rejected"})
                continue
            
            if classification["gift_quality"] < 5:
                logger.info(f"   ⚠️ BAJA CALIDAD ({classification['gift_quality']}/10): {title}...")
                log_processed_product(product, {"status": "rejected", "reason": f"calidad {classification['gift_quality']}"})
                continue
            
            # Producto aprobado - enriquecer con datos optimizados de Gemini
            original_title = product.get("title", "")
            
            # Usar marketing_title de Gemini como título principal
            marketing_title = classification.get("marketing_title", "")
            product["title"] = marketing_title if marketing_title else original_title
            product["original_title"] = original_title  # Guardar original por si acaso
            
            # Datos de clasificación según giftia_schema.json
            product["category"] = classification["category"]     # Tech, Gamer, Gourmet, etc.
            product["gemini_category"] = classification["category"]  # Compatibilidad legacy
            product["target_gender"] = classification["gender"]  # unisex, male, female, kids
            product["gift_quality"] = classification["gift_quality"]
            product["giftia_score"] = classification.get("giftia_score", 4.0)  # Estrellas 1-5
            product["classification_source"] = "gemini"
            
            # ==========================================
            # FICHA DE PRODUCTO COMPLETA (Gold Master v51)
            # ==========================================
            
            # Metadatos SEO (para Google SERP)
            product["seo_title"] = classification.get("seo_title", "")                     # Meta title 50-60 chars
            product["meta_description"] = classification.get("meta_description", "")       # Snippet 150-160 chars
            
            # Títulos y gancho
            product["h1_title"] = classification.get("h1_title", product.get("title", "")) # H1 persuasivo
            product["optimized_title"] = classification.get("h1_title", product.get("title", ""))
            product["marketing_title"] = classification.get("h1_title", product.get("title", ""))
            product["short_description"] = classification.get("short_description", "")     # Above the fold 80-120 palabras
            product["gift_headline"] = classification.get("short_description", "")         # Alias
            
            # Opinión del experto (E-E-A-T)
            product["expert_opinion"] = classification.get("expert_opinion", "")           # 100-150 palabras
            product["why_selected"] = classification.get("expert_opinion", "")             # Alias
            
            # Pros y Contras
            product["pros"] = classification.get("pros", [])                               # 5-6 bullets emocionales
            product["cons"] = classification.get("cons", [])                               # 2-3 bullets honestos
            product["gift_pros"] = classification.get("pros", [])                          # Alias
            
            # Descripción larga SEO (posiciona la URL)
            product["full_description"] = classification.get("full_description", "")       # 600-800 palabras con H2s
            product["seo_content"] = classification.get("full_description", "")            # Alias
            
            # Buyer persona
            product["who_is_for"] = classification.get("who_is_for", "")                   # 80-100 palabras
            product["perfect_for"] = classification.get("who_is_for", "")                  # Alias
            
            # FAQs (Featured Snippets)
            product["faqs"] = classification.get("faqs", [])                               # 4-5 Q&A
            
            # Veredicto final
            product["verdict"] = classification.get("verdict", "")                         # 50-80 palabras
            
            # URL slug
            product["seo_slug"] = classification.get("seo_slug", "")
            
            # ==========================================
            # TAXONOMÍAS SEGÚN giftia_schema.json
            # ==========================================
            product["ages"] = classification.get("ages", ["adultos"])           # ninos, adolescentes, jovenes, adultos, seniors, abuelos
            product["recipients"] = classification.get("recipients", ["amigo"]) # pareja, padre, amigo, hermano, etc.
            product["occasions"] = classification.get("occasions", ["cumpleanos", "navidad"])  # cumpleanos, navidad, etc.
            product["marketing_hook"] = classification.get("marketing_hook", "wildcard")  # core, habitat, style, hedonism, wildcard
            
            # Campos legacy para compatibilidad
            product["gift_score"] = classification["gift_quality"] * 10
            product["processed_at"] = datetime.now().isoformat()
            
            # Log con las nuevas dimensiones
            category = classification.get("category", "Tech")
            ages_str = ','.join(classification.get("ages", [])[:2])
            recipients_str = ','.join(classification.get("recipients", [])[:2])
            display_title = product["title"][:30]
            
            # Enviar a WordPress
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'X-GIFTIA-TOKEN': WP_TOKEN,
                    'User-Agent': 'GiftiaQueueProcessor/2.0'
                }
                
                response = requests.post(
                    WP_API_URL,
                    data=json.dumps(product, ensure_ascii=False).encode('utf-8'),
                    headers=headers,
                    timeout=15
                )
                
                # Verificar éxito: status 200 O respuesta contiene "success":true
                # (WordPress a veces devuelve 500 pero el producto sí se guarda)
                is_success = response.status_code == 200 or '"success":true' in response.text
                
                if is_success:
                    total_published += 1
                    # Añadir al inventario para futura deduplicación
                    add_to_inventory(product, classification)
                    logger.info(f"   ✅ [Q:{classification['gift_quality']}] [{category}] 👥{recipients_str} 🎂{ages_str}: {display_title}...")
                    log_processed_product(product, {"status": "published", "quality": classification["gift_quality"]})
                else:
                    logger.error(f"   ❌ Error WP {response.status_code}: {display_title}...")
                    log_processed_product(product, {"status": "error", "http_code": response.status_code})
            except Exception as e:
                logger.error(f"   ❌ Excepción WP: {e}")
                log_processed_product(product, {"status": "error", "exception": str(e)})
        
        # Pacing entre batches
        if get_pending_count() > 0:
            time.sleep(GEMINI_PACING_SECONDS)
    
    print(f"")
    print(f"═══════════════════════════════════════════")
    print(f"📊 RESUMEN FINAL")
    print(f"═══════════════════════════════════════════")
    print(f"🔢 Procesados: {total_processed}")
    print(f"✅ Publicados: {total_published}")
    print(f"📭 Quedan en cola: {get_pending_count()}")
    print(f"🔑 Llamadas Gemini: {gemini_call_count} (batches de {BATCH_SIZE})")
    return total_published

if __name__ == "__main__":
    try:
        run_processor()
    except KeyboardInterrupt:
        print(f"\n🛑 Interrumpido. Quedan {get_pending_count()} en cola.")
