#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GIFTIA HUNTER AWIN - Feed Processor
Procesa feeds de datos de Awin (CSV) para la cola de Giftia.

Uso: python hunter_awin.py <archivo_csv> [--limit N]
"""

import csv
import json
import argparse
import os
import sys
import time
import hashlib
from datetime import datetime

# Archivos de configuración
PENDING_QUEUE_FILE = os.path.join(os.path.dirname(__file__), "pending_products.json")
PROCESSED_LOG_FILE = os.path.join(os.path.dirname(__file__), "processed_products.json")
INVENTORY_FILE = os.path.join(os.path.dirname(__file__), "published_inventory.json")
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "giftia_schema.json")

# ==========================================
# FILTROS Y REGLAS DE NEGOCIO
# ==========================================

# Palabras que MATAN el producto inmediatamente
KILLER_KEYWORDS = [
    # Utilitario / Aburrido
    "recambio", "repuesto", "batería para", "pila", "cargador para", 
    "cable de", "adaptador", "funda para", "protector de pantalla",
    "toner", "cartucho", "tinta para", "filtro para", "bombilla",
    "tornillo", "tuerca", "herramienta de reparación",
    
    # Ropa básica / Lencería no regalo
    "braguita", "calzoncillo", "calcetines básicos", "medias", "lencería básica",
    
    # Libros de texto / Papelería oficina
    "cuaderno", "folio", "archivador", "clip", "grapadora",
    "libro de texto", "cuaderno de ejercicios", "agenda escolar",
    
    # Farmacia / Higiene básica
    "papel higiénico", "pañales", "compresa", "tampón", "pasta de dientes",
    "jabón de manos", "gel de ducha básico", "desodorante básico",
    "mascarilla quirúrgica", "tirita", "jarabe",
    
    # Automóvil / Bricolaje pesado
    "neumático", "limpiaparabrisas", "aceite de motor", "bujía",
    "cemento", "ladrillo", "tubería", "grifo", "fregadero",
    
    # Anti-Relleno Awin (Música física, Libros aburridos)
    " cd", "dvd", "vinilo", "lp-vinilo", "banda sonora", "soundtrack",
    "partitura", "blu-ray", "single cd",
    "libros de texto", "enciclopedia"
]

# CATEGORÍAS "ILUSIÓN" (TARGET)
# Solo aceptamos productos que encajen en estas verticales de regalo
TARGET_CATEGORIES = [
    "tech", "electrónica", "gadget", "informatica", "smart", "audio", "fotografía",
    "gaming", "videojuegos", "consola", "gamer",
    "juguete", "juego", "lego", "muñeca", "construcción",
    "deporte", "fitness", "outdoor", "bicicleta", "patinete", "tenis", "pádel", "fútbol",
    "gourmet", "cocina", "vinos", "vino", "jamón", "cafetera", "hogar", "decoración",
    "viaje", "equipaje", "mochila"
]

def load_schema_keywords():
    """Carga keywords positivas desde giftia_schema.json."""
    positive_keywords = set()
    try:
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            schema = json.load(f)
            categories = schema.get('categories', {})
            for cat_data in categories.values():
                for kw in cat_data.get('keywords', []):
                    positive_keywords.add(kw.lower())
    except Exception as e:
        print(f"⚠️ Error cargando schema: {e}")
        # Fallback básico si falla el archivo
        return {"regalo", "gift", "gourmet", "tech", "juguete", "moda", "decoración"}
        
    return positive_keywords

def load_delivery_schema():
    """Carga configuración de entrega desde giftia_schema.json."""
    try:
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            schema = json.load(f)
            return schema.get('delivery_types', {})
    except Exception as e:
        print(f"⚠️ Error cargando delivery schema: {e}")
        return {}

def classify_delivery_v52(product, delivery_text, delivery_config):
    """
    Clasifica el tipo de entrega usando el Schema Centralizado.
    Prioridad: 
    1. Match directo en campos de entrega (delivery_text).
    2. Match por título (para productos digitales/cards).
    """
    text_corpus = (str(delivery_text) + " " + product['title']).lower()
    
    # 1. Ordenar tipos por prioridad (Mayor a menor)
    sorted_types = sorted(
        delivery_config.items(), 
        key=lambda item: item[1].get('priority', 0), 
        reverse=True
    )
    
    # 2. Iterar y buscar match
    for slug, config in sorted_types:
        keywords = config.get('keywords', [])
        for kw in keywords:
            if kw.lower() in text_corpus:
                return slug
                
    # 3. Fallback
    return "standard"

def is_valid_product(product, positive_keywords):
    """
    Aplica las Reglas de Oro de Giftia:
    1. Precio > 12€ (evitar baratijas, salvo excepciones)
    2. No contiene Killer Keywords (recambios, útiles aburridos)
    3. Categoría no prohibida (Música, Libros de texto)
    4. Contiene al menos una Keyword Positiva del Schema (relevancia)
    """
    title_lower = product['title'].lower()
    cat_lower = product.get('category', '').lower()
    
    # 0. Filtro Categoría Prohibida
    BAD_CATEGORIES = ["música", "music", "libros de texto", "papelería", "bricolaje"]
    for bad in BAD_CATEGORIES:
        if bad in cat_lower:
            return False

    # 1. Filtro Precio (Cheap & Chic threshold)
    if product['price'] < 12.0:
        return False
        
    # 2. Filtro TARGET (Categorías de Ilusión)
    # Debe pertenecer a una de las categorías objetivo (Tech, Gaming, etc.)
    # O tener keywords muy fuertes en el título
    is_target_category = any(target in cat_lower for target in TARGET_CATEGORIES)
    
    # Si la categoría no es target explícito, chequeamos si el título salva el producto
    # (Ej: "Set de Manicura" en categoría "Belleza" que no está en target list pero es buen regalo)
    is_target_keyword = False
    if not is_target_category:
        for kw in positive_keywords:
            if kw in title_lower:
                is_target_keyword = True
                break
    
    # Si no es categoría target Y no tiene keywords target -> Rechazado
    if not (is_target_category or is_target_keyword):
        return False

    # 3. Filtro Asesino (Killer Keywords)
    for kw in KILLER_KEYWORDS:
        if kw in title_lower:
            return False
            
    return True # Ha sobrevivido a todos los filtros

def generate_id(product):
    """Genera un ID único para productos Awin."""
    # Preferimos Awin Product ID si existe
    if product.get('aw_product_id'):
        return f"awin_{product['aw_product_id']}"
    
    # Fallback a hash de la URL
    url = product.get('merchant_deep_link', '') or product.get('aw_deep_link', '')
    if url:
        return f"awin_url_{hashlib.md5(url.encode()).hexdigest()[:12]}"
    
    return f"awin_unk_{int(time.time()*1000)}"

def load_existing_ids():
    """Carga IDs ya procesados para deduplicación."""
    existing_ids = set()
    
    # 1. Chequear inventario publicado
    if os.path.exists(INVENTORY_FILE):
        try:
            with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
                inv = json.load(f)
                for cat in inv.values():
                    for item in cat:
                        if 'asin' in item and item['asin']:
                            existing_ids.add(item['asin'])
        except Exception as e:
            print(f"⚠️ Error leyendo inventario: {e}")

    # 2. Chequear log de procesados recientes
    if os.path.exists(PROCESSED_LOG_FILE):
        try:
            with open(PROCESSED_LOG_FILE, 'r', encoding='utf-8') as f:
                processed = json.load(f)
                for item in processed:
                    if 'asin' in item:
                        existing_ids.add(item['asin'])
        except Exception as e:
            print(f"⚠️ Error leyendo processed log: {e}")
            
    # 3. Chequear cola actual
    if os.path.exists(PENDING_QUEUE_FILE):
        try:
            with open(PENDING_QUEUE_FILE, 'r', encoding='utf-8') as f:
                queue = json.load(f)
                for item in queue:
                    if 'asin' in item:
                        existing_ids.add(item['asin'])
        except Exception as e:
            print(f"⚠️ Error leyendo cola pendiente: {e}")

    return existing_ids

def parse_price(price_str):
    try:
        return float(str(price_str).replace(',', '.').strip())
    except:
        return 0.0

def process_awin_feed(filepath, limit=None):
    print(f"📂 Abriendo feed: {filepath}")
    
    existing_ids = load_existing_ids()
    print(f"🔍 {len(existing_ids)} productos ya conocidos (se ignorarán)")
    
    new_products = []
    chunk_size = 500  # Leer y guardar cada 500 para proteger memoria
    count = 0
    added = 0
    skipped = 0
    
    try:
        # Detectar delimitador (o fallback a coma)
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            # Fallback forzado a coma porque Sniffer a veces falla con headers largos
            dialect = 'excel' 
            delimiter = ','
            
            try:
                sample = f.read(4096)
                if sample:
                    sniffer = csv.Sniffer()
                    dialect_obj = sniffer.sniff(sample)
                    delimiter = dialect_obj.delimiter
            except:
                pass # Usar default
            
            f.seek(0)
            
            # Forzar delimiter ',' si el detectado es raro o si sabemos que es coma
            reader = csv.DictReader(f, delimiter=delimiter)
            
            print(f"📊 Dialecto: {delimiter} | Columnas sample: {reader.fieldnames[:5]}...")
            
            # Cargar keywords del schema para filtrado
            positive_keywords = load_schema_keywords()
            delivery_schema = load_delivery_schema() # V52
            print(f"🧠 Cargadas {len(positive_keywords)} keywords y {len(delivery_schema)} reglas de envío")
            
            # Mapping de columnas comunes Awin -> Giftia
            # Buscamos columnas probables si el nombre exacto no existe
            cols = reader.fieldnames
            col_name = next((c for c in cols if 'product_name' in c or 'name' in c), None)
            col_desc = next((c for c in cols if 'description' in c), None)
            col_price = next((c for c in cols if 'search_price' in c or 'price' in c), None)
            col_img = next((c for c in cols if 'merchant_image_url' in c or 'image_url' in c or 'large_image' in c), None)
            col_url = next((c for c in cols if 'merchant_deep_link' in c or 'deep_link' in c or 'aw_deep_link' in c), None)
            col_id = next((c for c in cols if 'aw_product_id' in c or 'product_id' in c), None)
            col_cat = next((c for c in cols if 'merchant_category' in c or 'category' in c), None)
            
            # V52: Detectar columna de envío
            col_delivery = next((c for c in cols if 'delivery_time' in c or 'shipping' in c or 'delivery' in c), None)

            if not (col_name and col_price and col_url):
                print(f"❌ Error: No se encontraron columnas críticas (Name, Price, URL).")
                return

            current_queue = []
            # Si existe cola previa, cargarla para hacer append
            if os.path.exists(PENDING_QUEUE_FILE):
                try:
                    with open(PENDING_QUEUE_FILE, 'r', encoding='utf-8') as pf:
                        current_queue = json.load(pf)
                except:
                    current_queue = []

            for row in reader:
                if limit and added >= limit:
                    break
                
                count += 1
                
                # Construir objeto Giftia preliminar para validar
                temp_product = {
                    "title": row.get(col_name, "")[:200],
                    "original_title": row.get(col_name, ""),
                    "price": parse_price(row.get(col_price, "0")),
                    "description": row.get(col_desc, "")[:5000],
                    "category": row.get(col_cat, "") if col_cat else ""
                }
                
                # --- FILTRO DE CALIDAD (HUNTER EDGE) ---
                if not is_valid_product(temp_product, positive_keywords):
                    skipped += 1
                    # Debug progresivo de los rechazados (cada 1000)
                    if skipped % 1000 == 0:
                        print(f"   🗑️ Rechazado (ejemplo): {temp_product['title'][:50]}...")
                    continue
                # ---------------------------------------

                # Si pasa el filtro, construimos el objeto completo
                # V51: HACK de compatibilidad para servidor. ASIN debe ser 10 caracteres Alfanum.
                # Transformamos "2001" en "AWIN002001"
                raw_id = str(row.get(col_id, count)).strip()
                safe_digits = "".join(filter(str.isdigit, raw_id))
                if not safe_digits: safe_digits = str(count)
                
                # Tomar últimos 6 dígitos y añadir prefijo AWIN (Total 10)
                safe_digits = safe_digits[-6:].zfill(6)
                giftia_id = f"AWIN{safe_digits}"
                
                # Deduplicación
                if giftia_id in existing_ids:
                    skipped += 1
                    continue
                
                # V52: Clasificación de Envíos
                delivery_text = row.get(col_delivery, "") if col_delivery else ""
                delivery_type = classify_delivery_v52(temp_product, delivery_text, delivery_schema)

                # V52: Flags Booleanas (Compatibilidad Legacy y Badges Frontend)
                delivery_lower = delivery_text.lower()
                is_prime_val = "prime" in delivery_lower
                free_shipping_val = "gratis" in delivery_lower or "gratuito" in delivery_lower or "0€" in delivery_lower or "0 €" in delivery_lower

                product = {
                    "source": "awin",
                    "asin": giftia_id, # Usamos campo asin para el ID único
                    "title": temp_product["title"],
                    "original_title": temp_product["original_title"],
                    "price": temp_product["price"],
                    "currency": "EUR", # Asumimos EUR por ahora
                    "delivery_type": delivery_type, # Nuevo campo V52
                    "is_prime": is_prime_val,       # Compatibilidad V50
                    "free_shipping": free_shipping_val, # Compatibilidad V50
                    "image_url": row.get(col_img, ""),
                    "affiliate_url": row.get(col_url, ""),
                    "description": temp_product["description"], 
                    "captured_at": datetime.now().isoformat(),
                    "status": "pending_ai"
                }
                
                # Filtros básicos de integridad
                if not product['image_url'] or product['price'] == 0:
                    continue

                current_queue.append(product)
                existing_ids.add(giftia_id)
                added += 1
                
                # Guardado incremental
                if len(current_queue) % 100 == 0:
                     print(f"💾 Guardando lote... (Cola: {len(current_queue)})")
                     with open(PENDING_QUEUE_FILE, 'w', encoding='utf-8') as out:
                        json.dump(current_queue, out, ensure_ascii=False, indent=2)

            # Guardado final
            with open(PENDING_QUEUE_FILE, 'w', encoding='utf-8') as out:
                json.dump(current_queue, out, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"❌ Error fatal procesando CSV: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n✅ Proceso completado.")
    print(f"   Analizados: {count}")
    print(f"   Añadidos: {added}")
    print(f"   Duplicados ignorados: {skipped}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Hunter Awin Feeds')
    parser.add_argument('file', help='Ruta al archivo CSV de Awin')
    parser.add_argument('--limit', type=int, help='Límite de productos a importar', default=None)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"❌ El archivo {args.file} no existe")
        sys.exit(1)
        
    process_awin_feed(args.file, args.limit)
