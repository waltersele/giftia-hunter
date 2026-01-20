#!/usr/bin/env python3
"""Test que el affiliate link se guarda correctamente con GIFTIA-21"""
import json
import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GEMINI_API_KEY')
WP_API_URL = os.getenv('WP_API_URL')
WP_TOKEN = os.getenv('WP_API_TOKEN')
AMAZON_TAG = os.getenv('AMAZON_TAG', 'GIFTIA-21')

print(f"AMAZON_TAG: {AMAZON_TAG}")
print(f"WP_API_URL: {WP_API_URL}")

# Tomar un producto de la lista
with open('productos_a_reprocesar.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

# Usar el segundo producto (el primero ya se procesó)
test_product = products[5]  # Un producto más adelante
post_id = test_product['id']
title = test_product['title']

print(f"\nTest producto: ID={post_id}, Title={title[:50]}...")

# 1. Obtener detalles actuales
print("\n1. Obteniendo datos actuales...")
response = requests.get(
    f"https://giftia.es/wp-json/wp/v2/gf_gift/{post_id}",
    timeout=30
)
details = response.json()
meta = details.get('meta', {})

affiliate_url_antes = meta.get('_gf_affiliate_url', '')
print(f"   Affiliate URL ANTES: {affiliate_url_antes[:80] if affiliate_url_antes else 'VACIO'}...")

# Extraer ASIN
asin = meta.get('_gf_asin', '')
if not asin and affiliate_url_antes:
    match = re.search(r'/dp/([A-Z0-9]{10})', affiliate_url_antes)
    if match:
        asin = match.group(1)
print(f"   ASIN: {asin}")

# 2. Asegurar affiliate URL con tag correcto
if affiliate_url_antes and 'tag=' not in affiliate_url_antes:
    affiliate_url = f"{affiliate_url_antes}{'&' if '?' in affiliate_url_antes else '?'}tag={AMAZON_TAG}"
elif affiliate_url_antes and AMAZON_TAG not in affiliate_url_antes:
    affiliate_url = re.sub(r'tag=[^&]+', f'tag={AMAZON_TAG}', affiliate_url_antes)
elif not affiliate_url_antes and asin:
    affiliate_url = f"https://www.amazon.es/dp/{asin}?tag={AMAZON_TAG}"
else:
    affiliate_url = affiliate_url_antes

print(f"   Affiliate URL NUEVO: {affiliate_url}")

# 3. Clasificar con Gemini (simplificado)
print("\n2. Clasificando con Gemini...")
prompt = f"""Clasifica este producto como regalo:
PRODUCTO: {title}
Responde JSON con: category, age (lista), occasions (lista), recipients (lista), seo_title, meta_description, short_description
SOLO JSON."""

response = requests.post(
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}",
    json={
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 2048}
    },
    timeout=60
)

text = response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
json_match = re.search(r'\{[\s\S]*\}', text)
classification = json.loads(json_match.group()) if json_match else {}
print(f"   Gemini: category={classification.get('category')}")

# 4. Enviar a WordPress
print("\n3. Enviando a WordPress...")
product = {
    "asin": asin,
    "affiliate_url": affiliate_url,  # Campo correcto!
    "image_url": meta.get('_gf_image_url', ''),
    "source": "reprocess-test",
    "title": title,
    "original_title": title,
    "price": str(meta.get('_gf_current_price', 0)),
    "category": classification.get('category', 'Tech'),
    "ages": classification.get('age', ['adultos']),
    "occasions": classification.get('occasions', ['cumpleanos']),
    "recipients": classification.get('recipients', ['amigo']),
    "seo_title": classification.get('seo_title', title[:60]),
    "meta_description": classification.get('meta_description', ''),
    "short_description": classification.get('short_description', ''),
}

headers = {
    'Content-Type': 'application/json',
    'X-GIFTIA-TOKEN': WP_TOKEN
}

response = requests.post(
    WP_API_URL,
    data=json.dumps(product, ensure_ascii=False).encode('utf-8'),
    headers=headers,
    timeout=30
)

print(f"   Response: {response.status_code}")
print(f"   Body: {response.text[:200]}")

# 5. Verificar resultado
print("\n4. Verificando resultado...")
response = requests.get(
    f"https://giftia.es/wp-json/wp/v2/gf_gift/{post_id}",
    timeout=30
)
details = response.json()
meta = details.get('meta', {})

affiliate_url_despues = meta.get('_gf_affiliate_url', '')
print(f"   Affiliate URL DESPUES: {affiliate_url_despues}")

if AMAZON_TAG in affiliate_url_despues:
    print(f"\n✅ EXITO! El tag {AMAZON_TAG} está en el affiliate URL")
else:
    print(f"\n❌ ERROR! El tag {AMAZON_TAG} NO está en el affiliate URL")
