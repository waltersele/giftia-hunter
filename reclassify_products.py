#!/usr/bin/env python3
"""
Reclasificador de productos Giftia
==================================
Reclasifica productos existentes en WordPress usando las nuevas reglas de Gemini.

Uso:
    python reclassify_products.py                    # Modo dry-run (solo muestra cambios)
    python reclassify_products.py --apply            # Aplica cambios a WordPress
    python reclassify_products.py --category Fandom  # Solo productos de una categoría
    python reclassify_products.py --limit 50         # Limitar a N productos
"""

import os
import sys
import json
import time
import argparse
import requests
import google.generativeai as genai
from datetime import datetime

# Configuración
WP_API_URL = "https://giftia.es/wp-json/wp/v2/gf_gift"
WP_INGEST_URL = "https://giftia.es/wp-content/plugins/giftfinder-core/api-ingest.php"
WP_TOKEN = os.getenv("WP_TOKEN", "nu27OrX2t5VZQmrGXfoZk3pbcS97yiP5")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Cargar keys de .env si existe
ENV_PATH = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip('"').strip("'")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)

# Categorías válidas
VALID_CATEGORIES = [
    "Tech", "Gamer", "Gourmet", "Deporte", "Outdoor", "Viajes", "Moda", "Belleza",
    "Decoración", "Zen", "Lector", "Música", "Artista", "Fotografía", "Friki", 
    "Mascotas", "Lujo", "Infantil"
]

# Correcciones automáticas
CATEGORY_CORRECTIONS = {
    "fandom": "Friki", "coleccionismo": "Friki", "merchandising": "Friki", "geek": "Friki",
    "hogar": "Decoración", "casa": "Decoración", "interiores": "Decoración",
    "bienestar": "Zen", "relax": "Zen", "relajación": "Zen", "wellness": "Zen",
    "fitness": "Deporte", "gimnasio": "Deporte", "gym": "Deporte", "sport": "Deporte",
    "bebés": "Infantil", "bebes": "Infantil", "niños": "Infantil", "ninos": "Infantil",
    "kids": "Infantil", "puericultura": "Infantil", "juguetes": "Infantil",
    "cocina": "Gourmet", "gastronomía": "Gourmet", "food": "Gourmet", "bebidas": "Gourmet",
    "electrónica": "Tech", "tecnología": "Tech", "gadgets": "Tech",
    "videojuegos": "Gamer", "gaming": "Gamer",
    "aire libre": "Outdoor", "aventura": "Outdoor", "acampada": "Outdoor",
    "libros": "Lector", "lectura": "Lector",
    "manualidades": "Artista", "craft": "Artista", "arte": "Artista",
    "animales": "Mascotas", "perros": "Mascotas", "gatos": "Mascotas",
    "premium": "Lujo", "luxury": "Lujo",
}

def validate_category(category):
    """Valida y corrige categoría."""
    if not category:
        return None
    cat_lower = category.lower().strip()
    if cat_lower in CATEGORY_CORRECTIONS:
        return CATEGORY_CORRECTIONS[cat_lower]
    for valid in VALID_CATEGORIES:
        if valid.lower() == cat_lower:
            return valid
    return None

def get_all_products():
    """Obtiene todos los productos de WordPress."""
    print("📦 Obteniendo productos de WordPress...")
    headers = {'User-Agent': 'Giftia-Reclassifier/1.0'}
    all_products = []
    page = 1
    
    while True:
        resp = requests.get(f'{WP_API_URL}?per_page=100&page={page}', headers=headers, timeout=30)
        if resp.status_code != 200:
            break
        products = resp.json()
        if not products:
            break
        all_products.extend(products)
        print(f"   Página {page}: {len(products)} productos")
        page += 1
        if page > 20:  # Max 2000 productos
            break
    
    print(f"✅ Total: {len(all_products)} productos")
    return all_products

def get_categories_map():
    """Obtiene mapeo ID → nombre de categorías."""
    resp = requests.get('https://giftia.es/wp-json/wp/v2/gf_category?per_page=100', timeout=30)
    if resp.status_code != 200:
        return {}
    return {c['id']: c['name'] for c in resp.json()}

