#!/usr/bin/env python3
"""
TEST REPROCESAR - Solo 3 productos para verificar
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
print("TEST REPROCESADOR - 3 productos")
print("="*70)

API_KEY = os.getenv('GEMINI_API_KEY')
WP_API_URL = os.getenv('WP_API_URL')
WP_TOKEN = os.getenv('WP_API_TOKEN')

with open('giftia_schema.json', 'r', encoding='utf-8') as f:
    SCHEMA = json.load(f)

VALID_CATEGORIES = list(SCHEMA.get('categories', {}).keys())
VALID_AGES = list(SCHEMA.get('ages', {}).keys()) if isinstance(SCHEMA.get('ages'), dict) else SCHEMA.get('ages', [])
VALID_OCCASIONS = list(SCHEMA.get('occasions', {}).keys()) if isinstance(SCHEMA.get('occasions'), dict) else SCHEMA.get('occasions', [])
VALID_RECIPIENTS = list(SCHEMA.get('recipients', {}).keys()) if isinstance(SCHEMA.get('recipients'), dict) else SCHEMA.get('recipients', [])

with open('productos_a_reprocesar.json', 'r', encoding='utf-8') as f:
    productos = json.load(f)[:3]  # Solo 3

print(f"Productos a probar: {len(productos)}")

def get_product_details(post_id):
    url = f"https://giftia.es/wp-json/wp/v2/gf_gift/{post_id}"
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

def classify_with_gemini(title, price="0"):
    prompt = f"""Clasifica este producto como regalo:

PRODUCTO: {title}
PRECIO: {price}EUR

CATEGORIAS: {', '.join(VALID_CATEGORIES)}
EDADES: {', '.join(VALID_AGES)}
OCASIONES: {', '.join(VALID_OCCASIONS)}
DESTINATARIOS: {', '.join(VALID_RECIPIENTS)}

Responde JSON:
{{"ok": true, "q": 7, "giftia_score": 4.0, "category": "Tech", "age": ["adultos"], "gender": "unisex", "recipients": ["amigo"], "occasions": ["cumpleanos", "navidad"], "marketing_hook": "core", "seo_title": "Titulo SEO", "meta_description": "Meta desc", "h1_title": "H1 emocional", "short_description": "80+ palabras", "expert_opinion": "100+ palabras", "pros": ["pro1"], "cons": ["contra1"], "full_description": "600+ palabras", "who_is_for": "80+ palabras", "faqs": [{{"q": "?", "a": "!"}}], "verdict": "50+ palabras", "slug": "url-slug"}}

SOLO JSON."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    response = requests.post(url, json={
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 8192}
    }, timeout=60)
    
    if response.status_code == 200:
        text = response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json.loads(json_match.group())
    return None

for i, p in enumerate(productos):
    post_id = p['id']
    title = p['title']
    
    print(f"\n[{i+1}] Post {post_id}: {title[:50]}...")
    
    # Obtener detalles
    details = get_product_details(post_id)
    if not details:
        print("  ERROR: No se pudo obtener detalles")
        continue
    
    meta = details.get('meta', {})
    price = meta.get('_gf_current_price', 0)
    
    # Extraer ASIN del meta o de la URL
    asin = meta.get('_gf_asin', '')
    affiliate_url = meta.get('_gf_affiliate_url', '')
    
    if not asin and affiliate_url:
        # Extraer ASIN de URL: https://www.amazon.es/dp/B0FGJ6F5QM?tag=...
        import re as re_module
        asin_match = re_module.search(r'/dp/([A-Z0-9]{10})', affiliate_url)
        if asin_match:
            asin = asin_match.group(1)
    
    if not asin or len(asin) != 10:
        asin = f"RP{post_id:08d}"
    
    print(f"  ASIN: {asin}, Price: {price}")
    print(f"  Antes: gf_age={details.get('gf_age', [])}, gf_occasion={details.get('gf_occasion', [])}")
    
    # Clasificar
    print("  Clasificando con Gemini...")
    c = classify_with_gemini(title, str(price))
    if not c:
        print("  ERROR: Gemini fallo")
        continue
    
    print(f"  Gemini: category={c.get('category')}, age={c.get('age')}, occasions={c.get('occasions')[:2]}")
    
    # Construir payload
    product = {
        "asin": asin,
        "url": affiliate_url or f"https://amazon.es/dp/{asin}?tag=GIFTIA-21",
        "image": meta.get('_gf_image_url', ''),
        "source": "reprocess",
        "title": c.get('h1_title', title),
        "original_title": title,
        "price": str(price),
        "rating": str(meta.get('_gf_rating', 0)),
        "review_count": str(meta.get('_gf_reviews', 0)),
        "category": c.get('category', 'Tech'),
        "gemini_category": c.get('category', 'Tech'),
        "target_gender": c.get('gender', 'unisex'),
        "gift_quality": c.get('q', 5),
        "giftia_score": c.get('giftia_score', 4.0),
        "seo_title": c.get('seo_title', ''),
        "meta_description": c.get('meta_description', ''),
        "short_description": c.get('short_description', ''),
        "expert_opinion": c.get('expert_opinion', ''),
        "pros": c.get('pros', []),
        "cons": c.get('cons', []),
        "full_description": c.get('full_description', ''),
        "who_is_for": c.get('who_is_for', ''),
        "faqs": c.get('faqs', []),
        "verdict": c.get('verdict', ''),
        "seo_slug": c.get('slug', ''),
        "ages": c.get('age', ['adultos']),
        "recipients": c.get('recipients', ['amigo']),
        "occasions": c.get('occasions', ['cumpleanos']),
        "marketing_hook": c.get('marketing_hook', 'wildcard'),
        "processed_at": datetime.now().isoformat()
    }
    
    # Enviar
    print("  Enviando a WordPress...")
    headers = {'Content-Type': 'application/json', 'X-GIFTIA-TOKEN': WP_TOKEN}
    response = requests.post(WP_API_URL, data=json.dumps(product, ensure_ascii=False).encode('utf-8'), headers=headers, timeout=30)
    
    print(f"  Response: {response.status_code}")
    
    # Verificar
    time.sleep(1)
    verify = get_product_details(post_id)
    if verify:
        print(f"  Despues: gf_age={verify.get('gf_age', [])}, gf_occasion={verify.get('gf_occasion', [])}")
        if verify.get('gf_age') and verify.get('gf_occasion'):
            print("  EXITO!")
        else:
            print("  PARCIAL - verificar")
    
    time.sleep(2)

print("\n" + "="*70)
print("TEST COMPLETADO")
