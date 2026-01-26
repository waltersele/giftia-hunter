#!/usr/bin/env python3
"""
REPROCESAR PRODUCTOS EXISTENTES
Toma productos sin taxonomías completas, los pasa por Gemini y actualiza WordPress
"""
import json
import os
import re
import requests
import time
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

print("="*70)
print("REPROCESADOR DE PRODUCTOS - Giftia v51")
print("="*70)

# Configuracion
API_KEY = os.getenv('GEMINI_API_KEY')
WP_API_URL = os.getenv('WP_API_URL')
WP_TOKEN = os.getenv('WP_API_TOKEN')
AMAZON_TAG = os.getenv('AMAZON_TAG', 'GIFTIA-21')

# Cargar schema
with open('giftia_schema.json', 'r', encoding='utf-8') as f:
    SCHEMA = json.load(f)

VALID_CATEGORIES = list(SCHEMA.get('categories', {}).keys())
VALID_AGES = list(SCHEMA.get('ages', {}).keys()) if isinstance(SCHEMA.get('ages'), dict) else SCHEMA.get('ages', [])
VALID_OCCASIONS = list(SCHEMA.get('occasions', {}).keys()) if isinstance(SCHEMA.get('occasions'), dict) else SCHEMA.get('occasions', [])
VALID_RECIPIENTS = list(SCHEMA.get('recipients', {}).keys()) if isinstance(SCHEMA.get('recipients'), dict) else SCHEMA.get('recipients', [])

# Cargar lista de productos a reprocesar
with open('productos_a_reprocesar.json', 'r', encoding='utf-8') as f:
    productos = json.load(f)

print(f"\nProductos a reprocesar: {len(productos)}")
print(f"Categorias validas: {VALID_CATEGORIES}")
print(f"Edades validas: {VALID_AGES}")

# Estadisticas
stats = {'procesados': 0, 'exitosos': 0, 'errores': 0}

def get_product_details(post_id):
    """Obtener detalles completos del producto desde WP"""
    url = f"https://giftia.es/wp-json/wp/v2/gf_gift/{post_id}"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    return None

