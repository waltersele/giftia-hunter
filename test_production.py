#!/usr/bin/env python3
"""
TEST PRODUCCION - Producto real con ASIN de Amazon
"""
import json
import os
import re
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

print("="*70)
print("TEST PRODUCCION: Producto Real Amazon")
print("="*70)

API_KEY = os.getenv('GEMINI_API_KEY')
WP_API_URL = os.getenv('WP_API_URL')
WP_TOKEN = os.getenv('WP_API_TOKEN')

# Cargar schema
with open('giftia_schema.json', 'r', encoding='utf-8') as f:
    SCHEMA = json.load(f)

VALID_CATEGORIES = list(SCHEMA.get('categories', {}).keys())
VALID_AGES = list(SCHEMA.get('ages', {}).keys()) if isinstance(SCHEMA.get('ages'), dict) else SCHEMA.get('ages', [])
VALID_OCCASIONS = list(SCHEMA.get('occasions', {}).keys()) if isinstance(SCHEMA.get('occasions'), dict) else SCHEMA.get('occasions', [])
VALID_RECIPIENTS = list(SCHEMA.get('recipients', {}).keys()) if isinstance(SCHEMA.get('recipients'), dict) else SCHEMA.get('recipients', [])

# Producto REAL de Amazon
raw_product = {
    "asin": "B09V3KXJPB",  # ASIN real de Amazon
    "title": "Echo Dot (5a generacion, modelo de 2022) | Altavoz inteligente wifi y Bluetooth con Alexa",
    "price": "54.99",
    "rating": "4.6",
    "reviews_count": "89234",
    "url": "https://amazon.es/dp/B09V3KXJPB?tag=GIFTIA-21",
    "image": "https://m.media-amazon.com/images/I/71xoR4A6q-L._AC_SL1000_.jpg"
}

print(f"\n1. Producto: {raw_product['title'][:50]}...")
print(f"   ASIN: {raw_product['asin']} | Precio: {raw_product['price']}EUR")

# Clasificar con Gemini
print(f"\n2. Clasificando con Gemini...")
products_text = f"\n1. {raw_product['title'][:150]}\n   Precio: {raw_product['price']}EUR | Rating: {raw_product['rating']} | Reviews: {raw_product['reviews_count']}"

prompt = f"""Eres el CURADOR JEFE y EXPERTO SEO de Giftia.es.

PRODUCTO:{products_text}

CATEGORIAS: {', '.join(VALID_CATEGORIES)}
EDADES: {', '.join(VALID_AGES)}
OCASIONES: {', '.join(VALID_OCCASIONS)}
DESTINATARIOS: {', '.join(VALID_RECIPIENTS)}

Responde JSON:
[{{"ok": true, "q": 8, "giftia_score": 4.5, "category": "Tech", "age": ["adultos"], "gender": "unisex", "recipients": ["amigo"], "occasions": ["cumpleanos"], "marketing_hook": "core", "seo_title": "...", "meta_description": "...", "h1_title": "...", "short_description": "80+ palabras", "expert_opinion": "100+ palabras", "pros": ["..."], "cons": ["..."], "full_description": "600+ palabras con H2", "who_is_for": "80+ palabras", "faqs": [{{"q": "...", "a": "..."}}], "verdict": "50+ palabras", "slug": "..."}}]

SOLO JSON."""

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.4, "maxOutputTokens": 8192}}, timeout=60)

gemini_text = response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
json_match = re.search(r'\[[\s\S]*\]', gemini_text)
results = json.loads(json_match.group())
c = results[0]

print(f"   OK! category={c.get('category')}, q={c.get('q')}, ages={c.get('age')}")

# Construir payload
product = {
    "asin": raw_product['asin'], "url": raw_product['url'], "image": raw_product['image'], "source": "test_prod",
    "title": c.get('h1_title', raw_product['title']), "original_title": raw_product['title'],
    "h1_title": c.get('h1_title', ''), "optimized_title": c.get('h1_title', ''), "marketing_title": c.get('h1_title', ''),
    "price": raw_product['price'], "rating": raw_product['rating'], "review_count": raw_product['reviews_count'],
    "category": c.get('category', 'Tech'), "gemini_category": c.get('category', 'Tech'),
    "target_gender": c.get('gender', 'unisex'), "gift_quality": c.get('q', 5), "giftia_score": c.get('giftia_score', 4.0),
    "seo_title": c.get('seo_title', ''), "meta_description": c.get('meta_description', ''),
    "short_description": c.get('short_description', ''), "expert_opinion": c.get('expert_opinion', ''),
    "pros": c.get('pros', []), "cons": c.get('cons', []), "full_description": c.get('full_description', ''),
    "who_is_for": c.get('who_is_for', ''), "faqs": c.get('faqs', []), "verdict": c.get('verdict', ''),
    "seo_slug": c.get('slug', ''), "ages": c.get('age', ['adultos']), "recipients": c.get('recipients', ['amigo']),
    "occasions": c.get('occasions', ['cumpleanos']), "marketing_hook": c.get('marketing_hook', 'wildcard'),
    "processed_at": datetime.now().isoformat()
}

# Enviar a WordPress
print(f"\n3. Enviando a WordPress...")
headers = {'Content-Type': 'application/json', 'X-GIFTIA-TOKEN': WP_TOKEN, 'User-Agent': 'GiftiaProdTest/1.0'}
wp_response = requests.post(WP_API_URL, data=json.dumps(product, ensure_ascii=False).encode('utf-8'), headers=headers, timeout=30)

print(f"   Status: {wp_response.status_code}")

# Verificar
post_id_match = re.search(r'"post_id"[:\s]*"?(\d+)"?', wp_response.text)
if post_id_match:
    post_id = post_id_match.group(1)
    print(f"\n4. Verificando post {post_id}...")
    
    verify = requests.get(f"https://giftia.es/wp-json/wp/v2/gf_gift/{post_id}")
    if verify.status_code == 200:
        data = verify.json()
        meta = data.get('meta', {})
        
        checks = {
            'gf_category': bool(data.get('gf_category')),
            'gf_age': bool(data.get('gf_age')),
            'gf_recipient': bool(data.get('gf_recipient')),
            'gf_occasion': bool(data.get('gf_occasion')),
            '_gf_seo_title': bool(meta.get('_gf_seo_title')),
            '_gf_short_description': bool(meta.get('_gf_short_description')),
            '_gf_gift_quality': bool(meta.get('_gf_gift_quality')),
        }
        
        for k, v in checks.items():
            print(f"   {k}: {'OK' if v else 'FALTA'}")
        
        success = sum(checks.values()) / len(checks) * 100
        print(f"\n   SUCCESS RATE: {success:.0f}%")
        
        if success >= 80:
            print(f"\n   RESULTADO: EXITO - Producto listo en https://giftia.es/regalo/{data.get('slug', '')}/")
        else:
            print(f"\n   RESULTADO: PARCIAL - Revisar campos faltantes")
else:
    print(f"   Response: {wp_response.text[:300]}")

print("\n" + "="*70)
