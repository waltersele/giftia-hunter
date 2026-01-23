#!/usr/bin/env python3
"""
Hunter Awin Inteligente v2 - Con Filtro de Categoría
Procesa feeds Awin por lotes, filtrando solo categorías objetivo (Tech/Gaming/Electrónica)
Ejecutar cada 2 días para mantener inventario fresco
"""

import os, json, gzip, csv, sys, requests
from datetime import datetime
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

# Configuración
PENDING_QUEUE_FILE = "pending_products.json"
STATE_FILE = "hunter_awin_state.json"
LOG_FILE = "hunter_awin.log"
AWIN_API_KEY = os.getenv("AWIN_API_KEY", "")
AWIN_MERCHANTS = {
    13075: {"name": "elcorteingles", "feed_id": 89688},
    27904: {"name": "sprinter", "feed_id": 71705}
}

# Límites
PRODUCTS_PER_RUN = 100
PRODUCTS_PER_MERCHANT = 50
MAX_ROWS_TO_SCAN = 100000  # Balance tiempo/cobertura
MIN_PRICE = 12.0
MAX_PRICE = 300.0
MIN_TITLE_LENGTH = 15

# ============================================================================
# FILTRO ESPECÍFICO EL CORTE INGLÉS: Mismas categorías que Amazon
# ============================================================================
# Productos que buscamos (balance entre específico y flexible)
TARGET_PRODUCT_KEYWORDS = [
    # Tech - Audio (flexibles)
    "auriculares bluetooth", "auriculares inalambrico", "earbuds", "airpods",
    "cascos bluetooth", "cascos gaming", "headset",
    
    # Tech - Wearables
    "smartwatch", "reloj inteligente", "apple watch", 
    "pulsera actividad", "mi band", "fitbit", "garmin watch",
    
    # Tech - Otros
    "altavoz bluetooth", "altavoz portatil",
    "powerbank", "bateria externa",
    "traductor idiomas",
    "drone", "dron camara",
    "camara instantanea", "instax mini",
    "proyector portatil",
    "teclado gaming", "teclado mecanico",
    "raton gaming",
    "webcam",
    
    # Gaming
    "mando ps5", "mando playstation", "mando xbox", "controller",
    "silla gaming",
    "funko pop",
    
    # Gourmet (productos específicos)
    "cafetera express", "cafetera nespresso", "cafetera dolce",
    "molinillo cafe",
    "cuchillo chef",
    "decantador",
    
    # Deporte
    "mancuernas", "pesas",
    "esterilla yoga",
    "pistola masaje", "masajeador",
    "garmin", "reloj gps",
    "raqueta padel",
]

# Categorías objetivo (tech + deportes electrónicos) - MISMO FILTRO QUE AMAZON
TARGET_CATEGORIES = [
    # Tech
    "auriculares", "cascos", "headphones", "earbuds", "airpods",
    "smartwatch", "reloj inteligente", "fitness tracker", "pulsera actividad",
    "altavoz", "speaker", "bluetooth",
    "cargador inalambrico", "wireless charger",
    "powerbank", "bateria externa",
    "traductor", "translator",
    "drone", "dron",
    "camara instantanea", "instax",  # Eliminado "polaroid" para evitar gafas Polaroid
    "proyector", "tablet", "ipad",
    "teclado gaming", "raton gaming", "webcam",
    
    # Gaming
    "mando ps5", "mando xbox", "controller",
    "silla gaming",
    "funko pop",
    
    # Gourmet
    "cafetera", "coffee maker",
    "molinillo cafe",
    "set cuchillos", "cuchillo chef",
    "decantador",
    
    # Deporte
    "mancuernas", "pesas",
    "esterilla yoga", "yoga mat",
    "pistola masaje",
    "reloj gps", "garmin", "polar vantage",
    
    # Zen
    "difusor", "humidificador",
    "vela aromatica",
    "lampara sal"
]

# Bloqueados - KILLER KEYWORDS del hunter Amazon
BLOCKED_KEYWORDS = [
    # Consumibles/Repuestos
    "recambio", "repuesto", "pack de 10", "pack de 20", "pack de 50",
    "100 unidades", "tornillos", "tuercas", "recarga", "refill", "cartucho",
    
    # Granel
    "garrafa", "5 litros", "5l", "10 litros", "10l", "5kg", "10kg",
    "bulk", "industrial", "hosteleria",
    
    # Limpieza/Hogar aburrido  
    "fregona", "lejia", "detergente", "suavizante", "insecticida",
    "cemento", "masilla", "silicona", "estropajo", "bayeta", "escoba",
    
    # Fontanería/Industrial
    "fontaneria", "tuberia", "pvc", "manguera", "grifo", "valvula",
    
    # Bebé consumibles
    "pañales", "pañal", "toallitas humedas", "leche formula", "potito",
    
    # Accesorios tech baratos
    "funda", "carcasa", "cable", "protector", "soporte", "base",
    "alfombrilla", "adaptador", "correa",
    
    # Oficina aburrido
    "pack folios", "folios 500", "grapadora", "archivador",
    "carpeta", "clips", "chinchetas",
    
    # Ropa interior básica
    "pack calzoncillos", "pack bragas", "pack calcetines",
    
    # MODA GENERAL (El Corte Inglés tiene mucha ropa que NO es regalo)
    "gafas de sol", "gafas sol", "sunglasses",
    "bandolera", "bolso", "bolsa", "mochila", "cartera", "monedero",
    "cinturon", "corbata", "pañuelo", "bufanda", "guantes",
    "zapatillas", "zapatos", "botas", "sandalias", "chanclas",
    "camiseta", "camisa", "polo", "jersey", "sudadera",
    "pantalon", "vaquero", "chaqueta", "abrigo", "cazadora",
    "vestido", "falda", "short", "bermuda"
]

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + "\n")

