#!/usr/bin/env python3
"""
Test del flujo batch completo de process_queue.py
Simula exactamente lo que hace classify_batch_with_gemini()
"""
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("TEST BATCH - Flujo completo process_queue.py")
print("="*60)

# 1. Cargar schema
with open('giftia_schema.json', 'r', encoding='utf-8') as f:
    SCHEMA = json.load(f)

VALID_CATEGORIES = list(SCHEMA.get('categories', {}).keys())
VALID_AGES = list(SCHEMA.get('ages', {}).keys()) if isinstance(SCHEMA.get('ages'), dict) else SCHEMA.get('ages', [])
VALID_OCCASIONS = list(SCHEMA.get('occasions', {}).keys()) if isinstance(SCHEMA.get('occasions'), dict) else SCHEMA.get('occasions', [])
VALID_RECIPIENTS = list(SCHEMA.get('recipients', {}).keys()) if isinstance(SCHEMA.get('recipients'), dict) else SCHEMA.get('recipients', [])

print(f"\n📦 Schema cargado:")
print(f"   Categorías ({len(VALID_CATEGORIES)}): {VALID_CATEGORIES}")
print(f"   Edades ({len(VALID_AGES)}): {VALID_AGES}")
print(f"   Ocasiones ({len(VALID_OCCASIONS)}): {VALID_OCCASIONS[:5]}...")
print(f"   Destinatarios ({len(VALID_RECIPIENTS)}): {VALID_RECIPIENTS}")

# 2. API Key
API_KEY = os.getenv('GEMINI_API_KEY')
print(f"\n🔑 API Key: {API_KEY[:20]}..." if API_KEY else "❌ API Key no encontrada")

# 3. Producto de prueba
test_product = {
    "title": "Sony WH-1000XM5 Auriculares Inalambricos con Cancelacion de Ruido",
    "price": "299.99",
    "rating": "4.6",
    "reviews_count": "15234"
}

# 4. Construir prompt EXACTO como process_queue.py
products_text = f"\n1. {test_product['title'][:150]}\n   Precio: {test_product['price']}€ | Rating: {test_product['rating']} | Reviews: {test_product['reviews_count']}"

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
    "hook": "core",
    "seo_title": "Titulo SEO (50-60 chars)",
    "meta_description": "Meta description (150-160 chars)",
    "h1_title": "Titulo H1 emocional (40-70 chars)",
    "short_description": "Descripcion corta 80+ palabras",
    "expert_opinion": "Opinion experto 100+ palabras",
    "pros": ["Pro 1", "Pro 2", "Pro 3"],
    "cons": ["Contra 1", "Contra 2"],
    "full_description": "Descripcion larga con H2s, 600+ palabras",
    "who_is_for": "Para quien es, 80+ palabras",
    "faqs": [{{"q": "Pregunta 1", "a": "Respuesta 1"}}],
    "verdict": "Veredicto final 50+ palabras",
    "slug": "url-slug-amigable"
  }}
]

SOLO JSON VÁLIDO. Sin explicaciones. Sin markdown."""

print(f"\n📤 Prompt ({len(prompt)} chars)")

# 5. Llamar a Gemini
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

response = requests.post(url, json={
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {
        "temperature": 0.4,
        "maxOutputTokens": 8192
    }
})

print(f"\n📥 Response status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
    
    print(f"\n--- RESPUESTA GEMINI ({len(text)} chars) ---")
    print(text[:2000])
    if len(text) > 2000:
        print(f"... (+{len(text)-2000} chars)")
    
    # Parsear JSON
    import re
    json_match = re.search(r'\[[\s\S]*\]', text)
    if json_match:
        try:
            results = json.loads(json_match.group())
            print(f"\n--- RESULTADO PARSEADO ---")
            result = results[0] if results else {}
            
            # Verificar campos críticos
            print(f"\n✓ ok: {result.get('ok')}")
            print(f"✓ q (gift_quality): {result.get('q')}")
            print(f"✓ category: {result.get('category')} {'✅' if result.get('category') in VALID_CATEGORIES else '❌ INVÁLIDA'}")
            print(f"✓ age: {result.get('age')}")
            print(f"✓ gender: {result.get('gender')}")
            print(f"✓ occasions: {result.get('occasions', [])[:3]}...")
            print(f"✓ recipients: {result.get('recipients', [])[:3]}...")
            print(f"✓ hook: {result.get('hook')}")
            
            # SEO fields
            print(f"\n--- CAMPOS SEO ---")
            print(f"✓ seo_title: {result.get('seo_title', '')[:60]}...")
            print(f"✓ h1_title: {result.get('h1_title', '')[:60]}...")
            print(f"✓ short_description: {len(result.get('short_description', ''))} chars")
            print(f"✓ expert_opinion: {len(result.get('expert_opinion', ''))} chars")
            print(f"✓ full_description: {len(result.get('full_description', ''))} chars")
            print(f"✓ who_is_for: {len(result.get('who_is_for', ''))} chars")
            print(f"✓ pros: {result.get('pros', [])}")
            print(f"✓ cons: {result.get('cons', [])}")
            print(f"✓ faqs: {len(result.get('faqs', []))} preguntas")
            print(f"✓ verdict: {len(result.get('verdict', ''))} chars")
            print(f"✓ slug: {result.get('slug')}")
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
    else:
        print("❌ No se encontró array JSON en respuesta")
else:
    print(f"❌ Error API: {response.text}")

print("\n" + "="*60)
print("TEST COMPLETADO")
print("="*60)
