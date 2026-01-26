#!/usr/bin/env python3
"""
TEST END-TO-END COMPLETO
Simula el flujo real: Gemini clasifica → envía a WordPress
"""
import json
import os
import re
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

print("="*70)
print("TEST END-TO-END: Gemini → WordPress")
print("="*70)

# Configuración
API_KEY = os.getenv('GEMINI_API_KEY')
WP_API_URL = os.getenv('WP_API_URL')
WP_TOKEN = os.getenv('WP_API_TOKEN')

print(f"\n📡 WordPress: {WP_API_URL}")
print(f"🔑 Gemini: {API_KEY[:20]}...")

# Cargar schema
with open('giftia_schema.json', 'r', encoding='utf-8') as f:
    SCHEMA = json.load(f)

VALID_CATEGORIES = list(SCHEMA.get('categories', {}).keys())
VALID_AGES = list(SCHEMA.get('ages', {}).keys()) if isinstance(SCHEMA.get('ages'), dict) else SCHEMA.get('ages', [])
VALID_OCCASIONS = list(SCHEMA.get('occasions', {}).keys()) if isinstance(SCHEMA.get('occasions'), dict) else SCHEMA.get('occasions', [])
VALID_RECIPIENTS = list(SCHEMA.get('recipients', {}).keys()) if isinstance(SCHEMA.get('recipients'), dict) else SCHEMA.get('recipients', [])

# Producto de prueba (simulando lo que vendría de Hunter)
raw_product = {
    "asin": "B0E2ETEST1",  # Exactamente 10 chars
    "title": "Kindle Paperwhite 16GB - Pantalla de 6.8 pulgadas con luz cálida ajustable",
    "price": "159.99",
    "rating": "4.7",
    "reviews_count": "45678",
    "url": "https://amazon.es/dp/B09TMN58KL?tag=GIFTIA-21",
    "image": "https://m.media-amazon.com/images/I/61mOT8xk1GL._AC_SL1000_.jpg"
}

print(f"\n📦 PASO 1: Producto de prueba")
print(f"   ASIN: {raw_product['asin']}")
print(f"   Título: {raw_product['title'][:50]}...")
print(f"   Precio: {raw_product['price']}€")

# PASO 2: Clasificar con Gemini (igual que process_queue.py)
print(f"\n🧠 PASO 2: Clasificando con Gemini...")

products_text = f"\n1. {raw_product['title'][:150]}\n   Precio: {raw_product['price']}€ | Rating: {raw_product['rating']} | Reviews: {raw_product['reviews_count']}"

prompt = f"""Eres el CURADOR JEFE y EXPERTO SEO de Giftia.es. Tu trabajo es:
1. Seleccionar regalos que EMOCIONEN
2. Crear fichas de producto optimizadas para posicionar en Google

PRODUCTOS A EVALUAR:{products_text}

CATEGORÍAS VÁLIDAS: {', '.join(VALID_CATEGORIES)}
EDADES VÁLIDAS: {', '.join(VALID_AGES)}
OCASIONES VÁLIDAS: {', '.join(VALID_OCCASIONS)}
DESTINATARIOS VÁLIDOS: {', '.join(VALID_RECIPIENTS)}

Responde con un array JSON con un objeto por producto:
[
  {{
    "ok": true,
    "q": 8,
    "giftia_score": 4.5,
    "category": "Tech",
    "age": ["adultos", "jovenes"],
    "gender": "unisex",
    "recipients": ["amigo", "pareja"],
    "occasions": ["cumpleanos", "navidad"],
    "marketing_hook": "core",
    "seo_title": "Titulo SEO (50-60 chars)",
    "meta_description": "Meta description (150-160 chars)",
    "h1_title": "Titulo H1 emocional (40-70 chars)",
    "short_description": "Descripcion corta 80+ palabras con emocion y beneficios",
    "expert_opinion": "Opinion experto 100+ palabras con experiencia personal",
    "pros": ["Pro 1", "Pro 2", "Pro 3", "Pro 4", "Pro 5"],
    "cons": ["Contra 1", "Contra 2"],
    "full_description": "Descripcion larga con H2s, 600+ palabras, estructura SEO",
    "who_is_for": "Para quien es, 80+ palabras con perfiles concretos",
    "faqs": [{{"q": "Pregunta 1", "a": "Respuesta 1"}}, {{"q": "Pregunta 2", "a": "Respuesta 2"}}],
    "verdict": "Veredicto final 50+ palabras con puntuacion",
    "slug": "url-slug-amigable"
  }}
]

SOLO JSON VÁLIDO. Sin explicaciones. Sin markdown."""

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
response = requests.post(url, json={
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"temperature": 0.4, "maxOutputTokens": 8192}
})

if response.status_code != 200:
    print(f"❌ Error Gemini: {response.status_code}")
    exit(1)

gemini_text = response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
json_match = re.search(r'\[[\s\S]*\]', gemini_text)

if not json_match:
    print(f"❌ No se encontró JSON en respuesta Gemini")
    print(gemini_text[:500])
    exit(1)

results = json.loads(json_match.group())
classification = results[0]

print(f"   ✅ Clasificado:")
print(f"      category: {classification.get('category')}")
print(f"      age: {classification.get('age')}")
print(f"      recipients: {classification.get('recipients')}")
print(f"      occasions: {classification.get('occasions')}")
print(f"      gift_quality: {classification.get('q')}")