def parse_price(s):
    if not s: return 0.0
    clean = str(s).replace(',', '.').strip()
    try: return float(clean)
    except: return 0.0

def is_target_category(title, category, merchant_id=None):
    """Filtro MISMO QUE AMAZON: Tech/Gaming/Gourmet/Deporte buenos regalos"""
    title_lower = title.lower()
    cat_lower = category.lower()
    
    # Categorías tech/deportes en feeds
    FEED_CATEGORIES = [
        "electrónica", "electronica", "tecnología", "tecnologia",
        "informática", "informatica", "gaming", "videojuegos",
        "audio", "imagen", "sonido", "smartwatches", "wearables",
        "deportes", "fitness", "running", "yoga", "gym", "outdoor"
    ]
    
    # Si está en categoría válida del feed, buscar keywords específicas
    if any(fc in cat_lower for fc in FEED_CATEGORIES):
        # DEBE coincidir con al menos una keyword de TARGET_CATEGORIES
        has_match = any(target in title_lower for target in TARGET_CATEGORIES)
        return has_match
    
    # Fallback: buscar directamente en título
    return any(target in title_lower for target in TARGET_CATEGORIES)

def is_blocked(title):
    title_lower = title.lower()
    for keyword in BLOCKED_KEYWORDS:
        if keyword in title_lower:
            return True, keyword
    return False, None

