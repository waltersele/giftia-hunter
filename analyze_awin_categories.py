"""
Analizador de categorías de feeds Awin
Descarga un feed de muestra y lista todas las categorías para crear blacklist
"""

import os
import json
import gzip
import csv
import requests
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

AWIN_FEEDLIST_URL = os.getenv("AWIN_FEEDLIST_URL")
MERCHANT_NAMES = {
    13075: "El Corte Inglés",
    27904: "Sprinter", 
    24562: "Padel Market"
}

def fetch_feed_list():
    """Descarga lista de feeds"""
    print("📥 Fetching feed list...")
    response = requests.get(AWIN_FEEDLIST_URL, timeout=30)
    response.raise_for_status()
    
    lines = response.text.strip().split('\n')
    reader = csv.DictReader(lines)
    return list(reader)

def get_sample_feed(merchant_id):
    """Obtiene el primer feed de un merchant"""
    feed_list = fetch_feed_list()
    
    for feed in feed_list:
        if int(feed.get("Advertiser ID", 0)) == merchant_id:
            return feed
    return None

def analyze_categories(feed):
    """Descarga y analiza categorías de un feed"""
    feed_url = feed.get("URL")
    merchant_id = int(feed.get("Advertiser ID"))
    merchant_name = MERCHANT_NAMES.get(merchant_id, "Unknown")
    
    print(f"\n🔍 Analyzing {merchant_name} (ID {merchant_id})")
    print(f"   Feed: {feed.get('Feed ID')} - {feed.get('No of products')} products")
    print(f"   Downloading...")
    
    # Descargar feed
    response = requests.get(feed_url, timeout=120, stream=True)
    response.raise_for_status()
    
    # Parsear categorías
    categories = Counter()
    category_examples = {}
    total_products = 0
    
    with gzip.GzipFile(fileobj=response.raw) as gz:
        csv_content = gz.read().decode('utf-8', errors='ignore')
        csv_reader = csv.DictReader(csv_content.splitlines())
        
        for row in csv_reader:
            total_products += 1
            
            # Buscar campos de categoría (pueden variar)
            cat = (row.get("category_name") or 
                   row.get("merchant_category") or 
                   row.get("Category") or 
                   row.get("product_type") or
                   "Sin categoría")
            
            categories[cat] += 1
            
            # Guardar ejemplo de producto por categoría
            if cat not in category_examples:
                category_examples[cat] = {
                    "title": row.get("product_name", ""),
                    "price": row.get("search_price", ""),
                    "brand": row.get("brand_name", "")
                }
    
    print(f"\n📊 Analysis complete: {total_products} products, {len(categories)} categories\n")
    
    # Mostrar top 50 categorías
    print(f"{'CATEGORY':<60} {'COUNT':>8} {'%':>6}")
    print("=" * 80)
    
    for cat, count in categories.most_common(50):
        pct = (count / total_products) * 100
        print(f"{cat:<60} {count:>8} {pct:>5.1f}%")
        
        # Mostrar ejemplo
        if cat in category_examples:
            ex = category_examples[cat]
            print(f"  └─ Example: {ex['title'][:70]}")
            print(f"     {ex['brand']} - {ex['price']}\n")
    
    # Guardar análisis completo
    output_file = f"awin_categories_{merchant_id}.json"
    analysis = {
        "merchant_id": merchant_id,
        "merchant_name": merchant_name,
        "total_products": total_products,
        "total_categories": len(categories),
        "categories": dict(categories.most_common()),
        "examples": category_examples
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Full analysis saved to {output_file}")
    return analysis

def create_gift_blacklist(analysis):
    """Crea blacklist automática de categorías que NO son regalos"""
    
    # Patrones que claramente NO son regalos
    FORBIDDEN_PATTERNS = [
        # Alimentación/perecederos
        "alimentación", "aliment", "comida", "bebida", "fresco", "congelado",
        "lácteo", "carne", "pescado", "fruta", "verdura", "panadería",
        
        # Electrodomésticos grandes
        "electrodoméstico", "lavadora", "nevera", "frigorífico", "horno",
        "lavavajillas", "secadora", "aire acondicionado", "caldera",
        
        # Muebles grandes
        "mueble", "sofá", "armario", "cama", "colchón", "mesa grande",
        "silla comedor", "estantería grande",
        
        # Ropa con tallas (problemático para regalos)
        "pantalon", "vaquero", "jean", "camisa talla", "vestido talla",
        "traje", "chaqueta talla", "abrigo talla",
        
        # Zapatillas específicas (tallas)
        "zapatilla running", "zapatilla talla", "bota talla",
        
        # Productos de limpieza/hogar no-regalo
        "detergente", "limpieza", "lejía", "suavizante", "fregona",
        "escoba", "cubo", "bayeta",
        
        # Productos de higiene básica
        "papel higiénico", "pañal", "compresas", "tampón",
        
        # Construcción/bricolaje pesado
        "herramienta eléctrica", "taladro", "sierra", "hormigón",
        
        # Productos a granel/industrial
        "pack 24", "caja 100", "granel", "industrial",
        
        # Servicios/seguros
        "seguro", "suscripción", "servicio técnico", "garantía extendida"
    ]
    
    blacklisted = []
    whitelisted = []
    
    for category, count in analysis["categories"].items():
        cat_lower = category.lower()
        
        # Comprobar si coincide con algún patrón prohibido
        is_forbidden = any(pattern in cat_lower for pattern in FORBIDDEN_PATTERNS)
        
        if is_forbidden:
            blacklisted.append({
                "category": category,
                "count": count,
                "reason": "Pattern match"
            })
        else:
            # Potencialmente regalo
            whitelisted.append({
                "category": category,
                "count": count
            })
    
    print(f"\n🚫 BLACKLISTED: {len(blacklisted)} categories")
    for item in blacklisted[:20]:  # Top 20
        print(f"  ✗ {item['category']} ({item['count']} products)")
    
    print(f"\n✅ POTENTIALLY GIFT-WORTHY: {len(whitelisted)} categories")
    for item in whitelisted[:20]:  # Top 20
        print(f"  ✓ {item['category']} ({item['count']} products)")
    
    return {
        "blacklisted": blacklisted,
        "whitelisted": whitelisted
    }

def main():
    print("=" * 80)
    print("AWIN CATEGORY ANALYZER")
    print("=" * 80)
    
    # Analizar cada merchant
    for merchant_id in [13075, 27904, 24562]:
        try:
            feed = get_sample_feed(merchant_id)
            if not feed:
                print(f"✗ No feed found for {MERCHANT_NAMES[merchant_id]}")
                continue
            
            analysis = analyze_categories(feed)
            
            # Crear blacklist
            blacklist_data = create_gift_blacklist(analysis)
            
            # Guardar blacklist
            blacklist_file = f"awin_blacklist_{merchant_id}.json"
            with open(blacklist_file, "w", encoding="utf-8") as f:
                json.dump(blacklist_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✓ Blacklist saved to {blacklist_file}\n")
            print("=" * 80)
            
        except Exception as e:
            print(f"✗ Error analyzing {MERCHANT_NAMES[merchant_id]}: {e}")
            continue

if __name__ == "__main__":
    main()