def classify_with_gemini(title, price="0"):
    """Clasificar producto con Gemini"""
    prompt = f"""Clasifica este producto como regalo:

PRODUCTO: {title}
PRECIO: {price}EUR

CATEGORIAS: {', '.join(VALID_CATEGORIES)}
EDADES: {', '.join(VALID_AGES)}
OCASIONES: {', '.join(VALID_OCCASIONS)}
DESTINATARIOS: {', '.join(VALID_RECIPIENTS)}

Responde JSON:
{{"ok": true, "q": 7, "giftia_score": 4.0, "category": "Tech", "age": ["adultos"], "gender": "unisex", "recipients": ["amigo"], "occasions": ["cumpleanos", "navidad"], "marketing_hook": "core", "seo_title": "Titulo SEO 50-60 chars", "meta_description": "Meta 150-160 chars", "h1_title": "H1 emocional 40-70 chars", "short_description": "80+ palabras descripcion corta emocional", "expert_opinion": "100+ palabras opinion experto", "pros": ["pro1", "pro2", "pro3"], "cons": ["contra1", "contra2"], "full_description": "600+ palabras con H2 estructura SEO", "who_is_for": "80+ palabras perfiles ideales", "faqs": [{{"q": "pregunta", "a": "respuesta"}}], "verdict": "50+ palabras veredicto", "slug": "url-slug"}}

SOLO JSON."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    
    for attempt in range(3):  # 3 reintentos
        try:
            response = requests.post(url, json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.4, "maxOutputTokens": 8192}
            }, timeout=90)
            
            if response.status_code == 200:
                text = response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                json_match = re.search(r'\{[\s\S]*\}', text)
                if json_match:
                    return json.loads(json_match.group())
            elif response.status_code == 429:  # Rate limit
                print(f"    Rate limit, esperando 30s...")
                time.sleep(30)
                continue
        except requests.exceptions.Timeout:
            print(f"    Timeout, reintentando ({attempt+1}/3)...")
            time.sleep(5)
        except Exception as e:
            print(f"    Error Gemini: {e}")
            time.sleep(5)
    
    return None

def send_to_wordpress(product):
    """Enviar producto actualizado a WordPress"""
    headers = {
        'Content-Type': 'application/json',
        'X-GIFTIA-TOKEN': WP_TOKEN,
        'User-Agent': 'GiftiaReprocessor/1.0'
    }
    try:
        response = requests.post(
            WP_API_URL,
            data=json.dumps(product, ensure_ascii=False).encode('utf-8'),
            headers=headers,
            timeout=30
        )
        return response.status_code in [200, 500]  # 500 pero con success
    except:
        return False

def process_product(post_id, title):
    """Procesar un producto individual"""
    # 1. Obtener detalles actuales
    details = get_product_details(post_id)
    if not details:
        return False
    
    meta = details.get('meta', {})
    
    # Obtener precio actual
    price = meta.get('_gf_current_price', 0)
    
    # Extraer ASIN del meta o de la URL
    asin = meta.get('_gf_asin', '')
    affiliate_url = meta.get('_gf_affiliate_url', '')
    
    if not asin and affiliate_url:
        # Extraer ASIN de URL: https://www.amazon.es/dp/B0FGJ6F5QM?tag=...
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', affiliate_url)
        if asin_match:
            asin = asin_match.group(1)
    
    if not asin or len(asin) != 10:
        asin = f"RP{post_id:08d}"
    
    # 2. Clasificar con Gemini
    classification = classify_with_gemini(title, str(price))
    if not classification:
        return False
    
    # 3. Asegurar que el affiliate URL tiene el tag correcto
    if affiliate_url and 'tag=' not in affiliate_url:
        affiliate_url = f"{affiliate_url}{'&' if '?' in affiliate_url else '?'}tag={AMAZON_TAG}"
    elif affiliate_url and AMAZON_TAG not in affiliate_url:
        # Reemplazar tag existente con el correcto
        affiliate_url = re.sub(r'tag=[^&]+', f'tag={AMAZON_TAG}', affiliate_url)
    
    # Si no hay affiliate_url, construirlo desde ASIN
    if not affiliate_url and asin and len(asin) == 10:
        affiliate_url = f"https://www.amazon.es/dp/{asin}?tag={AMAZON_TAG}"
    
    # 3. Construir payload
    product = {
        "asin": asin,
        "affiliate_url": affiliate_url,  # Campo correcto para api-ingest.php
        "image_url": meta.get('_gf_image_url', ''),  # Campo correcto
        "source": "reprocess",
        
        "title": classification.get('h1_title', title),
        "original_title": title,
        "h1_title": classification.get('h1_title', ''),
        "optimized_title": classification.get('h1_title', ''),
        "marketing_title": classification.get('h1_title', ''),
        
        "price": str(price),
        "rating": str(meta.get('_gf_rating', 0)),
        "review_count": str(meta.get('_gf_reviews', 0)),
        
        "category": classification.get('category', 'Tech'),
        "gemini_category": classification.get('category', 'Tech'),
        "target_gender": classification.get('gender', 'unisex'),
        "gift_quality": classification.get('q', 5),
        "giftia_score": classification.get('giftia_score', 4.0),
        
        "seo_title": classification.get('seo_title', ''),
        "meta_description": classification.get('meta_description', ''),
        "short_description": classification.get('short_description', ''),
        "expert_opinion": classification.get('expert_opinion', ''),
        "pros": classification.get('pros', []),
        "cons": classification.get('cons', []),
        "full_description": classification.get('full_description', ''),
        "who_is_for": classification.get('who_is_for', ''),
        "faqs": classification.get('faqs', []),
        "verdict": classification.get('verdict', ''),
        "seo_slug": classification.get('slug', ''),
        
        "ages": classification.get('age', ['adultos']),
        "recipients": classification.get('recipients', ['amigo']),
        "occasions": classification.get('occasions', ['cumpleanos']),
        "marketing_hook": classification.get('marketing_hook', 'wildcard'),
        
        "processed_at": datetime.now().isoformat()
    }
    
    # 4. Enviar a WordPress
    return send_to_wordpress(product)

# Procesar en lotes
BATCH_SIZE = 10
DELAY_BETWEEN_PRODUCTS = 2  # segundos
DELAY_BETWEEN_BATCHES = 10  # segundos

print(f"\nIniciando reprocesamiento...")
print(f"Batch size: {BATCH_SIZE}, Delay: {DELAY_BETWEEN_PRODUCTS}s")
print("-"*70)

for i, p in enumerate(productos):
    post_id = p['id']
    title = p['title']
    
    print(f"[{i+1}/{len(productos)}] Procesando {post_id}: {title[:40]}...")
    
    try:
        success = process_product(post_id, title)
        stats['procesados'] += 1
        
        if success:
            stats['exitosos'] += 1
            print(f"    OK")
        else:
            stats['errores'] += 1
            print(f"    ERROR")
    except Exception as e:
        stats['errores'] += 1
        print(f"    EXCEPCION: {e}")
    
    # Delay para no saturar APIs
    time.sleep(DELAY_BETWEEN_PRODUCTS)
    
    # Pausa entre lotes
    if (i + 1) % BATCH_SIZE == 0:
        print(f"\n--- Lote {(i+1)//BATCH_SIZE} completado. Pausa {DELAY_BETWEEN_BATCHES}s ---")
        print(f"Stats: {stats['exitosos']}/{stats['procesados']} exitosos")
        time.sleep(DELAY_BETWEEN_BATCHES)

print("\n" + "="*70)
print("REPROCESAMIENTO COMPLETADO")
print(f"Procesados: {stats['procesados']}")
print(f"Exitosos: {stats['exitosos']}")
print(f"Errores: {stats['errores']}")
print("="*70)