# PASO 3: Construir payload para WordPress (igual que process_queue.py)
print(f"\n📋 PASO 3: Construyendo payload para WordPress...")

product = {
    # Identificadores
    "asin": raw_product['asin'],
    "url": raw_product['url'],
    "image": raw_product['image'],
    "source": "test_e2e",
    
    # Títulos
    "title": classification.get('h1_title', raw_product['title']),
    "original_title": raw_product['title'],
    "h1_title": classification.get('h1_title', ''),
    "optimized_title": classification.get('h1_title', ''),
    "marketing_title": classification.get('h1_title', ''),
    
    # Precio y ratings
    "price": raw_product['price'],
    "rating": raw_product['rating'],
    "review_count": raw_product['reviews_count'],
    
    # Clasificación
    "category": classification.get('category', 'Tech'),
    "gemini_category": classification.get('category', 'Tech'),
    "target_gender": classification.get('gender', 'unisex'),
    "gift_quality": classification.get('q', 5),
    "giftia_score": classification.get('giftia_score', 4.0),
    "classification_source": "gemini",
    
    # SEO v51
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
    
    # Taxonomías
    "ages": classification.get('age', ['adultos']),
    "recipients": classification.get('recipients', ['amigo']),
    "occasions": classification.get('occasions', ['cumpleanos']),
    "marketing_hook": classification.get('marketing_hook', 'wildcard'),
    
    # Metadatos
    "processed_at": datetime.now().isoformat()
}

print(f"   Campos SEO: seo_title={len(product['seo_title'])}chars, short_desc={len(product['short_description'])}chars")
print(f"   Taxonomías: ages={product['ages']}, recipients={product['recipients'][:2]}...")

# PASO 4: Enviar a WordPress
print(f"\n📤 PASO 4: Enviando a WordPress...")

headers = {
    'Content-Type': 'application/json',
    'X-GIFTIA-TOKEN': WP_TOKEN,
    'User-Agent': 'GiftiaE2ETest/1.0'
}

wp_response = requests.post(
    WP_API_URL,
    data=json.dumps(product, ensure_ascii=False).encode('utf-8'),
    headers=headers,
    timeout=30
)

print(f"   Status: {wp_response.status_code}")
print(f"   Response: {wp_response.text[:300]}")

# PASO 5: Verificar producto en WordPress
if 'post_id' in wp_response.text:
    post_id = re.search(r'"post_id"[:\s]*"?(\d+)"?', wp_response.text)
    if post_id:
        post_id = post_id.group(1)
        print(f"\n✅ PASO 5: Verificando producto {post_id}...")
        
        verify = requests.get(f"https://giftia.es/wp-json/wp/v2/gf_gift/{post_id}")
        if verify.status_code == 200:
            data = verify.json()
            print(f"\n   📊 RESULTADO FINAL:")
            print(f"   ├── Título: {data.get('title', {}).get('rendered', 'N/A')[:50]}...")
            print(f"   ├── gf_category: {data.get('gf_category', [])} {'✅' if data.get('gf_category') else '❌'}")
            print(f"   ├── gf_age: {data.get('gf_age', [])} {'✅' if data.get('gf_age') else '❌'}")
            print(f"   ├── gf_recipient: {data.get('gf_recipient', [])} {'✅' if data.get('gf_recipient') else '❌'}")
            print(f"   ├── gf_occasion: {data.get('gf_occasion', [])} {'✅' if data.get('gf_occasion') else '❌'}")
            
            meta = data.get('meta', {})
            print(f"   ├── _gf_seo_title: {meta.get('_gf_seo_title', '')[:40]}... {'✅' if meta.get('_gf_seo_title') else '❌'}")
            print(f"   ├── _gf_short_description: {len(meta.get('_gf_short_description', ''))} chars {'✅' if meta.get('_gf_short_description') else '❌'}")
            print(f"   ├── _gf_gift_quality: {meta.get('_gf_gift_quality', 0)} {'✅' if meta.get('_gf_gift_quality') else '❌'}")
            print(f"   ├── _gf_giftia_score: {meta.get('_gf_giftia_score', 0)} {'✅' if meta.get('_gf_giftia_score') else '❌'}")
            print(f"   └── _gf_hook: {meta.get('_gf_hook', '')} {'✅' if meta.get('_gf_hook') else '❌'}")
            
            # Contar éxitos
            checks = [
                bool(data.get('gf_category')),
                bool(data.get('gf_age')),
                bool(data.get('gf_recipient')),
                bool(data.get('gf_occasion')),
                bool(meta.get('_gf_seo_title')),
                bool(meta.get('_gf_short_description')),
                bool(meta.get('_gf_gift_quality')),
            ]
            success_rate = sum(checks) / len(checks) * 100
            
            print(f"\n   🎯 Success rate: {success_rate:.0f}% ({sum(checks)}/{len(checks)} campos)")
            
            if success_rate >= 80:
                print(f"\n🎉 ¡TEST EXITOSO! El flujo completo funciona correctamente.")
            else:
                print(f"\n⚠️ Test parcialmente exitoso. Revisar campos faltantes.")

print("\n" + "="*70)
print("TEST END-TO-END COMPLETADO")
print("="*70)
