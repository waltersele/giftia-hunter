#!/usr/bin/env python3
"""
Test de envío a WordPress - verifica que api-ingest.php recibe y guarda correctamente
"""
import json
import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

print("="*60)
print("TEST WORDPRESS - Envío de producto completo")
print("="*60)

WP_API_URL = os.getenv("WP_API_URL")
WP_TOKEN = os.getenv("WP_API_TOKEN")

print(f"\n📡 Endpoint: {WP_API_URL}")
print(f"🔑 Token: {WP_TOKEN[:10]}...")

# Producto de prueba con TODOS los campos v51
test_product = {
    # Identificadores Amazon
    "asin": "TEST123456",
    "url": "https://amazon.es/dp/TEST123456?tag=GIFTIA-21",
    "image": "https://m.media-amazon.com/images/I/71o8Q5XJS5L._AC_SL1500_.jpg",
    "source": "hunter_batch",
    
    # Títulos
    "title": "Auriculares Sony WH-1000XM5 Test",
    "original_title": "Sony WH-1000XM5 Auriculares Inalámbricos",
    "h1_title": "Tu Oasis de Sonido: Sony WH-1000XM5",
    "optimized_title": "Tu Oasis de Sonido: Sony WH-1000XM5",
    "marketing_title": "Tu Oasis de Sonido: Sony WH-1000XM5",
    
    # Precio y ratings
    "price": "299.99",
    "rating": "4.6",
    "review_count": "15234",
    
    # Clasificación Gemini
    "category": "Música",
    "gemini_category": "Música",
    "target_gender": "unisex",
    "gift_quality": 8,
    "giftia_score": 4.5,
    "classification_source": "gemini",
    "vibes": ["Música"],
    "gift_score": 80,
    
    # SEO v51
    "seo_title": "Sony WH-1000XM5: Auriculares con Cancelación de Ruido | Giftia",
    "meta_description": "Los mejores auriculares con cancelación de ruido del mercado. Regalo perfecto para amantes de la música. Análisis y precio en Giftia.",
    "short_description": "Sumérgete en la música con los Sony WH-1000XM5, los auriculares con la mejor cancelación de ruido del mercado. Perfectos para viajes, trabajo o relajarse en casa. Un regalo que transforma el día a día de quien lo recibe.",
    "expert_opinion": "Después de probar decenas de auriculares, los Sony WH-1000XM5 siguen siendo mi recomendación número uno. La cancelación de ruido es simplemente la mejor del mercado, y la calidad de sonido rivaliza con auriculares mucho más caros. Son cómodos para sesiones largas y la batería dura semanas de uso normal.",
    "pros": ["Cancelación de ruido líder", "Batería de 30 horas", "Muy cómodos", "Sonido excepcional", "Diseño elegante"],
    "cons": ["Precio elevado", "No son plegables"],
    "full_description": "## Por qué este regalo es especial\n\nLos Sony WH-1000XM5 representan la cúspide de la tecnología de auriculares inalámbricos. Su cancelación de ruido adaptativa te sumerge en tu música.\n\n## Características técnicas\n\nDrivers de 40mm, Bluetooth 5.2, batería 30h.\n\n## Para quién es ideal\n\nMelómanos, viajeros frecuentes, teletrabajadores.",
    "who_is_for": "Perfecto para amantes de la música que valoran cada matiz. Ideal para viajeros frecuentes que necesitan paz. Excelente para profesionales remotos que requieren concentración.",
    "faqs": [
        {"q": "¿Son buenos para llamadas?", "a": "Excelentes, con micrófonos con cancelación de ruido."},
        {"q": "¿Cuánto dura la batería?", "a": "Hasta 30 horas con cancelación activa."}
    ],
    "verdict": "Un regalo que se recuerda. Perfecto para quien valora su espacio sonoro. Puntuación Giftia: 4.5/5",
    "seo_slug": "auriculares-sony-wh1000xm5-test",
    "gift_headline": "El regalo perfecto para amantes del silencio y la música",
    "why_selected": "Seleccionado por ser el mejor en su categoría",
    
    # Taxonomías
    "ages": ["jovenes", "adultos"],
    "recipients": ["pareja", "amigo", "yo"],
    "occasions": ["cumpleanos", "navidad", "aniversario"],
    "marketing_hook": "hedonism",
    
    # Metadatos
    "processed_at": datetime.now().isoformat()
}

print(f"\n📦 Producto de prueba:")
print(f"   ASIN: {test_product['asin']}")
print(f"   Título: {test_product['title']}")
print(f"   Categoría: {test_product['category']}")
print(f"   Ages: {test_product['ages']}")
print(f"   Recipients: {test_product['recipients']}")
print(f"   Occasions: {test_product['occasions']}")

print(f"\n📤 Enviando a WordPress...")

headers = {
    'Content-Type': 'application/json',
    'X-GIFTIA-TOKEN': WP_TOKEN,
    'User-Agent': 'GiftiaTestScript/1.0'
}

try:
    response = requests.post(
        WP_API_URL,
        data=json.dumps(test_product, ensure_ascii=False).encode('utf-8'),
        headers=headers,
        timeout=30
    )
    
    print(f"\n📥 Response status: {response.status_code}")
    print(f"\n--- RESPUESTA WORDPRESS ---")
    print(response.text[:2000])
    
    if response.status_code == 200:
        try:
            result = response.json()
            print(f"\n✅ Producto creado/actualizado:")
            print(f"   Post ID: {result.get('post_id', result.get('id', 'N/A'))}")
            print(f"   URL: {result.get('url', result.get('permalink', 'N/A'))}")
        except:
            print("(respuesta no es JSON válido)")
    else:
        print(f"\n❌ Error: {response.status_code}")
        
except Exception as e:
    print(f"\n❌ Error de conexión: {e}")

print("\n" + "="*60)
print("TEST COMPLETADO")
print("="*60)