def classify_with_gemini(products_batch):
    """Clasifica batch de productos con Gemini."""
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY no configurada")
        return {}
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    products_text = ""
    for i, p in enumerate(products_batch):
        products_text += f"\n{i+1}. {p['title']}"
    
    prompt = f"""Clasifica estos productos en UNA de estas 18 categorías EXACTAS:

Tech, Gamer, Gourmet, Deporte, Outdoor, Viajes, Moda, Belleza, Decoración, Zen, Lector, Música, Artista, Fotografía, Friki, Mascotas, Lujo, Infantil

PRODUCTOS:{products_text}

REGLAS CRÍTICAS:
- Biberones, mantas bebé, juguetes Montessori, termómetros bebé → Infantil
- Barbacoas, utensilios cocina, sets té/café → Gourmet  
- Electroestimuladores, foam roller, paleteros pádel → Deporte
- Funko Pop, varitas Harry Potter, merchandising → Friki
- Tiendas campaña, bastones senderismo → Outdoor
- Robot aspirador, smart tracker → Tech
- "Fandom" NO existe, usar "Friki"

Responde SOLO con JSON array:
[{{"id": 1, "category": "Categoría"}}, ...]"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Extraer JSON
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]
        
        results = json.loads(text)
        return {r['id']: validate_category(r['category']) for r in results}
    except Exception as e:
        print(f"❌ Error Gemini: {e}")
        return {}

def update_product_category(post_id, new_category, dry_run=True):
    """Actualiza categoría de producto en WordPress."""
    if dry_run:
        return True
    
    headers = {
        'Content-Type': 'application/json',
        'X-GIFTIA-TOKEN': WP_TOKEN
    }
    
    payload = {
        'post_id': post_id,
        'category': new_category
    }
    
    try:
        # Usar action como query param
        url = f"{WP_INGEST_URL}?action=update_category"
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('success', False)
        else:
            print(f"   ❌ Error HTTP {resp.status_code}: {resp.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ Error actualizando {post_id}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Reclasificar productos Giftia')
    parser.add_argument('--apply', action='store_true', help='Aplicar cambios (sin esto es dry-run)')
    parser.add_argument('--category', type=str, help='Solo productos de esta categoría')
    parser.add_argument('--limit', type=int, default=0, help='Limitar a N productos')
    parser.add_argument('--batch-size', type=int, default=10, help='Tamaño de batch para Gemini')
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔄 RECLASIFICADOR DE PRODUCTOS GIFTIA")
    print("=" * 70)
    print(f"   Modo: {'APLICAR CAMBIOS' if args.apply else 'DRY-RUN (solo mostrar)'}")
    if args.category:
        print(f"   Filtro categoría: {args.category}")
    if args.limit:
        print(f"   Límite: {args.limit} productos")
    print("=" * 70)
    
    # Obtener productos y categorías
    products = get_all_products()
    cats_map = get_categories_map()
    
    # Filtrar por categoría si se especifica
    if args.category:
        cat_filter = args.category.lower()
        filtered = []
        for p in products:
            cat_ids = p.get('gf_category', [])
            cat_names = [cats_map.get(cid, '').lower() for cid in cat_ids]
            if any(cat_filter in name for name in cat_names):
                filtered.append(p)
        products = filtered
        print(f"📋 Filtrados: {len(products)} productos en '{args.category}'")
    
    if args.limit:
        products = products[:args.limit]
    
    # Preparar productos para clasificar
    to_classify = []
    for p in products:
        title = p.get('title', {}).get('rendered', 'Sin título')
        # Limpiar HTML
        title = title.replace('&#8211;', '-').replace('&#8217;', "'").replace('&amp;', '&')
        title = title.replace('&#8243;', '"').replace('&#215;', 'x')
        
        cat_ids = p.get('gf_category', [])
        current_cat = cats_map.get(cat_ids[0], 'Sin categoría') if cat_ids else 'Sin categoría'
        
        to_classify.append({
            'id': p['id'],
            'title': title[:100],
            'current_category': current_cat
        })
    
    print(f"\n🎯 Procesando {len(to_classify)} productos en batches de {args.batch_size}...")
    
    # Procesar en batches
    changes = []
    for i in range(0, len(to_classify), args.batch_size):
        batch = to_classify[i:i+args.batch_size]
        print(f"\n📦 Batch {i//args.batch_size + 1}/{(len(to_classify)-1)//args.batch_size + 1}...")
        
        # Clasificar con Gemini
        results = classify_with_gemini(batch)
        
        for j, product in enumerate(batch):
            idx = j + 1  # Gemini usa 1-indexed
            new_cat = results.get(idx)
            
            if new_cat and new_cat != product['current_category']:
                changes.append({
                    'id': product['id'],
                    'title': product['title'],
                    'old': product['current_category'],
                    'new': new_cat
                })
                print(f"   🔄 {product['title'][:50]}...")
                print(f"      {product['current_category']} → {new_cat}")
        
        time.sleep(1)  # Rate limiting
    
    # Resumen
    print("\n" + "=" * 70)
    print(f"📊 RESUMEN: {len(changes)} cambios detectados")
    print("=" * 70)
    
    if not changes:
        print("✅ Todos los productos están correctamente clasificados")
        return
    
    # Agrupar por tipo de cambio
    change_types = {}
    for c in changes:
        key = f"{c['old']} → {c['new']}"
        if key not in change_types:
            change_types[key] = []
        change_types[key].append(c['title'])
    
    for change_type, titles in sorted(change_types.items(), key=lambda x: -len(x[1])):
        print(f"\n{change_type} ({len(titles)} productos):")
        for title in titles[:5]:
            print(f"   • {title[:60]}")
        if len(titles) > 5:
            print(f"   ... y {len(titles) - 5} más")
    
    # Aplicar cambios si no es dry-run
    if args.apply:
        print("\n🚀 Aplicando cambios a WordPress...")
        success = 0
        for c in changes:
            if update_product_category(c['id'], c['new'], dry_run=False):
                success += 1
            time.sleep(0.5)  # Rate limiting
        print(f"✅ {success}/{len(changes)} productos actualizados")
    else:
        print(f"\n💡 Ejecuta con --apply para aplicar los {len(changes)} cambios")
    
    # Guardar log
    log_file = f"reclassify_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'dry_run': not args.apply,
            'total_products': len(to_classify),
            'changes': changes
        }, f, ensure_ascii=False, indent=2)
    print(f"📝 Log guardado: {log_file}")

if __name__ == "__main__":
    main()
