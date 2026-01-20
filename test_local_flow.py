#!/usr/bin/env python3
"""
TEST LOCAL - Prueba completa del flujo Gemini -> clasificacion
Sin enviar nada a WordPress
"""

import os
import json
import re
import requests
from dotenv import load_dotenv

# Cargar .env desde el directorio del script
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Fallback: leer directo del archivo
if not GEMINI_API_KEY:
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('GEMINI_API_KEY='):
                    GEMINI_API_KEY = line.split('=', 1)[1].strip()
                    break
    except:
        pass

print("=" * 60)
print("TEST LOCAL - Flujo Gemini")
print("=" * 60)

# 1. Verificar API Key
if not GEMINI_API_KEY:
    print("ERROR: No hay GEMINI_API_KEY en .env")
    exit(1)
    
print(f"API Key: {GEMINI_API_KEY[:20]}...")

# 2. Cargar schema
schema_path = os.path.join(os.path.dirname(__file__), "giftia_schema.json")
with open(schema_path, 'r', encoding='utf-8') as f:
    SCHEMA = json.load(f)

VALID_CATEGORIES = list(SCHEMA.get('categories', {}).keys())
VALID_AGES = list(SCHEMA.get('ages', {}).keys())
VALID_OCCASIONS = list(SCHEMA.get('occasions', {}).keys())
VALID_RECIPIENTS = list(SCHEMA.get('recipients', {}).keys())

print(f"\nSchema cargado:")
print(f"  Categorias: {VALID_CATEGORIES}")
print(f"  Edades: {VALID_AGES}")
print(f"  Ocasiones: {VALID_OCCASIONS[:5]}...")

# 3. Producto de prueba
test_product = {
    "title": "Sony WH-1000XM5 Auriculares Inalambricos con Cancelacion de Ruido",
    "price": "299.99",
    "rating": "4.6",
    "reviews_count": "15234",
    "asin": "B0BYL3R4ZN"
}

print(f"\nProducto de prueba:")
print(f"  {test_product['title']}")
print(f"  Precio: {test_product['price']} EUR")
print(f"  Rating: {test_product['rating']} ({test_product['reviews_count']} reviews)")

# 4. Construir prompt simplificado para clasificacion
prompt = f"""Eres el curador de Giftia.es. Clasifica este producto de Amazon:

PRODUCTO:
- Titulo: {test_product['title']}
- Precio: {test_product['price']} EUR
- Rating: {test_product['rating']}
- Reviews: {test_product['reviews_count']}

CLASIFICACION REQUERIDA - Usa EXACTAMENTE estos valores:

1. category: {', '.join(VALID_CATEGORIES)}
2. age (lista): {', '.join(VALID_AGES)}
3. occasions (lista): {', '.join(VALID_OCCASIONS)}
4. recipients (lista): {', '.join(VALID_RECIPIENTS)}
5. gender: unisex, male, female, kids
6. gift_quality: 1-10 (calidad como regalo)
7. is_good_gift: true/false

RESPONDE SOLO JSON:
{{
  "is_good_gift": true,
  "gift_quality": 8,
  "category": "Tech",
  "age": ["jovenes", "adultos"],
  "gender": "unisex",
  "occasions": ["cumpleanos", "navidad"],
  "recipients": ["pareja", "amigo"],
  "seo_title": "Titulo SEO 50-60 chars",
  "h1_title": "Titulo H1 persuasivo",
  "short_description": "Descripcion corta 80-120 palabras..."
}}

SOLO JSON VALIDO. Sin explicaciones."""

print(f"\nPrompt enviado a Gemini ({len(prompt)} chars)...")

# 5. Llamar a Gemini
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {
        "temperature": 0.2,
        "maxOutputTokens": 2048
    }
}

try:
    response = requests.post(url, json=payload, timeout=30)
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        if "candidates" in data and data["candidates"]:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            print(f"\n--- RESPUESTA GEMINI ({len(text)} chars) ---")
            print(text[:2000])
            
            # Parsear JSON
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    print(f"\n--- JSON PARSEADO ---")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                    
                    # Verificar campos
                    print(f"\n--- VERIFICACION ---")
                    cat = result.get("category", "N/A")
                    print(f"  category: {cat} {'OK' if cat in VALID_CATEGORIES else 'INVALIDO'}")
                    
                    ages = result.get("age", [])
                    valid_ages = [a for a in ages if a in VALID_AGES]
                    print(f"  ages: {ages} -> Validos: {valid_ages}")
                    
                    occs = result.get("occasions", [])
                    valid_occs = [o for o in occs if o in VALID_OCCASIONS]
                    print(f"  occasions: {occs} -> Validos: {valid_occs}")
                    
                    print(f"  gift_quality: {result.get('gift_quality', 'N/A')}")
                    print(f"  is_good_gift: {result.get('is_good_gift', 'N/A')}")
                    
                except json.JSONDecodeError as e:
                    print(f"ERROR parseando JSON: {e}")
                    print(f"Texto: {json_match.group()[:500]}")
            else:
                print("ERROR: No se encontro JSON en la respuesta")
        else:
            print("ERROR: Sin candidates en respuesta")
            print(data)
    else:
        print(f"ERROR HTTP: {response.status_code}")
        print(response.text[:500])
        
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETADO")