def apply_filters(row, processed_ids, merchant_id=None):
    ean = row.get("ean", "").strip()
    mpid = row.get("merchant_product_id", "").strip()
    
    if not ean and not mpid:
        return False, "sin_id"
    
    uid = ean if ean else f"mpid_{mpid}"
    
    if uid in processed_ids:
        return False, "duplicado"
    
    title = row.get("product_name", "").strip()
    if len(title) < MIN_TITLE_LENGTH:
        return False, "titulo_corto"
    
    category = row.get("category_name", "").strip()
    if not is_target_category(title, category, merchant_id):
        return False, "categoria_no_objetivo"
    
    blocked, kw = is_blocked(title)
    if blocked:
        return False, f"bloqueado:{kw}"
    
    price = parse_price(row.get("search_price", "0"))
    if price < MIN_PRICE:
        return False, "precio_bajo"
    if price > MAX_PRICE:
        return False, "precio_alto"
    
    stock = row.get("in_stock", "1")
    if stock == "0":
        return False, "sin_stock"
    
    return True, (price, uid)

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"last_run": None, "processed_ids": []}

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def load_queue():
    try:
        with open(PENDING_QUEUE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_to_queue(products):
    queue = load_queue()
    existing_ids = {p.get('identifiers', {}).get('ean') or p.get('identifiers', {}).get('merchant_product_id') for p in queue}
    
    new_count = 0
    for p in products:
        pid = p.get('identifiers', {}).get('ean') or p.get('identifiers', {}).get('merchant_product_id')
        if pid and pid not in existing_ids:
            p['queued_at'] = datetime.now().isoformat()
            queue.append(p)
            existing_ids.add(pid)
            new_count += 1
    
    with open(PENDING_QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
    
    return new_count

def get_feed_url(mid, fid):
    return f"https://productdata.awin.com/datafeed/download/apikey/{AWIN_API_KEY}/language/es/fid/{fid}/columns/aw_product_id,product_name,aw_deep_link,search_price,ean,merchant_product_id,brand_name,category_name,aw_image_url,description,in_stock/format/csv/delimiter/%2C/compression/gzip/adultcontent/1/"

def process_merchant(mid, mdata, state):
    mname = mdata["name"]
    fid = mdata["feed_id"]
    
    if not fid:
        log(f"⚠️ {mname}: sin feed_id")
        return [], []
    
    log(f"\n{'='*70}")
    log(f"📦 {mname.upper()} (ID: {mid})")
    log(f"{'='*70}")
    
    url = get_feed_url(mid, fid)
    processed_ids = set(state.get("processed_ids", []))
    
    products = []
    stats = {"total": 0, "sin_id": 0, "duplicado": 0, "titulo_corto": 0, "categoria_no_objetivo": 0, "bloqueado": 0, "precio": 0, "sin_stock": 0, "capturados": 0}
    
    try:
        log("📥 Descargando feed...")
        r = requests.get(url, timeout=120, stream=True)
        r.raise_for_status()
        
        log(f"🔍 Procesando (max {MAX_ROWS_TO_SCAN} filas, solo categorías objetivo)...")
        
        with gzip.GzipFile(fileobj=r.raw) as gz:
            header = gz.readline().decode('utf-8', errors='ignore')
            fieldnames = csv.DictReader([header], delimiter=',').fieldnames
            
            for line_bytes in gz:
                stats["total"] += 1
                
                if stats["total"] > MAX_ROWS_TO_SCAN:
                    break
                if stats["capturados"] >= PRODUCTS_PER_MERCHANT:
                    log(f"✅ Límite por merchant alcanzado ({PRODUCTS_PER_MERCHANT})")
                    break
                
                try:
                    line = line_bytes.decode('utf-8', errors='ignore').strip()
                    if not line: continue
                    
                    reader = csv.DictReader([line], fieldnames=fieldnames, delimiter=',')
                    row = next(reader)
                except:
                    continue
                
                is_valid, result = apply_filters(row, processed_ids, mid)
                
                if not is_valid:
                    if result in stats:
                        stats[result] += 1
                    elif "bloqueado:" in result:
                        stats["bloqueado"] += 1
                    elif result in ["precio_bajo", "precio_alto"]:
                        stats["precio"] += 1
                    continue
                
                price, uid = result
                
                product = {
                    "title": row.get("product_name", "").strip(),
                    "price": f"{price:.2f} €",
                    "rating_value": 0.0,
                    "review_count": 0,
                    "has_reviews": False,
                    "image_url": row.get("aw_image_url", ""),
                    "affiliate_url": row.get("aw_deep_link", ""),
                    "description": row.get("description", "").strip()[:500],
                    "vendor": mname.title(),
                    "merchant_id": str(mid),
                    "merchant_name": mname,
                    "brand": row.get("brand_name", ""),
                    "category": row.get("category_name", ""),
                    "identifiers": {
                        "ean": row.get("ean", ""),
                        "merchant_product_id": row.get("merchant_product_id", ""),
                        "awin_product_id": row.get("aw_product_id", "")
                    },
                    "source_vibe": "awin_feed"
                }
                
                products.append(product)
                processed_ids.add(uid)
                stats["capturados"] += 1
                
                if stats["capturados"] % 10 == 0:
                    log(f"   ✅ [{stats['capturados']}/{PRODUCTS_PER_RUN}] {price:.2f}€ - {product['title'][:50]}...")
        
        log(f"\n📊 RESUMEN {mname.upper()}")
        log(f"   Escaneadas: {stats['total']}")
        log(f"   Categoría no objetivo: {stats['categoria_no_objetivo']}")
        log(f"   Bloqueados: {stats['bloqueado']}")
        log(f"   Filtrados precio: {stats['precio']}")
        log(f"   ✅ Capturados: {stats['capturados']}")
        
        return products, list(processed_ids)
        
    except Exception as e:
        log(f"❌ Error: {e}")
        return [], list(processed_ids)

def run_hunter():
    log("\n" + "="*70)
    log("🎯 HUNTER AWIN INTELIGENTE v2")
    log("="*70)
    log(f"Límite: {PRODUCTS_PER_RUN} productos")
    log(f"Escaneo: max {MAX_ROWS_TO_SCAN} filas")
    log(f"Precio: {MIN_PRICE}€ - {MAX_PRICE}€")
    log(f"Categorías: Tech/Gaming/Electrónica")
    
    state = load_state()
    log(f"\n📂 Última ejecución: {state.get('last_run', 'Nunca')}")
    
    all_products = []
    all_ids = set(state.get("processed_ids", []))
    
    for mid, mdata in AWIN_MERCHANTS.items():
        products, ids = process_merchant(mid, mdata, state)
        all_products.extend(products)
        all_ids.update(ids)
        
        if len(all_products) >= PRODUCTS_PER_RUN:
            break
    
    if all_products:
        new_count = save_to_queue(all_products)
        log(f"\n💾 Nuevos en cola: {new_count}")
    else:
        log(f"\n⚠️ No se capturaron productos")
    
    state["last_run"] = datetime.now().isoformat()
    state["processed_ids"] = list(all_ids)[-50000:]
    save_state(state)
    
    log(f"\n{'='*70}")
    log(f"📊 RESUMEN FINAL")
    log(f"{'='*70}")
    log(f"✅ Capturados: {len(all_products)}")
    log(f"🆕 Añadidos: {new_count if all_products else 0}")
    log(f"📝 IDs en histórico: {len(state['processed_ids'])}")
    log(f"\n🚀 Ejecuta: python process_queue.py")
    log(f"⏰ Próxima ejecución: en 2 días")
    log("="*70)

if __name__ == "__main__":
    run_hunter()
