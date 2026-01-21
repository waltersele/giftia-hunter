"""
AWIN Feed Importer - Gold Master v51
Descarga feeds de productos de Awin, aplica filtros de calidad y añade a pending_products.json

Flujo:
1. Fetch feedList para auto-discovery de feeds actualizados
2. Filtrar por merchant IDs configurados (El Corte Inglés, Sprinter, Padel Market)
3. Comparar timestamps con última ejecución
4. Descargar feeds modificados (CSV gzipped)
5. Aplicar 4 Filtros de Excelencia
6. Añadir productos a pending_products.json con metadata de Awin
"""

import os
import json
import gzip
import csv
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Optional
import time

# Cargar configuración
load_dotenv()

# URLs y credenciales
AWIN_FEEDLIST_URL = os.getenv("AWIN_FEEDLIST_URL")
AWIN_PUBLISHER_ID = os.getenv("AWIN_PUBLISHER_ID")
AWIN_API_KEY = os.getenv("AWIN_API_KEY")
AWIN_MERCHANTS = [int(m) for m in os.getenv("AWIN_MERCHANTS", "").split(",")]

# Archivos de estado
FEED_TIMESTAMPS_FILE = "awin_feed_timestamps.json"
PENDING_PRODUCTS_FILE = "pending_products.json"
IMPORT_LOG_FILE = "awin_import_log.txt"

# Filtros de Excelencia (alineados con hunter.py)
# NOTA: Feeds Awin NO incluyen rating/reviews, solo filtramos por precio/stock/EAN
# Gemini AI hará el filtro de calidad en process_queue.py
MIN_PRICE = 12
MAX_PRICE = 200

# Mapeo de merchant IDs a nombres
MERCHANT_NAMES = {
    13075: "El Corte Inglés",
    27904: "Sprinter",
    24562: "Padel Market"
}


