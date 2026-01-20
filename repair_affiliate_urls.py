#!/usr/bin/env python3
"""
REPARAR AFFILIATE URLs
Busca productos en Amazon por título para recuperar el ASIN
"""
import json
import os
import re
import requests
import time
from dotenv import load_dotenv

load_dotenv()

WP_TOKEN = os.getenv('WP_API_TOKEN')
WP_API_URL = os.getenv('WP_API_URL')
AMAZON_TAG = os.getenv('AMAZON_TAG', 'GIFTIA-21')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

print("=" * 70)
print("REPARADOR DE AFFILIATE URLs")
print("=" * 70)
print(f"Amazon Tag: {AMAZON_TAG}")

# Cargar productos a reparar
with open('productos_a_reprocesar.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

def search_asin_via_gemini(title):
    """Usar Gemini para extraer posible ASIN de un título de Amazon"""
    # Simplificamos: solo buscamos si el título tiene un patrón de ASIN
    # En realidad, usaremos los datos guardados en WordPress de otra forma
    return None

def update_product_affiliate_url(post_id, asin, title):
    """Actualizar producto con affiliate URL correcto"""
    if not asin or len(asin) != 10:
        return False
    
    affiliate_url = f"https://www.amazon.es/dp/{asin}?tag={AMAZON_TAG}"
    
    # Obtener datos actuales
    response = requests.get(f"https://giftia.es/wp-json/wp/v2/gf_gift/{post_id}", timeout=30)
    if response.status_code != 200:
        return False
    
    details = response.json()
    meta = details.get('meta', {})
    
    # Construir payload mínimo para actualizar
    payload = {
        "asin": asin,
        "affiliate_url": affiliate_url,
        "image_url": meta.get('_gf_image_url', ''),
        "title": title,
        "price": str(meta.get('_gf_current_price', 0)),
        "source": "affiliate-fix",
        "category": "Tech",  # Mínimo requerido
        "ages": ["adultos"],
        "occasions": ["cumpleanos"],
        "recipients": ["amigo"],
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-GIFTIA-TOKEN': WP_TOKEN
    }
    
    response = requests.post(
        WP_API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers=headers,
        timeout=30
    )
    
    return response.status_code in [200, 201]

# Intentar buscar ASINs en diferentes fuentes
print("\nAnalizando productos para recuperar ASINs...")

# 1. Primero, veamos si hay productos que SÍ tienen ASIN en WP
# (puede que la API REST no lo exponga pero exista)

# 2. Buscar en la imagen URL - a veces contiene el ASIN
products_with_recovered_asin = []

for i, product in enumerate(products[:20]):  # Probar con 20 primero
    post_id = product['id']
    title = product['title']
    
    print(f"\n[{i+1}/20] Post {post_id}: {title[:50]}...")
    
    # Obtener detalles
    response = requests.get(f"https://giftia.es/wp-json/wp/v2/gf_gift/{post_id}", timeout=30)
    if response.status_code != 200:
        print(f"    Error obteniendo producto")
        continue
    
    details = response.json()
    meta = details.get('meta', {})
    
    image_url = meta.get('_gf_image_url', '')
    
    # Buscar ASIN en image URL (ej: https://m.media-amazon.com/images/I/B0XXX.jpg)
    # O en formato: /images/I/41xxx._xxx.jpg con ASIN en otra parte
    
    asin = None
    
    # Patrón 1: ASIN en la URL de imagen (raro pero posible)
    asin_match = re.search(r'/([A-Z0-9]{10})[\._]', image_url)
    if asin_match:
        possible_asin = asin_match.group(1)
        if possible_asin.startswith('B0'):  # Los ASINs de Amazon suelen empezar con B0
            asin = possible_asin
            print(f"    ASIN encontrado en imagen: {asin}")
    
    if asin:
        products_with_recovered_asin.append({
            'id': post_id,
            'title': title,
            'asin': asin
        })
        print(f"    ✅ ASIN recuperado: {asin}")
    else:
        print(f"    ❌ Sin ASIN recuperable")
        print(f"       Image URL: {image_url[:80]}...")

print("\n" + "=" * 70)
print(f"Productos con ASIN recuperado: {len(products_with_recovered_asin)}")
print(f"Productos sin ASIN: {20 - len(products_with_recovered_asin)}")
print("=" * 70)

if products_with_recovered_asin:
    print("\nProductos recuperables:")
    for p in products_with_recovered_asin:
        print(f"  {p['id']}: {p['asin']} - {p['title'][:50]}")