def log_message(message: str):
    """Log con timestamp a archivo y consola"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(IMPORT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")


def fetch_feed_list() -> List[Dict]:
    """Descarga lista de feeds disponibles desde Awin (CSV format)"""
    log_message(f"Fetching feed list from Awin...")
    
    try:
        response = requests.get(AWIN_FEEDLIST_URL, timeout=30)
        response.raise_for_status()
        
        # Parse CSV response
        lines = response.text.strip().split('\n')
        reader = csv.DictReader(lines)
        feed_list = list(reader)
        
        log_message(f"✓ Feed list retrieved: {len(feed_list)} feeds total")
        return feed_list
    
    except requests.exceptions.RequestException as e:
        log_message(f"✗ ERROR fetching feed list: {e}")
        return []
    except Exception as e:
        log_message(f"✗ ERROR parsing CSV: {e}")
        return []


def filter_merchant_feeds(feed_list: List[Dict]) -> List[Dict]:
    """Filtra feeds para nuestros merchants objetivo"""
    filtered = [
        feed for feed in feed_list 
        if int(feed.get("Advertiser ID", 0)) in AWIN_MERCHANTS
    ]
    
    log_message(f"✓ Filtered to {len(filtered)} feeds from target merchants:")
    for feed in filtered:
        merchant_id = int(feed["Advertiser ID"])
        merchant_name = MERCHANT_NAMES.get(merchant_id, "Unknown")
        log_message(f"  - {merchant_name} (ID {merchant_id}): Feed {feed.get('Feed ID')} - {feed.get('No of products')} products")
    
    return filtered


def load_feed_timestamps() -> Dict[str, str]:
    """Carga timestamps de última descarga"""
    if os.path.exists(FEED_TIMESTAMPS_FILE):
        with open(FEED_TIMESTAMPS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_feed_timestamps(timestamps: Dict[str, str]):
    """Guarda timestamps de feeds descargados"""
    with open(FEED_TIMESTAMPS_FILE, "w", encoding="utf-8") as f:
        json.dump(timestamps, f, indent=2, ensure_ascii=False)


def needs_update(feed: Dict, last_timestamps: Dict[str, str]) -> bool:
    """Verifica si el feed necesita actualizarse"""
    feed_id = str(feed.get("Feed ID"))
    last_updated = feed.get("Last Imported")
    
    if feed_id not in last_timestamps:
        return True
    
    return last_timestamps[feed_id] != last_updated


def download_and_parse_feed(feed: Dict) -> List[Dict]:
    """Descarga y parsea CSV gzipped de un feed"""
    feed_url = feed.get("URL")
    feed_id = feed.get("Feed ID")
    merchant_id = int(feed.get("Advertiser ID"))
    merchant_name = MERCHANT_NAMES.get(merchant_id, "Unknown")
    
    log_message(f"Downloading feed {feed_id} from {merchant_name}...")
    
    try:
        # Descargar CSV gzipped
        response = requests.get(feed_url, timeout=60, stream=True)
        response.raise_for_status()
        
        # Descomprimir y parsear
        products = []
        with gzip.GzipFile(fileobj=response.raw) as gz:
            csv_content = gz.read().decode('utf-8', errors='ignore')
            csv_reader = csv.DictReader(csv_content.splitlines())
            
            for row in csv_reader:
                products.append({
                    "merchant_id": merchant_id,
                    "merchant_name": merchant_name,
                    "feed_id": feed_id,
                    **row
                })
        
        log_message(f"✓ Parsed {len(products)} products from feed {feed_id}")
        return products
    
    except Exception as e:
        log_message(f"✗ ERROR downloading feed {feed_id}: {e}")
        return []


def apply_quality_filters(products: List[Dict]) -> List[Dict]:
    """Aplica Filtros de Excelencia (adaptados para Awin sin rating/reviews)"""
    log_message(f"\n🔍 Applying quality filters to {len(products)} products...")
    
    filtered = []
    stats = {
        "total": len(products),
        "out_of_price_range": 0,
        "missing_ean": 0,
        "out_of_stock": 0,
        "passed": 0
    }
    
    for product in products:
        # 1. Price check (12-200€)
        try:
            price_str = product.get("search_price", "0").replace(",", ".")
            price = float(price_str)
        except (ValueError, TypeError, AttributeError):
            stats["out_of_price_range"] += 1
            continue
        
        if price < MIN_PRICE or price > MAX_PRICE:
            stats["out_of_price_range"] += 1
            continue
        
        # 2. EAN check (crítico para multi-vendor matching)
        ean = product.get("ean", "") or product.get("product_GTIN", "")
        ean = str(ean).strip()
        if not ean or ean.lower() in ["null", "none", ""]:
            stats["missing_ean"] += 1
            continue
        
        # 3. Stock check
        in_stock = str(product.get("in_stock", "")).lower()
        stock_status = str(product.get("stock_status", "")).lower()
        
        if in_stock not in ["yes", "1", "true", "y"] and stock_status not in ["in stock", "instock"]:
            stats["out_of_stock"] += 1
            continue
        
        # ✓ Producto aprobado - rating/reviews los filtra Gemini
        filtered.append(product)
        stats["passed"] += 1
    
    # Resumen
    log_message(f"\n📊 Filter Results:")
    log_message(f"  Total products: {stats['total']}")
    log_message(f"  ✗ Price out of range (€{MIN_PRICE}-{MAX_PRICE}): {stats['out_of_price_range']}")
    log_message(f"  ✗ Missing EAN: {stats['missing_ean']}")
    log_message(f"  ✗ Out of stock: {stats['out_of_stock']}")
    log_message(f"  ✓ PASSED: {stats['passed']} ({(stats['passed']/stats['total']*100):.1f}%)")
    log_message(f"\n💡 NOTE: Rating/reviews not in Awin feeds. Gemini will filter quality.")
    
    return filtered


def transform_to_giftia_format(products: List[Dict]) -> List[Dict]:
    """Transforma productos de Awin al formato de pending_products.json"""
    log_message(f"\n🔄 Transforming {len(products)} products to Giftia format...")
    
    transformed = []
    for product in products:
        # Extraer datos básicos
        title = product.get("product_name", "").strip()
        description = product.get("description", "").strip()
        price_str = product.get("search_price", "0").replace(",", ".")
        price = float(price_str)
        
        # ⚠️ IMPORTANTE: Feeds de Awin NO incluyen columnas de rating/reviews
        # Los CSV de Awin no tienen campos como "rating", "stars", "reviews", etc.
        # Política: NO inventar reviews de vendors que no las tienen en su web
        # Referencia: AWIN_VENDOR_POLICY.md
        rating_value = 0.0
        review_count = 0
        has_reviews = False  # Flag para frontend: NO mostrar estrellas/reviews
        
        # Extraer delivery info
        delivery_time = product.get("delivery_time", "").strip()
        delivery_cost = product.get("delivery_cost", "0").strip()
        
        # Normalizar delivery_cost
        try:
            delivery_cost_float = float(delivery_cost.replace(",", "."))
            free_shipping = delivery_cost_float == 0
        except (ValueError, AttributeError):
            free_shipping = False
        
        # URL de afiliado Awin
        awin_deep_link = product.get("aw_deep_link", "")
        product_url = product.get("merchant_deep_link", "")
        
        # Imagen
        image_url = product.get("aw_image_url") or product.get("merchant_image_url", "")
        
        # Construir objeto Giftia (compatible con pending_products.json)
        giftia_product = {
            "title": title,
            "price": f"{price:.2f} €",
            "rating_value": rating_value,  # 0.0 para Awin (sin ratings)
            "review_count": review_count,  # 0 para Awin (sin reviews)
            "has_reviews": has_reviews,    # false - NO mostrar en frontend
            "image_url": image_url,
            "affiliate_url": awin_deep_link or product_url,
            "description": description,
            "vendor": MERCHANT_NAMES.get(int(product.get("merchant_id", 0)), "Awin"),
            "merchant_id": product.get("merchant_id"),
            "merchant_name": product.get("merchant_name"),
            "ean": product.get("ean") or product.get("product_GTIN", ""),
            "brand": product.get("brand_name", ""),
            "delivery_time": delivery_time,
            "free_shipping": free_shipping,
            "awin_product_id": product.get("aw_product_id"),
            "merchant_product_id": product.get("merchant_product_id"),
            "category": product.get("category_name", ""),
            "source_vibe": "",  # Gemini lo clasifica
            "queued_at": datetime.now().isoformat()
        }
        
        transformed.append(giftia_product)
    
    log_message(f"✓ Transformation complete: {len(transformed)} products ready")
    return transformed


def add_to_pending_queue(products: List[Dict]):
    """Añade productos a pending_products.json"""
    # Cargar cola existente
    if os.path.exists(PENDING_PRODUCTS_FILE):
        with open(PENDING_PRODUCTS_FILE, "r", encoding="utf-8") as f:
            pending = json.load(f)
    else:
        pending = []
    
    # Evitar duplicados por EAN
    existing_eans = {p.get("ean") for p in pending if p.get("ean")}
    new_products = [p for p in products if p.get("ean") not in existing_eans]
    
    # Añadir nuevos productos
    pending.extend(new_products)
    
    # Guardar
    with open(PENDING_PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(pending, f, indent=2, ensure_ascii=False)
    
    log_message(f"\n✓ Added {len(new_products)} new products to pending queue")
    log_message(f"  (Skipped {len(products) - len(new_products)} duplicates by EAN)")
    log_message(f"  Total pending: {len(pending)} products")


def main():
    """Flujo principal de importación"""
    log_message("=" * 80)
    log_message("AWIN FEED IMPORTER - Starting import process")
    log_message("=" * 80)
    
    start_time = time.time()
    
    # 1. Fetch feed list
    feed_list = fetch_feed_list()
    if not feed_list:
        log_message("✗ ABORT: Could not fetch feed list")
        return
    
    # 2. Filtrar por merchants objetivo
    target_feeds = filter_merchant_feeds(feed_list)
    if not target_feeds:
        log_message("✗ ABORT: No feeds found for target merchants")
        return
    
    # 3. Cargar timestamps previos
    last_timestamps = load_feed_timestamps()
    
    # 4. Identificar feeds que necesitan actualización
    feeds_to_update = [feed for feed in target_feeds if needs_update(feed, last_timestamps)]
    
    if not feeds_to_update:
        log_message("\n✓ All feeds are up to date. Nothing to import.")
        return
    
    log_message(f"\n📥 {len(feeds_to_update)} feeds need updating")
    
    # 5. Descargar y procesar feeds
    all_products = []
    new_timestamps = last_timestamps.copy()
    
    for feed in feeds_to_update:
        products = download_and_parse_feed(feed)
        all_products.extend(products)
        
        # Actualizar timestamp
        new_timestamps[str(feed.get("feed_id"))] = feed.get("last_updated")
        
        time.sleep(1)  # Rate limiting cortés
    
    if not all_products:
        log_message("✗ No products downloaded")
        return
    
    # 6. Aplicar filtros de calidad
    filtered_products = apply_quality_filters(all_products)
    
    if not filtered_products:
        log_message("✗ No products passed quality filters")
        return
    
    # 7. Transformar a formato Giftia
    giftia_products = transform_to_giftia_format(filtered_products)
    
    # 8. Añadir a pending queue
    add_to_pending_queue(giftia_products)
    
    # 9. Guardar timestamps
    save_feed_timestamps(new_timestamps)
    
    # Resumen final
    elapsed = time.time() - start_time
    log_message("\n" + "=" * 80)
    log_message(f"✓ IMPORT COMPLETE in {elapsed:.1f}s")
    log_message(f"  Feeds processed: {len(feeds_to_update)}")
    log_message(f"  Products downloaded: {len(all_products)}")
    log_message(f"  Products passed filters: {len(filtered_products)}")
    log_message(f"  New products added to queue: Ready for Gemini processing")
    log_message("=" * 80)


if __name__ == "__main__":
    main()
